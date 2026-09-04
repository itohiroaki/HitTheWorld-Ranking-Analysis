from pathlib import Path
import json
from collections import Counter


# ============================================================
# 設定
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

HISTORY_FILE = BASE_DIR / "data" / "history" / "player_history.json"

DAILY_ANALYSIS_DIR = BASE_DIR / "data" / "history" / "daily_analysis"
DAILY_ANALYSIS_LATEST_FILE = (
    BASE_DIR / "data" / "history" / "daily_analysis_latest.json"
)

RANKING_LIMIT = 10
GUILD_LIMIT = 20


EVENT_LABELS = {
    "server_ranking_entry": "TOP100ランキング入り",
    "server_ranking_exit": "TOP100ランキング圏外",
    "server_rank_up": "サーバー順位上昇",
    "server_rank_down": "サーバー順位下降",
    "server_ranking_level_up": "レベルアップ",
    "server_ranking_level_down": "レベルダウン",
    "server_ranking_server_change": "サーバー変更",
    "server_ranking_guild_change": "ギルド変更",
}


# ============================================================
# 読み込み
# ============================================================

def load_history():
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 基本情報
# ============================================================

def get_players(data):
    """
    player_history.json は

    {
        "キャラクター名": {...},
        "キャラクター名": {...}
    }

    という構造なので、そのまま返す。
    """

    if isinstance(data, dict):
        return data.get("players", data)

    return data


def get_all_dates(players):
    dates = set()

    for player in players.values():
        for record in player.get("history", []):
            date = record.get("date")

            if date:
                dates.add(str(date))

    return sorted(dates)


def get_latest_date(players):
    dates = get_all_dates(players)

    if not dates:
        return None

    return dates[-1]


def get_previous_date(players, latest_date):
    dates = get_all_dates(players)

    previous_dates = [
        date
        for date in dates
        if date < latest_date
    ]

    if not previous_dates:
        return None

    return previous_dates[-1]


# ============================================================
# history取得
# ============================================================

def get_history_record(player, date):
    for record in player.get("history", []):
        if str(record.get("date")) == str(date):
            return record

    return None


def get_server_record(player, date):
    """
    指定日のEda/Virbaランキング情報を取得。

    Edaを優先し、Edaが見えなければVirbaを見る。
    """

    record = get_history_record(player, date)

    if not record:
        return None

    server_ranking = record.get(
        "server_ranking",
        {}
    )

    eda = server_ranking.get(
        "Eda",
        {}
    )

    if eda.get("visible"):
        return {
            "group": "Eda",
            **eda,
        }

    virba = server_ranking.get(
        "Virba",
        {}
    )

    if virba.get("visible"):
        return {
            "group": "Virba",
            **virba,
        }

    return None


# ============================================================
# イベント取得
# ============================================================

def get_events_for_date(player, date):
    events = []

    for event in player.get("events", []):
        if str(event.get("date")) == str(date):
            events.append(event)

    return events


def collect_events(players, date):
    result = []

    for character, player in players.items():

        for event in get_events_for_date(
            player,
            date,
        ):

            event_data = {
                "character": character,
                "type": event.get("type"),
                "label": EVENT_LABELS.get(
                    event.get("type"),
                    event.get("type"),
                ),
                "group": event.get("group"),
                "old_value": event.get("old_value"),
                "new_value": event.get("new_value"),
            }

            # detailsなど追加情報も保持
            for key, value in event.items():

                if key not in {
                    "date",
                    "type",
                    "group",
                    "old_value",
                    "new_value",
                }:
                    event_data[key] = value

            result.append(event_data)

    return result


# ============================================================
# 数値変換
# ============================================================

def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ============================================================
# 急上昇ランキング
# ============================================================

def create_rank_up_ranking(events):

    ranking = []

    for event in events:

        if event.get("type") != "server_rank_up":
            continue

        old_rank = to_int(
            event.get("old_value")
        )

        new_rank = to_int(
            event.get("new_value")
        )

        if old_rank is None or new_rank is None:
            continue

        change = old_rank - new_rank

        ranking.append({
            "character": event["character"],
            "group": event.get("group"),
            "old_rank": old_rank,
            "new_rank": new_rank,
            "change": change,
        })

    ranking.sort(
        key=lambda x: (
            -x["change"],
            x["new_rank"],
        )
    )

    return ranking


