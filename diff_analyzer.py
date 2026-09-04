import pandas as pd
from pathlib import Path
import json


BASE_DIR = Path(__file__).resolve().parent

RANKING_DIR = BASE_DIR / "data" / "ranking"
SERVER_RANKING_DIR = BASE_DIR / "data" / "ranking_server"
DIFF_DIR = BASE_DIR / "data" / "diff"

DIFF_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CSV読み込み
# ============================================================

def load_ranking(file):
    """
    ランキングCSVを読み込む
    """

    if not file.exists():
        raise FileNotFoundError(
            f"CSVが見つかりません: {file}"
        )

    df = pd.read_csv(
        file,
        dtype=str
    )

    # --------------------------------------------------
    # 空欄を統一
    # --------------------------------------------------
    # pandas はCSVの空欄を NaN に変換するため、
    # ギルド・サーバー等の空欄を "" に統一する。
    # これにより、
    # 「無所属 → ギルド加入」
    # 「ギルド脱退 → 無所属」
    # を正しく判定できる。
    # --------------------------------------------------

    df["character"] = df["character"].fillna("").astype(str)
    df["guild"] = df["guild"].fillna("").astype(str)
    df["server"] = df["server"].fillna("").astype(str)

    # 数値列
    df["rank"] = pd.to_numeric(df["rank"])
    df["level"] = pd.to_numeric(df["level"])

    return df


# ============================================================
# 差分分析
# ============================================================

def analyze_diff(old_df, new_df):
    """
    2つのランキングを比較する
    """

    old = old_df.set_index("character")
    new = new_df.set_index("character")

    common = old.index.intersection(new.index)

    old_only = old.index.difference(new.index)
    new_only = new.index.difference(old.index)

    # --------------------------------------------------
    # 順位変動
    # --------------------------------------------------

    rank_changes = []

    for character in common:

        old_rank = int(old.loc[character, "rank"])
        new_rank = int(new.loc[character, "rank"])

        diff = old_rank - new_rank

        if diff != 0:

            rank_changes.append({
                "character": character,
                "old_rank": old_rank,
                "new_rank": new_rank,
                "change": diff,
            })

    rank_changes.sort(
        key=lambda x: x["change"],
        reverse=True
    )

    # --------------------------------------------------
    # レベル変動
    # --------------------------------------------------

    level_changes = []

    for character in common:

        old_level = int(old.loc[character, "level"])
        new_level = int(new.loc[character, "level"])

        diff = new_level - old_level

        if diff != 0:

            level_changes.append({
                "character": character,
                "old_level": old_level,
                "new_level": new_level,
                "change": diff,
            })

    level_changes.sort(
        key=lambda x: x["change"],
        reverse=True
    )

    # --------------------------------------------------
    # ギルド変更
    # --------------------------------------------------

    guild_changes = []

    for character in common:

        old_guild = old.loc[character, "guild"]
        new_guild = new.loc[character, "guild"]

        if old_guild != new_guild:

            guild_changes.append({
                "character": character,
                "old_guild": old_guild,
                "new_guild": new_guild,
            })

    # --------------------------------------------------
    # サーバー変更
    # --------------------------------------------------

    server_changes = []

    for character in common:

        old_server = old.loc[character, "server"]
        new_server = new.loc[character, "server"]

        if old_server != new_server:

            server_changes.append({
                "character": character,
                "old_server": old_server,
                "new_server": new_server,
                "old_guild": old.loc[
                    character,
                    "guild"
                ],
                "new_guild": new.loc[
                    character,
                    "guild"
                ],
            })

    # --------------------------------------------------
    # 結果
    # --------------------------------------------------

    return {
        "summary": {
            "old_count": len(old_df),
            "new_count": len(new_df),
            "common_count": len(common),
            "not_visible_count": len(old_only),
            "new_visible_count": len(new_only),
        },

        "rank_changes": rank_changes,

        "level_changes": level_changes,

        "guild_changes": guild_changes,

        "server_changes": server_changes,

        # 「ランキング圏外」ではなく
        # 「今回の取得範囲では確認できない」として保存
        "not_visible": [
            {
                "character": character,
                "old_rank": int(
                    old.loc[character, "rank"]
                ),
            }
            for character in old_only
        ],

        "new_visible": [
            {
                "character": character,
                "new_rank": int(
                    new.loc[character, "rank"]
                ),
            }
            for character in new_only
        ],
    }


# ============================================================
# コンソール表示
# ============================================================

