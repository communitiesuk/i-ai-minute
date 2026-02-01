import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.core.config import CACHE_DIR

COST_PER_HOUR = 0.262 # Get this from Azure website
COST_PER_SECOND = COST_PER_HOUR / 3600
INPUT_PATH = CACHE_DIR / "sped_transcriptions_output.json"

sns.set_theme(style="whitegrid")

# Load data from JSON
with open(str(INPUT_PATH)) as f:
    data = json.load(f)

rows = []
for file_id, speeds in data["data"].items():
    for speed_label, entry in speeds.items():
        rows.append({
            "file": file_id,
            "speed": float(speed_label.replace("x_speed", "")),
            "wer": entry["score"]["wer"],
            "duration": entry["meta"]["duration"]
        })
df = pd.DataFrame(rows)

# Calculations
df["cost"] = df["duration"] * COST_PER_SECOND

# Baseline deltas (1x speed)
baseline = df[df["speed"] == 1.0].set_index("file")[["wer", "cost"]]

df["wer_delta"] = df.apply(lambda r: r["wer"] - baseline.loc[r["file"], "wer"], axis=1)
df["cost_saving"] = df.apply(lambda r: baseline.loc[r["file"], "cost"] - r["cost"], axis=1)
df["wer_per_pound"] = df["wer_delta"] / df["cost_saving"]

# print(df)

# Only files that have been sped up
df_fast = df[df["speed"] > 1.0]

# --- PLOTS ---

# 1. WER distribution by speed
plt.figure(figsize=(6, 5))
sns.boxplot(data=df, x="speed", y="wer")
plt.xlabel("Speed factor")
plt.ylabel("WER")
plt.title("WER distribution by speed")
plt.tight_layout()
plt.show()

# 2. Change of WER relative to 1x
plt.figure(figsize=(6, 5))
sns.stripplot(
    data=df_fast,
    x="speed",
    y="wer_delta",
    jitter=True,
    alpha=0.9
)
plt.axhline(0, color="gray", linestyle="--")
plt.xlabel("Speed factor")
plt.ylabel("Change of WER from 1x")
plt.title("WER change relative to 1x")
plt.tight_layout()
plt.show()

# 3. Cost saved vs WER introduced (relative to 1x)
plt.figure(figsize=(6, 5))
sns.scatterplot(
    data=df_fast,
    x="cost_saving",
    y="wer_delta",
    hue="speed",
    palette="colorblind",
    s=100
)

plt.axhline(0, color="gray", linestyle="--")
plt.axvline(0, color="gray", linestyle="--")

plt.xlabel("Cost saved vs 1x (£)")
plt.ylabel("WER increase vs 1x")
plt.title("Cost saved vs WER introduced")

plt.tight_layout()
plt.show()

# 4. WER increase per £ saved
plt.figure(figsize=(6, 5))
sns.boxplot(
    data=df_fast,
    x="speed",
    y="wer_per_pound"
)
plt.xlabel("Speed factor")
plt.ylabel("Change of WER / £")
plt.title("WER increase per £ saved")
plt.tight_layout()
plt.show()