# ============================================================
# 急下降ランキング
# ============================================================

def create_rank_down_ranking(events):

    ranking = []

    for event in events:

        if event.get("type") != "server_rank_down":
            continue

        old_rank = to_int(
            event.get("old_value")
        )

        new_rank = to_int(
            event.get("new_value")
        )

        if old_rank is None or new_rank is None:
            continue

        change = new_rank - old_rank

        ranking.append({
            "character": event["character"],
            "group": event.get("group"),
            "old_rank": old_rank,
            "new_rank": new_rank,
            "change": change,
        })

    ranking.sort(
        key=lambda x: (
            -x["change"],
            x["new_rank"],
        )
    )

    return ranking


# ============================================================
# NEW ENTRY
# ============================================================

def create_entry_ranking(events):

    ranking = []

    for event in events:

        if event.get("type") != "server_ranking_entry":
            continue

        new_rank = to_int(
            event.get("new_value")
        )

        ranking.append({
            "character": event["character"],
            "group": event.get("group"),
            "new_rank": new_rank,
            "first_observation": event.get(
                "details",
                {}
            ).get(
                "first_observation",
                False,
            ),
        })

    ranking.sort(
        key=lambda x: (
            x["new_rank"]
            if x["new_rank"] is not None
            else 9999
        )
    )

    return ranking


# ============================================================
# OUT
# ============================================================

def create_exit_ranking(events):

    ranking = []

    for event in events:

        if event.get("type") != "server_ranking_exit":
            continue

        old_rank = to_int(
            event.get("old_value")
        )

        ranking.append({
            "character": event["character"],
            "group": event.get("group"),
            "old_rank": old_rank,
        })

    ranking.sort(
        key=lambda x: (
            x["old_rank"]
            if x["old_rank"] is not None
            else 9999
        )
    )

    return ranking


# ============================================================
# Lv UP
# ============================================================

def create_level_up_ranking(events):

    ranking = []

    for event in events:

        if event.get("type") != "server_ranking_level_up":
            continue

        old_level = to_int(
            event.get("old_value")
        )

        new_level = to_int(
            event.get("new_value")
        )

        if old_level is None or new_level is None:
            continue

        change = new_level - old_level

        ranking.append({
            "character": event["character"],
            "group": event.get("group"),
            "old_level": old_level,
            "new_level": new_level,
            "change": change,
        })

    ranking.sort(
        key=lambda x: (
            -x["change"],
            -x["new_level"],
        )
    )

    return ranking


# ============================================================
# Lv DOWN
# ============================================================

def create_level_down_ranking(events):

    ranking = []

    for event in events:

        if event.get("type") != "server_ranking_level_down":
            continue

        old_level = to_int(
            event.get("old_value")
        )

        new_level = to_int(
            event.get("new_value")
        )

        if old_level is None or new_level is None:
            continue

        change = old_level - new_level

        ranking.append({
            "character": event["character"],
            "group": event.get("group"),
            "old_level": old_level,
            "new_level": new_level,
            "change": change,
        })

    ranking.sort(
        key=lambda x: (
            -x["change"],
            -x["new_level"],
        )
    )

    return ranking


# ============================================================
# サーバー変更
# ============================================================

def create_server_change_list(events):

    result = []

    for event in events:

        if event.get("type") != "server_ranking_server_change":
            continue

        result.append({
            "character": event["character"],
            "group": event.get("group"),
            "old_value": event.get("old_value"),
            "new_value": event.get("new_value"),
            **{
                key: value
                for key, value in event.items()
                if key not in {
                    "character",
                    "type",
                    "label",
                    "group",
                    "old_value",
                    "new_value",
                }
            }
        })

    return result


# ============================================================
# ギルド変更
# ============================================================

def create_guild_change_list(events):

    result = []

    for event in events:

        if event.get("type") != "server_ranking_guild_change":
            continue

        result.append({
            "character": event["character"],
            "group": event.get("group"),
            "old_value": event.get("old_value"),
            "new_value": event.get("new_value"),
            **{
                key: value
                for key, value in event.items()
                if key not in {
                    "character",
                    "type",
                    "label",
                    "group",
                    "old_value",
                    "new_value",
                }
            }
        })

    return result


