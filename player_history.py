import json
import hashlib
import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

RANKING_DIR = BASE_DIR / "data" / "ranking"
SERVER_RANKING_DIR = BASE_DIR / "data" / "ranking_server"
HISTORY_DIR = BASE_DIR / "data" / "history"

HISTORY_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# データの役割
# ============================================================
#
# Worldランキング
# ----------------
# 「混沌」コンテンツ開始時点のスナップショット。
#
# ・現在順位として扱わない
# ・現在レベルとして扱わない
# ・現在サーバーとして扱わない
# ・現在ギルドとして扱わない
# ・日次イベント判定に使用しない
#
# ただし、
# ・混沌TOP1000
# ・混沌開始時点の順位
# ・混沌開始時点のサーバー
# ・混沌開始時点のギルド
# ・混沌開始時点のレベル
# ・サーバー別TOP100外の調査
# には使用する。
#
#
# Eda / Virba
# ------------
# 毎日取得する現在のサーバーランキングTOP100。
#
# ・現在順位
# ・現在レベル
# ・現在サーバー
# ・現在ギルド
# ・順位変動
# ・レベル変動
# ・ギルド変更
# ・サーバー移動
# をこちらから判断する。
# ============================================================


WORLD_RELIABLE_FOR_DAILY_CHANGE = False
SERVER_RELIABLE_FOR_DAILY_CHANGE = True


# ============================================================
# 共通
# ============================================================

def create_tracking_id(character):
    """
    現時点ではキャラクター名からtracking_idを作成。

    ※将来的に名前変更を確実に追跡する場合は、
      キャラクター名以外の恒久的なIDが必要。
    """

    hash_value = hashlib.sha256(
        character.encode("utf-8")
    ).hexdigest()[:16]

    return f"player_{hash_value}"


