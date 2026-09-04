import json
import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

RANKING_DIR = BASE_DIR / "data" / "ranking"
HISTORY_DIR = BASE_DIR / "data" / "history"

HISTORY_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================================
# ランキングCSV読み込み
# ==========================================================

def load_ranking(file_path):
    """ランキングCSVを読み込む"""

    df = pd.read_csv(
        file_path,
        dtype=str
    )

    df["rank"] = pd.to_numeric(
        df["rank"]
    )

    df["level"] = pd.to_numeric(
        df["level"]
    )

    # 空欄を統一
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

    df["character"] = (
        df["character"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    return df


# ==========================================================
# 候補スコア計算
# ==========================================================

def calculate_score(old_player, new_player):
    """
    旧キャラクターと新キャラクターが
    同一人物である可能性をスコアリングする。

    最大100点
    """

    score = 0
    reasons = []

    # ------------------------------------------------------
    # サーバー一致
    # ------------------------------------------------------

    if (
        old_player["server"]
        and new_player["server"]
        and old_player["server"]
        == new_player["server"]
    ):

        score += 30

        reasons.append(
            "サーバー一致"
        )

    # ------------------------------------------------------
    # ギルド一致
    # ------------------------------------------------------

    if (
        old_player["guild"]
        and new_player["guild"]
        and old_player["guild"]
        == new_player["guild"]
    ):

        score += 30

        reasons.append(
            "ギルド一致"
        )

    # ------------------------------------------------------
    # レベル一致
    # ------------------------------------------------------

    level_difference = abs(
        int(old_player["level"])
        - int(new_player["level"])
    )

    if level_difference == 0:

        score += 25

        reasons.append(
            "レベル一致"
        )

    elif level_difference == 1:

        score += 15

        reasons.append(
            "レベル差1"
        )

    elif level_difference == 2:

        score += 5

        reasons.append(
            "レベル差2"
        )

    # ------------------------------------------------------
    # 順位の近さ
    # ------------------------------------------------------

    rank_difference = abs(
        int(old_player["rank"])
        - int(new_player["rank"])
    )

    if rank_difference <= 10:

        score += 15

        reasons.append(
            "順位差10以内"
        )

    elif rank_difference <= 30:

        score += 10

        reasons.append(
            "順位差30以内"
        )

    elif rank_difference <= 100:

        score += 5

        reasons.append(
            "順位差100以内"
        )

    return score, reasons


# ==========================================================
# 信頼度判定
# ==========================================================

def get_confidence(score):

    if score >= 90:

        return "very_high"

    elif score >= 70:

        return "high"

    elif score >= 50:

        return "medium"

    elif score >= 30:

        return "low"

    else:

        return "very_low"


# ==========================================================
# メイン処理
# ==========================================================

def main():

    print("=" * 60)
    print("HIT : The World")
    print("同一人物候補分析")
    print("=" * 60)

    # ------------------------------------------------------
    # ランキングCSV
    # ------------------------------------------------------

    ranking_files = sorted(
        RANKING_DIR.glob(
            "ranking_*.csv"
        )
    )

    if len(ranking_files) < 2:

        print()
        print(
            "ランキングCSVが2日分以上必要です。"
        )

        return

    print()
    print(
        f"ランキングデータ: "
        f"{len(ranking_files)}日分"
    )

    # ------------------------------------------------------
    # 既存の履歴データ
    # ------------------------------------------------------

    history_file = (
        HISTORY_DIR /
        "player_history.json"
    )

    if history_file.exists():

        with open(
            history_file,
            "r",
            encoding="utf-8"
        ) as f:

            player_history = json.load(f)

    else:

        player_history = {}

    # ------------------------------------------------------
    # 候補一覧
    # ------------------------------------------------------

    candidates = []

    # ------------------------------------------------------
    # 連続するランキングを比較
    # ------------------------------------------------------

    for old_file, new_file in zip(
        ranking_files,
        ranking_files[1:]
    ):

        old_date = (
            old_file.stem
            .replace(
                "ranking_",
                ""
            )
        )

        new_date = (
            new_file.stem
            .replace(
                "ranking_",
                ""
            )
        )

        print()
        print(
            f"{old_date} → {new_date}"
        )

        old_df = load_ranking(
            old_file
        )

        new_df = load_ranking(
            new_file
        )

        # --------------------------------------------------
        # キャラクター → データ
        # --------------------------------------------------

        old_players = {
            row["character"]: row
            for _, row in old_df.iterrows()
            if row["character"]
        }

        new_players = {
            row["character"]: row
            for _, row in new_df.iterrows()
            if row["character"]
        }

        old_characters = set(
            old_players.keys()
        )

        new_characters = set(
            new_players.keys()
        )

        # --------------------------------------------------
        # OUT
        # --------------------------------------------------

        ranking_out = (
            old_characters
            - new_characters
        )

        # --------------------------------------------------
        # IN
        # --------------------------------------------------

        ranking_in = (
            new_characters
            - old_characters
        )

        print(
            f"  OUT: {len(ranking_out):,}人"
        )

        print(
            f"  IN : {len(ranking_in):,}人"
        )

        if not ranking_out or not ranking_in:

            continue

        # --------------------------------------------------
        # OUT × IN の全組み合わせを比較
        # --------------------------------------------------

        for old_character in ranking_out:

            old_player = old_players[
                old_character
            ]

            for new_character in ranking_in:

                new_player = new_players[
                    new_character
                ]

                score, reasons = calculate_score(
                    old_player,
                    new_player
                )

                confidence = get_confidence(
                    score
                )

                # --------------------------------------------------
                # 低スコアは保存しない
                # --------------------------------------------------

                if score < 50:

                    continue

                # --------------------------------------------------
                # tracking_id
                # --------------------------------------------------

                old_tracking_id = None
                new_tracking_id = None

                if old_character in player_history:

                    old_tracking_id = (
                        player_history[
                            old_character
                        ].get(
                            "tracking_id"
                        )
                    )

                if new_character in player_history:

                    new_tracking_id = (
                        player_history[
                            new_character
                        ].get(
                            "tracking_id"
                        )
                    )

                # --------------------------------------------------
                # 候補データ
                # --------------------------------------------------

                candidate = {

                    "date": new_date,

                    "old_character": old_character,

                    "new_character": new_character,

                    "old_tracking_id":
                        old_tracking_id,

                    "new_tracking_id":
                        new_tracking_id,

                    "old": {
                        "rank": int(
                            old_player["rank"]
                        ),
                        "level": int(
                            old_player["level"]
                        ),
                        "server":
                            old_player["server"],
                        "guild":
                            old_player["guild"]
                    },

                    "new": {
                        "rank": int(
                            new_player["rank"]
                        ),
                        "level": int(
                            new_player["level"]
                        ),
                        "server":
                            new_player["server"],
                        "guild":
                            new_player["guild"]
                    },

                    "score": score,

                    "confidence":
                        confidence,

                    "reasons":
                        reasons
                }

                candidates.append(
                    candidate
                )

    # ======================================================
    # スコア順に並べる
    # ======================================================

    candidates.sort(
        key=lambda candidate:
        candidate["score"],
        reverse=True
    )

    # ======================================================
    # JSON保存
    # ======================================================

    output_file = (
        HISTORY_DIR /
        "identity_candidates.json"
    )

    result = {

        "generated_at": (
            ranking_files[-1]
            .stem
            .replace(
                "ranking_",
                ""
            )
        ),

        "candidate_count":
            len(candidates),

        "candidates":
            candidates
    }

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )

    # ======================================================
    # 結果表示
    # ======================================================

    print()
    print("=" * 60)
    print("同一人物候補分析完了")
    print("=" * 60)

    print()
    print(
        f"候補数: "
        f"{len(candidates):,}"
    )

    print(
        f"保存先: "
        f"{output_file.resolve()}"
    )

    # ======================================================
    # 信頼度別集計
    # ======================================================

    confidence_counts = {}

    for candidate in candidates:

        confidence = candidate[
            "confidence"
        ]

        confidence_counts[
            confidence
        ] = (
            confidence_counts.get(
                confidence,
                0
            ) + 1
        )

    print()
    print("【信頼度別】")
    print("-" * 50)

    confidence_labels = {

        "very_high":
            "非常に高い",

        "high":
            "高い",

        "medium":
            "中程度",

        "low":
            "低い",

        "very_low":
            "非常に低い"
    }

    for confidence, label in (
        confidence_labels.items()
    ):

        print(
            f"  {label}: "
            f"{confidence_counts.get(confidence, 0):,}件"
        )

    # ======================================================
    # 上位候補表示
    # ======================================================

    print()
    print("【同一人物候補 TOP20】")
    print("-" * 50)

    for index, candidate in enumerate(
        candidates[:20],
        start=1
    ):

        print()

        print(
            f"{index}. "
            f"{candidate['old_character']}"
            f" → "
            f"{candidate['new_character']}"
        )

        print(
            f"   スコア: "
            f"{candidate['score']}/100"
        )

        print(
            f"   信頼度: "
            f"{candidate['confidence']}"
        )

        print(
            f"   理由: "
            f"{', '.join(candidate['reasons'])}"
        )

        print(
            f"   旧: "
            f"Lv{candidate['old']['level']} "
            f"{candidate['old']['rank']}位 "
            f"{candidate['old']['server']} "
            f"{candidate['old']['guild'] or '無所属'}"
        )

        print(
            f"   新: "
            f"Lv{candidate['new']['level']} "
            f"{candidate['new']['rank']}位 "
            f"{candidate['new']['server']} "
            f"{candidate['new']['guild'] or '無所属'}"
        )


if __name__ == "__main__":
    main()