# ============================================================
# 現在のランキング
# ============================================================

def collect_current_ranking(players):
    """
    最新の current データから Eda / Virba の現在ランキングを作成する。

    player_history.json の current 構造:

    "current": {
        "character": "...",
        "level": 102,
        "server": "Eda3",
        "guild": "...",
        "eda": {
            "visible": true,
            "rank": 1
        },
        "virba": {
            "visible": false,
            "rank": null
        }
    }
    """

    rankings = {
        "Eda": [],
        "Virba": [],
    }

    for player_name, player in players.items():

        current = player.get("current", {})

        if not current:
            continue

        character = current.get(
            "character",
            player.get("character", player_name)
        )

        level = current.get("level")
        server = current.get("server", "")
        guild = current.get("guild", "")

        # ----------------------------------------------------------
        # Eda
        # ----------------------------------------------------------
        eda = current.get("eda", {})

        if eda.get("visible") is True:
            rank = eda.get("rank")

            if rank is not None:
                rankings["Eda"].append({
                    "rank": rank,
                    "character": character,
                    "level": level,
                    "server": server,
                    "guild": guild,
                    "tracking_id": player.get("tracking_id"),
                })

        # ----------------------------------------------------------
        # Virba
        # ----------------------------------------------------------
        virba = current.get("virba", {})

        if virba.get("visible") is True:
            rank = virba.get("rank")

            if rank is not None:
                rankings["Virba"].append({
                    "rank": rank,
                    "character": character,
                    "level": level,
                    "server": server,
                    "guild": guild,
                    "tracking_id": player.get("tracking_id"),
                })

    # 順位順に並べる
    for group in rankings:
        rankings[group].sort(
            key=lambda x: x["rank"]
        )

    return rankings


# ============================================================
# レベル分布
# ============================================================

def create_level_distribution(current_ranking):

    result = {}

    for group, players in current_ranking.items():

        counter = Counter()

        for player in players:

            level = player.get(
                "level"
            )

            if level is not None:
                counter[str(level)] += 1

        result[group] = dict(
            sorted(
                counter.items(),
                key=lambda x: int(x[0]),
                reverse=True,
            )
        )

    return result


# ============================================================
# サーバー分布
# ============================================================

def create_server_distribution(current_ranking):

    result = {}

    for group, players in current_ranking.items():

        counter = Counter()

        for player in players:

            server = player.get(
                "server",
                ""
            )

            if server:
                counter[server] += 1

        result[group] = dict(
            counter.most_common()
        )

    return result


# ============================================================
# ギルド分布
# ============================================================

def create_guild_distribution(current_ranking):

    counter = Counter()

    for players in current_ranking.values():

        for player in players:

            guild = player.get(
                "guild",
                ""
            )

            if guild:
                counter[guild] += 1

    return dict(
        counter.most_common(
            GUILD_LIMIT
        )
    )


# ============================================================
# イベントサマリー
# ============================================================

def create_event_summary(events):

    counter = Counter(
        event.get("type")
        for event in events
    )

    return {
        "entry": counter.get(
            "server_ranking_entry",
            0
        ),
        "exit": counter.get(
            "server_ranking_exit",
            0
        ),
        "rank_up": counter.get(
            "server_rank_up",
            0
        ),
        "rank_down": counter.get(
            "server_rank_down",
            0
        ),
        "level_up": counter.get(
            "server_ranking_level_up",
            0
        ),
        "level_down": counter.get(
            "server_ranking_level_down",
            0
        ),
        "server_change": counter.get(
            "server_ranking_server_change",
            0
        ),
        "guild_change": counter.get(
            "server_ranking_guild_change",
            0
        ),
        "total": len(events),
    }


# ============================================================
# 日次分析データ作成
# ============================================================

