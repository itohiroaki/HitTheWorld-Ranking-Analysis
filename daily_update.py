from pathlib import Path
import subprocess
import sys
import shutil
import os
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
        print("❌ ファイルが見つかりません:")
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
# Web公開用データ同期
# ============================================================

def sync_web_data():

    print()
    print("=" * 70)
    print("Web公開用データ同期")
    print("=" * 70)

    source_history = (
        BASE_DIR
        / "data"
        / "history"
    )

    web_history = (
        BASE_DIR
        / "web"
        / "data"
        / "history"
    )

    web_daily_analysis = (
        web_history
        / "daily_analysis"
    )

    # --------------------------------------------------------
    # 保存先フォルダ作成
    # --------------------------------------------------------

    web_daily_analysis.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # daily_analysis
    # --------------------------------------------------------

    source_daily_analysis = (
        source_history
        / "daily_analysis"
    )

    copied_count = 0

    if source_daily_analysis.exists():

        for source_file in source_daily_analysis.glob("*.json"):

            # index.jsonは下で明示的にコピーするため、
            # ここでは二重コピーしない
            if source_file.name == "index.json":
                continue

            destination_file = (
                web_daily_analysis
                / source_file.name
            )

            shutil.copy2(
                source_file,
                destination_file,
            )

            print(
                f"  ✅ {source_file.name}"
            )

            copied_count += 1

    else:

        print(
            "  ❌ daily_analysis フォルダが"
            "見つかりません。"
        )

        return False

    # --------------------------------------------------------
    # daily_analysis_latest.json
    # --------------------------------------------------------

    latest_source = (
        source_history
        / "daily_analysis_latest.json"
    )

    latest_destination = (
        web_history
        / "daily_analysis_latest.json"
    )

    if latest_source.exists():

        shutil.copy2(
            latest_source,
            latest_destination,
        )

        print(
            "  ✅ daily_analysis_latest.json"
        )

        copied_count += 1

    else:

        print(
            "  ❌ daily_analysis_latest.json"
            " が見つかりません。"
        )

        return False

    # --------------------------------------------------------
    # index.json
    # --------------------------------------------------------

    index_source = (
        source_daily_analysis
        / "index.json"
    )

    index_destination = (
        web_daily_analysis
        / "index.json"
    )

    if index_source.exists():

        shutil.copy2(
            index_source,
            index_destination,
        )

        print(
            "  ✅ daily_analysis/index.json"
        )

        copied_count += 1

    else:

        print(
            "  ❌ daily_analysis/index.json"
            " が見つかりません。"
        )

        return False

    # --------------------------------------------------------
    # player_history.json
    # --------------------------------------------------------

    player_history_source = (
        source_history
        / "player_history.json"
    )

    player_history_destination = (
        web_history
        / "player_history.json"
    )

    if player_history_source.exists():

        shutil.copy2(
            player_history_source,
            player_history_destination,
        )

        print(
            "  ✅ player_history.json"
        )

        copied_count += 1

    else:

        print(
            "  ❌ player_history.json"
            " が見つかりません。"
        )

        return False

    # --------------------------------------------------------
    # 完了
    # --------------------------------------------------------

    print()
    print(
        f"Web公開用データ: "
        f"{copied_count} ファイル"
    )

    print(
        "✅ Web公開用データ同期完了"
    )

    return True


# ============================================================
# GitHub自動更新
# ============================================================

