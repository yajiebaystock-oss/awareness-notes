#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys
import io

# stdout を UTF-8 に設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERIES_FOLDER = Path(r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes\01_講義\T2Sセミナー")

def remove_duplicate_points_batch(content: str) -> str:
    """
    ポイント7の後の重複ブロック（2-7）を削除
    パターン: ポイント7の説明 -> 重複の2-7 -> 重要なポイント
    """
    lines = content.split('\n')
    result = []
    i = 0
    skip_until_important = False

    while i < len(lines):
        line = lines[i]

        # ポイント7を見つけたら、次の重複ブロックをスキップ
        if line.startswith('7. [ポイント7]'):
            result.append(line)
            i += 1

            # ポイント7の説明行を追加
            while i < len(lines) and lines[i].startswith('   '):
                result.append(lines[i])
                i += 1

            # ここから重複ブロックの開始：次の"2. [ポイント2]"を検出
            if i < len(lines) and lines[i].startswith('2. [ポイント2]'):
                # 重複ブロック開始：2-7と説明を全部スキップ
                while i < len(lines):
                    if lines[i].startswith('- **重要なポイント'):
                        # 重要なポイントに到達したら抜ける
                        break
                    if lines[i].startswith('> 学習'):
                        # 引用に到達したら抜ける
                        break
                    i += 1

                # ここで重複ブロックのスキップ完了
                continue

        result.append(line)
        i += 1

    return '\n'.join(result)

def main():
    print("T2Sセミナー 全ファイル重複ポイント一括削除")
    print("=" * 70)

    files = sorted(SERIES_FOLDER.glob("[0-9]*.md"))

    success_count = 0
    skip_count = 0

    for filepath in files:
        content = filepath.read_text(encoding="utf-8")
        original = content

        print(f"\n処理中: {filepath.name}")

        # 重複削除
        content = remove_duplicate_points_batch(content)

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
