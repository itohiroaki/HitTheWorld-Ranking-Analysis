import json
from pathlib import Path

import pandas as pd


# ============================================================
# パス設定
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
RANKING_DIR = DATA_DIR / "ranking"
ANALYSIS_DIR = DATA_DIR / "analysis"

WEB_DIR = BASE_DIR / "web"
HISTORY_DIR = WEB_DIR / "history"

WEB_DIR.mkdir(exist_ok=True)
HISTORY_DIR.mkdir(exist_ok=True)


# ============================================================
# 最新ランキングCSVを取得
# ============================================================

csv_files = sorted(
    RANKING_DIR.glob("ranking_*.csv")
)

if not csv_files:

    print("ランキングCSVが見つかりません。")
    exit()


latest_csv = csv_files[-1]

date_str = latest_csv.stem.replace(
    "ranking_",
    ""
)


print("=" * 60)
print("HIT : The World")
print("Web用データ生成")
print("=" * 60)

print()
print(f"対象ファイル: {latest_csv.name}")


# ============================================================
# CSV読み込み
# ============================================================

df = pd.read_csv(
    latest_csv,
    dtype={
        "rank": int,
        "level": int,
        "server": str,
        "guild": str,
        "character": str,
    }
)


# ============================================================
# 基本情報
# ============================================================

total = len(df)

max_level = int(
    df["level"].max()
)

min_level = int(
    df["level"].min()
)

average_level = round(
    float(df["level"].mean()),
    2
)


# ============================================================
# レベル別人数
# ============================================================

level_counts = (
    df["level"]
    .value_counts()
    .sort_index(ascending=False)
)

max_count = int(
    level_counts.max()
)

most_levels = [
    int(level)
    for level, count in level_counts.items()
    if count == max_count
]


level_data = {}

for level, count in level_counts.items():

    level_data[
        str(int(level))
    ] = int(count)


# ============================================================
# サーバー別人数
# ============================================================

server_series = (
    df["server"]
    .fillna("")
    .astype(str)
    .str.strip()
)

server_counts = (
    server_series
    .replace("", "不明")
    .value_counts()
)


server_data = {}

for server, count in server_counts.items():

    server_data[
        str(server)
    ] = int(count)


# ============================================================
# Eda / Virba
# ============================================================

eda_count = int(
    server_series
    .str.startswith("Eda")
    .sum()
)

virba_count = int(
    server_series
    .str.startswith("Virba")
    .sum()
)


# ============================================================
# ギルド
# ============================================================

guilds = (
    df["guild"]
    .fillna("")
    .astype(str)
    .str.strip()
)

no_guild = (
    (guilds == "")
    | (guilds == "nan")
)

no_guild_count = int(
    no_guild.sum()
)

guild_member_count = (
    total - no_guild_count
)


guild_counts = (
    guilds[~no_guild]
    .value_counts()
)


guild_top20 = []

for rank, (guild, count) in enumerate(
    guild_counts.head(20).items(),
    start=1
):

    guild_top20.append(
        {
            "rank": rank,
            "guild": str(guild),
            "count": int(count),
        }
    )


# ============================================================
# 高レベル帯
# ============================================================

high_level_data = {}

for level in [100, 99, 95, 90]:

    count = int(
        (df["level"] >= level).sum()
    )

    high_level_data[
        str(level)
    ] = count


# ============================================================
# ランキングデータ
# ============================================================

ranking_data = []

for _, row in df.iterrows():

    guild = row["guild"]

    if pd.isna(guild):
        guild = ""
    else:
        guild = str(guild)

    server = row["server"]

    if pd.isna(server):
        server = ""
    else:
        server = str(server)

    character = row["character"]

    if pd.isna(character):
        character = ""
    else:
        character = str(character)


    ranking_data.append(
        {
            "rank": int(row["rank"]),
            "level": int(row["level"]),
            "server": server,
            "guild": guild,
            "character": character,
        }
    )


# ============================================================
# Web用完全データ
# ============================================================

data = {

    "date": date_str,

    "total": total,

    "level": {

        "max": max_level,

        "min": min_level,

        "average": average_level,

        "most": most_levels,

        "most_count": max_count,

        "distribution": level_data,
    },

    "server": {

        "distribution": server_data,

        "eda": eda_count,

        "virba": virba_count,
    },

    "guild": {

        "members": guild_member_count,

        "no_guild": no_guild_count,

        "top20": guild_top20,
    },

    "high_level": high_level_data,

    "ranking": ranking_data,
}


# ============================================================
# 最新データ保存
# ============================================================

output_file = (
    WEB_DIR / "data.json"
)

with open(
    output_file,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        data,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# 日別データ保存
# ============================================================

print()
print("日別履歴データを保存中...")


history_data_file = (
    HISTORY_DIR /
    f"data_{date_str}.json"
)


with open(
    history_data_file,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        data,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# history.json
# ============================================================

history_file = (
    WEB_DIR / "history.json"
)


history = []


if history_file.exists():

    try:

        with open(
            history_file,
            "r",
            encoding="utf-8"
        ) as f:

            loaded = json.load(f)

            if isinstance(loaded, list):

                history = loaded

    except (
        json.JSONDecodeError,
        OSError
    ):

        history = []


# ==============================
# 履歴用データ作成
# ==============================

history_entry = data


# ============================================================
# 同じ日付を削除
# ============================================================

history = [
    item
    for item in history
    if item.get("date") != date_str
]


# ============================================================
# 追加
# ============================================================

history.append(
    history_entry
)


# ============================================================
# 新しい日付順
# ============================================================

history.sort(
    key=lambda x: x.get(
        "date",
        ""
    ),
    reverse=True
)


# ============================================================
# history.json保存
# ============================================================

with open(
    history_file,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        history,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# 結果表示
# ============================================================

print()
print("Web用データを生成しました.")

print()
print("最新データ:")
print(output_file)

print()
print("日別データ:")
print(history_data_file)

print()
print("履歴:")
print(history_file)

print()
print(f"履歴件数: {len(history)}日")

print()
print(f"ランキング人数: {total:,}人")

print()
print("JSON生成完了")

print("=" * 60)
