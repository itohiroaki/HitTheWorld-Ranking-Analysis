import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from datetime import datetime


URL = "https://hittheworld.nexon.com/ranking/worldranking"

# 全体ランキング
DATA_DIR = Path("data/ranking")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# サーバー別ランキング
SERVER_DATA_DIR = Path("data/ranking_server")
SERVER_DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_ranking_page():
    """公式ランキングページを取得"""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/139.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(
        URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    response.encoding = response.apparent_encoding

    return response.text


def get_cell_text(tr, class_name):
    """指定classのtdから文字列を取得"""

    cell = tr.find(
        "td",
        class_=class_name
    )

    if cell is None:
        return ""

    return cell.get_text(
        " ",
        strip=True
    )


def parse_table(table, max_rank):
    """
    指定されたランキングテーブルを解析

    max_rank:
        全体      → 1000
        Virba/Eda → 100
    """

    rankings = {}

    rows = table.find_all("tr")

    for tr in rows:

        # 名前セルがない行はスキップ
        master = tr.find(
            "td",
            class_="table__master"
        )

        if master is None:
            continue

        level = get_cell_text(
            tr,
            "table__level"
        )

        server = get_cell_text(
            tr,
            "table__server"
        )

        guild = get_cell_text(
            tr,
            "table__guild"
        )

        character = get_cell_text(
            tr,
            "table__master"
        )

        rank_cell = tr.find(
            "td",
            class_="table__rank"
        )

        if rank_cell is None:
            continue

        # --------------------------------
        # 順位取得
        # --------------------------------

        # 1～3位は画像
        img = rank_cell.find("img")

        if img is not None:

            src = img.get(
                "src",
                ""
            )

            if "rank_gold" in src:
                rank = 1

            elif "rank_silver" in src:
                rank = 2

            elif "rank_bronze" in src:
                rank = 3

            else:
                continue

        else:

            # 4位以降
            # table__hexagon-inner に順位が入っている
            rank_number = rank_cell.find(
                "div",
                class_="table__hexagon-inner"
            )

            if rank_number is None:
                continue

            rank_text = rank_number.get_text(
                " ",
                strip=True
            )

            if not rank_text.isdigit():
                continue

            rank = int(rank_text)

        # 指定範囲だけ採用
        if not 1 <= rank <= max_rank:
            continue

        # 同じ順位が複数存在する場合は最初の1件だけ
        if rank in rankings:
            continue

        rankings[rank] = {
            "rank": rank,
            "level": level,
            "server": server,
            "guild": guild,
            "character": character,
        }

    # 順位順に並べる
    rows = [
        rankings[rank]
        for rank in sorted(rankings)
    ]

    return rows


def parse_rankings(html):
    """
    公式ページ内のランキングテーブルを取得

    TABLE 1 → 全体
    TABLE 2 → Virba
    TABLE 3 → Eda
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    tables = soup.find_all(
        "table"
    )

    print(
        f"ランキングテーブル検出数: {len(tables)}"
    )

    if len(tables) < 3:
        print(
            "ランキングテーブルが3つ未満です。"
        )

        return [], [], []

    # --------------------------------
    # 全体
    # --------------------------------

    print()
    print("【全体ランキング】")

    world_rows = parse_table(
        tables[0],
        1000
    )

    print(
        f"取得件数: {len(world_rows)}"
    )

    # --------------------------------
    # Virba
    # --------------------------------

    print()
    print("【Virbaランキング】")

    virba_rows = parse_table(
        tables[1],
        100
    )

    print(
        f"取得件数: {len(virba_rows)}"
    )

    # --------------------------------
    # Eda
    # --------------------------------

    print()
    print("【Edaランキング】")

    eda_rows = parse_table(
        tables[2],
        100
    )

    print(
        f"取得件数: {len(eda_rows)}"
    )

    return (
        world_rows,
        virba_rows,
        eda_rows
    )


def save_world_csv(rows):
    """全体ランキングをCSVに保存"""

    if not rows:
        print()
        print(
            "全体ランキングデータを取得できませんでした。"
        )
        return

    df = pd.DataFrame(rows)

    today = datetime.now().strftime(
        "%Y%m%d"
    )

    filename = (
        DATA_DIR /
        f"ranking_{today}.csv"
    )

    df.to_csv(
        filename,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print(
        "========== 全体ランキング =========="
    )

    print(
        f"取得件数: {len(df)}"
    )

    print(
        f"保存先: {filename.resolve()}"
    )

    # 順位チェック
    expected = set(
        range(1, 1001)
    )

    actual = set(
        df["rank"]
    )

    missing = sorted(
        expected - actual
    )

    duplicate_count = (
        df["rank"]
        .duplicated()
        .sum()
    )

    print()

    if not missing:
        print(
            "順位チェック: OK"
        )

        print(
            "1～1000位がすべて揃っています。"
        )

    else:
        print(
            "順位チェック: NG"
        )

        print(
            f"欠落順位: {missing[:30]}"
        )

    print(
        f"重複順位: {duplicate_count}件"
    )

    print()

    print("【先頭10件】")

    print(
        df.head(10).to_string(
            index=False
        )
    )

    print()

    print("【末尾10件】")

    print(
        df.tail(10).to_string(
            index=False
        )
    )

    print(
        "======================================"
    )


def save_server_csv(
    rows,
    server_name
):
    """Virba / EdaランキングをCSVに保存"""

    if not rows:
        print()
        print(
            f"{server_name}ランキングデータを取得できませんでした。"
        )
        return

    df = pd.DataFrame(rows)

    today = datetime.now().strftime(
        "%Y%m%d"
    )

    filename = (
        SERVER_DATA_DIR /
        f"ranking_{server_name.lower()}_{today}.csv"
    )

    df.to_csv(
        filename,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print(
        f"========== {server_name}ランキング =========="
    )

    print(
        f"取得件数: {len(df)}"
    )

    print(
        f"保存先: {filename.resolve()}"
    )

    # 順位チェック
    expected = set(
        range(1, 101)
    )

    actual = set(
        df["rank"]
    )

    missing = sorted(
        expected - actual
    )

    duplicate_count = (
        df["rank"]
        .duplicated()
        .sum()
    )

    print()

    if not missing:
        print(
            "順位チェック: OK"
        )

        print(
            "1～100位がすべて揃っています。"
        )

    else:
        print(
            "順位チェック: NG"
        )

        print(
            f"欠落順位: {missing[:30]}"
        )

    print(
        f"重複順位: {duplicate_count}件"
    )

    print()

    print("【先頭5件】")

    print(
        df.head(5).to_string(
            index=False
        )
    )

    print()

    print("【末尾5件】")

    print(
        df.tail(5).to_string(
            index=False
        )
    )

    print(
        "======================================"
    )


def main():

    print(
        "HIT : The World ランキング取得"
    )

    print(
        "=" * 50
    )

    print(
        "公式サイトへ接続中..."
    )

    html = get_ranking_page()

    print(
        f"取得HTMLサイズ: "
        f"{len(html):,} bytes"
    )

    print()

    print(
        "ランキングを解析中..."
    )

    (
        world_rows,
        virba_rows,
        eda_rows
    ) = parse_rankings(html)

    # 全体
    save_world_csv(
        world_rows
    )

    # Virba
    save_server_csv(
        virba_rows,
        "Virba"
    )

    # Eda
    save_server_csv(
        eda_rows,
        "Eda"
    )


if __name__ == "__main__":
    main()