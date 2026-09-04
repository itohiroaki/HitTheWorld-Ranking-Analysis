import json
import re
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd


# ============================================================
# パス
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

HISTORY_FILE = (
    BASE_DIR
    / "data"
    / "history"
    / "player_history.json"
)

SERVER_RANKING_DIR = (
    BASE_DIR
    / "data"
    / "ranking_server"
)


# ============================================================
# イベント名
#
# player_history.py の実際のイベント名に合わせる
# ============================================================

EVENT_LABELS = {
    "server_ranking_entry": "TOP100ランキング入り",
    "server_ranking_exit": "TOP100ランキング圏外",

    # ★重要
    # 実際のイベント名は server_rank_up / down
    "server_rank_up": "サーバー順位上昇",
    "server_rank_down": "サーバー順位下降",

    "server_ranking_level_up": "サーバーランキングレベルアップ",
    "server_ranking_level_down": "サーバーランキングレベルダウン",
    "server_ranking_server_change": "サーバーランキングサーバー変更",
    "server_ranking_guild_change": "サーバーランキングギルド変更",
}


# ============================================================
# 共通関数
# ============================================================

def load_history():
    """player_history.jsonを読み込む"""

    if not HISTORY_FILE.exists():

        print()
        print("ERROR: 履歴ファイルがありません。")
        print(f"  {HISTORY_FILE}")

        return None

    try:

        with HISTORY_FILE.open(
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except json.JSONDecodeError as e:

        print()
        print("ERROR: JSONの読み込みに失敗しました。")
        print(f"  {e}")

        return None


def normalize(value):
    """None等を空文字に統一"""

    if value is None:
        return ""

    return str(value).strip()


def to_int(value):
    """数値化"""

    if value is None or value == "":
        return None

    try:
        return int(value)

    except (TypeError, ValueError):
        return None


def get_players(data):
    """player_history.jsonのplayersを取得"""

    if isinstance(data, dict):

        players = data.get(
            "players",
            data
        )

    else:

        players = data

    if isinstance(players, dict):

        return players

    if isinstance(players, list):

        result = {}

        for player in players:

            if not isinstance(
                player,
                dict
            ):
                continue

            character = normalize(
                player.get("character")
            )

            if character:

                result[character] = player

        return result

    return {}


def get_history(player):
    """historyを日付順に取得"""

    history = player.get(
        "history",
        []
    )

    if not isinstance(
        history,
        list
    ):

        return []

    return sorted(
        [
            x
            for x in history
            if isinstance(x, dict)
        ],
        key=lambda x: normalize(
            x.get("date")
        )
    )


def get_server_record(record):
    """
    その日のEda / Virba TOP100状態を取得。

    Edaを優先。
    EdaにいなければVirba。
    """

    server_ranking = record.get(
        "server_ranking",
        {}
    )

    if not isinstance(
        server_ranking,
        dict
    ):

        return None, None

    for group in (
        "Eda",
        "Virba"
    ):

        item = server_ranking.get(
            group
        )

        if (
            isinstance(item, dict)
            and item.get("visible") is True
        ):

            return group, item

    return None, None


def event_type(event):
    """
    イベント種別。

    player_history.pyでは type を使用。

    event_type は過去形式との互換用。
    """

    if not isinstance(
        event,
        dict
    ):

        return ""

    return normalize(
        event.get("type")
        or event.get("event_type")
    )


def event_date(event):
    """イベント日付"""

    if not isinstance(
        event,
        dict
    ):

        return ""

    return normalize(
        event.get("date")
    )


def add_error(
    errors,
    message
):

    errors.append(message)


def add_warning(
    warnings,
    message
):

    warnings.append(message)


# ============================================================
# CSV関連
# ============================================================

def extract_date_from_filename(path):
    """ファイル名からYYYYMMDDを取得"""

    match = re.search(
        r"(20\d{6})",
        path.stem
    )

    if match:

        return match.group(1)

    return None


def get_group_from_filename(path):
    """ファイル名からEda / Virbaを取得"""

    name = path.stem.lower()

    if "virba" in name:

        return "Virba"

    if "eda" in name:

        return "Eda"

    return None


def load_server_csv_availability():
    """
    data/ranking_server内のCSV存在状況を取得。

    戻り値:

        {
            "20260902": {
                "Eda": True,
                "Virba": True
            }
        }
    """

    availability = defaultdict(
        lambda: {
            "Eda": False,
            "Virba": False
        }
    )

    if not SERVER_RANKING_DIR.exists():

        return {}

    csv_files = sorted(
        SERVER_RANKING_DIR.glob("*.csv")
    )

    for file_path in csv_files:

        date = extract_date_from_filename(
            file_path
        )

        group = get_group_from_filename(
            file_path
        )

        if not date:
            continue

        if group not in (
            "Eda",
            "Virba"
        ):
            continue

        availability[
            date
        ][group] = True

    return dict(availability)


def load_server_csv_players():
    """
    元CSVから各日・各グループの
    TOP100キャラクターを取得。
    """

    result = defaultdict(
        lambda: {
            "Eda": set(),
            "Virba": set()
        }
    )

    if not SERVER_RANKING_DIR.exists():

        return {}

    csv_files = sorted(
        SERVER_RANKING_DIR.glob("*.csv")
    )

    for file_path in csv_files:

        date = extract_date_from_filename(
            file_path
        )

        group = get_group_from_filename(
            file_path
        )

        if not date:
            continue

        if group not in (
            "Eda",
            "Virba"
        ):
            continue

        try:

            df = pd.read_csv(
                file_path,
                dtype=str
            )

        except Exception:

            continue

        if df.empty:

            continue

        # ----------------------------------------------------
        # character列を探す
        # ----------------------------------------------------

        character_column = None

        for column in df.columns:

            normalized = str(
                column
            ).strip().lower()

            if normalized in (
                "character",
                "キャラクター",
                "キャラ",
                "name",
                "名前",
            ):

                character_column = column
                break

        if character_column is None:

            continue

        for value in df[
            character_column
        ].dropna():

            character = normalize(
                value
            )

            if character:

                result[
                    date
                ][group].add(
                    character
                )

    return {
        date: {
            "Eda": set(data["Eda"]),
            "Virba": set(data["Virba"])
        }
        for date, data in result.items()
    }


# ============================================================
# 1. 基本構造チェック
# ============================================================

def verify_basic_structure(
    players,
    errors,
    warnings
):

    print()
    print("[1] 基本構造チェック")
    print("-" * 50)

    required_player_keys = {
        "tracking_id",
        "character",
        "names",
        "status",
        "world_snapshot",
        "current",
        "last_known",
        "summary",
        "events",
        "history",
    }

    for character, player in players.items():

        if not isinstance(
            player,
            dict
        ):

            add_error(
                errors,
                f"{character}: playerデータがdictではありません"
            )

            continue

        missing = (
            required_player_keys
            - set(player.keys())
        )

        if missing:

            add_error(
                errors,
                f"{character}: 必須キー不足 "
                f"{sorted(missing)}"
            )

        if not isinstance(
            player.get("history", []),
            list
        ):

            add_error(
                errors,
                f"{character}: historyがlistではありません"
            )

        if not isinstance(
            player.get("events", []),
            list
        ):

            add_error(
                errors,
                f"{character}: eventsがlistではありません"
            )

    print(
        f"  プレイヤー数: {len(players):,}人"
    )


# ============================================================
# 2. historyチェック
# ============================================================

def verify_history(
    players,
    errors,
    warnings
):

    print()
    print("[2] historyチェック")
    print("-" * 50)

    total_records = 0

    for character, player in players.items():

        history = get_history(
            player
        )

        total_records += len(
            history
        )

        dates = []

        for record in history:

            date = normalize(
                record.get("date")
            )

            if not date:

                add_error(
                    errors,
                    f"{character}: historyに日付なし"
                )

                continue

            dates.append(date)

        duplicates = [
            date
            for date, count
            in Counter(dates).items()
            if count > 1
        ]

        if duplicates:

            add_error(
                errors,
                f"{character}: historyの日付重複 "
                f"{duplicates}"
            )

    print(
        f"  historyレコード数: "
        f"{total_records:,}件"
    )


# ============================================================
# 3. current / last_known / status
# ============================================================

def verify_current_and_last_known(
    players,
    errors,
    warnings
):

    print()
    print("[3] current / last_known / statusチェック")
    print("-" * 50)

    checked = 0

    for character, player in players.items():

        history = get_history(
            player
        )

        if not history:
            continue

        checked += 1

        latest_record = history[-1]

        latest_date = normalize(
            latest_record.get("date")
        )

        current = player.get(
            "current",
            {}
        )

        last_known = player.get(
            "last_known",
            {}
        )

        status = player.get(
            "status",
            {}
        )

        latest_group, latest_server_record = (
            get_server_record(
                latest_record
            )
        )

        active = (
            status.get("active") is True
        )

        # ----------------------------------------------------
        # 最新日にTOP100表示
        # ----------------------------------------------------

        if latest_group is not None:

            if not active:

                add_error(
                    errors,
                    f"{character}: "
                    f"{latest_date}にTOP100表示なのに"
                    f"active=False"
                )

            expected_level = to_int(
                latest_server_record.get(
                    "level"
                )
            )

            actual_level = to_int(
                current.get("level")
            )

            if expected_level != actual_level:

                add_error(
                    errors,
                    f"{character}: current.level不一致 "
                    f"(expected={expected_level}, "
                    f"actual={actual_level})"
                )

            expected_server = normalize(
                latest_server_record.get(
                    "server"
                )
            )

            actual_server = normalize(
                current.get("server")
            )

            if expected_server != actual_server:

                add_error(
                    errors,
                    f"{character}: current.server不一致 "
                    f"(expected={expected_server}, "
                    f"actual={actual_server})"
                )

        # ----------------------------------------------------
        # 最新日にTOP100非表示
        # ----------------------------------------------------

        else:

            if active:

                add_error(
                    errors,
                    f"{character}: "
                    f"{latest_date}にTOP100非表示なのに"
                    f"active=True"
                )

            current_level = current.get(
                "level"
            )

            if current_level not in (
                None,
                "",
                "-"
            ):

                add_error(
                    errors,
                    f"{character}: inactiveなのに"
                    f"current.levelが残っています "
                    f"({current_level})"
                )

            current_server = normalize(
                current.get("server")
            )

            if current_server:

                add_error(
                    errors,
                    f"{character}: inactiveなのに"
                    f"current.serverが残っています "
                    f"({current_server})"
                )

        # ----------------------------------------------------
        # last_known
        # ----------------------------------------------------

        expected = None

        for record in reversed(
            history
        ):

            group, server_record = (
                get_server_record(
                    record
                )
            )

            if group is not None:

                expected = (
                    normalize(
                        record.get("date")
                    ),
                    group,
                    server_record
                )

                break

        if expected is None:

            continue

        expected_date = expected[0]
        expected_group = expected[1]
        expected_record = expected[2]

        actual_date = normalize(
            last_known.get("date")
        )

        if actual_date != expected_date:

            add_error(
                errors,
                f"{character}: last_known.date不一致 "
                f"(expected={expected_date}, "
                f"actual={actual_date})"
            )

        actual_group = normalize(
            last_known.get("group")
        )

        if actual_group != expected_group:

            add_error(
                errors,
                f"{character}: last_known.group不一致 "
                f"(expected={expected_group}, "
                f"actual={actual_group})"
            )

        expected_level = to_int(
            expected_record.get("level")
        )

        actual_level = to_int(
            last_known.get("level")
        )

        if expected_level != actual_level:

            add_error(
                errors,
                f"{character}: last_known.level不一致 "
                f"(expected={expected_level}, "
                f"actual={actual_level})"
            )

    print(
        f"  チェック対象: {checked:,}人"
    )


# ============================================================
# 4. イベント構造チェック
# ============================================================

def verify_events_structure(
    players,
    errors,
    warnings
):

    print()
    print("[4] イベント基本チェック")
    print("-" * 50)

    counter = Counter()
    total = 0

    for character, player in players.items():

        events = player.get(
            "events",
            []
        )

        for event in events:

            if not isinstance(
                event,
                dict
            ):

                add_error(
                    errors,
                    f"{character}: eventがdictではありません"
                )

                continue

            total += 1

            etype = event_type(
                event
            )

            date = event_date(
                event
            )

            if not etype:

                add_error(
                    errors,
                    f"{character}: "
                    f"イベント種別がありません"
                )

                continue

            if not date:

                add_error(
                    errors,
                    f"{character}: "
                    f"イベント日付がありません "
                    f"({etype})"
                )

            counter[etype] += 1

            event_character = normalize(
                event.get("character")
            )

            if (
                event_character
                and event_character != character
            ):

                add_error(
                    errors,
                    f"{character}: "
                    f"event.character不一致 "
                    f"({event_character})"
                )

    print(
        f"  イベント総数: {total:,}件"
    )

    print()

    for etype, count in counter.most_common():

        print(
            f"    "
            f"{EVENT_LABELS.get(etype, etype)}: "
            f"{count}件"
        )

    return counter


# ============================================================
# 5. TOP100 entry / exit
# ============================================================

def verify_entry_exit_logic(
    players,
    errors,
    warnings,
    csv_availability,
    csv_players
):

    print()
    print("[5] TOP100入り / 圏外イベント論理チェック")
    print("-" * 50)

    checked_days = 0
    theoretical_entries = 0
    theoretical_exits = 0

    all_dates = set()

    for player in players.values():

        for record in get_history(
            player
        ):

            date = normalize(
                record.get("date")
            )

            if date:

                all_dates.add(date)

    print()
    print("  サーバーランキングCSV状況:")

    for date in sorted(
        all_dates
    ):

        available = csv_availability.get(
            date,
            {
                "Eda": False,
                "Virba": False
            }
        )

        print(
            f"    {date}: "
            f"Eda={'あり' if available['Eda'] else 'なし'}, "
            f"Virba={'あり' if available['Virba'] else 'なし'}"
        )

    print()

    for character, player in players.items():

        history = get_history(
            player
        )

        events = player.get(
            "events",
            []
        )

        event_map = defaultdict(
            list
        )

        for event in events:

            event_map[
                event_date(event)
            ].append(event)

        previous_visible = False
        has_previous_observation = False

        for record in history:

            date = normalize(
                record.get("date")
            )

            if not date:
                continue

            available = csv_availability.get(
                date,
                {
                    "Eda": False,
                    "Virba": False
                }
            )

            # ------------------------------------------------
            # EdaとVirbaの両方のCSVが存在する日だけ
            # entry / exitを判定
            # ------------------------------------------------

            ranking_available = (
                available.get("Eda") is True
                and available.get("Virba") is True
            )

            if not ranking_available:

                continue

            checked_days += 1

            daily_players = csv_players.get(
                date,
                {
                    "Eda": set(),
                    "Virba": set()
                }
            )

            current_visible = (
                character in daily_players.get(
                    "Eda",
                    set()
                )
                or
                character in daily_players.get(
                    "Virba",
                    set()
                )
            )

            day_events = event_map.get(
                date,
                []
            )

            entry_events = [
                e
                for e in day_events
                if event_type(e)
                == "server_ranking_entry"
            ]

            exit_events = [
                e
                for e in day_events
                if event_type(e)
                == "server_ranking_exit"
            ]

            # ------------------------------------------------
            # 初回観測
            # ------------------------------------------------

            if not has_previous_observation:

                if current_visible:

                    theoretical_entries += 1

                    if not entry_events:

                        add_error(
                            errors,
                            f"{character}: {date} "
                            f"初回TOP100表示なのに "
                            f"entryイベントなし"
                        )

                has_previous_observation = True
                previous_visible = current_visible

                continue

            # ------------------------------------------------
            # 圏外 → TOP100
            # ------------------------------------------------

            if (
                not previous_visible
                and current_visible
            ):

                theoretical_entries += 1

                if not entry_events:

                    add_error(
                        errors,
                        f"{character}: {date} "
                        f"TOP100表示なのに "
                        f"entryイベントなし"
                    )

            # ------------------------------------------------
            # TOP100 → 圏外
            # ------------------------------------------------

            elif (
                previous_visible
                and not current_visible
            ):

                theoretical_exits += 1

                if not exit_events:

                    add_error(
                        errors,
                        f"{character}: {date} "
                        f"TOP100圏外なのに "
                        f"exitイベントなし"
                    )

            # ------------------------------------------------
            # TOP100継続
            # ------------------------------------------------

            elif (
                previous_visible
                and current_visible
            ):

                if entry_events:

                    add_error(
                        errors,
                        f"{character}: {date} "
                        f"TOP100継続なのに "
                        f"entryイベントあり"
                    )

                if exit_events:

                    add_error(
                        errors,
                        f"{character}: {date} "
                        f"TOP100継続なのに "
                        f"exitイベントあり"
                    )

            previous_visible = current_visible

    print(
        f"  判定可能な日次状態: "
        f"{checked_days:,}件"
    )

    print(
        f"  理論上のentryイベント: "
        f"{theoretical_entries:,}件"
    )

    print(
        f"  理論上のexitイベント: "
        f"{theoretical_exits:,}件"
    )


# ============================================================
# 6. 順位 / Lv / サーバー / ギルド
# ============================================================

def verify_change_events(
    players,
    errors,
    warnings
):

    print()
    print(
        "[6] 順位 / Lv / サーバー / "
        "ギルド変更イベントチェック"
    )
    print("-" * 50)

    expected_counts = Counter()

    for character, player in players.items():

        history = get_history(
            player
        )

        events = player.get(
            "events",
            []
        )

        event_by_date = defaultdict(
            list
        )

        for event in events:

            event_by_date[
                event_date(event)
            ].append(event)

        previous_record = None

        for record in history:

            date = normalize(
                record.get("date")
            )

            group, current_record = (
                get_server_record(
                    record
                )
            )

            # ------------------------------------------------
            # TOP100でなければ比較しない
            # ------------------------------------------------

            if (
                group is None
                or current_record is None
            ):

                continue

            # ------------------------------------------------
            # 初回観測
            # ------------------------------------------------

            if previous_record is None:

                previous_record = current_record

                continue

            day_events = event_by_date.get(
                date,
                []
            )

            # ------------------------------------------------
            # 順位
            #
            # ★実際のイベント名:
            #   server_rank_up
            #   server_rank_down
            # ------------------------------------------------

            old_rank = to_int(
                previous_record.get("rank")
            )

            new_rank = to_int(
                current_record.get("rank")
            )

            if (
                old_rank is not None
                and new_rank is not None
            ):

                if new_rank < old_rank:

                    expected_type = (
                        "server_rank_up"
                    )

                elif new_rank > old_rank:

                    expected_type = (
                        "server_rank_down"
                    )

                else:

                    expected_type = None

                if expected_type:

                    expected_counts[
                        expected_type
                    ] += 1

                    matching = [
                        e
                        for e in day_events
                        if event_type(e)
                        == expected_type
                    ]

                    if not matching:

                        add_error(
                            errors,
                            f"{character}: {date} "
                            f"{old_rank}位→{new_rank}位なのに "
                            f"{expected_type}なし"
                        )

            # ------------------------------------------------
            # レベル
            # ------------------------------------------------

            old_level = to_int(
                previous_record.get("level")
            )

            new_level = to_int(
                current_record.get("level")
            )

            if (
                old_level is not None
                and new_level is not None
            ):

                if new_level > old_level:

                    expected_type = (
                        "server_ranking_level_up"
                    )

                elif new_level < old_level:

                    expected_type = (
                        "server_ranking_level_down"
                    )

                else:

                    expected_type = None

                if expected_type:

                    expected_counts[
                        expected_type
                    ] += 1

                    matching = [
                        e
                        for e in day_events
                        if event_type(e)
                        == expected_type
                    ]

                    if not matching:

                        add_error(
                            errors,
                            f"{character}: {date} "
                            f"Lv{old_level}→Lv{new_level}なのに "
                            f"{expected_type}なし"
                        )

            # ------------------------------------------------
            # サーバー変更
            # ------------------------------------------------

            old_server = normalize(
                previous_record.get("server")
            )

            new_server = normalize(
                current_record.get("server")
            )

            if (
                old_server
                and new_server
                and old_server != new_server
            ):

                expected_type = (
                    "server_ranking_server_change"
                )

                expected_counts[
                    expected_type
                ] += 1

                matching = [
                    e
                    for e in day_events
                    if event_type(e)
                    == expected_type
                ]

                if not matching:

                    add_error(
                        errors,
                        f"{character}: {date} "
                        f"{old_server}→{new_server}なのに "
                        f"サーバー変更イベントなし"
                    )

            # ------------------------------------------------
            # ギルド変更
            #
            # 両方に値がある場合だけ変更とみなす
            # ------------------------------------------------

            old_guild = normalize(
                previous_record.get("guild")
            )

            new_guild = normalize(
                current_record.get("guild")
            )

            if (
                old_guild
                and new_guild
                and old_guild != new_guild
            ):

                expected_type = (
                    "server_ranking_guild_change"
                )

                expected_counts[
                    expected_type
                ] += 1

                matching = [
                    e
                    for e in day_events
                    if event_type(e)
                    == expected_type
                ]

                if not matching:

                    add_error(
                        errors,
                        f"{character}: {date} "
                        f"ギルド変更なのに "
                        f"イベントなし "
                        f"({old_guild!r}→{new_guild!r})"
                    )

            previous_record = current_record

    print(
        "  理論上検出される変更:"
    )

    if not expected_counts:

        print(
            "    変更なし"
        )

    else:

        for etype, count in (
            expected_counts.items()
        ):

            print(
                f"    "
                f"{EVENT_LABELS.get(etype, etype)}: "
                f"{count}件"
            )


# ============================================================
# 7. 欠損日 / 圏外判定
# ============================================================

def verify_missing_day_handling(
    players,
    errors,
    warnings,
    csv_availability
):

    print()
    print(
        "[7] 欠損日 / 圏外判定チェック"
    )
    print("-" * 50)

    suspicious = 0

    dates = set()

    for player in players.values():

        for record in get_history(
            player
        ):

            date = normalize(
                record.get("date")
            )

            if date:

                dates.add(date)

    missing_days = []

    for date in sorted(
        dates
    ):

        available = csv_availability.get(
            date,
            {
                "Eda": False,
                "Virba": False
            }
        )

        if not (
            available.get("Eda") is True
            and available.get("Virba") is True
        ):

            missing_days.append(
                date
            )

    if missing_days:

        print(
            "  サーバーランキング欠損日:"
        )

        for date in missing_days:

            available = csv_availability.get(
                date,
                {
                    "Eda": False,
                    "Virba": False
                }
            )

            print(
                f"    {date}: "
                f"Eda={'あり' if available.get('Eda') else 'なし'}, "
                f"Virba={'あり' if available.get('Virba') else 'なし'}"
            )

    else:

        print(
            "  サーバーランキング欠損日: なし"
        )

    # --------------------------------------------------------
    # 欠損日にexitがないか
    # --------------------------------------------------------

    for character, player in players.items():

        events = player.get(
            "events",
            []
        )

        for event in events:

            if (
                event_type(event)
                != "server_ranking_exit"
            ):

                continue

            date = event_date(
                event
            )

            available = csv_availability.get(
                date,
                {
                    "Eda": False,
                    "Virba": False
                }
            )

            ranking_available = (
                available.get("Eda") is True
                and available.get("Virba") is True
            )

            if not ranking_available:

                suspicious += 1

                add_error(
                    errors,
                    f"{character}: {date} "
                    f"サーバーランキングCSV欠損日なのに "
                    f"exitイベントあり"
                )

    print(
        f"  欠損日での不正exit候補: "
        f"{suspicious}件"
    )


# ============================================================
# 8. 保存済みイベント集計
# ============================================================

def print_event_summary(
    counter
):

    print()
    print(
        "[8] 保存済みイベント集計"
    )
    print("-" * 50)

    for etype, label in EVENT_LABELS.items():

        print(
            f"  {label}: "
            f"{counter.get(etype, 0)}件"
        )

    unknown = {
        key: value
        for key, value in counter.items()
        if key not in EVENT_LABELS
    }

    if unknown:

        print()
        print(
            "  【未定義イベント】"
        )

        for etype, count in unknown.items():

            print(
                f"    {etype}: {count}件"
            )


# ============================================================
# 9. 特定キャラクター詳細
# ============================================================

def inspect_character(
    players,
    character
):

    if character not in players:

        return

    player = players[
        character
    ]

    print()
    print("=" * 60)
    print(
        f"詳細確認: {character}"
    )
    print("=" * 60)

    print(
        f"tracking_id : "
        f"{player.get('tracking_id')}"
    )

    print(
        f"status      : "
        f"{player.get('status')}"
    )

    print(
        f"current     : "
        f"{player.get('current')}"
    )

    print(
        f"last_known  : "
        f"{player.get('last_known')}"
    )

    print()
    print("イベント:")

    events = player.get(
        "events",
        []
    )

    if not events:

        print("  なし")

    else:

        for event in events:

            print(
                f"  {event.get('date')} "
                f"{event_type(event)} "
                f"{event.get('old_value')} "
                f"-> "
                f"{event.get('new_value')}"
            )

    print()
    print("history:")

    for record in get_history(
        player
    ):

        date = normalize(
            record.get("date")
        )

        group, server_record = (
            get_server_record(
                record
            )
        )

        if group:

            print(
                f"  {date} "
                f"{group}: "
                f"rank={server_record.get('rank')} "
                f"Lv={server_record.get('level')} "
                f"server={server_record.get('server')} "
                f"guild={server_record.get('guild')}"
            )

        else:

            print(
                f"  {date} "
                f"Eda=- Virba=-"
            )


# ============================================================
# main
# ============================================================

def main():

    print("=" * 60)
    print("HIT : The World")
    print("player_history.json 検証ツール")
    print("=" * 60)

    print()
    print("読み込み:")
    print(
        f"  {HISTORY_FILE}"
    )

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    data = load_history()

    if data is None:

        return 1

    players = get_players(
        data
    )

    if not players:

        print()
        print(
            "ERROR: プレイヤーデータが"
            "見つかりません。"
        )

        return 1

    # --------------------------------------------------------
    # CSV状況
    # --------------------------------------------------------

    print()
    print("元CSV確認:")
    print(
        f"  {SERVER_RANKING_DIR}"
    )

    csv_availability = (
        load_server_csv_availability()
    )

    csv_players = (
        load_server_csv_players()
    )

    print(
        f"  CSV日数: "
        f"{len(csv_availability):,}日"
    )

    # --------------------------------------------------------
    # エラー / 警告
    # --------------------------------------------------------

    errors = []
    warnings = []

    # --------------------------------------------------------
    # 検証
    # --------------------------------------------------------

    verify_basic_structure(
        players,
        errors,
        warnings
    )

    verify_history(
        players,
        errors,
        warnings
    )

    verify_current_and_last_known(
        players,
        errors,
        warnings
    )

    counter = verify_events_structure(
        players,
        errors,
        warnings
    )

    verify_entry_exit_logic(
        players,
        errors,
        warnings,
        csv_availability,
        csv_players
    )

    verify_change_events(
        players,
        errors,
        warnings
    )

    verify_missing_day_handling(
        players,
        errors,
        warnings,
        csv_availability
    )

    print_event_summary(
        counter
    )

    # --------------------------------------------------------
    # サンプル確認
    # --------------------------------------------------------

    for character in (
        "きゅあじい",
        "魔法少女かおる一",
        "魔法少女首領閣下",
        "みんな元気でね",
        "激辛Sugar",
    ):

        inspect_character(
            players,
            character
        )

    # --------------------------------------------------------
    # 最終結果
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("検証結果")
    print("=" * 60)

    if errors:

        print()
        print(
            f"❌ エラー: "
            f"{len(errors)}件"
        )

        print()
        print(
            "【エラー一覧】"
        )

        max_display = 100

        for i, error in enumerate(
            errors[:max_display],
            start=1
        ):

            print(
                f"  {i}. {error}"
            )

        if len(errors) > max_display:

            print()
            print(
                f"  ... 残り "
                f"{len(errors) - max_display}件"
            )

        print()
        print(
            "→ player_history.py または "
            "元CSVとの整合性を確認してください。"
        )

        return 2

    print()
    print(
        "✅ エラーはありません。"
    )

    print(
        "   player_history.json の"
        "基本整合性は正常です。"
    )

    if warnings:

        print()
        print(
            f"⚠️ 警告: "
            f"{len(warnings)}件"
        )

        for warning in warnings[:50]:

            print(
                f"  - {warning}"
            )

    print()
    print("検証完了。")

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
