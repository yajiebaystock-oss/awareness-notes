#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
セットアップ検証スクリプト

このスクリプトは、URL 更新ツールを使用する前に、
環境が正しく設定されているかを確認します。

使用方法:
    python verify_setup.py
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Python バージョンをチェック"""
    print("\n[1] Python バージョン確認")
    print("=" * 50)

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    print(f"✓ Python バージョン: {version_str}")

    if version.major >= 3 and version.minor >= 7:
        print("✓ 必要なバージョン（3.7以上）を満たしています")
        return True
    else:
        print("✗ Python 3.7 以上が必要です")
        return False


def check_required_files():
    """必要なファイルをチェック"""
    print("\n[2] 必要なファイル確認")
    print("=" * 50)

    base_dir = Path(__file__).parent.parent / "01_講義" / "10の能力動画"

    required_files = [
        "【10の能力動画】無限大の原則.md",
        "【10の能力動画】繰の原則.md",
        "【10の能力動画】潜在意識の原則.md",
    ]

    all_exist = True
    for file_name in required_files:
        file_path = base_dir / file_name
        if file_path.exists():
            print(f"✓ {file_name}")
        else:
            print(f"✗ {file_name} が見つかりません")
            print(f"  期待される場所: {file_path}")
            all_exist = False

    return all_exist


def check_python_modules():
    """必要な Python モジュールをチェック"""
    print("\n[3] Python モジュール確認")
    print("=" * 50)

    required_modules = [
        ("re", "正規表現モジュール"),
        ("os", "OS インターフェース"),
        ("pathlib", "パス処理モジュール"),
        ("datetime", "日時モジュール"),
        ("urllib.parse", "URL パース モジュール"),
    ]

    all_available = True
    for module_name, description in required_modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name:20} - {description}")
        except ImportError:
            print(f"✗ {module_name:20} - {description} (見つかりません)")
            all_available = False

    return all_available


def check_file_permissions():
    """ファイル書き込み権限をチェック"""
    print("\n[4] ファイル書き込み権限確認")
    print("=" * 50)

    base_dir = Path(__file__).parent.parent / "01_講義" / "10の能力動画"

    if not base_dir.exists():
        print("✗ ディレクトリが見つかりません")
        return False

    # テストファイルを作成して権限をチェック
    test_file = base_dir / ".write_test"
    try:
        test_file.write_text("test")
        test_file.unlink()
        print(f"✓ ディレクトリに書き込み権限があります")
        print(f"  パス: {base_dir}")
        return True
    except PermissionError:
        print(f"✗ ディレクトリに書き込み権限がありません")
        print(f"  パス: {base_dir}")
        print("  → フォルダを右クリック → プロパティ → セキュリティから確認してください")
        return False
    except Exception as e:
        print(f"⚠ 権限チェック中にエラーが発生しました: {str(e)}")
        return False


def check_guide_files():
    """ガイドファイルをチェック"""
    print("\n[5] ガイド・スクリプトファイル確認")
    print("=" * 50)

    script_dir = Path(__file__).parent

    required_scripts = [
        ("update_video_urls.py", "URL 更新スクリプト"),
        ("batch_check_urls.py", "URL 確認スクリプト"),
        ("URL確認ガイド_10の能力動画.md", "詳細ガイド"),
        ("クイックレファレンス_URL確認.md", "クイックリファレンス"),
        ("ビジュアルガイド_URL取得フロー.txt", "ビジュアルガイド"),
        ("README_URL取得手順.md", "スタートガイド"),
    ]

    all_exist = True
    for file_name, description in required_scripts:
        file_path = script_dir / file_name
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✓ {file_name:40} - {description} ({size} bytes)")
        else:
            print(f"✗ {file_name:40} - {description} (見つかりません)")
            all_exist = False

    return all_exist


def check_url_format():
    """URL フォーマット検証テスト"""
    print("\n[6] URL フォーマット検証テスト")
    print("=" * 50)

    test_urls = [
        {
            "url": "https://www.awareness.co.jp/mypage/archives/study-watch/348/375/2024/",
            "expected": True,
            "name": "完全な URL（無限大の原則）"
        },
        {
            "url": "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/XXXX",
            "expected": False,
            "name": "不完全な URL（プレースホルダー含む）"
        },
        {
            "url": "https://www.awareness.co.jp/mypage/archives/study-watch/348/",
            "expected": False,
            "name": "不完全な URL（末尾が不足）"
        },
        {
            "url": "http://example.com",
            "expected": False,
            "name": "別ドメインの URL"
        },
    ]

    all_pass = True
    for test_case in test_urls:
        url = test_case["url"]
        expected = test_case["expected"]
        name = test_case["name"]

        # 簡易的な検証
        is_valid = (
            url.startswith("https://") and
            "awareness.co.jp" in url and
            "/348/" in url and
            "XXX" not in url and
            "XXXX" not in url
        )

        if is_valid == expected:
            result = "✓"
        else:
            result = "✗"
            all_pass = False

        print(f"{result} {name}")
        print(f"  URL: {url}")
        print()

    return all_pass


def show_summary(results):
    """チェック結果のサマリーを表示"""
    print("\n" + "=" * 50)
    print("【セットアップ検証結果】")
    print("=" * 50)

    checks = [
        ("Python バージョン", results[0]),
        ("必要なファイル", results[1]),
        ("Python モジュール", results[2]),
        ("ファイル書き込み権限", results[3]),
        ("ガイド・スクリプトファイル", results[4]),
        ("URL フォーマット検証", results[5]),
    ]

    passed = sum(1 for _, result in checks if result)
    total = len(checks)

    print()
    for check_name, result in checks:
        status = "✓ OK" if result else "✗ NG"
        print(f"{status:6} {check_name}")

    print()
    print(f"結果: {passed}/{total} チェック成功")
    print()

    if all(results):
        print("✅ セットアップ完了！")
        print()
        print("次のステップ:")
        print("  1. ビジュアルガイド_URL取得フロー.txt を読む")
        print("  2. awareness.co.jp で URL を取得")
        print("  3. python update_video_urls.py を実行")
        print()
        return True
    else:
        print("⚠️  いくつか問題が見つかりました。上記を確認してください。")
        print()
        if not results[0]:
            print("  → Python 3.7 以上をインストール: https://www.python.org/downloads/")
        if not results[1]:
            print("  → 対象ファイルを確認: 01_講義/10の能力動画/")
        if not results[3]:
            print("  → フォルダの権限を確認（右クリック → プロパティ）")
        print()
        return False


def main():
    """メイン関数"""
    print("\n" + "=" * 50)
    print("【10の能力動画】セットアップ検証")
    print("=" * 50)

    results = [
        check_python_version(),
        check_required_files(),
        check_python_modules(),
        check_file_permissions(),
        check_guide_files(),
        check_url_format(),
    ]

    success = show_summary(results)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⊘ ユーザーにより中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 予期しないエラーが発生しました: {str(e)}")
        sys.exit(1)
