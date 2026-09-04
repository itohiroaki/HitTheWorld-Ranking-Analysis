import requests
from bs4 import BeautifulSoup


URL = "https://hittheworld.nexon.com/ranking/worldranking"


def get_html():

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


def inspect_table(table, name):

    print()
    print("=" * 80)
    print(f"{name} TABLE")
    print("=" * 80)

    rows = table.find_all("tr")

    print(
        f"tr数: {len(rows)}"
    )

    count = 0

    for index, tr in enumerate(rows):

        master = tr.find(
            "td",
            class_="table__master"
        )

        if master is None:
            continue

        character = master.get_text(
            " ",
            strip=True
        )

        rank_cell = tr.find(
            "td",
            class_="table__rank"
        )

        if rank_cell is None:
            print()
            print(
                f"ROW {index}: 順位セルなし"
            )
            print(
                tr.prettify()[:3000]
            )
            continue

        rank_text = rank_cell.get_text(
            " ",
            strip=True
        )

        img = rank_cell.find("img")

        img_src = ""

        if img is not None:
            img_src = img.get(
                "src",
                ""
            )

        print()
        print(
            f"ROW {index}"
        )

        print(
            f" character = {character}"
        )

        print(
            f" rank_text = {rank_text!r}"
        )

        print(
            f" img_src = {img_src!r}"
        )

        print(
            " rank_html:"
        )

        print(
            rank_cell.prettify()
        )

        count += 1

        if count >= 20:
            break


def main():

    print(
        "公式ランキングページ取得中..."
    )

    html = get_html()

    print(
        f"HTMLサイズ: {len(html):,} bytes"
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    tables = soup.find_all(
        "table"
    )

    print(
        f"table数: {len(tables)}"
    )

    if len(tables) < 3:
        print(
            "ランキングテーブルが3つ見つかりません。"
        )
        return

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