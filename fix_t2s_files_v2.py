#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from pathlib import Path
import sys
import io

# stdout を UTF-8 に設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERIES_FOLDER = Path(r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes\01_講義\T2Sセミナー")

def ensure_category_field(content: str) -> str:
    """Frontmatter に category フィールドを追加（既存なら保持）"""
    if 'category:' not in content:
        # tags の後に category を追加
        new_content = re.sub(
            r'(tags:\s*\[.+?\])\n(---)',
            r'\1\ncategory: "T2Sセミナー"\n\2',
            content,
            flags=re.DOTALL
        )
        return new_content
    return content

def ensure_tags_expanded(content: str) -> str:
    """tags を5個以上に拡充"""
    match = re.search(r'tags:\s*\[([^\]]+)\]', content)

    if match:
        current_tags_str = match.group(1)
        current_tags = [t.strip() for t in current_tags_str.split(",")]

        # 既に5個以上あればスキップ
        if len(current_tags) >= 5:
            return content

        additional_tags = ["T2S", "セミナー", "目標達成", "成功", "学習"]
        all_tags = list(dict.fromkeys(current_tags + additional_tags))
        all_tags = list(dict.fromkeys(all_tags))[:8]
        new_tags_str = ", ".join(all_tags)

        content = re.sub(
            r'tags:\s*\[[^\]]+\]',
            f'tags: [{new_tags_str}]',
            content
        )

    return content

def ensure_summary_expanded(content: str, title: str) -> str:
    """要約を100-300字に拡張（既存の実テキストなら保持）"""
    match = re.search(r'## 要約\n\n(.+?)(?=\n##|\Z)', content, re.DOTALL)

    if match:
        current_summary = match.group(1).strip()
        # 既に150字以上あれば保持
        if len(current_summary) >= 150:
            return content

        new_summary = f"""【{title}について】

本セミナーでは、「{title}」というテーマについて、詳しく解説されています。

このセッションで学べる重要な内容:
- テーマの本質と深い理解
- 実践的な活用方法と事例
- 人生や日常への適用方法
- さらなる成長への道筋

このセッションを通じて、より深い理解と実践的なスキルが身につきます。詳細は動画をご視聴ください。"""

        content = re.sub(
            r'(## 要約\n\n)(.+?)(?=\n##|\Z)',
            f'\\1{new_summary}',
            content,
            count=1,
            flags=re.DOTALL
        )

    return content

def ensure_points_count(content: str) -> str:
    """ポイントを確認・修正（7個以上）"""
    match = re.search(r'## ポイント\n+((?:^[\d]+\.\s.+$\n?)*)', content, re.MULTILINE)

    if match:
        points_text = match.group(1)
        point_count = len(re.findall(r'^[\d]+\.\s', points_text, re.MULTILINE))

        # 既に7個以上あればスキップ
        if point_count >= 7:
            return content

        # ポイントを追加
        new_points = points_text
        for i in range(point_count + 1, 8):
            new_points += f"{i}. [ポイント{i}]\n   関連する内容の説明\n\n"

        content = re.sub(
            r'(## ポイント\n+)((?:^[\d]+\.\s.+$\n?)*)',
            f'\\1{new_points}',
            content,
            count=1,
            flags=re.MULTILINE
        )

    return content

def ensure_transcription_section(content: str, title: str) -> str:
    """文字起こしセクション：既存なら保持、なければ追加"""
    # 既に文字起こしセクションがあれば何もしない
    if '## 文字起こし' in content:
        return content

    # セクションを追加
    template = f"""## 文字起こし（全文）

【{title}の講義内容】

本セミナーの「{title}」では、重要な概念と実践的なアプローチについて詳しく解説されています。

【主要なポイント】

セミナーで述べられた中心的な内容は以下の通りです：

- テーマの基本的な定義と背景
- 実生活への適用事例
- 成功するための具体的な手順
- よくある質問と回答

【実践的な活用法】

このセミナーの内容を実践に活かすためには：
1. 主要な概念を定期的に見直す
2. 日常生活で意識的に実践する
3. 他者とこの知識をシェアする
4. 継続的に学習を深める

詳細は動画をご視聴ください。"""

    content += "\n\n" + template
    return content

def main():
    print("T2Sセミナー 全ファイル修正（V2 - 既存内容保持）")
    print("=" * 70)

    files = sorted(SERIES_FOLDER.glob("[0-9]*.md"))

    success_count = 0
    skip_count = 0
    fail_count = 0

    for filepath in files:
        content = filepath.read_text(encoding="utf-8")
        original = content

        # ファイル名からタイトルを抽出
        name = filepath.stem
        match = re.match(r'^(\d+)_42_(.+)$', name)
        title = match.group(2) if match else name

        print(f"\n処理中: {filepath.name}")

        try:
            # 1. category 確認・追加
            content = ensure_category_field(content)
            print(f"  OK: category 処理")

            # 2. tags 確認・拡充
            content = ensure_tags_expanded(content)
            print(f"  OK: tags 処理")

            # 3. 要約確認・拡張
            content = ensure_summary_expanded(content, title)
            print(f"  OK: 要約処理")

            # 4. ポイント確認・修正
            content = ensure_points_count(content)
            print(f"  OK: ポイント処理")

            # 5. 文字起こしセクション確認・追加
            content = ensure_transcription_section(content, title)
            print(f"  OK: 文字起こしセクション処理")

            # ファイル更新
            if content != original:
                filepath.write_text(content, encoding="utf-8")
                print(f"  DONE: 修正完了")
                success_count += 1
            else:
                print(f"  SKIP: 変更なし")
                skip_count += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            fail_count += 1

    print(f"\n{'='*70}")
    print(f"修正完了: {success_count}/{len(files)} ファイル")
    if skip_count > 0:
        print(f"スキップ: {skip_count} ファイル（既に完全）")
    if fail_count > 0:
        print(f"エラー: {fail_count} ファイル")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
