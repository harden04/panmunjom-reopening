"""주관식 응답 전처리: 파생필드·무의미 답변 플래그·개인정보 스크리닝.

원칙: 행을 삭제하지 않는다(4,517행 보존) — 필터는 플래그 컬럼으로만.
산출: data/processed/responses_clean.csv
"""
import re

import pandas as pd

MEANINGLESS = re.compile(
    r"^[\s.,!~^ㅋㅎ♡♥-]*("
    r"없음|없습니다|없어요|없다|무|X|x|굿|good|Good|"
    r"감사합니다|감사|수고하세요|수고하셨습니다|"
    r"좋았습니다|좋았음|좋아요|좋음|만족|만족합니다|매우\s?만족"
    r")[\s.,!~^♡♥-]*$"
)
# 전화번호 / 이메일 / 이름+직급 호칭 패턴 (보수적 — 오탐은 수동 확인)
PII = re.compile(
    r"(?:01[016789][-\s.]?\d{3,4}[-\s.]?\d{4})"
    r"|(?:[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)"
    r"|(?:[가-힣]{2,4}\s?(?:팀장|과장|계장|주무관|사무관|병장|상병|일병|이병|대위|중위|소위|하사|중사|상사|원사|해설사))"
)
# 검토 결과(2026-08-03): pii_flag 27건 전부 군인·해설사 실명 칭찬 — 인용 시 실명 마스킹 필수, 분석 사용은 가능


def check(df: pd.DataFrame) -> None:
    assert len(df) == 4517, f"행 손실: {len(df)}"
    assert df["id"].is_unique
    assert set(df["year"].unique()) <= {2021, 2022, 2023, 2025}, sorted(df["year"].unique())
    assert df.loc[df["is_substantive"], "n_chars"].min() >= 2
    assert int(df["pii_flag"].sum()) < 100, f"pii 과다: {df['pii_flag'].sum()}"
    print("CHECK OK",
          "| substantive:", int(df["is_substantive"].sum()),
          "| pii:", int(df["pii_flag"].sum()),
          "| years:", df.groupby("year").size().to_dict())


def run(src: str = "data/raw/panmunjom_subjective_20250917.csv",
        dst: str = "data/processed/responses_clean.csv") -> pd.DataFrame:
    df = pd.read_csv(src, encoding="utf-8-sig")
    df.columns = ["survey", "question", "text", "created", "updated"]
    df["text"] = df["text"].astype(str).str.strip()
    df = df.reset_index(drop=True)
    df["id"] = df.index
    df["created"] = df["created"].astype(str)
    df["year"] = df["created"].str[:4].astype(int)
    df["month"] = df["created"].str[5:7].astype(int)
    df["n_chars"] = df["text"].str.len()
    df["is_substantive"] = (df["n_chars"] >= 5) & ~df["text"].str.match(MEANINGLESS)
    df["pii_flag"] = df["text"].str.contains(PII)
    out = df[["id", "survey", "question", "text", "created",
              "year", "month", "n_chars", "is_substantive", "pii_flag"]]
    out.to_csv(dst, index=False, encoding="utf-8-sig")
    check(out)
    return out


if __name__ == "__main__":
    run()
