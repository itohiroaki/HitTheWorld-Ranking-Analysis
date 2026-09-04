from pathlib import Path
import subprocess
import sys
from datetime import datetime


# ============================================================
# 設定
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

SCRIPTS = [
    ("① ランキング取得", "main.py"),
    ("② 前日差分解析", "diff_analyzer.py"),
    ("③ プレイヤー履歴更新", "player_history.py"),
    ("④ 日次分析生成", "ranking_analysis.py"),
]


# ============================================================
# 共通処理
# ============================================================

def run_script(label, script_name):
    """
    指定したPythonスクリプトを実行する。
    エラーが発生した場合はFalseを返す。
    """

    script_path = BASE_DIR / script_name

    print()
    print("=" * 70)
    print(label)
    print("=" * 70)

    print()
    print(f"実行: {script_name}")
    print()

    if not script_path.exists():
        print(f"❌ ファイルが見つかりません:")
        print(f"   {script_path}")
        return False

    try:

        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
            ],
            cwd=BASE_DIR,
            check=False,
        )

        if result.returncode != 0:

            print()
            print(f"❌ {script_name} が失敗しました。")
            print(
                f"終了コード: "
                f"{result.returncode}"
            )

            return False

        print()
        print(f"✅ {script_name} 完了")

        return True

    except Exception as e:

        print()
        print(
            f"❌ {script_name} の実行中に"
            f"エラーが発生しました。"
        )

        print(
            f"エラー: {e}"
        )

        return False


# ============================================================
# 出力確認
# ============================================================

def check_output_files():

    print()
    print("=" * 70)
    print("出力ファイル確認")
    print("=" * 70)

    today = datetime.now().strftime("%Y%m%d")

    expected_files = [
        BASE_DIR
        / "data"
        / "ranking"
        / f"ranking_{today}.csv",

        BASE_DIR
        / "data"
        / "ranking_server"
        / f"ranking_virba_{today}.csv",

        BASE_DIR
        / "data"
        / "ranking_server"
        / f"ranking_eda_{today}.csv",

        BASE_DIR
        / "data"
        / "diff"
        / f"diff_{today}.json",

        BASE_DIR
        / "data"
        / "history"
        / "player_history.json",

        BASE_DIR
        / "data"
        / "history"
        / "daily_analysis"
        / f"{today}.json",

        BASE_DIR
        / "data"
        / "history"
        / "daily_analysis_latest.json",

        BASE_DIR
        / "data"
        / "history"
        / "daily_analysis"
        / "index.json",
    ]

    all_ok = True

    print()

    for file_path in expected_files:

        if file_path.exists():

            print(
                f"  ✅ {file_path.relative_to(BASE_DIR)}"
            )

        else:

            print(
                f"  ❌ {file_path.relative_to(BASE_DIR)}"
                f"  ← 見つかりません"
            )

            all_ok = False

    return all_ok


# ============================================================
# メイン
# ============================================================

def main():

    start_time = datetime.now()

    print("=" * 70)
    print("HIT : The World")
    print("日次ランキング自動更新")
    print("=" * 70)

    print()
    print(
        f"開始時刻: "
        f"{start_time.strftime('%Y/%m/%d %H:%M:%S')}"
    )

    print()
    print(
        f"作業フォルダ:"
    )
    print(
        f"  {BASE_DIR}"
    )

    # --------------------------------------------------------
    # 4本を順番に実行
    # --------------------------------------------------------

    for label, script_name in SCRIPTS:

        success = run_script(
            label,
            script_name,
        )

        if not success:

            print()
            print("=" * 70)
            print("❌ 日次更新中止")
            print("=" * 70)

            print()
            print(
                f"失敗した処理: "
                f"{script_name}"
            )

            print()
            print(
                "後続処理は実行していません。"
            )

            print()
            print(
                "原因を確認してから、"
                "再度 daily_update.py を実行してください。"
            )

            return 1

    # --------------------------------------------------------
    # 出力確認
    # --------------------------------------------------------

    output_ok = check_output_files()

    # --------------------------------------------------------
    # 完了
    # --------------------------------------------------------

    end_time = datetime.now()

    elapsed = end_time - start_time

    print()
    print("=" * 70)

    if output_ok:

        print("🎉 日次更新完了")

    else:

        print("⚠️ 日次更新は完了しましたが、")
        print("   一部の出力ファイルを確認できませんでした。")

    print("=" * 70)

    print()
    print(
        f"終了時刻: "
        f"{end_time.strftime('%Y/%m/%d %H:%M:%S')}"
    )

    print(
        f"処理時間: "
        f"{elapsed}"
    )

    print()

    if output_ok:
        print("Webサイト用データの更新が完了しました。")
        return 0

    return 1


# ============================================================
# 実行
# ============================================================

if __name__ == "__main__":
    sys.exit(main())
