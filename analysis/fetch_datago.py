"""data.go.kr 파일데이터 다운로드 (로그인 불필요 체인).

체인: 상세페이지에서 uddi 추출 -> selectFileDataDownload.do 로 atchFileId 획득
      -> cmm/cmm/fileDownload.do 로 실파일 수신.
검증: 2026-08-03, 15150927(판문점 주관식 4,517행)으로 체인 동작 확인.
"""
import json
import re
import sys
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def _get(url: str, referer: str | None = None, data: dict | None = None) -> bytes:
    headers = dict(UA)
    if referer:
        headers["Referer"] = referer
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, headers=headers, data=body)
    return urllib.request.urlopen(req, timeout=60).read()


def download(pk: str, out_path: str) -> int:
    """publicDataPk 기준으로 파일을 내려받아 out_path 저장, 바이트 수 반환."""
    page_url = f"https://www.data.go.kr/data/{pk}/fileData.do"
    page = _get(page_url).decode("utf-8", "ignore")
    m = re.search(rf"fn_fileDataDown\('{pk}',\s*'(uddi:[^']+)'", page)
    if not m:
        raise RuntimeError(f"{pk}: 상세페이지에서 uddi 미발견")
    resp = json.loads(_get(
        "https://www.data.go.kr/tcs/dss/selectFileDataDownload.do",
        referer=page_url,
        data={"publicDataPk": pk, "publicDataDetailPk": m.group(1)},
    ))
    if not resp.get("status"):
        raise RuntimeError(f"{pk}: 다운로드 체크 실패 (status={resp.get('status')})")
    fid = resp["atchFileId"]
    sn = resp.get("fileDetailSn") or "1"
    blob = _get(
        f"https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId={fid}"
        f"&fileDetailSn={sn}&insertDataPrcus=N",
        referer=page_url,
    )
    if blob[:15].lstrip().lower().startswith(b"<!doctype") or blob[:6].lower() == b"<html>":
        raise RuntimeError(f"{pk}: 파일 대신 HTML 수신 ({len(blob)} bytes)")
    with open(out_path, "wb") as f:
        f.write(blob)
    return len(blob)


TARGETS = {
    "15150900": "data/raw/panmunjom_aggregate.csv",   # 통일부_판문점견학 설문 응답 집계 (262행)
    "15150827": "data/raw/panmunjom_surveys.zip",     # 통일부_판문점견학 설문정보 (실물 ZIP: CSV 3개)
    "15153986": "data/raw/paju_dmz_tour_usage.csv",   # 경기도 파주시_DMZ평화관광이용현황
}

if __name__ == "__main__":
    failed = []
    for pk, path in TARGETS.items():
        try:
            print(pk, download(pk, path), "bytes ->", path)
        except Exception as e:  # 재시도 1회
            try:
                print(pk, download(pk, path), "bytes -> (재시도)", path)
            except Exception as e2:
                failed.append((pk, str(e2)))
                print(pk, "FAILED:", e2, file=sys.stderr)
    sys.exit(1 if failed else 0)
