import pandas as pd
from pathlib import Path

SOURCE_DIR = Path("data/data/full_dataset")
OUTPUT_FILE = Path("data/emotion_train.csv")

FILES = [
    "goemotions_1.csv",
    "goemotions_2.csv",
    "goemotions_3.csv"
]

# Map GoEmotions → mental-health signals
LABEL_MAP = {
    "stress": ["nervousness", "annoyance", "confusion"],
    "anxiety": ["fear", "nervousness"],
    "sadness": ["sadness", "grief", "remorse"],
    "anger": ["anger", "disgust", "disapproval"],
    "fear": ["fear"],
    "neutral": ["neutral"]
}

def load_all_csvs():
    dfs = []
    for file in FILES:
        path = SOURCE_DIR / file
        print(f"Loading {path}")
        dfs.append(pd.read_csv(path))
    return pd.concat(dfs, ignore_index=True)

def build_dataset(df):
    out = pd.DataFrame()
    out["text"] = df["text"].astype(str)

    for new_label, old_labels in LABEL_MAP.items():
        out[new_label] = df[old_labels].max(axis=1)

    return out

def main():
    df = load_all_csvs()
    final_df = build_dataset(df)

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    final_df.to_csv(OUTPUT_FILE, index=False)

    print(f"✅ Saved {len(final_df)} samples to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()