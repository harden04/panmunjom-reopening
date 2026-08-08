"""LLM 분류용 배치 파일 생성: substantive 행을 300행 단위 JSON으로 분할."""
import json
import os

import pandas as pd

BATCH_SIZE = 300


def run(src: str = "data/processed/responses_clean.csv",
        out_dir: str = "data/processed/batches") -> int:
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(src, encoding="utf-8-sig")
    sub = df[df["is_substantive"]][["id", "survey", "year", "text"]].reset_index(drop=True)
    n_batches = 0
    for i in range(0, len(sub), BATCH_SIZE):
        chunk = sub.iloc[i:i + BATCH_SIZE]
        items = chunk.to_dict(orient="records")
        path = os.path.join(out_dir, f"batch_{i // BATCH_SIZE:02d}.json")
        json.dump(items, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        n_batches += 1
    print(f"batches: {n_batches} | rows: {len(sub)}")
    return n_batches


if __name__ == "__main__":
    run()
