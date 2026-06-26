#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import sys
from pathlib import Path

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

VAULT_PATH = Path(r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes")
ABILITY_FOLDER = VAULT_PATH / "01_講義" / "10の能力動画"

# 修正対象
files_to_fix = {
    "【10の能力動画】原因と結果の原則.md": {
        "fix_points": True,
        "fix_tags": True,
        "add_tags": ["因果関係", "行動", "結果"]
    },
    "【10の能力動画】表裏一体の原則.md": {
        "fix_points": True,
        "fix_tags": True,
        "add_tags": ["二律背反", "相互関係", "バランス"]
    },
    "【10の能力動画】道徳（決断）の原則.md": {
        "fix_points": True,
        "fix_tags": True,
        "add_tags": ["倫理", "判断基準", "責任"]
    },
    "【10の能力動画】思考の原則.md": {
        "fix_points": False,
        "fix_tags": True,
        "add_tags": ["思考法", "思考パターン", "脳科学"]
    },
    "【10の能力動画】成長と変化の原則.md": {
        "fix_points": False,
        "fix_tags": True,
        "add_tags": ["自己啓発", "進化", "変革"]
    },
    "【10の能力動画】潜在意識の原則.md": {
        "fix_points": False,
        "fix_tags": True,
        "add_tags": ["潜在意識", "心理学"]
    }
}

def fix_points_format(content: str) -> str:
    """ポイントの「-」形式を「1.」形式に統一"""
    # ## ポイント 以降の全ての行をスキャン
    lines = content.split("\n")
    output_lines = []
    in_points_section = False
    point_num = 1

    for line in lines:
        if line.strip() == "## ポイント":
            in_points_section = True
            point_num = 1
            output_lines.append(line)
        elif in_points_section:
            # ポイントセクション終了判定（次のセクション開始）
            if line.startswith("##") or (line.startswith(">") and line.strip() != ">"):
                in_points_section = False
                output_lines.append(line)
            # 「-」で始まるポイントを「1.」形式に変更
            elif line.strip().startswith("- "):
                # インデントを保持
                indent = len(line) - len(line.lstrip())
                content_part = line.lstrip()[2:]
                output_lines.append(f"{' ' * indent}{point_num}. {content_part}")
                point_num += 1
            # その他の行（空行や説明等）
            else:
                output_lines.append(line)
        else:
            output_lines.append(line)

    return "\n".join(output_lines)

def fix_tags(content: str, add_tags: list) -> str:
    """tags を拡充"""
    # 現在の tags を抽出
    match = re.search(r'tags:\s*\[([^\]]+)\]', content)

    if match:
        current_tags_str = match.group(1)
        current_tags = [t.strip() for t in current_tags_str.split(",")]

        # 新しいタグを追加（重複排除）
        all_tags = list(dict.fromkeys(current_tags + add_tags))

        # 5個以上に確保（重複を避けながら）
        if len(all_tags) < 5 and len(add_tags) > 0:
            all_tags = list(dict.fromkeys(all_tags + add_tags))

        # 最大8個に制限
        all_tags = all_tags[:8]

        new_tags_str = ", ".join(all_tags)

        # 置換
        content = re.sub(
            r'tags:\s*\[[^\]]+\]',
            f'tags: [{new_tags_str}]',
            content
        )

    return content

def main():
    print("\n" + "=" * 70)
    print("10の能力動画 形式修正（ポイント形式 + tags拡充）")
    print("=" * 70)

    for filename, config in files_to_fix.items():
        filepath = ABILITY_FOLDER / filename

        if not filepath.exists():
            print(f"⏭️  スキップ: {filename} (ファイル未検出)")
            continue

        print(f"\n📝 修正中: {filename}")

        content = filepath.read_text(encoding="utf-8")
        original = content

        # ポイント形式修正
        if config["fix_points"]:
            content = fix_points_format(content)
            print(f"  ✅ ポイント形式統一")

        # tags 修正
        if config["fix_tags"]:
            content = fix_tags(content, config["add_tags"])
            print(f"  ✅ tags 拡充: {', '.join(config['add_tags'])}")

        # ファイル更新
        if content != original:
            filepath.write_text(content, encoding="utf-8")
            print(f"  ✅ ファイル更新完了")
        else:
            print(f"  ⏭️  変更なし")

    print(f"\n{'='*70}")
    print("形式修正完了")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