def load_ranking(file_path):

    df = pd.read_csv(
        file_path,
        dtype=str
    )

    df["rank"] = pd.to_numeric(
        df["rank"],
        errors="coerce"
    )

    df["level"] = pd.to_numeric(
        df["level"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "rank",
            "level",
            "character"
        ]
    )

    df["character"] = (
        df["character"]
        .astype(str)
        .str.strip()
    )

    df["server"] = (
        df["server"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["guild"] = (
        df["guild"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    return df


def extract_date(file_path):

    stem = file_path.stem

    parts = stem.split("_")

    for part in reversed(parts):

        if len(part) == 8 and part.isdigit():
            return part

    return ""


def get_server_group_from_filename(file_path):

    stem = file_path.stem.lower()

    if "ranking_virba_" in stem:
        return "Virba"

    if "ranking_eda_" in stem:
        return "Eda"

    return ""


# ============================================================
# プレイヤー作成
# ============================================================

def create_player(character):

    return {

        "tracking_id":
            create_tracking_id(character),

        "character":
            character,

        "names": [
            character
        ],

        "status": {

            "active": True,

            "last_seen": ""
        },

        # ----------------------------------------------------
        # World固定スナップショット
        # ----------------------------------------------------

        "world_snapshot": {

            "visible": False,

            "rank": None,

            "level": None,

            "server": "",

            "guild": "",

            "snapshot_dates": []
        },

        # ----------------------------------------------------
        # 最新日現在の状態
        # ----------------------------------------------------

        "current": {

            "character":
                character,

            "level": None,

            "server": "",

            "guild": "",

            "eda": {

                "visible": False,

                "rank": None
            },

            "virba": {

                "visible": False,

                "rank": None
            }
        },

        # ----------------------------------------------------
        # 最後にEda/Virbaで確認できた状態
        # ----------------------------------------------------

        "last_known": {

            "date": "",

            "character":
                character,

            "level": None,

            "server": "",

            "guild": "",

            "group": "",

            "rank": None
        },

        "summary": {},

        "events": [],

        "history": []
    }


# ============================================================
# History
# ============================================================

def find_history_record(history, date):

    for record in history:

        if record["date"] == date:
            return record

    return None


def ensure_history_record(player, date):

    record = find_history_record(
        player["history"],
        date
    )

    if record is None:

        record = {

            "date": date,

            # ------------------------------------------------
            # World
            # ------------------------------------------------

            "world": {

                "visible": False,

                "rank": None,

                "level": None,

                "server": "",

                "guild": "",

                "reliable_for_daily_change":
                    WORLD_RELIABLE_FOR_DAILY_CHANGE
            },

            # ------------------------------------------------
            # Server Ranking
            # ------------------------------------------------

            "server_ranking": {

                "Eda": {

                    "visible": False,

                    "rank": None,

                    "level": None,

                    "server": "",

                    "guild": "",

                    "reliable_for_daily_change":
                        SERVER_RELIABLE_FOR_DAILY_CHANGE
                },

                "Virba": {

                    "visible": False,

                    "rank": None,

                    "level": None,

                    "server": "",

                    "guild": "",

                    "reliable_for_daily_change":
                        SERVER_RELIABLE_FOR_DAILY_CHANGE
                }
            }
        }

        player["history"].append(
            record
        )

    return record


# ============================================================
# World更新
# ============================================================

def update_world_record(
    player,
    date,
    row
):

    record = ensure_history_record(
        player,
        date
    )

    record["world"] = {

        "visible": True,

        "rank": int(row["rank"]),

        "level": int(row["level"]),

        "server":
            str(row["server"]).strip(),

        "guild":
            str(row["guild"]).strip(),

        "reliable_for_daily_change":
            WORLD_RELIABLE_FOR_DAILY_CHANGE
    }


# ============================================================
# Server Ranking更新
# ============================================================

def update_server_record(
    player,
    date,
    row,
    group
):

    if group not in [
        "Eda",
        "Virba"
    ]:
        return

    record = ensure_history_record(
        player,
        date
    )

    record["server_ranking"][group] = {

        "visible": True,

        "rank": int(row["rank"]),

        "level": int(row["level"]),

        "server":
            str(row["server"]).strip(),

        "guild":
            str(row["guild"]).strip(),

        "reliable_for_daily_change":
            SERVER_RELIABLE_FOR_DAILY_CHANGE
    }


# ============================================================
# 履歴ソート
# ============================================================

def sort_history(player_history):

    for player in player_history.values():

        player["history"].sort(
            key=lambda record: record["date"]
        )


# ============================================================
# Worldスナップショット作成
# ============================================================

def create_world_snapshot(player):

    history = player["history"]

    world_records = [

        record

        for record in history

        if record["world"]["visible"]

    ]

    if not world_records:

        return {

            "visible": False,

            "rank": None,

            "level": None,

            "server": "",

            "guild": "",

            "snapshot_dates": []
        }


    # --------------------------------------------------------
    # Worldは同じスナップショットが複数日存在する可能性が
    # あるため、最初に取得した内容を固定値として採用。
    # --------------------------------------------------------

    first = world_records[0]["world"]


    snapshot_dates = [

        record["date"]

        for record in world_records

    ]


    return {

        "visible": True,

        "rank":
            first["rank"],

        "level":
            first["level"],

        "server":
            first["server"],

        "guild":
            first["guild"],

        "snapshot_dates":
            snapshot_dates
    }


# ============================================================
# 現在情報作成
# ============================================================
#
# 重要：
#
# 「現在」は最新のEda/Virba確認日ではない。
#
# 全データの最新日を基準にする。
#
# 例：
#
# 9/2 Virba1位
# 9/3 圏外
#
# → 9/3 currentは空
#
# 9/2の情報はlast_knownに残す。
# ============================================================

def create_current(player):

    history = player["history"]


    # --------------------------------------------------------
    # 履歴がない場合
    # --------------------------------------------------------

    if not history:

        return {

            "character":
                player["character"],

            "level": None,

            "server": "",

            "guild": "",

            "eda": {

                "visible": False,

                "rank": None
            },

            "virba": {

                "visible": False,

                "rank": None
            }
        }


    # --------------------------------------------------------
    # 全体の最新日
    # --------------------------------------------------------

    latest_date = max(

        record["date"]

        for record in history

    )


    latest_record = find_history_record(

        history,

        latest_date

    )


    if latest_record is None:

        return {

            "character":
                player["character"],

            "level": None,

            "server": "",

            "guild": "",

            "eda": {

                "visible": False,

                "rank": None
            },

            "virba": {

                "visible": False,

                "rank": None
            }
        }


    # --------------------------------------------------------
    # 最新日のEda / Virba
    # --------------------------------------------------------

    eda = latest_record[
        "server_ranking"
    ]["Eda"]

    virba = latest_record[
        "server_ranking"
    ]["Virba"]


    # --------------------------------------------------------
    # 最新日にどちらにも存在しない
    # --------------------------------------------------------

    if (
        not eda["visible"]
        and
        not virba["visible"]
    ):

        return {

            "character":
                player["character"],

            "level": None,

            "server": "",

            "guild": "",

            "eda": {

                "visible": False,

                "rank": None
            },

            "virba": {

                "visible": False,

                "rank": None
            }
        }


    # --------------------------------------------------------
    # 現在のレベル・サーバー・ギルド
    # --------------------------------------------------------
    #
    # 両方に存在する場合はEdaを優先。
    # --------------------------------------------------------

    if eda["visible"]:

        current_level = eda["level"]

        current_server = eda["server"]

        current_guild = eda["guild"]

    else:

        current_level = virba["level"]

        current_server = virba["server"]

        current_guild = virba["guild"]


    return {

        "character":
            player["character"],

        "level":
            current_level,

        "server":
            current_server,

        "guild":
            current_guild,

        "eda": {

            "visible":
                eda["visible"],

            "rank":
                eda["rank"]
                if eda["visible"]
                else None
        },

        "virba": {

            "visible":
                virba["visible"],

            "rank":
                virba["rank"]
                if virba["visible"]
                else None
        }
    }


# ============================================================
# 最後に確認した状態
# ============================================================
#
# 最新日ではなく、
# Eda / Virbaで最後に実際に確認できた日を返す。
#
# 例：
#
# 9/2 Virba1位
# 9/3 圏外
#
# → last_known = 9/2 Virba1位
# ============================================================

def create_last_known(player):

    history = player["history"]


    # --------------------------------------------------------
    # 後ろから検索
    # --------------------------------------------------------

    for record in reversed(history):

        eda = record[
            "server_ranking"
        ]["Eda"]

        virba = record[
            "server_ranking"
        ]["Virba"]


        # ----------------------------------------------------
        # Eda
        # ----------------------------------------------------

        if eda["visible"]:

            return {

                "date":
                    record["date"],

                "character":
                    player["character"],

                "level":
                    eda["level"],

                "server":
                    eda["server"],

                "guild":
                    eda["guild"],

                "group":
                    "Eda",

                "rank":
                    eda["rank"]
            }


        # ----------------------------------------------------
        # Virba
        # ----------------------------------------------------

        if virba["visible"]:

            return {

                "date":
                    record["date"],

                "character":
                    player["character"],

                "level":
                    virba["level"],

                "server":
                    virba["server"],

                "guild":
                    virba["guild"],

                "group":
                    "Virba",

                "rank":
                    virba["rank"]
            }


    # --------------------------------------------------------
    # 一度もEda/Virbaで確認できていない
    # --------------------------------------------------------

    return {

        "date": "",

        "character":
            player["character"],

        "level": None,

        "server": "",

        "guild": "",

        "group": "",

        "rank": None
    }


# ============================================================
# 現在状態
# ============================================================

def update_status(player_history):

    if not player_history:

        return 0, 0


    # --------------------------------------------------------
    # 全体の最新日
    # --------------------------------------------------------

    latest_date = ""

    for player in player_history.values():

        for record in player["history"]:

            if record["date"] > latest_date:

                latest_date = record["date"]


    active_count = 0
    inactive_count = 0


    # --------------------------------------------------------
    # 最新日のEda / Virbaだけで現在状態を判断
    # --------------------------------------------------------

    for player in player_history.values():

        latest_record = find_history_record(

            player["history"],

            latest_date

        )


        if latest_record is None:

            player["status"]["active"] = False

            player["status"]["last_seen"] = ""

            inactive_count += 1

            continue


        eda_visible = (

            latest_record[
                "server_ranking"
            ]["Eda"]["visible"]

        )

        virba_visible = (

            latest_record[
                "server_ranking"
            ]["Virba"]["visible"]

        )


        # ----------------------------------------------------
        # 最新日に確認できた
        # ----------------------------------------------------

        if eda_visible or virba_visible:

            player["status"]["active"] = True

            player["status"]["last_seen"] = (
                latest_date
            )

            active_count += 1

        # ----------------------------------------------------
        # 最新日に確認できない
        # ----------------------------------------------------

        else:

            player["status"]["active"] = False


            last_server_seen = ""


            for record in reversed(
                player["history"]
            ):

                if (

                    record[
                        "server_ranking"
                    ]["Eda"]["visible"]

                    or

                    record[
                        "server_ranking"
                    ]["Virba"]["visible"]

                ):

                    last_server_seen = (
                        record["date"]
                    )

                    break


            player["status"]["last_seen"] = (
                last_server_seen
            )

            inactive_count += 1


    return active_count, inactive_count


# ============================================================
# 順位取得
# ============================================================

def get_visible_server_rank(
    record,
    group
):

    if not record:

        return None


    if group not in [
        "Eda",
        "Virba"
    ]:

        return None


    server_record = (

        record[
            "server_ranking"
        ][group]

    )


    if not server_record["visible"]:

        return None


    return server_record["rank"]


# ============================================================
# イベント作成
# ============================================================

def create_events(
    player,
    server_data_available
):
    """
    サーバーランキング（Eda / Virba）の履歴から
    イベントを作成する。

    対象イベント:
      - server_ranking_entry
      - server_ranking_exit
      - server_rank_up
      - server_rank_down
      - server_ranking_level_up
      - server_ranking_level_down
      - server_ranking_guild_change
      - server_ranking_server_change

    Worldランキングはイベント判定には使用しない。

    --------------------------------------------------------
    CSVが存在しない日とTOP100圏外を区別
    --------------------------------------------------------

    server_data_available の例:

        {
            "20260901": {
                "Eda": False,
                "Virba": False
            },

            "20260902": {
                "Eda": True,
                "Virba": True
            },

            "20260903": {
                "Eda": True,
                "Virba": True
            }
        }

    CSVが存在しない日は、

        「ランキング圏外」

    とは判定しない。

    --------------------------------------------------------
    重要
    --------------------------------------------------------

    CSVがない日を挟んでも、
    最後に実際に確認できた状態は保持する。

    例:

        9/3  Eda3
        9/4  CSVなし
        9/5  Eda7

    → 9/4 exitなし
    → 9/5 Eda3 → Eda7
    """

    events = []

    history = player.get(
        "history",
        []
    )

    if not history:
        return events


    # --------------------------------------------------------
    # 日付順
    # --------------------------------------------------------

    history = sorted(
        history,
        key=lambda x: x.get("date", "")
    )


    # --------------------------------------------------------
    # その日のEda / Virba状態を取得
    # --------------------------------------------------------

    def get_server_record(record):

        server_ranking = record.get(
            "server_ranking",
            {}
        )

        eda = server_ranking.get(
            "Eda",
            {}
        )

        virba = server_ranking.get(
            "Virba",
            {}
        )

        if eda.get("visible"):

            return "Eda", eda

        if virba.get("visible"):

            return "Virba", virba

        return None, None


    # --------------------------------------------------------
    # イベント追加
    # --------------------------------------------------------

    def add_event(
        date,
        event_type,
        group="",
        old_value=None,
        new_value=None,
        details=None
    ):

        event = {

            "date":
                date,

            "type":
                event_type,

            "group":
                group,

            "old_value":
                old_value,

            "new_value":
                new_value
        }

        if details:

            event["details"] = details

        events.append(
            event
        )


    # --------------------------------------------------------
    # 最後に確認できたサーバーランキング状態
    #
    # CSVが存在しない日は更新しない。
    # 圏外になった日も状態は保持する。
    # --------------------------------------------------------

    last_visible_group = None

    last_visible_record = None

    last_visible_date = None

    # 最後に確認できた「所属ギルド」
    # 無所属の場合は更新しない。
    last_visible_guild = None

    # --------------------------------------------------------
    # 直前の「判定可能な日」の状態
    #
    # True  = TOP100に存在
    # False = CSVが存在していてTOP100に存在しない
    # None  = まだ判定できていない
    # --------------------------------------------------------

    previous_visible = None


    # ========================================================
    # 履歴ループ
    # ========================================================

    for record in history:

        date = record.get(
            "date",
            ""
        )


        # ----------------------------------------------------
        # その日のCSV存在状況
        # ----------------------------------------------------

        availability = (
            server_data_available.get(
                date,
                {}
            )
        )

        eda_available = (
            availability.get(
                "Eda",
                False
            )
        )

        virba_available = (
            availability.get(
                "Virba",
                False
            )
        )


        # ----------------------------------------------------
        # Eda / Virba両方のデータが存在するか
        #
        # TOP100への「入り / 圏外」は
        # 両サーバーのランキングが揃っている日だけ
        # 判定する。
        # ----------------------------------------------------

        ranking_status_available = (

            eda_available
            and
            virba_available

        )


        current_group, current_record = (
            get_server_record(record)
        )


        current_visible = (
            current_record is not None
        )


        # ====================================================
        # CSVが存在しない日
        # ====================================================
        #
        # ここでは絶対に
        #
        #   entry
        #   exit
        #
        # を発生させない。
        #
        # また、前回状態も変更しない。
        # ====================================================

        if not ranking_status_available:

            continue


        # ====================================================
        # 初回の判定可能日
        # ====================================================

        if previous_visible is None:

            if current_visible:

                # ------------------------------------------------
                # 初めてTOP100で確認
                # ------------------------------------------------

                add_event(

                    date=date,

                    event_type=
                        "server_ranking_entry",

                    group=current_group,

                    old_value=None,

                    new_value=
                        current_record.get(
                            "rank"
                        ),

                    details={

                        "rank":
                            current_record.get(
                                "rank"
                            ),

                        "level":
                            current_record.get(
                                "level"
                            ),

                        "server":
                            current_record.get(
                                "server"
                            ),

                        "guild":
                            current_record.get(
                                "guild"
                            ),

                        "group":
                            current_group,

                        "first_observation":
                            True
                    }
                )

            # ------------------------------------------------
            # 初回判定可能日に圏外
            # ------------------------------------------------

            previous_visible = (
                current_visible
            )


            # ------------------------------------------------
            # 表示されていた場合は
            # 最後の確認状態を保存
            # ------------------------------------------------

            if current_visible:

                last_visible_group = (
                    current_group
                )

                last_visible_record = (
                    current_record
                )

                last_visible_date = (
                    date
                )

                current_guild = (
                    current_record.get(
                        "guild",
                        ""
                    )
                )

                if current_guild:
                    last_visible_guild = (
                        current_guild
                    )

            continue


        # ====================================================
        # 前回も表示 → 今回も表示
        # ====================================================

        if previous_visible and current_visible:

            previous_group = (
                last_visible_group
            )

            previous_record = (
                last_visible_record
            )


            # ------------------------------------------------
            # 順位変動
            # ------------------------------------------------

            previous_rank = (
                previous_record.get(
                    "rank"
                )
            )

            current_rank = (
                current_record.get(
                    "rank"
                )
            )


            if (
                previous_rank is not None
                and
                current_rank is not None
            ):

                if current_rank < previous_rank:

                    add_event(

                        date=date,

                        event_type=
                            "server_rank_up",

                        group=current_group,

                        old_value=
                            previous_rank,

                        new_value=
                            current_rank,

                        details={

                            "change":
                                previous_rank
                                - current_rank
                        }
                    )

                elif current_rank > previous_rank:

                    add_event(

                        date=date,

                        event_type=
                            "server_rank_down",

                        group=current_group,

                        old_value=
                            previous_rank,

                        new_value=
                            current_rank,

                        details={

                            "change":
                                current_rank
                                - previous_rank
                        }
                    )


            # ------------------------------------------------
            # レベル変動
            # ------------------------------------------------

            previous_level = (
                previous_record.get(
                    "level"
                )
            )

            current_level = (
                current_record.get(
                    "level"
                )
            )


            if (
                previous_level is not None
                and
                current_level is not None
            ):

                if current_level > previous_level:

                    # --------------------------------------------------------
                    # レベルアップそのものは、
                    # 前回Lv → 今回Lvという実測結果があるため確定。
                    # --------------------------------------------------------

                    details = {

                        "change":
                            current_level
                            - previous_level,

                        "confirmed":
                            True
                    }

                    # --------------------------------------------------------
                    # 直前のレベルアップイベントを探す
                    #
                    # 例:
                    #
                    # 9/3 Lv97 → Lv98
                    # 9/5 Lv98 → Lv99
                    #
                    # → Lv98になった9/3を開始日として、
                    #    9/5までの2日間を算出。
                    #
                    # --------------------------------------------------------

                    previous_level_up = None

                    for event in reversed(events):

                        if (
                                event.get("type")
                                == "server_ranking_level_up"
                                and
                                event.get("group")
                                == current_group
                                and
                                event.get("new_value")
                                == previous_level
                        ):
                            previous_level_up = event

                            break

                    # --------------------------------------------------------
                    # 前回のレベルアップが確認できている場合
                    # --------------------------------------------------------

                    if previous_level_up:
                        start_date = (
                            previous_level_up["date"]
                        )

                        start_dt = pd.to_datetime(

                            start_date,

                            format="%Y%m%d"

                        )

                        current_dt = pd.to_datetime(

                            date,

                            format="%Y%m%d"

                        )

                        duration_days = (

                                current_dt - start_dt

                        ).days

                        details.update({

                            "duration_confirmed":
                                True,

                            "duration_days":
                                duration_days,

                            "level_start_date":
                                start_date
                        })

                    # --------------------------------------------------------
                    # レベルアップイベントを保存
                    # --------------------------------------------------------

                    add_event(

                        date=date,

                        event_type=
                        "server_ranking_level_up",

                        group=current_group,

                        old_value=
                        previous_level,

                        new_value=
                        current_level,

                        details=details
                    )

                elif current_level < previous_level:

                    add_event(

                        date=date,

                        event_type=
                            "server_ranking_level_down",

                        group=current_group,

                        old_value=
                            previous_level,

                        new_value=
                            current_level,

                        details={

                            "change":
                                current_level
                                - previous_level
                        }
                    )


            # ------------------------------------------------
            # ギルド変更
            # ------------------------------------------------

            previous_guild = (
                    last_visible_guild or ""
            )

            current_guild = (
                current_record.get(
                    "guild",
                    ""
                )
            )


            if (
                previous_guild
                and
                current_guild
                and
                previous_guild != current_guild
            ):

                add_event(

                    date=date,

                    event_type=
                        "server_ranking_guild_change",

                    group=current_group,

                    old_value=
                        previous_guild,

                    new_value=
                        current_guild,

                    details={

                        "from_guild":
                            previous_guild,

                        "to_guild":
                            current_guild
                    }
                )


            # ------------------------------------------------
            # サーバー変更
            # ------------------------------------------------

            previous_server = (
                previous_record.get(
                    "server",
                    ""
                )
            )

            current_server = (
                current_record.get(
                    "server",
                    ""
                )
            )


            if (
                previous_server
                and
                current_server
                and
                previous_server != current_server
            ):

                add_event(

                    date=date,

                    event_type=
                        "server_ranking_server_change",

                    group=current_group,

                    old_value=
                        previous_server,

                    new_value=
                        current_server,

                    details={

                        "from_server":
                            previous_server,

                        "to_server":
                            current_server,

                        "gap":
                            False
                    }
                )


        # ====================================================
        # 前回表示 → 今回圏外
        # ====================================================

        elif previous_visible and not current_visible:

            add_event(

                date=date,

                event_type=
                    "server_ranking_exit",

                group=
                    last_visible_group,

                old_value=
                    last_visible_record.get(
                        "rank"
                    ),

                new_value=None,

                details={

                    "last_rank":
                        last_visible_record.get(
                            "rank"
                        ),

                    "last_level":
                        last_visible_record.get(
                            "level"
                        ),

                    "last_server":
                        last_visible_record.get(
                            "server"
                        ),

                    "last_guild":
                        last_visible_record.get(
                            "guild"
                        ),

                    "last_group":
                        last_visible_group,

                    "last_seen_date":
                        last_visible_date
                }
            )


        # ====================================================
        # 前回圏外 → 今回表示
        # ====================================================

        elif not previous_visible and current_visible:

            # ====================================================
            # 初めてTOP100で確認された場合
            #
            # 例:
            #
            # 9/1 CSVなし
            # 9/2 Eda 50位
            #
            # → 「TOP100ランキング入り」
            #
            # この時点では過去のランキング確認がないため、
            # サーバー変更は判定しない。
            # ====================================================

            if last_visible_record is None:

                add_event(

                    date=date,

                    event_type=
                    "server_ranking_entry",

                    group=current_group,

                    old_value=None,

                    new_value=
                    current_record.get(
                        "rank"
                    ),

                    details={

                        "rank":
                            current_record.get(
                                "rank"
                            ),

                        "level":
                            current_record.get(
                                "level"
                            ),

                        "server":
                            current_record.get(
                                "server"
                            ),

                        "guild":
                            current_record.get(
                                "guild"
                            ),

                        "group":
                            current_group,

                        "first_observation":
                            True
                    }
                )


            # ====================================================
            # 過去に一度でもTOP100で確認されている場合
            #
            # 例:
            #
            # 9/2 Eda3 50位
            # 9/3 Eda3 圏外
            # 9/4 Eda3 80位
            #
            # → TOP100ランキング入り
            #
            # ====================================================

            else:

                add_event(

                    date=date,

                    event_type=
                    "server_ranking_entry",

                    group=current_group,

                    old_value=None,

                    new_value=
                    current_record.get(
                        "rank"
                    ),

                    details={

                        "rank":
                            current_record.get(
                                "rank"
                            ),

                        "level":
                            current_record.get(
                                "level"
                            ),

                        "server":
                            current_record.get(
                                "server"
                            ),

                        "guild":
                            current_record.get(
                                "guild"
                            ),

                        "group":
                            current_group,

                        "first_observation":
                            False
                    }
                )

                # ====================================================
                # 圏外期間を挟んだサーバー変更
                #
                # 例:
                #
                # 9/2 Eda3
                # 9/3 圏外
                # 9/4 Eda7
                #
                # → Eda3 → Eda7
                #
                # CSVが存在しない日は
                # previous_visible / last_visible_record を
                # 変更していないため、ここでも正しく比較できる。
                # ====================================================

                previous_server = (
                    last_visible_record.get(
                        "server",
                        ""
                    )
                )

                # ====================================================
                # 圏外期間を挟んだギルド変更
                #
                # 例:
                #
                # 9/3  Lien
                # 9/4  無所属
                # 9/5  別ギルド
                #
                # → Lien → 別ギルド
                #
                # 無所属期間が何日続いても、
                # last_visible_record を基準に比較する。
                # ====================================================

                previous_guild = (
                        last_visible_guild or ""
                )

                current_guild = (
                    current_record.get(
                        "guild",
                        ""
                    )
                )

                if (
                    previous_guild
                    and
                    current_guild
                    and
                    previous_guild != current_guild
                ):

                    add_event(

                        date=date,

                        event_type=
                            "server_ranking_guild_change",

                        group=current_group,

                        old_value=
                            previous_guild,

                        new_value=
                            current_guild,

                        details={

                            "from_guild":
                                previous_guild,

                            "to_guild":
                                current_guild,

                            "gap":
                                True,

                            "last_seen_date":
                                last_visible_date
                        }
                    )

                current_server = (
                    current_record.get(
                        "server",
                        ""
                    )
                )

                if (
                        previous_server
                        and
                        current_server
                        and
                        previous_server != current_server
                ):
                    add_event(

                        date=date,

                        event_type=
                        "server_ranking_server_change",

                        group=current_group,

                        old_value=
                        previous_server,

                        new_value=
                        current_server,

                        details={

                            "from_server":
                                previous_server,

                            "to_server":
                                current_server,

                            "gap":
                                True,

                            "last_seen_date":
                                last_visible_date
                        }
                    )


        # ====================================================
        # 判定可能な日の状態を更新
        # ====================================================

        previous_visible = (
            current_visible
        )


        # ----------------------------------------------------
        # TOP100に存在していた場合だけ
        # 最後に確認した状態を更新
        # ----------------------------------------------------

        if current_visible:

            last_visible_group = (
                current_group
            )

            last_visible_record = (
                current_record
            )

            last_visible_date = (
                date
            )

            current_guild = (
                current_record.get(
                    "guild",
                    ""
                )
            )

            # 無所属の場合は、
            # 最後に所属していたギルドを保持する。
            if current_guild:
                last_visible_guild = (
                    current_guild
                )

    # ========================================================
    # デスペナ回復判定
    # ========================================================
    #
    # 例:
    #
    # 9/5 Lv99 → Lv98
    # 9/6 Lv98 → Lv99
    #
    # この場合、9/6のLv99復帰は
    # 通常の成長ではなく、
    # デスペナからの回復とみなす。
    #
    # 成長速度統計からは除外する。
    # ========================================================

    for i in range(1, len(events)):

        previous_event = events[i - 1]

        current_event = events[i]

        # ----------------------------------------------------
        # 前のイベントがレベルダウン
        # ----------------------------------------------------

        if (
            previous_event.get("type")
            != "server_ranking_level_down"
        ):
            continue

        # ----------------------------------------------------
        # 今回がレベルアップ
        # ----------------------------------------------------

        if (
            current_event.get("type")
            != "server_ranking_level_up"
        ):
            continue

        # ----------------------------------------------------
        # 同じサーバー
        # ----------------------------------------------------

        if (
            previous_event.get("group")
            != current_event.get("group")
        ):
            continue

        # ----------------------------------------------------
        # デスペナによる1Lvダウン→元レベル復帰
        #
        # 例:
        #
        # Lv99 → Lv98
        # Lv98 → Lv99
        # ----------------------------------------------------

        old_level = (
            previous_event.get(
                "old_value"
            )
        )

        down_level = (
            previous_event.get(
                "new_value"
            )
        )

        recovery_old_level = (
            current_event.get(
                "old_value"
            )
        )

        recovery_new_level = (
            current_event.get(
                "new_value"
            )
        )

        if (
            old_level is None
            or down_level is None
            or recovery_old_level is None
            or recovery_new_level is None
        ):
            continue

        if (
            down_level != old_level - 1
        ):
            continue

        if (
            recovery_old_level != down_level
        ):
            continue

        if (
            recovery_new_level != old_level
        ):
            continue

        # ----------------------------------------------------
        # デスペナ回復として記録
        # ----------------------------------------------------

        if "details" not in current_event:

            current_event["details"] = {}

        current_event["details"].update({

            "death_penalty_recovery":
                True,

            "excluded_from_growth_speed":
                True,

            "recovery_from_level":
                down_level,

            "recovery_to_level":
                old_level,

            "death_penalty_date":
                previous_event.get(
                    "date"
                )
        })

        # ----------------------------------------------------
        # Lvダウン側にも情報を付加
        # ----------------------------------------------------

        if "details" not in previous_event:

            previous_event["details"] = {}

        previous_event["details"].update({

            "possible_death_penalty":
                True,

            "recovered":
                True,

            "recovery_date":
                current_event.get(
                    "date"
                )
        })


    return events

# ============================================================
# Summary
# ============================================================

def create_summary(player):

    history = player["history"]

    if not history:

        return {}


    # ========================================================
    # World
    # ========================================================

    world_records = [

        record

        for record in history

        if record["world"]["visible"]

    ]


    world_ranks = [

        record["world"]["rank"]

        for record in world_records

        if record["world"]["rank"] is not None

    ]


    # ========================================================
    # Eda
    # ========================================================

    eda_records = [

        record

        for record in history

        if record[
            "server_ranking"
        ]["Eda"]["visible"]

    ]


    eda_ranks = [

        record[
            "server_ranking"
        ]["Eda"]["rank"]

        for record in eda_records

        if record[
            "server_ranking"
        ]["Eda"]["rank"] is not None

    ]


    # ========================================================
    # Virba
    # ========================================================

    virba_records = [

        record

        for record in history

        if record[
            "server_ranking"
        ]["Virba"]["visible"]

    ]


    virba_ranks = [

        record[
            "server_ranking"
        ]["Virba"]["rank"]

        for record in virba_records

        if record[
            "server_ranking"
        ]["Virba"]["rank"] is not None

    ]


    # ========================================================
    # Worldスナップショット
    # ========================================================

    world_snapshot = (

        player["world_snapshot"]

    )


    # ========================================================
    # 現在情報
    # ========================================================

    current = player["current"]


    # ========================================================
    # 最後に確認した状態
    # ========================================================

    last_known = player["last_known"]


    # ========================================================
    # レベル履歴
    # ========================================================
    #
    # Eda/Virbaのみ。
    #
    # Worldは使用しない。
    # ========================================================

    server_level_records = []


    for record in history:

        if (

            record[
                "server_ranking"
            ]["Eda"]["visible"]

        ):

            server_level_records.append(

                (

                    record["date"],

                    record[
                        "server_ranking"
                    ]["Eda"]["level"]

                )

            )

        elif (

            record[
                "server_ranking"
            ]["Virba"]["visible"]

        ):

            server_level_records.append(

                (

                    record["date"],

                    record[
                        "server_ranking"
                    ]["Virba"]["level"]

                )

            )

    if server_level_records:

        first_level = (
            server_level_records[0][1]
        )

        last_known_level = (
            server_level_records[-1][1]
        )

    else:

        first_level = None

        last_known_level = None

    # --------------------------------------------------------
    # Currentは「最新日現在」
    #
    # 最新日にランキング外ならNone
    # --------------------------------------------------------

    current_level = (
        player["current"]["level"]
    )


    # ========================================================
    # Summary
    # ========================================================

    return {

        "first_seen":
            history[0]["date"],

        "last_seen":
            history[-1]["date"],


        # ----------------------------------------------------
        # World
        # ----------------------------------------------------

        "world_snapshot": {

            "rank":
                world_snapshot["rank"],

            "level":
                world_snapshot["level"],

            "server":
                world_snapshot["server"],

            "guild":
                world_snapshot["guild"],

            "snapshot_dates":
                world_snapshot["snapshot_dates"],

            "reliable_for_daily_change":
                WORLD_RELIABLE_FOR_DAILY_CHANGE
        },


        # ----------------------------------------------------
        # 現在
        # ----------------------------------------------------

        "current": {

            "character":
                current["character"],

            "level":
                current["level"],

            "server":
                current["server"],

            "guild":
                current["guild"],

            "eda":
                current["eda"],

            "virba":
                current["virba"]
        },


        # ----------------------------------------------------
        # 最後に確認した状態
        # ----------------------------------------------------

        "last_known": {

            "date":
                last_known["date"],

            "character":
                last_known["character"],

            "level":
                last_known["level"],

            "server":
                last_known["server"],

            "guild":
                last_known["guild"],

            "group":
                last_known["group"],

            "rank":
                last_known["rank"]
        },


        # ----------------------------------------------------
        # レベル
        # ----------------------------------------------------

        "first_level":
            first_level,

        "last_known_level":
            last_known_level,

        "current_level":
            current_level,

        "level_change": (

            current_level - first_level

            if (

                    first_level is not None

                    and
                    current_level is not None

            )

            else None

        ),


        # ----------------------------------------------------
        # World統計
        # ----------------------------------------------------

        "world_observation_days":
            len(world_records),

        "best_world_rank": (

            min(world_ranks)

            if world_ranks

            else None

        ),

        "worst_world_rank": (

            max(world_ranks)

            if world_ranks

            else None

        ),


        # ----------------------------------------------------
        # Eda
        # ----------------------------------------------------

        "eda": {

            "observation_days":
                len(eda_records),

            "current_rank":
                current["eda"]["rank"],

            "best_rank": (

                min(eda_ranks)

                if eda_ranks

                else None

            ),

            "reliable_for_daily_change":
                SERVER_RELIABLE_FOR_DAILY_CHANGE
        },


        # ----------------------------------------------------
        # Virba
        # ----------------------------------------------------

        "virba": {

            "observation_days":
                len(virba_records),

            "current_rank":
                current["virba"]["rank"],

            "best_rank": (

                min(virba_ranks)

                if virba_ranks

                else None

            ),

            "reliable_for_daily_change":
                SERVER_RELIABLE_FOR_DAILY_CHANGE
        }
    }


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)

    print("HIT : The World")

    print("キャラクター履歴作成")

    print("=" * 60)


    # ========================================================
    # World
    # ========================================================

    ranking_files = sorted(

        RANKING_DIR.glob(
            "ranking_*.csv"
        )

    )


    if not ranking_files:

        print()

        print(
            "全体ランキングCSVが"
            "見つかりません。"
        )

        return


    print()

    print(
        f"全体ランキングデータ: "
        f"{len(ranking_files)}日分"
    )

    print(
        "  日次変化信頼性: 対象外"
    )

    print(
        "  用途: 混沌開始時点の"
        "スナップショット"
    )

    print(
        "        TOP1000 / "
        "サーバー別TOP100外調査"
    )


    # ========================================================
    # Server
    # ========================================================

    virba_files = sorted(

        SERVER_RANKING_DIR.glob(
            "ranking_virba_*.csv"
        )

    )

    eda_files = sorted(

        SERVER_RANKING_DIR.glob(
            "ranking_eda_*.csv"
        )

    )

    # ========================================================
    # サーバーランキングCSV存在状況
    # ========================================================
    #
    # 重要:
    #
    # CSVが存在しない日
    #     ≠
    # TOP100圏外
    #
    # Eda / Virbaそれぞれについて、
    # 実際にランキングCSVが存在した日を記録する。
    # ========================================================

    server_data_available = {}

    for file_path in (
            virba_files
            +
            eda_files
    ):

        date = extract_date(
            file_path
        )

        group = (
            get_server_group_from_filename(
                file_path
            )
        )

        if not date or not group:
            continue

        if date not in server_data_available:
            server_data_available[date] = {

                "Eda": False,

                "Virba": False
            }

        server_data_available[date][group] = True

    print(

        f"Virbaランキングデータ: "
        f"{len(virba_files)}日分"

    )

    print(

        f"Edaランキングデータ: "
        f"{len(eda_files)}日分"

    )


    player_history = {}


    # ========================================================
    # World処理
    # ========================================================

    print()

    print("=" * 60)

    print("混沌 World TOP1000を処理")

    print("=" * 60)


    for file_path in ranking_files:

        date = extract_date(
            file_path
        )

        if not date:
            continue


        print()

        print(
            f"{date} を読み込み中..."
        )


        df = load_ranking(
            file_path
        )


        print(
            f"  {len(df):,}人"
        )


        for _, row in df.iterrows():

            character = str(
                row["character"]
            ).strip()


            if not character:
                continue


            if character not in player_history:

                player_history[character] = (

                    create_player(
                        character
                    )

                )


            player = player_history[
                character
            ]


            if character not in player["names"]:

                player["names"].append(
                    character
                )


            update_world_record(

                player,

                date,

                row

            )


    # ========================================================
    # Serverランキング処理
    # ========================================================

    server_files = []


    server_files.extend(
        virba_files
    )

    server_files.extend(
        eda_files
    )


    server_files.sort(

        key=lambda path: (

            extract_date(path),

            path.name

        )

    )


    print()

    print("=" * 60)

    print("Eda / Virba TOP100を処理")

    print("=" * 60)


    for file_path in server_files:

        date = extract_date(
            file_path
        )

        group = (
            get_server_group_from_filename(
                file_path
            )
        )


        if not date or not group:
            continue


        print()

        print(
            f"{date} {group} を"
            "読み込み中..."
        )


        df = load_ranking(
            file_path
        )


        print(
            f"  {len(df):,}人"
        )


        for _, row in df.iterrows():

            character = str(
                row["character"]
            ).strip()


            if not character:
                continue


            if character not in player_history:

                player_history[character] = (

                    create_player(
                        character
                    )

                )


            player = player_history[
                character
            ]


            if character not in player["names"]:

                player["names"].append(
                    character
                )


            update_server_record(

                player,

                date,

                row,

                group

            )


    # ========================================================
    # 整理
    # ========================================================

    sort_history(
        player_history
    )


    # ========================================================
    # World / Current / Last Known生成
    # ========================================================

    print()

    print(
        "Worldスナップショット・"
        "現在情報・最後の確認情報を整理中..."
    )


    for player in player_history.values():

        # ----------------------------------------------------
        # World
        # ----------------------------------------------------

        player["world_snapshot"] = (

            create_world_snapshot(
                player
            )

        )


        # ----------------------------------------------------
        # Current
        # ----------------------------------------------------

        player["current"] = (

            create_current(
                player
            )

        )


        # ----------------------------------------------------
        # Last Known
        # ----------------------------------------------------

        player["last_known"] = (

            create_last_known(
                player
            )

        )


    # ========================================================
    # Status
    # ========================================================

    active_count, inactive_count = (

        update_status(
            player_history
        )

    )


    # ========================================================
    # Summary / Events
    # ========================================================

    print(

        "キャラクター統計情報・"
        "イベントを作成中..."

    )


    total_events = 0

    event_counts = {}


    for player in player_history.values():

        player["summary"] = (

            create_summary(
                player
            )

        )

        player["events"] = (

            create_events(
                player,
                server_data_available
            )

        )


        total_events += len(
            player["events"]
        )


        for event in player["events"]:

            event_type = event["type"]


            event_counts[event_type] = (

                event_counts.get(
                    event_type,
                    0
                ) + 1

            )


    # ========================================================
    # 保存
    # ========================================================

    output_file = (

        HISTORY_DIR /

        "player_history.json"

    )


    with open(

        output_file,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            player_history,

            f,

            ensure_ascii=False,

            indent=2

        )


    # ========================================================
    # 結果
    # ========================================================

    print()

    print("=" * 60)

    print("履歴作成完了")

    print("=" * 60)

    print()

    print(

        f"キャラクター数: "
        f"{len(player_history):,}"

    )

    print(

        f"イベント数: "
        f"{total_events:,}"

    )

    print(

        f"現在確認可能: "
        f"{active_count:,}人"

    )

    print(

        f"現在未確認: "
        f"{inactive_count:,}人"

    )


    # ========================================================
    # データの扱い
    # ========================================================

    print()

    print("【データの扱い】")

    print()

    print("  World:")

    print(
        "    混沌開始時点の"
        "スナップショット"
    )

    print(
        "    日次変化: 対象外"
    )

    print(
        "    現在情報: 使用しない"
    )

    print(
        "    TOP1000: 利用"
    )

    print(
        "    サーバー別TOP100外:"
        " 利用"
    )


    print()

    print("  Eda:")

    print(
        "    現在ランキングTOP100"
    )

    print(
        "    日次更新: 有効"
    )


    print()

    print("  Virba:")

    print(
        "    現在ランキングTOP100"
    )

    print(
        "    日次更新: 有効"
    )


    print()

    print(
        f"保存先: "
        f"{output_file.resolve()}"
    )


    # ========================================================
    # イベント集計
    # ========================================================

    print()

    print("【イベント集計】")

    print("-" * 50)

    event_labels = {

        # --------------------------------------------------------
        # TOP100
        # --------------------------------------------------------

        "server_ranking_entry":
            "TOP100ランキング入り",

        "server_ranking_exit":
            "TOP100ランキング圏外",

        # --------------------------------------------------------
        # 順位
        # --------------------------------------------------------

        "server_rank_up":
            "サーバー順位上昇",

        "server_rank_down":
            "サーバー順位下降",

        # --------------------------------------------------------
        # レベル
        # --------------------------------------------------------

        "server_ranking_level_up":
            "サーバーランキングレベルアップ",

        "server_ranking_level_down":
            "サーバーランキングレベルダウン",

        # --------------------------------------------------------
        # 所属
        # --------------------------------------------------------

        "server_ranking_server_change":
            "サーバーランキングサーバー変更",

        "server_ranking_guild_change":
            "サーバーランキングギルド変更"
    }


    for event_type, label in (

        event_labels.items()

    ):

        print(

            f"  {label}: "
            f"{event_counts.get(event_type, 0):,}件"

        )


    # ========================================================
    # サンプル
    # ========================================================

    print()

    print("【サンプル】")

    print("-" * 50)


    sample_players = list(

        player_history.values()

    )[:5]


    for player in sample_players:

        summary = player["summary"]

        world = (
            player["world_snapshot"]
        )

        current = (
            player["current"]
        )

        last_known = (
            player["last_known"]
        )


        print()

        print(
            f"キャラクター: "
            f"{player['character']}"
        )

        print(
            f"  tracking_id: "
            f"{player['tracking_id']}"
        )

        print(
            f"  名前履歴: "
            f"{', '.join(player['names'])}"
        )

        print(
            f"  status: "
            f"{'active' if player['status']['active'] else 'inactive'}"
        )

        print(
            f"  last_seen: "
            f"{player['status']['last_seen'] or '-'}"
        )


        # ----------------------------------------------------
        # World
        # ----------------------------------------------------

        print()

        print(
            "  【混沌Worldスナップショット】"
        )

        print(
            f"    順位: "
            f"{world['rank'] or '-'}"
        )

        print(
            f"    Lv: "
            f"{world['level'] or '-'}"
        )

        print(
            f"    サーバー: "
            f"{world['server'] or '-'}"
        )

        print(
            f"    ギルド: "
            f"{world['guild'] or '無所属'}"
        )


        # ----------------------------------------------------
        # Current
        # ----------------------------------------------------

        print()

        print(
            "  【現在】"
        )

        print(
            f"    Lv: "
            f"{current['level'] or '-'}"
        )

        print(
            f"    サーバー: "
            f"{current['server'] or '-'}"
        )

        print(
            f"    ギルド: "
            f"{current['guild'] or '無所属'}"
        )

        print(
            f"    Eda: "
            f"{current['eda']['rank'] or '-'}位"
        )

        print(
            f"    Virba: "
            f"{current['virba']['rank'] or '-'}位"
        )


        # ----------------------------------------------------
        # Last Known
        # ----------------------------------------------------

        print()

        print(
            "  【最後に確認した状態】"
        )

        print(
            f"    日付: "
            f"{last_known['date'] or '-'}"
        )

        print(
            f"    グループ: "
            f"{last_known['group'] or '-'}"
        )

        print(
            f"    Lv: "
            f"{last_known['level'] or '-'}"
        )

        print(
            f"    サーバー: "
            f"{last_known['server'] or '-'}"
        )

        print(
            f"    ギルド: "
            f"{last_known['guild'] or '無所属'}"
        )

        print(
            f"    順位: "
            f"{last_known['rank'] or '-'}位"
        )


        # ----------------------------------------------------
        # Level
        # ----------------------------------------------------

        print()

        print(
            "  【レベル情報】"
        )

        print(
            f"    初回確認Lv: "
            f"{summary.get('first_level') or '-'}"
        )

        print(
            f"    最終確認Lv: "
            f"{summary.get('last_known_level') or '-'}"
        )

        print(
            f"    現在Lv: "
            f"{summary.get('current_level') or '-'}"
        )

        print(
            f"    初回→現在の変化: "
            f"{summary.get('level_change')}"
        )


        # ----------------------------------------------------
        # Events
        # ----------------------------------------------------

        print(
            f"  イベント数: "
            f"{len(player['events']):,}件"
        )


        # ----------------------------------------------------
        # 日別履歴
        # ----------------------------------------------------

        for record in player["history"]:

            world_record = (
                record["world"]
            )

            eda = (
                record[
                    "server_ranking"
                ]["Eda"]
            )

            virba = (
                record[
                    "server_ranking"
                ]["Virba"]
            )


            world_rank = (

                world_record["rank"]

                if world_record["visible"]

                else "-"

            )

            eda_rank = (

                eda["rank"]

                if eda["visible"]

                else "-"

            )

            virba_rank = (

                virba["rank"]

                if virba["visible"]

                else "-"

            )


            print(

                f"    {record['date']} "

                f"World:{world_rank}位 "

                f"Eda:{eda_rank}位 "

                f"Virba:{virba_rank}位 "

                f"WorldLv:"
                f"{world_record['level'] or '-'} "

                f"EdaLv:"
                f"{eda['level'] or '-'} "

                f"VirbaLv:"
                f"{virba['level'] or '-'}"

            )


# ============================================================
# 実行
# ============================================================

if __name__ == "__main__":

    main()