def git_sync_web_data():
    """
    Web公開用データをGitHubへ自動commit / pushする。

    Task Schedulerから実行した場合に、
    GitHub認証待ちなどで無限に停止しないようにする。
    """

    print()
    print("=" * 70)
    print("GitHub自動更新")
    print("=" * 70)

    # --------------------------------------------------------
    # Git用環境変数
    # --------------------------------------------------------

    git_env = os.environ.copy()

    # Gitが認証入力を求めても、
    # Task Scheduler上で無限待機しないようにする
    git_env["GIT_TERMINAL_PROMPT"] = "0"

    try:

        # ----------------------------------------------------
        # Gitの状態確認
        # ----------------------------------------------------

        print()
        print("  Git状態を確認しています...")

        result = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "--",
                "web/data",
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=git_env,
            timeout=120,
        )

        if result.returncode != 0:

            print(
                "❌ Git statusに失敗しました。"
            )

            print(
                result.stderr
            )

            return False

        # ----------------------------------------------------
        # 変更がない場合
        # ----------------------------------------------------

        if not result.stdout.strip():

            print(
                "  ℹ️ Web公開用データに変更はありません。"
            )

            print(
                "  GitHubへのpushは不要です。"
            )

            return True

        print(
            "  Web公開用データの変更を検出しました。"
        )

        # ----------------------------------------------------
        # web/dataだけをステージ
        # ----------------------------------------------------

        print()
        print("  Git addを実行しています...")

        result = subprocess.run(
            [
                "git",
                "add",
                "web/data",
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=git_env,
            timeout=120,
        )

        if result.returncode != 0:

            print(
                "❌ git add に失敗しました。"
            )

            print(
                result.stderr
            )

            return False

        print(
            "  ✅ git add 完了"
        )

        # ----------------------------------------------------
        # commit
        # ----------------------------------------------------

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        commit_message = (
            f"Daily ranking update {today}"
        )

        print()
        print(
            "  Git commitを実行しています..."
        )

        result = subprocess.run(
            [
                "git",
                "commit",
                "-m",
                commit_message,
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=git_env,
            timeout=120,
        )

        if result.returncode != 0:

            print(
                "❌ git commit に失敗しました。"
            )

            print(
                result.stdout
            )

            print(
                result.stderr
            )

            return False

        print(
            f"  ✅ commit: {commit_message}"
        )

        # ----------------------------------------------------
        # push
        # ----------------------------------------------------

        print()
        print(
            "  GitHubへpushしています..."
        )

        result = subprocess.run(
            [
                "git",
                "push",
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=git_env,
            timeout=120,
        )

        if result.returncode != 0:

            print()
            print(
                "❌ git push に失敗しました。"
            )

            print()

            if result.stdout:
                print(
                    result.stdout
                )

            if result.stderr:
                print(
                    result.stderr
                )

            print()
            print(
                "考えられる原因:"
            )
            print(
                "  ・GitHub認証情報が取得できない"
            )
            print(
                "  ・Task Schedulerの実行環境からGitHubへ接続できない"
            )
            print(
                "  ・GitHubへのpush権限がない"
            )

            return False

        print(
            "  ✅ GitHubへのpush完了"
        )

        return True

    except subprocess.TimeoutExpired as e:

        print()
        print(
            "❌ Git処理が120秒以内に終了しませんでした。"
        )

        print(
            "  GitHub認証またはGit通信で"
            "待機している可能性があります。"
        )

        print(
            f"  対象コマンド: {e.cmd}"
        )

        return False

    except Exception as e:

        print()
        print(
            "❌ GitHub自動更新中に"
            "エラーが発生しました。"
        )

        print(
            f"   {e}"
        )

        return False


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
        "作業フォルダ:"
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
    # Web公開用データ同期
    # --------------------------------------------------------

    if output_ok:

        web_data_ok = sync_web_data()

    else:

        web_data_ok = False

    # --------------------------------------------------------
    # GitHub自動更新
    # --------------------------------------------------------

    if web_data_ok:

        git_ok = git_sync_web_data()

    else:

        git_ok = False

    # --------------------------------------------------------
    # 完了
    # --------------------------------------------------------

    end_time = datetime.now()

    elapsed = end_time - start_time

    print()
    print("=" * 70)

    if output_ok and web_data_ok and git_ok:

        print(
            "🎉 日次更新完了"
        )

        print(
            "   GitHubへの公開データ更新も完了しました。"
        )

    else:

        print(
            "⚠️ 日次更新は完了しましたが、"
        )

        print(
            "   一部の処理または出力ファイルを"
            "確認できませんでした。"
        )

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

    if output_ok and web_data_ok and git_ok:

        print(
            "Webサイト用データの更新が完了しました。"
        )

        print(
            "GitHubへのpushも完了しました。"
        )

        return 0

    return 1


# ============================================================
# 実行
# ============================================================

if __name__ == "__main__":
    sys.exit(main())
