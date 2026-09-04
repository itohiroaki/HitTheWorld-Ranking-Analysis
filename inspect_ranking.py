import requests
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path


# ==========================================================
# 設定
# ==========================================================

URL = "https://hittheworld.nexon.com/ranking/worldranking"

BASE_DIR = Path(__file__).resolve().parent

TEST_DIR = BASE_DIR / "data" / "ranking_test"

TEST_DIR.mkdir(
    parents=True,
    exist_ok=True
)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    )
}


# ==========================================================
# ランキング取得
# ==========================================================

def extract_ranking(table, ranking_type):
    """
    指定されたtableからランキングを取得する。
    """

    rows = table.find_all("tr")

    data = []

    for row in rows[1:]:
        cells = row.find_all(["th", "td"])

        if len(cells) < 5:
            continue

        # --------------------------------------------------
        # 順位
        # --------------------------------------------------

        rank_cell = cells[0]

        # 画像順位
        rank_image = rank_cell.find("img")

        if rank_image:

            class_list = rank_image.get("class", [])

            rank = None

            for class_name in class_list:

                if "gold" in class_name:
                    rank = 1
                    break

                if "silver" in class_name:
                    rank = 2
                    break

                if "bronze" in class_name:
                    rank = 3
                    break

        else:

            rank_text = rank_cell.get_text(
                strip=True
            )

            try:
                rank = int(rank_text)

            except ValueError:
                rank = None

        # --------------------------------------------------
        # 各項目
        # --------------------------------------------------

        level_text = cells[1].get_text(
            strip=True
        )

        server = cells[2].get_text(
            strip=True
        )

        guild = cells[3].get_text(
            strip=True
        )

        character = cells[4].get_text(
            strip=True
        )

        # --------------------------------------------------
        # 数値変換
        # --------------------------------------------------

        try:
            level = int(level_text)

        except ValueError:
            continue

        if rank is None:
            continue

        # --------------------------------------------------
        # データ追加
        # --------------------------------------------------

        data.append({
            "ranking_type": ranking_type,
            "rank": rank,
            "level": level,
            "server": server,
            "guild": guild,
            "character": character
        })

    return pd.DataFrame(data)


# ==========================================================
# メイン
# ==========================================================

def main():

    print("=" * 60)
    print("HIT : The World")
    print("3ランキング取得テスト")
    print("=" * 60)

    # ------------------------------------------------------
    # HTML取得
    # ------------------------------------------------------

    print()
    print("公式ランキングページを取得しています...")

    response = requests.get(
        URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    html = response.text

    print(
        f"HTMLサイズ: {len(html):,} bytes"
    )

    # ------------------------------------------------------
    # BeautifulSoup
    # ------------------------------------------------------

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    tables = soup.find_all("table")

    print(
        f"table数: {len(tables)}"
    )

    # ------------------------------------------------------
    # TABLE確認
    # ------------------------------------------------------

    if len(tables) < 3:

        print()
        print(
            "エラー：ランキングtableが3つ見つかりません。"
        )

        return

    # ------------------------------------------------------
    # 3ランキング取得
    # ------------------------------------------------------

    ranking_tables = {

        "world":
            tables[0],

        "virba":
            tables[1],

        "eda":
            tables[2]
    }

    results = {}

    for ranking_type, table in ranking_tables.items():

        print()
        print(
            "-" * 60
        )

        print(
            f"{ranking_type.upper()}ランキング取得"
        )

        df = extract_ranking(
            table,
            ranking_type
        )

        results[ranking_type] = df

        print(
            f"取得人数: {len(df):,}人"
        )

        # --------------------------------------------------
        # CSV保存
        # --------------------------------------------------

        output_file = (
            TEST_DIR /
            f"ranking_{ranking_type}_test.csv"
        )

        df.to_csv(
            output_file,
            index=False,
            encoding="utf-8-sig"
        )

        print(
            f"保存先: {output_file}"
        )

        # --------------------------------------------------
        # 上位5人
        # --------------------------------------------------

        print()
        print("【TOP5】")

        for _, row in df.head(5).iterrows():

            print(
                f"{int(row['rank']):>3}位 "
                f"Lv{int(row['level'])} "
                f"{row['server']} "
                f"{row['guild'] or '無所属'} "
                f"{row['character']}"
            )

        # --------------------------------------------------
        # 最終順位
        # --------------------------------------------------

        if not df.empty:

            last = df.iloc[-1]

            print()
            print(
                "【最終順位】"
            )

            print(
                f"{int(last['rank'])}位 "
                f"Lv{int(last['level'])} "
                f"{last['server']} "
                f"{last['guild'] or '無所属'} "
                f"{last['character']}"
            )

    # ======================================================
    # 最終確認
    # ======================================================

    print()
    print("=" * 60)
    print("取得結果")
    print("=" * 60)

    for ranking_type, df in results.items():

        print(
            f"{ranking_type.upper():>6}: "
            f"{len(df):>4}人"
        )

    print()
    print(
        "テスト完了"
    )


if __name__ == "__main__":
    main()