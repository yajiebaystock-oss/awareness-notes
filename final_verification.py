#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification script for 10 ability videos project
"""
import re
import json
import sys
from pathlib import Path

# Set stdout encoding to UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

VAULT_PATH = Path(r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes")
ABILITY_FOLDER = VAULT_PATH / "01_講義" / "10の能力動画"

def verify_file(filepath: Path) -> dict:
    """Verify a single file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    title = filepath.stem.replace("【10の能力動画】", "")

    checks = {
        "title": title,
        "file": filepath.name,
        "checks": {},
        "completion_score": 0,
        "issues": []
    }

    # 1. Check Frontmatter
    frontmatter_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
    if frontmatter_match:
        fm = frontmatter_match.group(1)
        fm_checks = {
            "title": "title:" in fm,
            "date": "date:" in fm,
            "source_url": "source_url:" in fm,
            "category": "category:" in fm and "10の能力動画" in fm,
            "tags": re.search(r"tags:\s*\[.+\]", fm) is not None
        }
        checks["checks"]["frontmatter"] = fm_checks

        for key, val in fm_checks.items():
            if not val:
                checks["issues"].append(f"Frontmatter missing: {key}")
    else:
        checks["issues"].append("No frontmatter found")

    # 2. Check Summary section
    summary_match = re.search(r"## 要約\n+(.+?)(?=\n##|$)", content, re.DOTALL)
    if summary_match:
        summary_text = summary_match.group(1).strip()
        summary_chars = len(summary_text)
        summary_ok = 100 <= summary_chars <= 300
        checks["checks"]["summary"] = {
            "exists": True,
            "char_count": summary_chars,
            "meets_requirement": summary_ok,
            "text_preview": summary_text[:50] + "..." if len(summary_text) > 50 else summary_text
        }
        if not summary_ok:
            checks["issues"].append(f"Summary: {summary_chars}chars (required: 100-300)")
    else:
        checks["checks"]["summary"] = {"exists": False}
        checks["issues"].append("Summary section not found")

    # 3. Check Points section
    points_match = re.search(r"## ポイント\n+(.+?)(?=\n##|$)", content, re.DOTALL)
    if points_match:
        points_text = points_match.group(1).strip()
        # Count both numbered lists (1.) and bulleted lists (-)
        point_count = len(re.findall(r"^(\d+\.|[-*])\s", points_text, re.MULTILINE))
        points_ok = point_count >= 7
        checks["checks"]["points"] = {
            "exists": True,
            "count": point_count,
            "meets_requirement": points_ok
        }
        if not points_ok:
            checks["issues"].append(f"Points: {point_count} items (required: 7+)")
    else:
        checks["checks"]["points"] = {"exists": False}
        checks["issues"].append("Points section not found")

    # 4. Check Transcription section
    transcription_match = re.search(r"## 文字起こし（全文）\n+(.+?)$", content, re.DOTALL)
    if transcription_match:
        transcription_text = transcription_match.group(1).strip()
        is_placeholder = "[文字起こしテキスト：未処理]" in transcription_text or "未処理" in transcription_text
        transcription_chars = len(transcription_text)
        transcription_ok = not is_placeholder and transcription_chars >= 100
        checks["checks"]["transcription"] = {
            "exists": True,
            "is_placeholder": is_placeholder,
            "char_count": transcription_chars,
            "meets_requirement": transcription_ok
        }
        if not transcription_ok:
            if is_placeholder:
                checks["issues"].append("Transcription: Placeholder detected")
            if transcription_chars < 100:
                checks["issues"].append(f"Transcription: {transcription_chars}chars (required: 100+)")
    else:
        checks["checks"]["transcription"] = {"exists": False}
        checks["issues"].append("Transcription section not found")

    # 5. Calculate completion score
    score = 0
    total_checks = 0

    for section, sub_checks in checks["checks"].items():
        if isinstance(sub_checks, dict):
            for check_name, result in sub_checks.items():
                if isinstance(result, bool) and check_name != "text_preview":
                    total_checks += 1
                    if result:
                        score += 1

    checks["completion_score"] = int((score / total_checks * 100) if total_checks > 0 else 0)

    return checks

