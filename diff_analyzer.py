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
    # サーバーランキングを基準に対象日を決定
    # ==================================================

    server_files_by_group = {}

    for group in ["virba", "eda"]:
        files = sorted(
            SERVER_RANKING_DIR.glob(
                f"ranking_{group}_*.csv"
            )
        )

        if len(files) < 2:
            raise RuntimeError(
                f"{group.capitalize()}の比較可能なCSVが"
                "2日分ありません。"
            )

        server_files_by_group[group] = files

    # 各サーバーの最新2日分を取得
    selected = {}

    for group, files in server_files_by_group.items():
        old_file = files[-2]
        new_file = files[-1]

        old_date = old_file.stem.replace(
            f"ranking_{group}_", ""
        )
        new_date = new_file.stem.replace(
            f"ranking_{group}_", ""
        )

        selected[group] = {
            "old_file": old_file,
            "new_file": new_file,
            "old_date": old_date,
            "new_date": new_date,
        }

    # VirbaとEdaの最新日が一致しなければ停止
    virba_date = selected["virba"]["new_date"]
    eda_date = selected["eda"]["new_date"]

    if virba_date != eda_date:
        raise RuntimeError(
            "VirbaとEdaの最新CSVの日付が一致しません。"
            f" Virba={virba_date}, Eda={eda_date}"
        )

    new_date = virba_date

    print(f"\n今回の対象日: {new_date}")

    # ==================================================
    # サーバー別ランキングの差分分析
    # ==================================================

    server_results = {}

    for group in ["virba", "eda"]:
        info = selected[group]

        old_date = info["old_date"]
        new_date_group = info["new_date"]

        print()
        print("=" * 60)
        print(f"{group.capitalize()}ランキング")
        print("=" * 60)
        print(f"比較対象: {old_date} → {new_date_group}")

        old_df = load_ranking(info["old_file"])
        new_df = load_ranking(info["new_file"])

        result = analyze_diff(old_df, new_df)

        print_analysis(
            f"【{group.capitalize()}ランキング】",
            old_date,
            new_date_group,
            result
        )

        identical = check_csv_identical(old_df, new_df)

        print()
        print(f"CSV完全一致: {'はい' if identical else 'いいえ'}")

        server_results[group.capitalize()] = {
            "old_date": old_date,
            "new_date": new_date_group,
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
    # 全体ランキングは任意扱い
    # ==================================================

    world_result = {
        "old_date": None,
        "new_date": None,
        "source": "world_ranking",
        "available": False,
        "daily_change_reliability": "unavailable",
        "summary": {
            "old_count": 0,
            "new_count": 0,
            "common_count": 0,
            "not_visible_count": 0,
            "new_visible_count": 0,
        },
        "rank_changes": [],
        "level_changes": [],
        "guild_changes": [],
        "server_changes": [],
        "not_visible": [],
        "new_visible": [],
        "csv_identical": None,
    }

    world_old_file = RANKING_DIR / f"ranking_{selected['virba']['old_date']}.csv"
    world_new_file = RANKING_DIR / f"ranking_{new_date}.csv"

    if world_old_file.exists() and world_new_file.exists():
        old_world_df = load_ranking(world_old_file)
        new_world_df = load_ranking(world_new_file)

        # 全体ランキングにはVirbaとEdaの両方が含まれる想定。
        # VirbaだけのCSVなどを全体ランキングと誤認しない。
        def has_multiple_server_families(df):
            servers = df["server"].fillna("").astype(str)

            has_virba = servers.str.startswith("Virba").any()
            has_eda = servers.str.startswith("Eda").any()

            return has_virba and has_eda

        if (
            has_multiple_server_families(old_world_df)
            and has_multiple_server_families(new_world_df)
        ):
            world_result = analyze_diff(
                old_world_df,
                new_world_df
            )

            world_identical = check_csv_identical(
                old_world_df,
                new_world_df
            )

            world_result = {
                "old_date": selected["virba"]["old_date"],
                "new_date": new_date,
                "source": "world_ranking",
                "available": True,
                "daily_change_reliability": "reference_only",
                "summary": world_result["summary"],
                "rank_changes": world_result["rank_changes"],
                "level_changes": world_result["level_changes"],
                "guild_changes": world_result["guild_changes"],
                "server_changes": world_result["server_changes"],
                "not_visible": world_result["not_visible"],
                "new_visible": world_result["new_visible"],
                "csv_identical": world_identical,
            }

            print("\n全体ランキング: 比較しました")
        else:
            print(
                "\n全体ランキング: 有効な全体データと"
                "確認できないため、今回は比較しません。"
            )
    else:
        print(
            "\n全体ランキング: 対象日のCSVが揃っていないため、"
            "今回は比較しません。"
        )

    # ==================================================
    # JSON保存
    # ==================================================

    diff_data = {
        "world": world_result,
        "server_ranking": server_results,
    }

    diff_file = DIFF_DIR / f"diff_{new_date}.json"

    with open(diff_file, "w", encoding="utf-8") as f:
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
    print(f"保存先: {diff_file.resolve()}")


if __name__ == "__main__":
    main()

