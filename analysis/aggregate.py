"""집계·Top10 랭킹·대시보드 데이터(data.js) 생성.

산출:
- dashboard/data.js : const DATA = {yearly, topics, top10, before_after, quotes, paju, meta}
- 콘솔: Top10 표 + sanity check
랭킹 산식(문서에 명시): score = 정규화빈도(NEG+SUGGEST) x 불만강도 x 난이도가중치
  - 난이도가중치: OPS=1.0(즉시 실행 가능할수록 재개 설계에서 우선) / BUDGET=0.7 / POLICY=0.4
"""
import json
import re

import pandas as pd

DIFF_W = {"OPS": 1.0, "BUDGET": 0.7, "POLICY": 0.4, "NA": 0.0}
TOPIC_KO = {
    "RESERVE": "예약·신청", "ACCESS": "교통·집결·접근성", "GUIDE": "해설·안내 품질",
    "TIME": "시간 배분", "COURSE": "코스·콘텐츠", "FACILITY": "시설·편의",
    "SOUVENIR": "기념품·기록", "CROWD": "인원·질서·통제", "REOPEN": "재개·대상 확대",
    "EMOTION": "정서·의미", "INFO": "사전 안내·정보", "BALANCE": "해설 균형·표현", "ETC": "기타",
}
NAME_MASK = re.compile(r"([가-힣]{2,4})(\s?)(상병|일병|병장|이병|하사|중사|상사|대위|중위|소위|해설사)")


def mask(text: str) -> str:
    """인용 안전용 실명 마스킹 (pii_flag 행은 애초에 인용 제외지만 이중 방어)."""
    return NAME_MASK.sub(lambda m: "○" * len(m.group(1)) + m.group(2) + m.group(3), text)


def run(src: str = "data/processed/classified.csv",
        agg_src: str = "data/raw/panmunjom_aggregate.csv",
        paju_src: str = "data/raw/paju_dmz_tour_usage.csv",
        dst: str = "dashboard/data.js") -> dict:
    df = pd.read_csv(src, encoding="utf-8-sig")
    sub = df[df["is_substantive"]].copy()

    # ── 1. 연도별 응답량 (전체 4,517 기준 — 2024 공백 시각화)
    yearly = []
    for y in [2021, 2022, 2023, 2024, 2025]:
        yearly.append({"year": y, "n": int((df["year"] == y).sum())})

    # ── 2. topic × sentiment 매트릭스
    topics = []
    for t, g in sub.groupby("topic"):
        if t == "ETC":
            continue
        topics.append({
            "code": t, "name": TOPIC_KO[t], "n": len(g),
            "pos": int((g["sentiment"] == "POS").sum()),
            "neg": int((g["sentiment"] == "NEG").sum()),
            "suggest": int((g["sentiment"] == "SUGGEST").sum()),
        })
    topics.sort(key=lambda x: -x["n"])

    # ── 3. Top10 개선 과제 랭킹 (EMOTION 등 순수 소감 topic 제외)
    rank_rows = []
    demand = sub[sub["sentiment"].isin(["NEG", "SUGGEST"])]
    n_demand = len(demand)
    for t, g in demand.groupby("topic"):
        if t in ("EMOTION", "ETC"):
            continue
        freq = len(g) / n_demand
        neg_ratio = (g["sentiment"] == "NEG").sum() / len(g) * 0.5 + 0.5  # 0.5~1.0
        diff_w = g["difficulty"].map(DIFF_W).mean()
        rank_rows.append({
            "code": t, "name": TOPIC_KO[t], "n": len(g),
            "freq": round(freq, 4), "neg_ratio": round(neg_ratio, 3),
            "diff_w": round(diff_w, 3),
            "score": round(freq * neg_ratio * diff_w * 1000, 1),
        })
    top10 = sorted(rank_rows, key=lambda x: -x["score"])[:10]

    # ── 4. 전후 비교: 일반견학기(2021~23) vs 특별견학기(2025)
    def dist(frame):
        d = frame.groupby("topic").size()
        total = d.sum()
        return {k: round(v / total, 4) for k, v in d.items()}
    before_after = {
        "before": dist(sub[sub["year"] <= 2023]),
        "after": dist(sub[sub["year"] == 2025]),
        "n_before": int((sub["year"] <= 2023).sum()),
        "n_after": int((sub["year"] == 2025).sum()),
    }

    # ── 5. 인용 후보 (quote_worthy & ~pii_flag, 마스킹 이중 적용)
    q = sub[sub["quote_worthy"] & ~sub["pii_flag"]].copy()
    q["len"] = q["text"].str.len()
    q = q.sort_values("len", ascending=False).head(24)
    quotes = [{"id": int(r["id"]), "year": int(r["year"]), "topic": r["topic"],
               "text": mask(r["text"])} for _, r in q.iterrows()]

    # ── 6. 파주시 DMZ 관광 수요 (결합 데이터)
    pj = pd.read_csv(paju_src, encoding="utf-8-sig")
    paju = [{"ym": r["통계연월"], "total": int(r["총관광객수"]),
             "domestic": int(r["내국인수"]), "foreign": int(r["외국인수"])}
            for _, r in pj.iterrows()]

    # ── 7. 주별 응답 집계 (통일부 응답 집계 데이터)
    ag = pd.read_csv(agg_src, encoding="utf-8-sig")
    weekly = [{"date": r["기준 일자"], "survey": r["설문 제목"], "n": int(r["설문 응답 수"])}
              for _, r in ag.iterrows()]

    data = {"yearly": yearly, "topics": topics, "top10": top10,
            "before_after": before_after, "quotes": quotes, "paju": paju,
            "weekly": weekly,
            "meta": {"n_total": 4517, "n_substantive": int(len(sub)),
                     "generated": "2026-08-03",
                     "source": "통일부_판문점견학 설문 주관식 응답 결과 외 3종 (data.go.kr)"}}
    with open(dst, "w", encoding="utf-8") as f:
        f.write("const DATA = ")
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write(";\n")

    # sanity
    assert sum(y["n"] for y in yearly) == 4517
    assert all(t["code"] != "ETC" for t in top10)
    print("TOP10:")
    for i, t in enumerate(top10, 1):
        print(f"  {i:2d}. {t['name']:12s} n={t['n']:4d} score={t['score']}")
    print("quotes:", len(quotes), "| topics:", len(topics), "->", dst)
    return data


if __name__ == "__main__":
    import os
    os.makedirs("dashboard", exist_ok=True)
    run()