def print_analysis(
    title,
    old_date,
    new_date,
    result
):

    print()
    print("=" * 60)
    print(title)
    print(f"{old_date} → {new_date}")
    print("=" * 60)

    summary = result["summary"]

    print()
    print("【概要】")
    print("-" * 50)

    print(
        f'前日: {summary["old_count"]:,}人'
    )

    print(
        f'当日: {summary["new_count"]:,}人'
    )

    print(
        f'共通: {summary["common_count"]:,}人'
    )

    print(
        f'今回未確認: '
        f'{summary["not_visible_count"]:,}人'
    )

    print(
        f'新たに確認: '
        f'{summary["new_visible_count"]:,}人'
    )

    # --------------------------------------------------
    # 順位UP
    # --------------------------------------------------

    print()
    print("【順位UP TOP20】")
    print("-" * 50)

    rank_changes = result["rank_changes"]

    up_count = 0

    for row in rank_changes:

        if row["change"] <= 0:
            continue

        print(
            f'{row["character"]:20} '
            f'{row["old_rank"]:4}位 → '
            f'{row["new_rank"]:4}位 '
            f'▲{row["change"]}'
        )

        up_count += 1

        if up_count >= 20:
            break

    if up_count == 0:
        print("順位UPなし")

    # --------------------------------------------------
    # 順位DOWN
    # --------------------------------------------------

    print()
    print("【順位DOWN TOP20】")
    print("-" * 50)

    down_count = 0

    for row in sorted(
        rank_changes,
        key=lambda x: x["change"]
    ):

        if row["change"] >= 0:
            continue

        print(
            f'{row["character"]:20} '
            f'{row["old_rank"]:4}位 → '
            f'{row["new_rank"]:4}位 '
            f'▼{abs(row["change"])}'
        )

        down_count += 1

        if down_count >= 20:
            break

    if down_count == 0:
        print("順位DOWNなし")

    # --------------------------------------------------
    # レベル
    # --------------------------------------------------

    print()
    print("【レベル変動】")
    print("-" * 50)

    if result["level_changes"]:

        for row in result["level_changes"][:30]:

            if row["change"] > 0:
                arrow = "▲"
            else:
                arrow = "▼"

            print(
                f'{row["character"]:20} '
                f'Lv{row["old_level"]} → '
                f'Lv{row["new_level"]} '
                f'{arrow}{abs(row["change"])}'
            )

    else:
        print("レベル変動なし")

    # --------------------------------------------------
    # ギルド
    # --------------------------------------------------

    print()
    print("【ギルド変更】")
    print("-" * 50)

    if result["guild_changes"]:

        for row in result["guild_changes"]:

            old_guild = (
                row["old_guild"]
                if row["old_guild"]
                else "無所属"
            )

            new_guild = (
                row["new_guild"]
                if row["new_guild"]
                else "無所属"
            )

            print(
                f'{row["character"]:20} '
                f'{old_guild} → {new_guild}'
            )

    else:
        print("ギルド変更なし")

    # --------------------------------------------------
    # サーバー
    # --------------------------------------------------

    print()
    print("【サーバー変更】")
    print("-" * 50)

    if result["server_changes"]:

        for row in result["server_changes"]:

            print(
                f'{row["character"]:20} '
                f'{row["old_server"]} → '
                f'{row["new_server"]}'
            )

    else:
        print("サーバー変更なし")

    # --------------------------------------------------
    # 未確認
    # --------------------------------------------------

    print()
    print("【今回の取得範囲で未確認】")
    print("-" * 50)

    if result["not_visible"]:

        for row in result["not_visible"]:

            print(
                f'{row["character"]:20} '
                f'{row["old_rank"]}位 → 未確認'
            )

    else:
        print("なし")

    # --------------------------------------------------
    # 新規確認
    # --------------------------------------------------

    print()
    print("【今回新たに確認】")
    print("-" * 50)

    if result["new_visible"]:

        for row in result["new_visible"]:

            print(
                f'{row["character"]:20} '
                f'未確認 → '
                f'{row["new_rank"]}位'
            )

    else:
        print("なし")


# ============================================================
# CSV完全一致
# ============================================================

def check_csv_identical(
    old_df,
    new_df
):

    old_raw = old_df.to_csv(
        index=False
    )

    new_raw = new_df.to_csv(
        index=False
    )

    return old_raw == new_raw


# ============================================================
# メイン
# ============================================================

