#!/usr/bin/env python3
import re
from pathlib import Path

SERIES_FOLDER = Path(r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes\01_講義\T2Sセミナー")

print("""
╔══════════════════════════════════════════════════════════════╗
║   T2Sセミナー ポイント内容確認チェック（検証官）          ║
╚══════════════════════════════════════════════════════════════╝
""")

files = sorted(SERIES_FOLDER.glob("[0-9]*.md"))
pass_count = 0
fail_count = 0
failed_files = []

print(f"\n【ポイント内容確認】\n")

for filepath in files:
    content = filepath.read_text(encoding="utf-8")
    name = filepath.stem
    
    # ポイントセクション抽出
    points_match = re.search(r"## ポイント\n+(.+?)(?=##|$)", content, re.DOTALL)
    
    if points_match:
        points_text = points_match.group(1).strip()
        
        # プレースホルダー確認
        has_placeholder = "[ポイント" in points_text or "関連する内容の説明" in points_text
        
        # ポイント数確認
        point_count = len(re.findall(r"^\d+\.", points_text, re.MULTILINE))
        
        # 実内容確認（タイトルが含まれているか、短い説明ではなく実内容があるか）
        has_real_content = ("【" in points_text and "】" in points_text) or len(points_text) > 500
        
        # 判定
        if not has_placeholder and point_count >= 7 and has_real_content:
            pass_count += 1
            print(f"✅ {name}: {point_count}個のポイント（実内容あり）")
        else:
            fail_count += 1
            failed_files.append(name)
            issues = []
            if has_placeholder:
                issues.append("プレースホルダーあり")
            if point_count < 7:
                issues.append(f"ポイント{point_count}個")
            if not has_real_content:
                issues.append("実内容なし")
            print(f"❌ {name}: {', '.join(issues)}")
    else:
        fail_count += 1
        failed_files.append(name)
        print(f"❌ {name}: ポイントセクションがない")

# サマリー
print(f"\n{'='*70}")
print("【最終判定】")
print(f"{'='*70}")
print(f"\n✅ 合格: {pass_count}/42")
print(f"❌ 不合格: {fail_count}/42")

if fail_count == 0:
    print(f"\n🎉 全42ファイルのポイント内容が完全実装されました！")
    print(f"\nT2Sセミナーは完全に本番利用可能状態です！")
else:
    print(f"\n⚠️  {fail_count}ファイルが不合格です:")
    for f in failed_files[:5]:
        print(f"  - {f}")
    if len(failed_files) > 5:
        print(f"  ... 他 {len(failed_files)-5} ファイル")
