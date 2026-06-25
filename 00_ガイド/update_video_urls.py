#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
【10の能力動画】URL 確認・更新ツール

このスクリプトは、awareness.co.jp 内の3つの動画の完全な URL を取得し、
対応する Markdown ファイルの source_url フィールドを自動更新します。

使用方法:
    python update_video_urls.py

前提条件:
    - Python 3.7 以上
    - 対象ファイルが 01_講義/10の能力動画/ ディレクトリに存在すること
"""

import re
import os
import sys
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse


class VideoURLUpdater:
    """動画 URL 更新クラス"""

    def __init__(self):
        """初期化"""
        self.base_dir = Path(__file__).parent.parent / "01_講義" / "10の能力動画"
        self.videos = {
            "無限大の原則": {
                "file": "【10の能力動画】無限大の原則.md",
                "pattern": r"(source_url:\s+\")https://www\.awareness\.co\.jp/mypage/archives/study-watch/348/[^\"]+(\"\n)"
            },
            "繰の原則": {
                "file": "【10の能力動画】繰の原則.md",
                "pattern": r"(source_url:\s+\")https://www\.awareness\.co\.jp/mypage/archives/study-watch/348/[^\"]+(\"\n)"
            },
            "潜在意識の原則": {
                "file": "【10の能力動画】潜在意識の原則.md",
                "pattern": r"(source_url:\s+\")([^\"]+)(\"\n)"
            }
        }
        self.updates = {}
        self.errors = []

    def validate_url(self, url: str) -> tuple[bool, str]:
        """
        URL の妥当性をチェック

        Args:
            url: チェック対象の URL

        Returns:
            (is_valid, error_message) のタプル
        """
        url = url.strip()

        # 空文字列チェック
        if not url:
            return False, "URL が空です"

        # HTTPS チェック
        if not url.startswith("https://") and not url.startswith("http://"):
            return False, "URL は https:// または http:// で始まる必要があります"

        # awareness.co.jp チェック
        if "awareness.co.jp" not in url:
            return False, "URL が awareness.co.jp ドメインを含んでいません"

        # /348/ を含むチェック
        if "/348/" not in url:
            return False, "URL が正しい形式ではありません（/348/を含む必要があります）"

        # プレースホルダーチェック
        if "XXX" in url or "XXXX" in url or "[" in url:
            return False, "URL にプレースホルダー（XXX、XXXX など）が含まれています"

        # URL オブジェクトの作成
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return False, "URL が無効な形式です"
        except Exception as e:
            return False, f"URL パース エラー: {str(e)}"

        return True, ""

    def prompt_for_url(self, video_name: str, current_url: str = None) -> str:
        """
        ユーザーに URL の入力を求める

        Args:
            video_name: 動画名
            current_url: 現在の URL（表示用）

        Returns:
            入力された URL
        """
        print(f"\n【{video_name}】")
        if current_url:
            print(f"現在の URL: {current_url}")

        while True:
            url = input("新しい URL を入力（またはスキップは 's' を入力）> ").strip()

            # スキップ処理
            if url.lower() == 's':
                print("⊘ スキップしました")
                return None

            # URL 検証
            is_valid, error_msg = self.validate_url(url)
            if not is_valid:
                print(f"✗ エラー: {error_msg}")
                print(f"  例: https://www.awareness.co.jp/mypage/archives/study-watch/348/376/2024/")
                continue

            # 確認
            print(f"✓ URL が有効です: {url}")
            confirm = input("この URL で更新しますか？ (y/n) > ").strip().lower()
            if confirm == 'y':
                return url

    def read_file(self, file_path: Path) -> str:
        """ファイルを読み込む"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.errors.append(f"ファイル読み込み エラー ({file_path}): {str(e)}")
            return None

    def extract_current_url(self, content: str) -> str:
        """ファイルから現在の URL を抽出"""
        match = re.search(r'source_url:\s+"([^"]+)"', content)
        if match:
            return match.group(1)
        return None

    def update_file(self, file_path: Path, new_url: str, video_name: str) -> bool:
        """
        ファイルの URL を更新

        Args:
            file_path: 更新対象ファイル
            new_url: 新しい URL
            video_name: 動画名

        Returns:
            成功時は True、失敗時は False
        """
        try:
            # ファイルを読み込む
            content = self.read_file(file_path)
            if content is None:
                return False

            # バックアップを作成
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            try:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  → バックアップを作成しました: {backup_path.name}")
            except Exception as e:
                print(f"  ⚠ バックアップ作成に失敗しました: {str(e)}")

            # URL を更新
            # source_url フィールドの URL 部分を置き換え
            pattern = r'source_url:\s+"[^"]*"'
            new_content = re.sub(
                pattern,
                f'source_url: "{new_url}"',
                content
            )

            # 内容が変わらなかった場合のエラーチェック
            if new_content == content:
                self.errors.append(
                    f"ファイル更新に失敗しました ({file_path.name}): "
                    "source_url フィールドが見つかりません"
                )
                return False

            # ファイルに書き込む
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f"  ✓ ファイルが更新されました: {file_path.name}")
            self.updates[video_name] = {
                "file": file_path.name,
                "url": new_url,
                "timestamp": datetime.now().isoformat()
            }
            return True

        except Exception as e:
            self.errors.append(f"ファイル更新に失敗しました ({file_path.name}): {str(e)}")
            return False

    def show_header(self):
        """ヘッダーを表示"""
        print("\n" + "="*50)
        print("【10の能力動画】URL 確認・更新ツール")
        print("="*50)
        print("\nこのツールは、awareness.co.jp 内の3つの動画の")
        print("完全な URL を取得し、Markdown ファイルを自動更新します。")
        print("\n各ステップ:")
        print("1. awareness.co.jp で各動画ページにアクセス")
        print("2. ブラウザのアドレスバーから URL をコピー")
        print("3. 以下で URL を貼り付けて Enter キー")
        print("\n※ スキップしたい場合は 's' を入力してください\n")

    def show_current_status(self):
        """現在のファイル状況を表示"""
        print("【現在のファイル状況】\n")

        for video_name, video_info in self.videos.items():
            file_path = self.base_dir / video_info["file"]

            if not file_path.exists():
                print(f"✗ {video_name}")
                print(f"  ファイルが見つかりません: {file_path}\n")
                continue

            content = self.read_file(file_path)
            if content is None:
                print(f"✗ {video_name}")
                print(f"  ファイルの読み込みに失敗しました\n")
                continue

            current_url = self.extract_current_url(content)
            if current_url:
                # URL の完全性を判定
                if "XXX" in current_url or "XXXX" in current_url:
                    status = "⚠ 不完全"
                elif current_url == "Unable to extract - authentication required":
                    status = "✗ 未取得"
                else:
                    status = "✓ 完全"

                print(f"{status} {video_name}")
                print(f"  現在: {current_url}\n")
            else:
                print(f"? {video_name}")
                print(f"  source_url フィールドが見つかりません\n")

    def run(self):
        """メインの実行処理"""
        self.show_header()

        # 現在の状況を表示
        self.show_current_status()

        # URL の入力を促す
        print("\n" + "="*50)
        print("【URL 入力フェーズ】")
        print("="*50)

        for i, (video_name, video_info) in enumerate(self.videos.items(), 1):
            file_path = self.base_dir / video_info["file"]

            if not file_path.exists():
                print(f"\n✗ [{i}/3] {video_name}")
                print(f"  ファイルが見つかりません\n")
                self.errors.append(f"ファイルが見つかりません: {file_path}")
                continue

            # 現在の URL を取得
            content = self.read_file(file_path)
            current_url = self.extract_current_url(content) if content else None

            print(f"\n[{i}/3]", end=" ")
            new_url = self.prompt_for_url(video_name, current_url)

            # URL が入力された場合は更新
            if new_url:
                self.update_file(file_path, new_url, video_name)

        # 処理結果をサマリーで表示
        self.show_summary()

    def show_summary(self):
        """処理結果のサマリーを表示"""
        print("\n" + "="*50)
        print("【処理完了】")
        print("="*50)

        if self.updates:
            print("\n✓ 以下のファイルが更新されました:\n")
            for video_name, update_info in self.updates.items():
                print(f"  • {video_name}")
                print(f"    ファイル: {update_info['file']}")
                print(f"    URL: {update_info['url']}")
                print(f"    更新日時: {update_info['timestamp']}\n")
        else:
            print("\n⊘ 更新されたファイルはありません\n")

        if self.errors:
            print("\n⚠ エラーが発生しました:\n")
            for error in self.errors:
                print(f"  • {error}\n")

        print("="*50)
        print("\n処理が完了しました。")
        print("Markdown ファイルを開いて、URL が正しく更新されたか確認してください。\n")


def main():
    """メイン関数"""
    try:
        updater = VideoURLUpdater()
        updater.run()
    except KeyboardInterrupt:
        print("\n\n⊘ ユーザーにより中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 予期しないエラーが発生しました: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
