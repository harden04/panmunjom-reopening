"""분류 결과(out_*.json) 병합 → classified.csv, 커버리지·유효성 검증."""
import glob
import json
import os
import sys

import pandas as pd

TOPICS = {"RESERVE", "ACCESS", "GUIDE", "TIME", "COURSE", "FACILITY", "SOUVENIR",
          "CROWD", "REOPEN", "EMOTION", "INFO", "BALANCE", "ETC"}
SENTIMENTS = {"POS", "NEG", "SUGGEST"}
DIFFICULTIES = {"OPS", "BUDGET", "POLICY", "NA"}


def run(clean: str = "data/processed/responses_clean.csv",
        batches_dir: str = "data/processed/batches",
        dst: str = "data/processed/classified.csv") -> None:
    labels = {}
    dupes = 0
    for path in sorted(glob.glob(os.path.join(batches_dir, "out_*.json"))):
        for row in json.load(open(path, encoding="utf-8")):
            rid = int(row["id"])
            if rid in labels:
                dupes += 1
            labels[rid] = {
                "topic": row.get("topic", "ETC"),
                "topic2": row.get("topic2") or "",
                "sentiment": row.get("sentiment", "POS"),
                "difficulty": row.get("difficulty", "NA"),
                "quote_worthy": bool(row.get("quote_worthy", False)),
            }

    df = pd.read_csv(clean, encoding="utf-8-sig")
    sub_ids = set(df.loc[df["is_substantive"], "id"])
    missing = sorted(sub_ids - set(labels))
    extra = sorted(set(labels) - sub_ids)

    bad_topic = [r for r, v in labels.items()
                 if v["topic"] not in TOPICS or (v["topic2"] and v["topic2"] not in TOPICS)]
    bad_sent = [r for r, v in labels.items() if v["sentiment"] not in SENTIMENTS]
    bad_diff = [r for r, v in labels.items() if v["difficulty"] not in DIFFICULTIES]

    if missing:
        # 누락분 재분류 배치 자동 생성
        chunk = df[df["id"].isin(missing)][["id", "survey", "year", "text"]]
        path = os.path.join(batches_dir, "batch_retry.json")
        json.dump(chunk.to_dict(orient="records"),
                  open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"MISSING {len(missing)} rows -> {path} 생성 (재분류 필요)")

    for name, bad in [("topic", bad_topic), ("sentiment", bad_sent), ("difficulty", bad_diff)]:
        if bad:
            print(f"INVALID {name}: {len(bad)}건 예) {bad[:5]}")

    if missing or bad_topic or bad_sent or bad_diff:
        sys.exit(1)

    lab = pd.DataFrame.from_dict(labels, orient="index")
    lab.index.name = "id"
    out = df.merge(lab, on="id", how="left")
    out.loc[~out["is_substantive"], ["topic", "sentiment", "difficulty"]] = ["ETC", "POS", "NA"]
    out["quote_worthy"] = out["quote_worthy"].fillna(False)
    out.to_csv(dst, index=False, encoding="utf-8-sig")

    n = len(sub_ids)
    etc = int((out.loc[out["is_substantive"], "topic"] == "ETC").sum())
    print(f"MERGED n={n} coverage=100% dupes={dupes} extra={len(extra)} "
          f"etc={etc} ({etc / n:.1%})")
    dist = out.loc[out["is_substantive"]].groupby("topic").size().sort_values(ascending=False)
    print(dist.to_string())


if __name__ == "__main__":
    run()
