import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import json
from datetime import datetime


# 日本語フォント設定
jp_fonts = [
    "Yu Gothic",
    "Meiryo",
    "MS Gothic"
]

for font_name in jp_fonts:
    if any(font_name.lower() in f.name.lower()
           for f in fm.fontManager.ttflist):
        plt.rcParams["font.family"] = font_name
        break

# 日本語フォント設定
plt.rcParams["font.family"] = "Yu Gothic"

DATA_DIR = Path("data") / "ranking"
ANALYSIS_DIR = Path("data") / "analysis"
CHART_DIR = Path("charts")

ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)


CHART_DIR.mkdir(exist_ok=True)


def load_latest_csv():
    """最新のランキングCSVを読み込む"""

    files = sorted(
        DATA_DIR.glob("ranking_*.csv")
    )

    if not files:
        print("ランキングCSVが見つかりません。")
        return None

    latest_file = files[-1]

    print(f"分析対象: {latest_file.name}")

    df = pd.read_csv(
        latest_file,
        dtype={
            "rank": int,
            "level": int,
            "server": str,
            "guild": str,
            "character": str,
        }
    )

    return df


def analyze_level(df):
    """レベル分析"""

    print()
    print("【レベル分析】")
    print("-" * 50)

    max_level = df["level"].max()
    min_level = df["level"].min()
    average_level = df["level"].mean()

    level_counts = (
        df["level"]
        .value_counts()
        .sort_index(ascending=False)
    )

    max_count = level_counts.max()

    most_levels = level_counts[
        level_counts == max_count
    ].index.tolist()

    print(f"最高レベル : Lv{max_level}")
    print(f"最低レベル : Lv{min_level}")
    print(f"平均レベル : Lv{average_level:.2f}")

    if len(most_levels) == 1:

        print(
            f"最多レベル : "
            f"Lv{most_levels[0]}"
            f"（{max_count}人）"
        )

    else:

        levels = ", ".join(
            f"Lv{x}"
            for x in most_levels
        )

        print(
            f"最多レベル : "
            f"{levels}"
            f"（各{max_count}人）"
        )

    print()
    print("レベル別人数")

    for level, count in level_counts.items():

        percentage = (
            count / len(df) * 100
        )

        print(
            f"Lv{level:>3} : "
            f"{count:>4}人 "
            f"({percentage:>5.1f}%)"
        )

    # グラフ
    plot_level_distribution(
        level_counts
    )


def plot_level_distribution(level_counts):
    """レベル分布グラフ"""

    levels = [
        str(level)
        for level in level_counts.index
    ]

    counts = level_counts.values

    plt.figure(figsize=(10, 6))

    plt.bar(
        levels,
        counts
    )

    plt.title(
        "HIT : The World - Level Distribution"
    )

    plt.xlabel("Level")
    plt.ylabel("Players")

    plt.grid(
        axis="y",
        alpha=0.3
    )

    plt.tight_layout()

    path = (
        CHART_DIR /
        "level_distribution.png"
    )

    plt.savefig(path)

    plt.close()

    print()
    print(
        f"レベル分布グラフ: "
        f"{path}"
    )


