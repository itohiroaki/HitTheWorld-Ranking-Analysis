import requests
from bs4 import BeautifulSoup
from pathlib import Path


URL = "https://hittheworld.nexon.com/ranking/worldranking"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    )
}


def inspect_table(table, name):

    print()
    print("=" * 70)
    print(f"{name}ランキング")
    print("=" * 70)

    rows = table.find_all("tr")

    print(
        f"HTML上の行数: {len(rows)}"
    )

    for index, row in enumerate(rows):

        cells = row.find_all(
            ["th", "td"]
        )

        values = [
            cell.get_text(
                " ",
                strip=True
            )
            for cell in cells
        ]

        # ----------------------------------------------
        # データ行だけ確認
        # ----------------------------------------------

        if index == 0:
            continue

        # 5セル未満の行を表示
        if len(cells) < 5:

            print()
            print(
                f"★ 特殊行 "
                f"(HTML行 {index})"
            )

            print(
                f"セル数: {len(cells)}"
            )

            print(
                f"テキスト: {values}"
            )

            print(
                "HTML:"
            )

            print(
                row.prettify()[:3000]
            )

            continue

        # ----------------------------------------------
        # 順位が取れない行を確認
        # ----------------------------------------------

        rank_cell = cells[0]

        rank_text = rank_cell.get_text(
            " ",
            strip=True
        )

        rank_image = rank_cell.find("img")

        if not rank_text and rank_image:

            print()
            print(
                f"★ 画像順位行 "
                f"(HTML行 {index})"
            )

            print(
                f"セル内容: {values}"
            )

            print(
                f"画像class: "
                f"{rank_image.get('class')}"
            )

            print(
                f"画像src: "
                f"{rank_image.get('src')}"
            )

            print(
                "HTML:"
            )

            print(
                row.prettify()[:3000]
            )


def main():

    print("=" * 70)
    print("HIT : The World")
    print("ランキング行構造調査")
    print("=" * 70)

    response = requests.get(
        URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    tables = soup.find_all("table")

    print()
    print(
        f"table数: {len(tables)}"
    )

    if len(tables) < 3:

        print(
            "ランキングtableが3つありません。"
        )

        return

    inspect_table(
        tables[0],
        "WORLD"
    )

    inspect_table(
        tables[1],
        "VIRBA"
    )

    inspect_table(
        tables[2],
        "EDA"
    )


if __name__ == "__main__":
    main()