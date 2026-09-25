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


def get_player_names(player):

    names = set(
        player.get(
            "names",
            []
        )
    )

    current_name = (
        player.get(
            "character",
            ""
        )
    )

    if current_name:
        names.add(
            current_name
        )

    return names


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

    for character_name, player in players.items():

        all_names = get_player_names(
            player
        )

        if any(
            keyword in str(name).lower()
            for name in all_names
        ):

            candidates.append({
                "tracking_id":
                    player.get(
                        "tracking_id",
                        ""
                    ),

                "character":
                    player.get(
                        "character",
                        character_name
                    ),

                "names":
                    sorted(
                        all_names
                    )
            })

    return candidates


def find_exact_name(
    players,
    name
):

    name = str(name).strip()

    if not name:
        return []

    candidates = []

    for character_name, player in players.items():

        all_names = get_player_names(
            player
        )

        if name in all_names:

            candidates.append({
                "tracking_id":
                    player.get(
                        "tracking_id",
                        ""
                    ),

                "character":
                    player.get(
                        "character",
                        character_name
                    ),

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


def merge_links(
    links,
    tracking_ids,
    canonical_tracking_id=None
):

    tracking_ids = list(
        dict.fromkeys(
            tracking_ids
        )
    )

    if not tracking_ids:
        return

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

    # 新規登録
    if not groups:

        if canonical_tracking_id is None:
            canonical_tracking_id = tracking_ids[0]

        links.append({
            "canonical_tracking_id":
                canonical_tracking_id,

            "tracking_ids":
                tracking_ids,

            "confirmed":
                True,

            "reason":
                "ユーザー確認"
        })

        return

    # 既存グループを統合
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

    # canonicalを明示指定していれば、
    # それを優先する
    if canonical_tracking_id is None:

        canonical = groups[0].get(
            "canonical_tracking_id",
            tracking_ids[0]
        )

    else:

        canonical = canonical_tracking_id

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


def save_link(
    links_data,
    links,
    tracking_ids,
    canonical_tracking_id=None
):

    merge_links(
        links,
        tracking_ids,
        canonical_tracking_id
    )

    links_data["links"] = links

    save_json(
        PLAYER_LINKS_FILE,
        links_data
    )


def search_and_link(
    players,
    links_data,
    links
):

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

    print()
    print("-" * 60)
    print("以下を同一人物としてリンクします。")
    print("-" * 60)

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

    save_link(
        links_data,
        links,
        tracking_ids
    )

    print(
        "\n同一人物リンクを保存しました。"
    )


def manual_link_by_names(
    players,
    links_data,
    links
):

    print()
    print("-" * 60)
    print("現在名・過去名を指定して紐づけ")
    print("-" * 60)

    current_name = input(
        "\n現在のキャラクター名: "
    ).strip()

    if not current_name:

        print(
            "\nキャンセルしました。"
        )

        return

    old_name = input(
        "過去のキャラクター名: "
    ).strip()

    if not old_name:

        print(
            "\nキャンセルしました。"
        )

        return

    current_candidates = find_exact_name(
        players,
        current_name
    )

    old_candidates = find_exact_name(
        players,
        old_name
    )

    if not current_candidates:

        print(
            f"\n現在名「{current_name}」が"
            "履歴から見つかりません。"
        )

        return

    if not old_candidates:

        print(
            f"\n過去名「{old_name}」が"
            "履歴から見つかりません。"
        )

        return

    print()
    print("現在名の候補")
    print("-" * 60)

    for index, candidate in enumerate(
        current_candidates,
        start=1
    ):

        print_candidate(
            index,
            candidate
        )

    print()
    print("過去名の候補")
    print("-" * 60)

    for index, candidate in enumerate(
        old_candidates,
        start=1
    ):

        print_candidate(
            index,
            candidate
        )

    if len(current_candidates) == 1:

        current = current_candidates[0]

        print()
        print(
            "現在名は1件に特定されました。"
        )

    else:

        print()
        print(
            "現在名の候補から使用する番号を入力してください。"
        )

        current_selection = input(
            "> "
        ).strip()

        try:
            current_index = (
                int(current_selection) - 1
            )
        except ValueError:

            print(
                "\n入力が正しくありません。"
            )

            return

        if (
            current_index < 0
            or current_index >= len(
                current_candidates
            )
        ):

            print(
                "\n番号が不正です。"
            )

            return

        current = current_candidates[
            current_index
        ]

    if len(old_candidates) == 1:

        old = old_candidates[0]

        print(
            "過去名も1件に特定されました。"
        )

    else:

        print()
        print(
            "過去名の候補から使用する番号を入力してください。"
        )

        old_selection = input(
            "> "
        ).strip()

        try:
            old_index = (
                int(old_selection) - 1
            )
        except ValueError:

            print(
                "\n入力が正しくありません。"
            )

            return

        if (
            old_index < 0
            or old_index >= len(
                old_candidates
            )
        ):

            print(
                "\n番号が不正です。"
            )

            return

        old = old_candidates[
            old_index
        ]

    if (
        current["tracking_id"]
        ==
        old["tracking_id"]
    ):

        print()
        print(
            "この2つの名前は、すでに"
            "同じプレイヤー履歴です。"
        )

        return

    existing_current = get_link_group(
        links,
        current["tracking_id"]
    )

    existing_old = get_link_group(
        links,
        old["tracking_id"]
    )

    if existing_current:

        print()
        print(
            "注意: 現在名はすでに"
            "別の紐づけに登録されています。"
        )

    if existing_old:

        print(
            "注意: 過去名はすでに"
            "別の紐づけに登録されています。"
        )

    print()
    print("=" * 60)
    print("最終確認")
    print("=" * 60)

    print(
        f"過去名 : {old['character']}"
    )

    print(
        f"         {old['tracking_id']}"
    )

    print()
    print("        ↓")

    print()

    print(
        f"現在名 : {current['character']}"
    )

    print(
        f"         {current['tracking_id']}"
    )

    print("=" * 60)

    confirm = input(
        "\nこの内容で登録しますか？ [y/N]: "
    ).strip().lower()

    if confirm != "y":

        print(
            "\nキャンセルしました。"
        )

        return

    # 現在名側をcanonicalにする
    save_link(
        links_data,
        links,
        [
            old["tracking_id"],
            current["tracking_id"]
        ],
        canonical_tracking_id=current["tracking_id"]
    )

    print()
    print(
        "同一人物リンクを保存しました。"
    )

    print(
        f"{old['character']} → "
        f"{current['character']}"
    )


def show_links(
    players,
    links
):

    print()
    print("=" * 60)
    print("現在の手動紐づけ一覧")
    print("=" * 60)

    if not links:

        print(
            "登録されている紐づけはありません。"
        )

        return

    # tracking_id → プレイヤー情報
    tracking_map = {}

    for character_name, player in players.items():

        tracking_id = player.get(
            "tracking_id",
            ""
        )

        if tracking_id:

            tracking_map[tracking_id] = player

    for index, link in enumerate(
        links,
        start=1
    ):

        tracking_ids = link.get(
            "tracking_ids",
            []
        )

        canonical_id = link.get(
            "canonical_tracking_id",
            ""
        )

        current = tracking_map.get(
            canonical_id
        )

        old_names = []

        for tracking_id in tracking_ids:

            if tracking_id == canonical_id:
                continue

            player = tracking_map.get(
                tracking_id
            )

            if not player:
                continue

            old_names.extend(
                get_player_names(
                    player
                )
            )

        print()
        print(
            f"[{index}]"
        )

        if current:

            print(
                f"    現在名: "
                f"{current.get('character', '')}"
            )

            print(
                f"    tracking_id: "
                f"{canonical_id}"
            )

        else:

            print(
                f"    現在名: 不明"
            )

            print(
                f"    canonical_tracking_id: "
                f"{canonical_id}"
            )

        current_name = (
            current.get("character", "")
            if current
            else ""
        )

        old_names = sorted(
            set(
                name
                for name in old_names
                if name != current_name
            )
        )

        if old_names:

            print(
                "    過去名: "
                + " / ".join(
                    old_names
                )
            )

        print(
            f"    紐づけ人数: "
            f"{len(tracking_ids)}人"
        )


def test_resolve_tracking_id():

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
        print(
            "テスト結果: 全てOK"
        )
    else:
        print(
            "テスト結果: NGあり"
        )

    print("=" * 60)

    return success


def test_real_player_links():

    links = load_json(
        PLAYER_LINKS_FILE
    )

    print()
    print("=" * 60)
    print("実データによる同一人物リンク解決テスト")
    print("=" * 60)

    if not links.get("links"):

        print(
            "リンク情報がありません。"
        )

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

            ok = (
                result
                ==
                canonical_id
            )

            print(
                f"  {tracking_id} -> "
                f"{result} "
                f"{'OK' if ok else 'NG'}"
            )

            if not ok:
                success = False

    print()

    if success:
        print(
            "テスト結果: 全てOK"
        )
    else:
        print(
            "テスト結果: NGあり"
        )

    print("=" * 60)

    return success


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

    while True:

        print()
        print("=" * 60)
        print("メニュー")
        print("=" * 60)

        print(
            "1. 名前を検索して紐づけ"
        )

        print(
            "2. 現在名・過去名を指定して紐づけ"
        )

        print(
            "3. 現在の紐づけ一覧"
        )

        print(
            "4. 実データのリンクテスト"
        )

        print(
            "5. 終了"
        )

        choice = input(
            "\n番号を選択してください: "
        ).strip()

        if choice == "1":

            search_and_link(
                players,
                links_data,
                links
            )

        elif choice == "2":

            manual_link_by_names(
                players,
                links_data,
                links
            )

        elif choice == "3":

            show_links(
                players,
                links
            )

        elif choice == "4":

            test_real_player_links()

        elif choice == "5":

            print(
                "\n終了します。"
            )

            break

        else:

            print(
                "\n1～5の番号を入力してください。"
            )


if __name__ == "__main__":
    main()