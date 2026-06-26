#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from pathlib import Path
import sys
import io

# stdout を UTF-8 に設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERIES_FOLDER = Path(r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes\01_講義\T2Sセミナー")

def cleanup_duplicate_points(content: str) -> str:
    """ポイント重複を削除"""
    # ポイントセクションを検出
    match = re.search(r'(## ポイント\n+)', content)
    if not match:
        return content

    # ポイントセクションの開始位置
    points_start = match.end()

    # 次のセクション（##）の位置を検出
    next_section_match = re.search(r'\n(## )', content[points_start:])
    if next_section_match:
        points_end = points_start + next_section_match.start()
    else:
        points_end = len(content)

    points_content = content[points_start:points_end]

    # ポイント1-7を検出（最初の出現のみ）
    point_lines = points_content.split('\n')
    cleaned_lines = []
    point_count = 0
    found_important = False

    for i, line in enumerate(point_lines):
        # ポイント番号の判定
        if re.match(r'^[\d]+\.\s', line):
            num = int(line.split('.')[0].strip())
            if num <= 7:
                cleaned_lines.append(line)
                point_count = max(point_count, num)
            # 8以上は追加しない（重複排除）
        # 重要なポイント以降は取得（ただし最初の重要なポイントのグループまで）
        elif '- **重要なポイント' in line:
            cleaned_lines.append(line)
            found_important = True
        elif found_important and line.startswith('- **'):
            cleaned_lines.append(line)
        elif found_important and line.startswith('>'):
            cleaned_lines.append(line)
        elif not found_important and line.strip() and not re.match(r'^[\d]+\.', line):
            # ポイント7の後の説明
            if point_count >= 7:
                cleaned_lines.append(line)
        elif found_important and '学習効果' in line:
            cleaned_lines.append(line)

    # 最後の空行を削除
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()

    new_points_section = '\n'.join(cleaned_lines)

    # 元のファイルを新しいポイントセクションで置き換え
    new_content = content[:points_start] + new_points_section + content[points_end:]

    return new_content

def main():
    print("T2Sセミナー ポイント重複クリーンアップ V2")
    print("=" * 70)

    files = sorted(SERIES_FOLDER.glob("[0-9]*.md"))

    success_count = 0
    skip_count = 0

    for filepath in files:
        content = filepath.read_text(encoding="utf-8")
        original = content

        print(f"\nクリーンアップ中: {filepath.name}")

        # ポイント重複削除
        content = cleanup_duplicate_points(content)

        # ファイル更新
        if content != original:
            filepath.write_text(content, encoding="utf-8")
            print(f"  DONE: クリーンアップ完了")
            success_count += 1
        else:
            print(f"  SKIP: 重複なし")
            skip_count += 1

    print(f"\n{'='*70}")
    print(f"クリーンアップ完了: {success_count}/{len(files)} ファイル")
    if skip_count > 0:
        print(f"スキップ: {skip_count} ファイル")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
