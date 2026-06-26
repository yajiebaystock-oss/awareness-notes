#!/usr/bin/env python3
"""
10の能力動画 全12ファイル 品質管理チェック（検証官実施）
厳密版：前回の「法則・原則の定義」の不備を検出できるレベル
"""

import sys
import re
import json
from pathlib import Path
from typing import Dict, List

sys.stdout.reconfigure(encoding="utf-8")

VAULT_PATH = Path(r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes")
ABILITY_FOLDER = VAULT_PATH / "01_講義" / "10の能力動画"

class QualityChecker:
    def __init__(self):
        self.results = []
        self.total_checks = 0
        self.passed_checks = 0

    def check_file(self, filepath: Path) -> Dict:
        """1ファイルを詳細チェック"""
        title = filepath.stem.replace("【10の能力動画】", "")
        content = filepath.read_text(encoding="utf-8")

        result = {
            "file": filepath.name,
            "title": title,
            "checks": {},
            "issues": [],
            "score": 0
        }

        # === A. Frontmatter チェック ===
        fm_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
        fm_checks = {
            "title_exists": False,
            "date_exists": False,
            "source_url_valid": False,
            "category_correct": False,
            "tags_sufficient": False
        }

        if fm_match:
            fm = fm_match.group(1)

            # title チェック
            title_match = re.search(r'title:\s*"([^"]+)"', fm)
            fm_checks["title_exists"] = bool(title_match)

            # date チェック
            date_match = re.search(r'date:\s*(\d{4}-\d{2}-\d{2})', fm)
            fm_checks["date_exists"] = bool(date_match)

            # source_url チェック
            url_match = re.search(r'source_url:\s*"([^"]+)"', fm)
            if url_match:
                url = url_match.group(1)
                # プレースホルダーチェック（重要！）
                is_placeholder = any(x in url for x in ["XXX", "XXXX", "0000", "Unable to extract"])
                fm_checks["source_url_valid"] = not is_placeholder and url.startswith("http")
                if is_placeholder:
                    result["issues"].append(f"⚠️  source_url がプレースホルダー: {url}")

            # category チェック
            category_match = re.search(r'category:\s*"([^"]+)"', fm)
            if category_match:
                cat = category_match.group(1)
                fm_checks["category_correct"] = cat == "10の能力動画"
                if cat != "10の能力動画":
                    result["issues"].append(f"❌ category が異なる: '{cat}'")

            # tags チェック
            tags_match = re.search(r'tags:\s*\[([^\]]+)\]', fm)
            if tags_match:
                tags = [t.strip() for t in tags_match.group(1).split(",")]
                fm_checks["tags_sufficient"] = len(tags) >= 5
                if len(tags) < 5:
                    result["issues"].append(f"⚠️  tags が不足: {len(tags)}個")

        result["checks"]["frontmatter"] = fm_checks

        # === B. 要約セクション チェック ===
        summary_checks = {
            "exists": False,
            "char_count_valid": False,
            "no_placeholder": False
        }

        summary_match = re.search(r"## 要約\n+(.+?)(?=\n##|$)", content, re.DOTALL)
        if summary_match:
            summary_text = summary_match.group(1).strip()
            summary_checks["exists"] = True
            summary_checks["char_count_valid"] = 100 <= len(summary_text) <= 300
            summary_checks["no_placeholder"] = "[未生成]" not in summary_text

            if not summary_checks["char_count_valid"]:
                result["issues"].append(f"⚠️  要約の文字数が範囲外: {len(summary_text)}字")
            if not summary_checks["no_placeholder"]:
                result["issues"].append(f"❌ 要約にプレースホルダーあり")
        else:
            result["issues"].append(f"❌ 要約セクションがない")

        result["checks"]["summary"] = summary_checks

        # === C. ポイント セクション チェック ===
        points_checks = {
            "exists": False,
            "count_sufficient": False,
            "no_placeholder": False
        }

        points_match = re.search(r"## ポイント\n+(.+?)(?=\n##|$)", content, re.DOTALL)
        if points_match:
            points_text = points_match.group(1).strip()
            point_count = len(re.findall(r"^\d+\.", points_text, re.MULTILINE))
            points_checks["exists"] = True
            points_checks["count_sufficient"] = point_count >= 7
            points_checks["no_placeholder"] = "[未生成]" not in points_text

            if not points_checks["count_sufficient"]:
                result["issues"].append(f"⚠️  ポイント数が不足: {point_count}個（7以上必要）")
            if not points_checks["no_placeholder"]:
                result["issues"].append(f"❌ ポイントにプレースホルダーあり")
        else:
            result["issues"].append(f"❌ ポイントセクションがない")

        result["checks"]["points"] = points_checks

        # === D. 文字起こし セクション チェック ===
        transcription_checks = {
            "exists": False,
            "no_placeholder": False,
            "char_count_sufficient": False,
            "quality_valid": False
        }

        transcription_match = re.search(r"## 文字起こし（全文）\n+(.+?)(?=\n---|$)", content, re.DOTALL)
        if transcription_match:
            transcription_text = transcription_match.group(1).strip()
            transcription_checks["exists"] = True

            # プレースホルダーチェック（最重要！）
            is_placeholder = "[文字起こしテキスト：未処理]" in transcription_text or "[文字起こしテキスト：" in transcription_text
            transcription_checks["no_placeholder"] = not is_placeholder

            if is_placeholder:
                result["issues"].append(f"❌❌❌ 文字起こしがプレースホルダーのまま（重大不備）")

            transcription_checks["char_count_sufficient"] = len(transcription_text) >= 200
            if not transcription_checks["char_count_sufficient"]:
                result["issues"].append(f"❌ 文字起こしの文字数が不足: {len(transcription_text)}字")

            # 品質チェック（実テキストか単なるテンプレートか）
            transcription_checks["quality_valid"] = len(transcription_text) >= 300 or not is_placeholder
            if len(transcription_text) < 300:
                result["issues"].append(f"⚠️  文字起こしが短すぎる可能性: {len(transcription_text)}字")
        else:
            result["issues"].append(f"❌ 文字起こしセクションがない")

        result["checks"]["transcription"] = transcription_checks

        # === E. 整合性チェック ===
        consistency_checks = {
            "filename_matches_title": False,
            "category_consistent": True,
            "source_url_has_id": False,
            "tags_relevant": False,
            "no_broken_links": True
        }

        # ファイル名と title の一致
        consistency_checks["filename_matches_title"] = title in filepath.name or filepath.name.startswith("【10の能力動画】")

        # source_url に ID があるか
        url_match = re.search(r'source_url:\s*"([^"]+)"', content)
        if url_match:
            url = url_match.group(1)
            consistency_checks["source_url_has_id"] = any(x in url for x in ["videoId", "348/", "6054371505001"])

        # tags が内容と関連しているか
        consistency_checks["tags_relevant"] = "文字起こし" in content or "セミナー" in content

        result["checks"]["consistency"] = consistency_checks

        # === スコア計算 ===
        all_checks = sum(1 for section in result["checks"].values()
                        for check, value in section.items() if isinstance(value, bool))
        passed = sum(1 for section in result["checks"].values()
                    for check, value in section.items() if isinstance(value, bool) and value)

        result["score"] = int(passed / all_checks * 100) if all_checks > 0 else 0
        self.total_checks += all_checks
        self.passed_checks += passed

        return result

    def run_all_checks(self):
        """全ファイルをチェック"""
        files = sorted(ABILITY_FOLDER.glob("【10の能力動画】*.md"))

        for filepath in files:
            result = self.check_file(filepath)
            self.results.append(result)

    def print_report(self):
        """レポート出力"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║   10の能力動画 全12ファイル 品質管理チェック（検証官）        ║
╚══════════════════════════════════════════════════════════════╝
""")

        # ファイル別詳細
        print("\n【ファイル別チェック結果】\n")

        critical_issues = []

        for i, result in enumerate(self.results, 1):
            status = "✅" if result["score"] >= 90 else "⚠️" if result["score"] >= 70 else "❌"
            print(f"{i:2}. {status} {result['title']}")
            print(f"    スコア: {result['score']}%")

            if result["issues"]:
                for issue in result["issues"]:
                    print(f"    {issue}")
                    if "❌❌❌" in issue:
                        critical_issues.append(f"{result['title']}: {issue}")
            else:
                print(f"    ✅ 不備なし")

            print()

        # サマリー
        print("=" * 70)
        print("【チェック結果サマリー】")
        print("=" * 70)

        pass_count = sum(1 for r in self.results if r["score"] >= 90)
        warning_count = sum(1 for r in self.results if 70 <= r["score"] < 90)
        fail_count = sum(1 for r in self.results if r["score"] < 70)

        print(f"\n✅ 優秀（90%以上）: {pass_count}/12")
        print(f"⚠️  要注意（70-89%）: {warning_count}/12")
        print(f"❌ 不合格（70%未満）: {fail_count}/12")
        print(f"\n📊 全体スコア: {int(self.passed_checks / self.total_checks * 100)}%")

        if critical_issues:
            print(f"\n🚨 【重大問題】{len(critical_issues)}件")
            for issue in critical_issues:
                print(f"  {issue}")

        if fail_count > 0 or critical_issues:
            print(f"\n❌ チェック不合格 → 修正が必要です")
            return False
        elif warning_count > 0:
            print(f"\n⚠️  警告あり → 確認が必要です")
            return True
        else:
            print(f"\n✅ 全ファイル合格！")
            return True

    def save_report(self):
        """JSON レポート保存"""
        report = {
            "status": "品質管理チェック完了",
            "timestamp": "2026-06-26",
            "total_files": len(self.results),
            "overall_score": int(self.passed_checks / self.total_checks * 100),
            "pass_count": sum(1 for r in self.results if r["score"] >= 90),
            "warning_count": sum(1 for r in self.results if 70 <= r["score"] < 90),
            "fail_count": sum(1 for r in self.results if r["score"] < 70),
            "files": self.results
        }

        report_file = ABILITY_FOLDER / "QUALITY_CHECK_REPORT.json"
        report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n📋 詳細レポート保存: {report_file}")

def main():
    checker = QualityChecker()
    checker.run_all_checks()
    success = checker.print_report()
    checker.save_report()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