def create_daily_analysis(
    players,
    latest_date,
    previous_date,
):

    events = collect_events(
        players,
        latest_date,
    )

    current_ranking = collect_current_ranking(
        players
    )

    rank_up = create_rank_up_ranking(
        events
    )

    rank_down = create_rank_down_ranking(
        events
    )

    entry = create_entry_ranking(
        events
    )

    exit_ranking = create_exit_ranking(
        events
    )

    level_up = create_level_up_ranking(
        events
    )

    level_down = create_level_down_ranking(
        events
    )

    server_change = create_server_change_list(
        events
    )

    guild_change = create_guild_change_list(
        events
    )

    analysis = {

        # ----------------------------------------------------
        # 日付
        # ----------------------------------------------------

        "date": latest_date,

        "previous_date": previous_date,

        # ----------------------------------------------------
        # 基本情報
        # ----------------------------------------------------

        "player_count": len(players),

        # ----------------------------------------------------
        # イベント集計
        # ----------------------------------------------------

        "event_summary": create_event_summary(
            events
        ),

        # ----------------------------------------------------
        # ランキング
        # ----------------------------------------------------

        "rankings": {

            "rank_up": rank_up,

            "rank_down": rank_down,

            "entry": entry,

            "exit": exit_ranking,

            "level_up": level_up,

            "level_down": level_down,
        },

        # ----------------------------------------------------
        # その他の変更
        # ----------------------------------------------------

        "changes": {

            "server_change": server_change,

            "guild_change": guild_change,
        },

        # ----------------------------------------------------
        # 現在のランキング
        # ----------------------------------------------------

        "current_ranking": current_ranking,

        # ----------------------------------------------------
        # 統計
        # ----------------------------------------------------

        "statistics": {

            "level_distribution":
                create_level_distribution(
                    current_ranking
                ),

            "server_distribution":
                create_server_distribution(
                    current_ranking
                ),

            "guild_distribution":
                create_guild_distribution(
                    current_ranking
                ),
        },

        # ----------------------------------------------------
        # メタ情報
        # ----------------------------------------------------

        "meta": {

            "ranking_limit":
                RANKING_LIMIT,

            "guild_limit":
                GUILD_LIMIT,
        },
    }

    return analysis


# ============================================================
# JSON保存
# ============================================================

