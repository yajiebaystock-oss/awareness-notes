#!/usr/bin/env python3
"""
スキマニT2S全18ファイルの修正内容を検証
"""

import re
from pathlib import Path

VAULT_PATH = Path(r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes")
SERIES_FOLDER = VAULT_PATH / "01_講義" / "スキマニT2S"

def verify_file(filepath):
    """ファイルの修正内容を検証"""
    content = filepath.read_text(encoding='utf-8')

    # 1. category チェック
    has_category = '"スキマニT2S"' in content

    # 2. tags チェック
    tags_match = re.search(r'tags: \[([^\]]+)\]', content)
    tag_count = len(tags_match.group(1).split(',')) if tags_match else 0

    # 3. 要約文字数
    summary_match = re.search(r'## 要約\n\n(.+?)\n\n##', content, re.DOTALL)
    summary_chars = len(summary_match.group(1)) if summary_match else 0

    # 4. ポイント数
    points_match = re.search(r'## ポイント\n\n(.*?)(?=\n##)', content, re.DOTALL)
    point_count = len(re.findall(r'^[\d]+\.', points_match.group(1), re.MULTILINE)) if points_match else 0

    # 5. 文字起こし文字数
    trans_match = re.search(r'## 文字起こし（全文）\n\n(.+?)$', content, re.DOTALL)
    trans_chars = len(trans_match.group(1)) if trans_match else 0

    return {
        'category_ok': has_category,
        'tag_count': tag_count,
        'summary_chars': summary_chars,
        'point_count': point_count,
        'trans_chars': trans_chars
    }

def main():
    print("""
========================================================
   スキマニT2S全18ファイル 修正内容検証
========================================================
""")

    files = sorted(SERIES_FOLDER.glob("【スキマニT2S】*.md"))

    print(f"{'No.':<4} {'Category':<8} {'Tags':<6} {'Summary':<10} {'Points':<7} {'Trans':<7}")
    print("-" * 70)

    category_ok_count = 0
    tags_ok_count = 0
    summary_ok_count = 0
    points_ok_count = 0
    trans_ok_count = 0

    for idx, filepath in enumerate(files, start=1):
        result = verify_file(filepath)

        # チェック
        cat_ok = "OK" if result['category_ok'] else "NG"
        tag_ok = "OK" if result['tag_count'] >= 5 else f"NG({result['tag_count']})"
        sum_ok = "OK" if result['summary_chars'] >= 100 else f"NG({result['summary_chars']})"
        pt_ok = "OK" if result['point_count'] >= 7 else f"NG({result['point_count']})"

        # 文字起こしは#8と#18で300字以上
        if idx == 8 or idx == 18:
            trans_ok = "OK" if result['trans_chars'] >= 300 else f"NG({result['trans_chars']})"
        else:
            trans_ok = "OK" if result['trans_chars'] >= 100 else f"OK({result['trans_chars']})"

        print(f"{idx:<4} {cat_ok:<8} {tag_ok:<6} {sum_ok:<10} {pt_ok:<7} {trans_ok:<7}")

        if result['category_ok']:
            category_ok_count += 1
        if result['tag_count'] >= 5:
            tags_ok_count += 1
        if result['summary_chars'] >= 100:
            summary_ok_count += 1
        if result['point_count'] >= 7:
            points_ok_count += 1

        if idx == 8 or idx == 18:
            if result['trans_chars'] >= 300:
                trans_ok_count += 1
        else:
            if result['trans_chars'] >= 100:
                trans_ok_count += 1

    print()
    print(f"{'='*70}")
    print(f"Category: {category_ok_count}/18")
    print(f"Tags (5+): {tags_ok_count}/18")
    print(f"Summary (100+): {summary_ok_count}/18")
    print(f"Points (7+): {points_ok_count}/18")
    print(f"Trans (#8,#18 300+): {trans_ok_count}/18")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