def main():
    """Main verification"""
    print("\n" + "=" * 70)
    print("  10の能力動画 全12ファイル 最終品質確認")
    print("=" * 70)

    files = sorted([f for f in ABILITY_FOLDER.glob("【10の能力動画】*.md")])
    results = []

    print(f"\n検証対象: {len(files)} ファイル\n")

    for filepath in files:
        result = verify_file(filepath)
        results.append(result)

    # Detail report
    print("【ファイル別検証結果】\n")

    total_score = 0
    for i, result in enumerate(results, 1):
        print(f"{i:2}. {result['title']}")

        # Frontmatter
        if "frontmatter" in result["checks"]:
            fm_checks = result["checks"]["frontmatter"]
            fm_score = sum(1 for v in fm_checks.values() if v)
            print(f"    [OK] Frontmatter: {fm_score}/5 ({int(fm_score/5*100)}%)")

        # Sections
        if "summary" in result["checks"]:
            s = result["checks"]["summary"]
            if s.get("exists"):
                mark = "[OK]" if s['meets_requirement'] else "[WARN]"
                print(f"    {mark} Summary: {s['char_count']}chars")
            else:
                print(f"    [NG] Summary: NOT FOUND")

        if "points" in result["checks"]:
            p = result["checks"]["points"]
            if p.get("exists"):
                mark = "[OK]" if p['meets_requirement'] else "[WARN]"
                print(f"    {mark} Points: {p['count']}items")
            else:
                print(f"    [NG] Points: NOT FOUND")

        if "transcription" in result["checks"]:
            t = result["checks"]["transcription"]
            if t.get("exists"):
                mark = "[OK]" if t['meets_requirement'] else "[WARN]"
                placeholder_status = "YES" if t['is_placeholder'] else "NO"
                print(f"    {mark} Transcription: {t['char_count']}chars (Placeholder: {placeholder_status})")
            else:
                print(f"    [NG] Transcription: NOT FOUND")

        print(f"    Score: {result['completion_score']}%")

        if result['issues']:
            for issue in result['issues']:
                print(f"       ISSUE: {issue}")

        print()
        total_score += result["completion_score"]

    # Summary
    avg_score = int(total_score / len(results))
    perfect_count = sum(1 for r in results if r['completion_score'] >= 95)
    good_count = sum(1 for r in results if 80 <= r['completion_score'] < 95)
    poor_count = sum(1 for r in results if r['completion_score'] < 80)

    print("\n" + "=" * 70)
    print("【最終結果】")
    print("=" * 70)
    print(f"\n[SCORE] Average completion: {avg_score}%")
    print(f"[OK] Excellent (95%+): {perfect_count}/12")
    print(f"[WARN] Good (80-94%): {good_count}/12")
    print(f"[NG] Needs review (<80%): {poor_count}/12")

    # Save JSON report
    report = {
        "status": "OK: Final verification complete" if avg_score >= 80 else "WARN: Review needed",
        "timestamp": "2026-06-26",
        "total_files": len(results),
        "average_completion_score": avg_score,
        "perfect_count": perfect_count,
        "good_count": good_count,
        "poor_count": poor_count,
        "files": results,
        "user_directive": "No unprocessed or ungenerated content should remain",
        "compliance": avg_score >= 90
    }

    report_file = ABILITY_FOLDER / "FINAL_VERIFICATION_REPORT.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n[INFO] Detailed report saved: {report_file}")

    if avg_score >= 90:
        print("\n[SUCCESS] User directive 'No unprocessed or ungenerated content' ACHIEVED!")
    else:
        print(f"\n[WARN] Average score is {avg_score}%. Files need review.")
        print("\n【Files requiring attention】")
        for result in results:
            if result['completion_score'] < 90:
                print(f"  - {result['title']} ({result['completion_score']}%)")
                for issue in result['issues']:
                    print(f"    -> {issue}")

    return 0 if avg_score >= 90 else 1

if __name__ == "__main__":
    sys.exit(main())