def save_daily_analysis(data):
    """
    日別分析JSONと最新データを保存する。

    保存先:
        data/history/daily_analysis/YYYYMMDD.json
        data/history/daily_analysis_latest.json
        data/history/daily_analysis/index.json

    index.jsonには、Web側の日付選択用として
    利用可能な分析日を保存する。
    """

    DAILY_ANALYSIS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    date = str(
        data.get("date", "")
    )

    if not date:
        raise ValueError(
            "分析データにdateがありません"
        )


    # ---------------------------------------------------------
    # 日付別JSON
    # ---------------------------------------------------------

    daily_file = (
        DAILY_ANALYSIS_DIR /
        f"{date}.json"
    )

    with open(
        daily_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


    # ---------------------------------------------------------
    # 最新JSON
    # ---------------------------------------------------------

    latest_file = (
        BASE_DIR /
        "data" /
        "history" /
        "daily_analysis_latest.json"
    )

    with open(
        latest_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


    # ---------------------------------------------------------
    # 日付一覧を更新
    # ---------------------------------------------------------

    index_file = (
        DAILY_ANALYSIS_DIR /
        "index.json"
    )


    dates = []


    # 既存indexを読み込む
    if index_file.exists():

        try:

            with open(
                index_file,
                "r",
                encoding="utf-8"
            ) as f:

                index_data = json.load(f)


            if isinstance(
                index_data,
                dict
            ):

                dates = index_data.get(
                    "dates",
                    []
                )

            elif isinstance(
                index_data,
                list
            ):

                dates = index_data


        except (
            json.JSONDecodeError,
            OSError
        ):

            dates = []


    # 日付を追加
    dates = [
        str(item)
        for item in dates
        if item
    ]

    if date not in dates:

        dates.append(date)


    # 実際に存在するJSONファイルも確認
    for file in DAILY_ANALYSIS_DIR.glob(
        "*.json"
    ):

        filename = file.stem

        if (
            filename.isdigit()
            and len(filename) == 8
        ):

            if filename not in dates:

                dates.append(filename)


    # 新しい順
    dates = sorted(
        set(dates),
        reverse=True
    )


    index_data = {
        "dates": dates
    }


    with open(
        index_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            index_data,
            f,
            ensure_ascii=False,
            indent=2
        )


    print(
        f"日別分析保存: {daily_file}"
    )

    print(
        f"最新分析保存: {latest_file}"
    )

    print(
        f"日付一覧保存: {index_file}"
    )
    return daily_file


# ============================================================
# コンソール表示
# ============================================================

def print_event_summary(summary):

    print()
    print("【本日のイベント集計】")
    print("-" * 70)

    labels = [
        ("entry", "TOP100ランキング入り"),
        ("exit", "TOP100ランキング圏外"),
        ("rank_up", "サーバー順位上昇"),
        ("rank_down", "サーバー順位下降"),
        ("level_up", "レベルアップ"),
        ("guild_change", "ギルド変更"),
    ]

    for key, label in labels:

        print(
            f"  {label:<35}"
            f"{summary[key]:>5}件"
        )

    print("-" * 70)

    print(
        f"  {'合計':<35}"
        f"{summary['total']:>5}件"
    )


def print_rank_up(ranking):

    print()
    print("【📈 本日の急上昇 TOP10】")
    print("-" * 70)

    if not ranking:

        print("  該当なし")
        return

    for index, item in enumerate(
        ranking[:RANKING_LIMIT],
        start=1,
    ):

        print(
            f"  {index:>2}位 "
            f"{item['character']:<25} "
            f"[{item['group']}] "
            f"{item['old_rank']:>3} → "
            f"{item['new_rank']:>3} "
            f"(+{item['change']})"
        )


def print_rank_down(ranking):

    print()
    print("【📉 本日の急下降 TOP10】")
    print("-" * 70)

    if not ranking:

        print("  該当なし")
        return

    for index, item in enumerate(
        ranking[:RANKING_LIMIT],
        start=1,
    ):

        print(
            f"  {index:>2}位 "
            f"{item['character']:<25} "
            f"[{item['group']}] "
            f"{item['old_rank']:>3} → "
            f"{item['new_rank']:>3} "
            f"(-{item['change']})"
        )


def print_entry(ranking):

    print()
    print("【🆕 NEW ENTRY】")
    print("-" * 70)

    if not ranking:

        print("  該当なし")
        return

    for index, item in enumerate(
        ranking,
        start=1,
    ):

        first = ""

        if item.get(
            "first_observation"
        ):
            first = " ★初観測"

        print(
            f"  {index:>2}. "
            f"{item['character']:<25} "
            f"[{item['group']}] "
            f"{item['new_rank']:>3}位"
            f"{first}"
        )


def print_exit(ranking):

    print()
    print("【🚪 OUT】")
    print("-" * 70)

    if not ranking:

        print("  該当なし")
        return

    for index, item in enumerate(
        ranking,
        start=1,
    ):

        print(
            f"  {index:>2}. "
            f"{item['character']:<25} "
            f"[{item['group']}] "
            f"{item['old_rank']:>3}位 → 圏外"
        )


def print_level_up(ranking):

    print()
    print("【🆙 本日のLv UP】")
    print("-" * 70)

    if not ranking:

        print("  該当なし")
        return

    for index, item in enumerate(
        ranking,
        start=1,
    ):

        print(
            f"  {index:>2}位 "
            f"{item['character']:<25} "
            f"[{item['group']}] "
            f"Lv{item['old_level']} → "
            f"Lv{item['new_level']} "
            f"(+{item['change']})"
        )


def print_level_down(ranking):

    print()
    print("【本日のLv DOWN】")
    print("-" * 70)

    if not ranking:

        print("  該当なし")
        return

    for index, item in enumerate(
        ranking,
        start=1,
    ):

        print(
            f"  {index:>2}位 "
            f"{item['character']:<25} "
            f"[{item['group']}] "
            f"Lv{item['old_level']} → "
            f"Lv{item['new_level']} "
            f"(-{item['change']})"
        )


def print_server_change(changes):

    print()
    print("【本日のサーバー変更】")
    print("-" * 70)

    if not changes:

        print("  該当なし")
        return

    for item in changes:

        print(
            f"  {item['character']:<25} "
            f"[{item['group']}] "
            f"{item['old_value']} → "
            f"{item['new_value']}"
        )


def print_guild_change(changes):

    print()
    print("【本日のギルド変更】")
    print("-" * 70)

    if not changes:

        print("  該当なし")
        return

    for item in changes:

        print(
            f"  {item['character']:<25} "
            f"[{item['group']}] "
            f"{item['old_value']} → "
            f"{item['new_value']}"
        )


# ============================================================
# 現在ランキング表示
# ============================================================

def print_current_ranking(current_ranking):

    print()
    print("=" * 70)
    print("現在のランキング")
    print("=" * 70)

    print()

    print(
        f"Eda   : "
        f"{len(current_ranking['Eda'])}人"
    )

    print(
        f"Virba : "
        f"{len(current_ranking['Virba'])}人"
    )

    for group in ["Eda", "Virba"]:

        print()
        print(f"【{group} TOP10】")
        print("-" * 70)

        for player in current_ranking[group][
            :RANKING_LIMIT
        ]:

            level_text = (
                f"Lv{player['level']}"
                if player["level"] is not None
                else "Lv--"
            )

            print(
                f"  {player['rank']:>3}位  "
                f"{level_text:<6} "
                f"{player['character']:<25} "
                f"{player['server']:<8} "
                f"{player['guild']}"
            )


# ============================================================
# 統計表示
# ============================================================

def print_statistics(statistics):

    print()
    print("【レベル分布】")
    print("-" * 70)

    for group, levels in statistics[
        "level_distribution"
    ].items():

        print()
        print(f"  {group}")

        for level, count in levels.items():

            print(
                f"    Lv{level}: {count}人"
            )

    print()
    print("【サーバー別人数】")
    print("-" * 70)

    for group, servers in statistics[
        "server_distribution"
    ].items():

        print()
        print(f"  {group}")

        for server, count in servers.items():

            print(
                f"    {server:<10}"
                f"{count:>4}人"
            )

    print()
    print("【ギルド人数 TOP20】")
    print("-" * 70)

    for guild, count in statistics[
        "guild_distribution"
    ].items():

        print(
            f"  {guild:<30}"
            f"{count:>4}人"
        )


# ============================================================
# メイン
# ============================================================

def main():

    print("=" * 70)
    print("HIT : The World")
    print("ランキング分析 Ver.3.1")
    print("=" * 70)

    print()
    print("読み込み:")
    print(f"  {HISTORY_FILE}")

    data = load_history()

    players = get_players(data)

    print()
    print(
        f"プレイヤー数: "
        f"{len(players):,}人"
    )

    latest_date = get_latest_date(
        players
    )

    if not latest_date:

        print()
        print("分析対象日がありません。")
        return

    previous_date = get_previous_date(
        players,
        latest_date,
    )

    print()
    print(
        f"分析対象日: "
        f"{latest_date}"
    )

    print(
        f"比較対象日: "
        f"{previous_date if previous_date else 'なし'}"
    )

    # --------------------------------------------------------
    # 分析
    # --------------------------------------------------------

    analysis = create_daily_analysis(
        players,
        latest_date,
        previous_date,
    )

    summary = analysis[
        "event_summary"
    ]

    print_event_summary(
        summary
    )

    print()
    print("=" * 70)
    print("本日の注目ランキング")
    print("=" * 70)

    print_rank_up(
        analysis["rankings"]["rank_up"]
    )

    print_rank_down(
        analysis["rankings"]["rank_down"]
    )

    print_entry(
        analysis["rankings"]["entry"]
    )

    print_exit(
        analysis["rankings"]["exit"]
    )

    print_level_up(
        analysis["rankings"]["level_up"]
    )

    print_level_down(
        analysis["rankings"]["level_down"]
    )

    print_server_change(
        analysis["changes"]["server_change"]
    )

    print_guild_change(
        analysis["changes"]["guild_change"]
    )

    print_current_ranking(
        analysis["current_ranking"]
    )

    print_statistics(
        analysis["statistics"]
    )

    # --------------------------------------------------------
    # JSON保存
    # --------------------------------------------------------

    output_file = save_daily_analysis(
        analysis
    )

    print()
    print("=" * 70)
    print("分析データ保存")
    print("=" * 70)

    print()
    print("日次分析:")
    print(f"  {output_file}")

    print()
    print("最新分析:")
    print(
        f"  {DAILY_ANALYSIS_LATEST_FILE}"
    )

    print()
    print("=" * 70)
    print("分析完了")
    print("=" * 70)


if __name__ == "__main__":
    main()
