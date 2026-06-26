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
    # ポイントセクション全体を抽出
    match = re.search(
        r'(## ポイント\n+)((?:.*?\n)*?)(?=## |\Z)',
        content,
        re.DOTALL
    )

    if not match:
        return content

    points_section = match.group(2)

    # ポイント1-7と重要なポイント部分を抽出
    # 最初のポイント1-7のブロックを検出
    first_points_match = re.search(
        r'^((?:^[\d]+\.\s.+$\n?)*)',
        points_section,
        re.MULTILINE
    )

    if not first_points_match:
        return content

    # 最初の7個のポイントだけを抽出
    first_points_text = first_points_match.group(1)
    lines = first_points_text.strip().split('\n')

    # "7. [ポイント7]..." まで集める
    cleaned_lines = []
    point_count = 0

    for line in lines:
        cleaned_lines.append(line)
        if re.match(r'^[\d]+\.\s', line):
            point_count += 1
            if point_count >= 7:
                break

    # 整形：最後の説明まで含める
    if cleaned_lines and not cleaned_lines[-1].startswith('-'):
        # 次の行があれば説明を追加
        idx = lines.index(cleaned_lines[-1])
        if idx + 1 < len(lines) and not lines[idx + 1].startswith(('7.', '8.', '-', '>', '**')):
            cleaned_lines.append(lines[idx + 1])

    # 重要なポイント部分を追加
    important_match = re.search(
        r'(- \*\*重要なポイント.+?\n)',
        points_section,
        re.DOTALL
    )

    cleaned_points = '\n'.join(cleaned_lines)
    if important_match:
        # 重要なポイント3行を抽出
        important_lines = []
        for line in points_section.split('\n'):
            if '重要なポイント' in line or (important_lines and line.startswith('-')):
                important_lines.append(line)
                if len(important_lines) >= 3:
                    break

        cleaned_points += '\n\n' + '\n'.join(important_lines)

    # 最後の引用を追加
    quote_match = re.search(r'(> 学習効果を高めるために.*)', points_section, re.DOTALL)
    if quote_match:
        cleaned_points += '\n\n' + quote_match.group(1)

    # ポイントセクション全体を置き換え
    new_content = re.sub(
        r'(## ポイント\n+)(?:.*?)(?=##)',
        rf'\1{cleaned_points}\n\n##',
        content,
        count=1,
        flags=re.DOTALL
    )

    return new_content

def main():
    print("T2Sセミナー ポイント重複クリーンアップ")
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
