#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys
import io
import re

# stdout を UTF-8 に設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERIES_FOLDER = Path(r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes\01_講義\T2Sセミナー")

def remove_duplicate_points(content: str) -> str:
    """ポイント2-7の重複をシンプルに削除"""
    # パターン: "7. [ポイント7]" から始まる重複ブロック内の2-7を削除
    # 重複のパターン: "7. [ポイント7]..." の後に改行、説明、その後 "2. [ポイント2]"

    # ポイント7の後の重複セクションを削除
    pattern = r'(7\. \[ポイント7\][^\n]*\n   関連する内容の説明\n   関連する内容の説明)\n2\. \[ポイント2\].*?(?=\n- \*\*重要なポイント)'

    matches = re.finditer(pattern, content, re.DOTALL)
    if not matches:
        # マッチしない場合は別パターンを試す
        pattern2 = r'(7\. \[ポイント7\][^\n]*\n[^\n]*)\n\n2\. \[ポイント2\].*?(?=\n- )'
        content = re.sub(pattern2, r'\1\n\n-', content, flags=re.DOTALL)
        return content

    # マッチした場合は削除
    content = re.sub(pattern, r'\1\n\n- ', content, flags=re.DOTALL)
    return content

def main():
    print("T2Sセミナー 重複ポイント簡易削除")
    print("=" * 70)

    files = sorted(SERIES_FOLDER.glob("[0-9]*.md"))

    success_count = 0
    skip_count = 0

    for filepath in files:
        content = filepath.read_text(encoding="utf-8")
        original = content

        print(f"\n処理中: {filepath.name}")

        # 重複削除
        content = remove_duplicate_points(content)

        # ファイル更新
        if content != original:
            filepath.write_text(content, encoding="utf-8")
            print(f"  DONE: 重複削除完了")
            success_count += 1
        else:
            print(f"  SKIP: 重複なし")
            skip_count += 1

    print(f"\n{'='*70}")
    print(f"処理完了: {success_count}/{len(files)} ファイル")
    if skip_count > 0:
        print(f"スキップ: {skip_count} ファイル")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