def main():

    print("=" * 60)
    print("HIT : The World")
    print("ランキング差分分析")
    print("=" * 60)

    # ==================================================
    # 全体ランキング
    # ==================================================

    ranking_files = sorted(
        RANKING_DIR.glob(
            "ranking_*.csv"
        )
    )

    if len(ranking_files) < 2:

        print()
        print(
            "比較できる全体ランキングCSVが"
            "2日分以上ありません。"
        )

        return

    old_world_file = ranking_files[-2]
    new_world_file = ranking_files[-1]

    old_world_date = (
        old_world_file.stem
        .replace("ranking_", "")
    )

    new_world_date = (
        new_world_file.stem
        .replace("ranking_", "")
    )

    print()
    print(
        f"全体ランキング: "
        f"{old_world_date} → "
        f"{new_world_date}"
    )

    old_world_df = load_ranking(
        old_world_file
    )

    new_world_df = load_ranking(
        new_world_file
    )

    world_result = analyze_diff(
        old_world_df,
        new_world_df
    )

    print_analysis(
        "【全体ランキング】",
        old_world_date,
        new_world_date,
        world_result
    )

    world_identical = check_csv_identical(
        old_world_df,
        new_world_df
    )

    print()
    print("【全体CSV完全一致チェック】")
    print("-" * 50)

    if world_identical:
        print("CSVは完全に同一です")
    else:
        print("CSVには差があります")

    # ==================================================
    # サーバーランキング
    # ==================================================

    server_results = {}

    for group in [
        "virba",
        "eda"
    ]:

        server_files = sorted(
            SERVER_RANKING_DIR.glob(
                f"ranking_{group}_*.csv"
            )
        )

        print()
        print(
            "=" * 60
        )
        print(
            f"{group.capitalize()}ランキング"
        )
        print(
            "=" * 60
        )

        if len(server_files) < 2:

            print(
                f"{group.capitalize()}は"
                "比較できるCSVが2日分ありません。"
            )

            continue

        old_server_file = server_files[-2]
        new_server_file = server_files[-1]

        old_server_date = (
            old_server_file.stem
            .replace(
                f"ranking_{group}_",
                ""
            )
        )

        new_server_date = (
            new_server_file.stem
            .replace(
                f"ranking_{group}_",
                ""
            )
        )

        print()
        print(
            f"比較対象: "
            f"{old_server_date} → "
            f"{new_server_date}"
        )

        old_server_df = load_ranking(
            old_server_file
        )

        new_server_df = load_ranking(
            new_server_file
        )

        result = analyze_diff(
            old_server_df,
            new_server_df
        )

        print_analysis(
            f"【{group.capitalize()}ランキング】",
            old_server_date,
            new_server_date,
            result
        )

        identical = check_csv_identical(
            old_server_df,
            new_server_df
        )

        print()
        print(
            f"【{group.capitalize()} "
            f"CSV完全一致チェック】"
        )

        print("-" * 50)

        if identical:
            print("CSVは完全に同一です")
        else:
            print("CSVには差があります")

        server_results[group.capitalize()] = {
            "old_date": old_server_date,
            "new_date": new_server_date,
            "summary": result["summary"],
            "rank_changes": result["rank_changes"],
            "level_changes": result["level_changes"],
            "guild_changes": result["guild_changes"],
            "server_changes": result["server_changes"],
            "not_visible": result["not_visible"],
            "new_visible": result["new_visible"],
            "csv_identical": identical,
        }

    # ==================================================
    # JSON保存
    # ==================================================

    diff_data = {

        "world": {
            "old_date": old_world_date,
            "new_date": new_world_date,

            "source": "world_ranking",

            "daily_change_reliability":
                "reference_only",

            "summary":
                world_result["summary"],

            "rank_changes":
                world_result["rank_changes"],

            "level_changes":
                world_result["level_changes"],

            "guild_changes":
                world_result["guild_changes"],

            "server_changes":
                world_result["server_changes"],

            "not_visible":
                world_result["not_visible"],

            "new_visible":
                world_result["new_visible"],

            "csv_identical":
                world_identical,
        },

        "server_ranking":
            server_results,
    }

    diff_file = (
        DIFF_DIR /
        f"diff_{new_world_date}.json"
    )

    with open(
        diff_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            diff_data,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("=" * 60)
    print("差分分析終了")
    print("=" * 60)

    print()
    print("【差分データ保存】")
    print("-" * 50)
    print(
        f"保存先: "
        f"{diff_file.resolve()}"
    )


if __name__ == "__main__":
    main()
