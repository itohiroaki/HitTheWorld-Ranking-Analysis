import json
from pathlib import Path

from player_history import resolve_tracking_id


BASE_DIR = Path(__file__).resolve().parent

PLAYER_HISTORY_FILE = (
    BASE_DIR
    / "data"
    / "history"
    / "player_history.json"
)

PLAYER_LINKS_FILE = (
    BASE_DIR
    / "data"
    / "history"
    / "player_links.json"
)


def load_json(path):
    if not path.exists():
        return {}

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def save_json(path, data):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


def load_players():

    data = load_json(
        PLAYER_HISTORY_FILE
    )

    return data


def find_candidates(
    players,
    keyword
):

    keyword = (
        str(keyword)
        .strip()
        .lower()
    )

    candidates = []

    for tracking_id, player in players.items():

        names = player.get(
            "names",
            []
        )

        current_name = (
            player.get(
                "character",
                ""
            )
        )

        all_names = set(
            names
        )

        if current_name:
            all_names.add(
                current_name
            )

        if any(
            keyword in str(name).lower()
            for name in all_names
        ):

            candidates.append({
                "tracking_id":
                    tracking_id,

                "character":
                    current_name,

                "names":
                    sorted(
                        all_names
                    )
            })

    return candidates


def get_link_group(
    links,
    tracking_id
):

    for link in links:

        if tracking_id in link.get(
            "tracking_ids",
            []
        ):

            return link

    return None


def test_resolve_tracking_id():
    """
    同一人物リンク解決機能の簡易テスト。
    実ファイルは変更しない。
    """

    test_links = [
        {
            "canonical_tracking_id":
                "player_main",

            "tracking_ids": [
                "player_old",
                "player_middle",
                "player_main"
            ],

            "confirmed":
                True
        }
    ]

    test_cases = [
        (
            "player_old",
            "player_main"
        ),
        (
            "player_middle",
            "player_main"
        ),
        (
            "player_main",
            "player_main"
        ),
        (
            "player_unknown",
            "player_unknown"
        ),
    ]

    print()
    print("=" * 60)
    print("同一人物リンク解決テスト")
    print("=" * 60)

    success = True

    for tracking_id, expected in test_cases:

        result = resolve_tracking_id(
            tracking_id,
            test_links
        )

        ok = result == expected

        print(
            f"{tracking_id} -> "
            f"{result} "
            f"{'OK' if ok else 'NG'}"
        )

        if not ok:
            success = False

    print()

    if success:
        print("テスト結果: 全てOK")
    else:
        print("テスト結果: NGあり")

    print("=" * 60)

    return success

def test_real_player_links():
    """
    実際の player_links.json を読み込み、
    登録されている tracking_id が
    canonical_tracking_id に解決できるか確認する。
    """

    links = load_json(
        PLAYER_LINKS_FILE
    )

    print()
    print("=" * 60)
    print("実データによる同一人物リンク解決テスト")
    print("=" * 60)

    if not links.get("links"):
        print("リンク情報がありません。")
        print("=" * 60)
        return True

    success = True

    for link in links["links"]:

        canonical_id = link.get(
            "canonical_tracking_id"
        )

        tracking_ids = link.get(
            "tracking_ids",
            []
        )

        print()
        print(
            f"canonical: {canonical_id}"
        )

        for tracking_id in tracking_ids:

            result = resolve_tracking_id(
                tracking_id,
                links["links"]
            )

            ok = result == canonical_id

            print(
                f"  {tracking_id} -> "
                f"{result} "
                f"{'OK' if ok else 'NG'}"
            )

            if not ok:
                success = False

    print()

    if success:
        print("テスト結果: 全てOK")
    else:
        print("テスト結果: NGあり")

    print("=" * 60)

    return success

def merge_links(
    links,
    tracking_ids
):

    tracking_ids = list(
        dict.fromkeys(
            tracking_ids
        )
    )

    groups = []

    for link in links:

        if any(
            tracking_id in link.get(
                "tracking_ids",
                []
            )
            for tracking_id in tracking_ids
        ):

            groups.append(link)

    if not groups:

        links.append({
            "canonical_tracking_id":
                tracking_ids[0],

            "tracking_ids":
                tracking_ids,

            "confirmed":
                True,

            "reason":
                "ユーザー確認"
        })

        return

    canonical = groups[0].get(
        "canonical_tracking_id",
        tracking_ids[0]
    )

    merged_ids = set(
        tracking_ids
    )

    for group in groups:

        merged_ids.update(
            group.get(
                "tracking_ids",
                []
            )
        )

    links[:] = [
        link
        for link in links
        if link not in groups
    ]

    links.append({
        "canonical_tracking_id":
            canonical,

        "tracking_ids":
            sorted(
                merged_ids
            ),

        "confirmed":
            True,

        "reason":
            "ユーザー確認"
    })


def print_candidate(
    index,
    candidate
):

    print(
        f"\n[{index}] "
        f"{candidate['character']}"
    )

    print(
        f"    tracking_id: "
        f"{candidate['tracking_id']}"
    )

    print(
        "    名前履歴: "
        + " → ".join(
            candidate["names"]
        )
    )


def main():

    print("=" * 60)
    print("HIT : The World")
    print("キャラクター同一人物リンク管理")
    print("=" * 60)

    players = load_players()

    if not players:

        print(
            "\nplayer_history.json "
            "からプレイヤーを取得できません。"
        )

        return

    links_data = load_json(
        PLAYER_LINKS_FILE
    )

    links = links_data.get(
        "links",
        []
    )

    keyword = input(
        "\nキャラクター名を入力: "
    ).strip()

    if not keyword:

        return

    candidates = find_candidates(
        players,
        keyword
    )

    if not candidates:

        print(
            "\n候補が見つかりません。"
        )

        return

    print(
        f"\n候補: {len(candidates)}件"
    )

    for index, candidate in enumerate(
        candidates,
        start=1
    ):

        print_candidate(
            index,
            candidate
        )

    print(
        "\n同一人物としてリンクする番号を"
        "スペース区切りで入力してください。"
    )

    print(
        "例: 1 2 3"
    )

    selection = input(
        "> "
    ).strip()

    if not selection:

        return

    try:

        indexes = [
            int(value) - 1
            for value in selection.split()
        ]

    except ValueError:

        print(
            "\n入力が正しくありません。"
        )

        return

    selected = []

    for index in indexes:

        if (
            index < 0
            or index >= len(candidates)
        ):

            print(
                f"\n番号が不正です: "
                f"{index + 1}"
            )

            return

        selected.append(
            candidates[index]
        )

    tracking_ids = [
        candidate["tracking_id"]
        for candidate in selected
    ]

    if len(tracking_ids) < 2:

        print(
            "\n2人以上を選択してください。"
        )

        return

    print("\n----------------------------------------")
    print("以下を同一人物としてリンクします。")
    print("----------------------------------------")

    for candidate in selected:

        print(
            f"- {candidate['character']}"
            f" ({candidate['tracking_id']})"
        )

    confirm = input(
        "\n確定しますか？ [y/N]: "
    ).strip().lower()

    if confirm != "y":

        print(
            "\nキャンセルしました。"
        )

        return

    merge_links(
        links,
        tracking_ids
    )

    links_data["links"] = links

    save_json(
        PLAYER_LINKS_FILE,
        links_data
    )

    print(
        "\n同一人物リンクを保存しました。"
    )


if __name__ == "__main__":
    main()