def analyze_level_ranges(df):
    """5レベル刻みのレベル帯分析"""

    print()
    print("【レベル帯分析】")
    print("-" * 50)

    max_level = df["level"].max()
    min_level = df["level"].min()

    # 最大レベルを含む5刻みにする
    start = (
        (max_level // 5) * 5
    )

    # 最低レベル側まで含める
    while start + 4 >= min_level:

        end = start + 4

        count = df[
            df["level"].between(
                start,
                end
            )
        ].shape[0]

        percentage = (
            count / len(df) * 100
        )

        print(
            f"Lv{start}～Lv{end} : "
            f"{count:>4}人 "
            f"({percentage:>5.1f}%)"
        )

        start -= 5


def analyze_server(df):
    """サーバー別分析"""

    print()
    print("【サーバー別人数】")
    print("-" * 50)

    counts = (
        df["server"]
        .fillna("不明")
        .value_counts()
    )

    for server, count in counts.items():

        percentage = (
            count / len(df) * 100
        )

        print(
            f"{server:<8} : "
            f"{count:>4}人 "
            f"({percentage:>5.1f}%)"
        )

    # Eda / Virba
    eda_count = (
        df["server"]
        .str.startswith("Eda")
        .sum()
    )

    virba_count = (
        df["server"]
        .str.startswith("Virba")
        .sum()
    )

    print()
    print("【サーバー勢力】")

    print(
        f"Eda系   : "
        f"{eda_count:>4}人 "
        f"({eda_count / len(df) * 100:.1f}%)"
    )

    print(
        f"Virba系 : "
        f"{virba_count:>4}人 "
        f"({virba_count / len(df) * 100:.1f}%)"
    )

    plot_server_distribution(
        counts
    )


def plot_server_distribution(counts):
    """サーバー分布グラフ"""

    plt.figure(figsize=(10, 6))

    plt.bar(
        counts.index,
        counts.values
    )

    plt.title(
        "HIT : The World - Server Distribution"
    )

    plt.xlabel("Server")
    plt.ylabel("Players")

    plt.xticks(
        rotation=45
    )

    plt.grid(
        axis="y",
        alpha=0.3
    )

    plt.tight_layout()

    path = (
        CHART_DIR /
        "server_distribution.png"
    )

    plt.savefig(path)

    plt.close()

    print(
        f"サーバー分布グラフ: "
        f"{path}"
    )


def analyze_guild(df):
    """ギルド分析"""

    print()
    print("【ギルド分析】")
    print("-" * 50)

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

    no_guild_count = no_guild.sum()

    guild_member_count = (
        len(df) - no_guild_count
    )

    print(
        f"ギルド所属 : "
        f"{guild_member_count}人 "
        f"({guild_member_count / len(df) * 100:.1f}%)"
    )

    print(
        f"無所属     : "
        f"{no_guild_count}人 "
        f"({no_guild_count / len(df) * 100:.1f}%)"
    )

    guild_counts = (
        guilds[~no_guild]
        .value_counts()
    )

    print()
    print("ギルド掲載人数 TOP20")

    for rank, (guild, count) in enumerate(
        guild_counts.head(20).items(),
        start=1
    ):

        percentage = (
            count / len(df) * 100
        )

        print(
            f"{rank:>2}位 "
            f"{guild:<20} "
            f"{count:>4}人 "
            f"({percentage:>5.1f}%)"
        )

    plot_guild_distribution(
        guild_counts
    )


def plot_guild_distribution(guild_counts):
    """ギルドTOP20グラフ"""

    top20 = guild_counts.head(20)

    plt.figure(figsize=(12, 7))

    plt.barh(
        top20.index[::-1],
        top20.values[::-1]
    )

    plt.title(
        "HIT : The World - Guild Ranking"
    )

    plt.xlabel("Players")

    plt.tight_layout()

    path = (
        CHART_DIR /
        "guild_top20.png"
    )

    plt.savefig(path)

    plt.close()

    print(
        f"ギルドTOP20グラフ: "
        f"{path}"
    )


def analyze_high_level(df):
    """高レベル帯分析"""

    print()
    print("【高レベル帯】")
    print("-" * 50)

    for level in [100, 99, 95, 90]:

        count = (
            df["level"] >= level
        ).sum()

        percentage = (
            count / len(df) * 100
        )

        print(
            f"Lv{level}以上 : "
            f"{count:>4}人 "
            f"({percentage:>5.1f}%)"
        )

def save_daily_analysis(df):
    """日別の分析結果をJSON保存"""

    # 今日の日付
    today = datetime.now().strftime("%Y-%m-%d")
    date_key = datetime.now().strftime("%Y%m%d")

    total = len(df)

    # ==============================
    # レベル分析
    # ==============================

    level_counts = (
        df["level"]
        .value_counts()
        .sort_index(ascending=False)
    )

    max_level = int(df["level"].max())
    min_level = int(df["level"].min())
    average_level = round(float(df["level"].mean()), 2)

    max_count = int(level_counts.max())

    most_levels = [
        int(level)
        for level, count in level_counts.items()
        if count == max_count
    ]

    # ==============================
    # レベル帯
    # ==============================

    level_ranges = {}

    start = (max_level // 5) * 5

    while start + 4 >= min_level:

        end = start + 4

        count = int(
            df["level"]
            .between(start, end)
            .sum()
        )

        level_ranges[f"Lv{start}～Lv{end}"] = count

        start -= 5

    # ==============================
    # サーバー
    # ==============================

    server_counts = (
        df["server"]
        .fillna("不明")
        .value_counts()
    )

    server_distribution = {
        str(server): int(count)
        for server, count
        in server_counts.items()
    }

    eda_count = int(
        df["server"]
        .fillna("")
        .str.startswith("Eda")
        .sum()
    )

    virba_count = int(
        df["server"]
        .fillna("")
        .str.startswith("Virba")
        .sum()
    )

    # ==============================
    # ギルド
    # ==============================

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

    no_guild_count = int(no_guild.sum())

    guild_member_count = int(
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
        guild_top20.append({
            "rank": rank,
            "guild": str(guild),
            "count": int(count)
        })

    # ==============================
    # 高レベル帯
    # ==============================

    high_level = {}

    for level in [100, 99, 95, 90]:

        count = int(
            (df["level"] >= level).sum()
        )

        high_level[str(level)] = count

    # ==============================
    # JSONデータ
    # ==============================

    data = {
        "date": today,

        "ranking": {
            "count": total
        },

        "level": {
            "max": max_level,
            "min": min_level,
            "average": average_level,
            "most_levels": most_levels,
            "most_count": max_count,
            "distribution": {
                str(int(level)): int(count)
                for level, count
                in level_counts.items()
            },
            "ranges": level_ranges,
            "high_level": high_level
        },

        "server": {
            "distribution": server_distribution,
            "eda": eda_count,
            "virba": virba_count
        },

        "guild": {
            "member_count": guild_member_count,
            "no_guild_count": no_guild_count,
            "top20": guild_top20
        }
    }

    # ==============================
    # 保存
    # ==============================

    output_file = (
        ANALYSIS_DIR /
        f"analysis_{date_key}.json"
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

    print()
    print(
        f"日別分析データ: "
        f"{output_file}"
    )



def main():

    print("=" * 60)
    print("HIT : The World")
    print("ランキング分析")
    print("=" * 60)

    df = load_latest_csv()

    if df is None:
        return

    print()
    print(
        f"ランキング人数 : "
        f"{len(df):,}人"
    )

    analyze_level(df)

    analyze_level_ranges(df)

    analyze_server(df)

    analyze_guild(df)

    analyze_high_level(df)

    # 日別分析データを保存
    save_daily_analysis(df)

    print()
    print("=" * 60)

    print("分析終了")
    print("=" * 60)


if __name__ == "__main__":
    main()
