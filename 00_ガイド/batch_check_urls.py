#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
【10の能力動画】URL 一括確認ツール

このスクリプトは、awareness.co.jp 内の3つの動画ファイルの URL 状態を
一括で確認し、不完全な URL や問題を検出します。

使用方法:
    python batch_check_urls.py

出力:
    - 各ファイルの URL 状態（完全/不完全/未取得）
    - URL の詳細情報
    - 問題点と推奨アクション
"""

import re
from pathlib import Path
from tabulate import tabulate if __import__('sys').modules.get('tabulate') else None


class URLChecker:
    """URL 一括確認クラス"""

    def __init__(self):
        """初期化"""
        self.base_dir = Path(__file__).parent.parent / "01_講義" / "10の能力動画"
        self.videos = [
            {
                "name": "無限大の原則",
                "file": "【10の能力動画】無限大の原則.md",
                "expected_id": "375"  # 例
            },
            {
                "name": "繰の原則",
                "file": "【10の能力動画】繰の原則.md",
                "expected_id": "376"
            },
            {
                "name": "潜在意識の原則",
                "file": "【10の能力動画】潜在意識の原則.md",
                "expected_id": "377"  # 例
            }
        ]
        self.results = []

    def read_file(self, file_path: Path) -> str:
        """ファイルを読み込む"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"ERROR: {str(e)}"

    def extract_url(self, content: str) -> str:
        """ファイルから URL を抽出"""
        match = re.search(r'source_url:\s+"([^"]+)"', content)
        if match:
            return match.group(1)
        return None

    def check_url_completeness(self, url: str) -> dict:
        """
        URL の完全性をチェック

        Args:
            url: チェック対象の URL

        Returns:
            {
                "status": "完全" | "不完全" | "未取得" | "エラー",
                "icon": "✓" | "⚠" | "✗" | "?",
                "issues": []
            }
        """
        issues = []
        status = "完全"
        icon = "✓"

        if not url:
            return {"status": "エラー", "icon": "?", "issues": ["URL が取得できませんでした"]}

        # 未取得パターン
        if url == "Unable to extract - authentication required":
            return {
                "status": "未取得",
                "icon": "✗",
                "issues": ["認証が必要で URL が取得できません"]
            }

        # プレースホルダーチェック
        if "XXX" in url or "XXXX" in url:
            issues.append("URL に プレースホルダー（XXX/XXXX）が含まれています")
            status = "不完全"
            icon = "⚠"

        # awareness.co.jp チェック
        if "awareness.co.jp" not in url:
            issues.append("awareness.co.jp ドメインが含まれていません")
            status = "不完全"
            icon = "⚠"

        # /348/ チェック
        if "/348/" not in url:
            issues.append("/348/ が含まれていません")
            status = "不完全"
            icon = "⚠"

        # HTTPS チェック
        if not url.startswith("https://"):
            issues.append("HTTPS で始まっていません")
            status = "不完全"
            icon = "⚠"

        # 最後が [数字]/ パターンかチェック
        if not re.search(r'/\d+/?$', url):
            issues.append("URL の最後に数字が見当たりません")
            status = "不完全"
            icon = "⚠"

        return {
            "status": status,
            "icon": icon,
            "issues": issues
        }

    def run(self):
        """メイン実行処理"""
        self.show_header()

        print("\n【URL 確認結果】\n")

        for video in self.videos:
            file_path = self.base_dir / video["file"]

            # ファイルの存在チェック
            if not file_path.exists():
                print(f"✗ {video['name']}")
                print(f"  ファイルが見つかりません: {file_path}\n")
                self.results.append({
                    "動画": video['name'],
                    "状態": "✗ ファイルなし",
                    "URL": "N/A",
                    "問題": "ファイルが見つかりません"
                })
                continue

            # ファイルを読み込み
            content = self.read_file(file_path)
            if content.startswith("ERROR:"):
                print(f"✗ {video['name']}")
                print(f"  ファイル読み込みエラー: {content}\n")
                self.results.append({
                    "動画": video['name'],
                    "状態": "✗ エラー",
                    "URL": "N/A",
                    "問題": content
                })
                continue

            # URL を抽出
            url = self.extract_url(content)
            check_result = self.check_url_completeness(url)

            # 結果を表示
            print(f"{check_result['icon']} {video['name']}")
            print(f"  状態: {check_result['status']}")
            print(f"  URL: {url if url else '(取得不可)'}")

            if check_result['issues']:
                print(f"  問題:")
                for issue in check_result['issues']:
                    print(f"    • {issue}")

            # 推奨アクション
            if check_result['status'] != "完全":
                print(f"  推奨アクション:")
                if "プレースホルダー" in str(check_result['issues']):
                    print(f"    → update_video_urls.py を実行して URL を更新してください")
                if "認証が必要" in str(check_result['issues']):
                    print(f"    → awareness.co.jp にログインして URL を取得してください")

            print()

            self.results.append({
                "動画": video['name'],
                "状態": f"{check_result['icon']} {check_result['status']}",
                "URL": url if url else "未取得",
                "問題": " | ".join(check_result['issues']) if check_result['issues'] else "なし"
            })

        # サマリーを表示
        self.show_summary()

    def show_header(self):
        """ヘッダーを表示"""
        print("\n" + "="*70)
        print("【10の能力動画】URL 一括確認ツール")
        print("="*70)

    def show_summary(self):
        """サマリーを表示"""
        print("\n" + "="*70)
        print("【サマリー】")
        print("="*70 + "\n")

        # 統計
        total = len(self.results)
        complete = sum(1 for r in self.results if "✓" in r["状態"])
        incomplete = sum(1 for r in self.results if "⚠" in r["状態"])
        errors = sum(1 for r in self.results if "✗" in r["状態"])

        print(f"確認済みファイル: {total}個")
        print(f"  ✓ 完全: {complete}個")
        print(f"  ⚠ 不完全: {incomplete}個")
        print(f"  ✗ エラー/未取得: {errors}個\n")

        # 詳細テーブル
        print("詳細:")
        print()
        for result in self.results:
            print(f"  {result['動画']}")
            print(f"    状態: {result['状態']}")
            print(f"    URL: {result['URL'][:60]}..." if len(result['URL']) > 60 else f"    URL: {result['URL']}")
            if result['問題'] != "なし":
                print(f"    問題: {result['問題']}")
            print()

        # 推奨アクション
        if incomplete > 0 or errors > 0:
            print("【推奨アクション】\n")
            if incomplete > 0:
                print("  • URL が不完全なファイルを更新:")
                print("    $ python update_video_urls.py")
                print()
            if errors > 0:
                print("  • エラーが発生したファイルを確認:")
                print("    - awareness.co.jp へのログインを確認")
                print("    - ファイルの権限を確認")
                print()

        print("="*70 + "\n")


def main():
    """メイン関数"""
    try:
        checker = URLChecker()
        checker.run()
    except KeyboardInterrupt:
        print("\n\n⊘ ユーザーにより中断されました")
    except Exception as e:
        print(f"\n✗ 予期しないエラーが発生しました: {str(e)}")


if __name__ == "__main__":
    main()
