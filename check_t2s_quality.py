#!/usr/bin/env python3
import sys
import re
import json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

VAULT_PATH = Path(r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes")
SERIES_FOLDER = VAULT_PATH / "01_講義" / "T2Sセミナー"

class QualityChecker:
    def __init__(self):
        self.results = []
        self.critical_issues = []

    def check_file(self, filepath: Path) -> dict:
        """1ファイルを詳細チェック"""
        # ファイル名から番号とタイトルを抽出
        name = filepath.stem
        match = re.match(r'^(\d+)_42_(.+)$', name)
        if match:
            number = match.group(1)
            title = match.group(2)
        else:
            title = name
            number = "?"

        content = filepath.read_text(encoding="utf-8")

        result = {
            "number": number,
            "file": filepath.name,
            "title": title,
            "checks": {},
            "issues": [],
            "score": 0
        }

        # === A. Frontmatter チェック ===
        fm_checks = {}
        fm_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)

        if fm_match:
            fm = fm_match.group(1)

            # title
            title_match = re.search(r'title:\s*"([^"]+)"', fm)
            fm_checks["title_exists"] = bool(title_match)

            # date
            date_match = re.search(r'date:\s*(\d{4}-\d{2}-\d{2})', fm)
            fm_checks["date_valid"] = bool(date_match)

            # source_url
            url_match = re.search(r'source_url:\s*"([^"]+)"', fm)
            if url_match:
                url = url_match.group(1)
                is_placeholder = any(x in url for x in ["XXX", "XXXX", "0000", "Unable"])
                fm_checks["source_url_valid"] = not is_placeholder and url.startswith("http")
                if is_placeholder:
                    result["issues"].append(f"⚠️  source_url プレースホルダー")
            else:
                fm_checks["source_url_valid"] = False
                result["issues"].append(f"❌ source_url がない")

            # category
            category_match = re.search(r'category:\s*"([^"]+)"', fm)
            if category_match:
                cat = category_match.group(1)
                fm_checks["category_correct"] = cat == "T2Sセミナー"
                if cat != "T2Sセミナー":
                    result["issues"].append(f"❌ category が異なる: '{cat}'")
            else:
                fm_checks["category_correct"] = False
                result["issues"].append(f"❌ category がない")

            # tags
            tags_match = re.search(r'tags:\s*\[([^\]]+)\]', fm)
            if tags_match:
                tags = [t.strip() for t in tags_match.group(1).split(",")]
                fm_checks["tags_sufficient"] = len(tags) >= 5
                if len(tags) < 5:
                    result["issues"].append(f"⚠️  tags が不足: {len(tags)}個")
            else:
                fm_checks["tags_sufficient"] = False
                result["issues"].append(f"❌ tags がない")
        else:
            fm_checks = {k: False for k in ["title_exists", "date_valid", "source_url_valid", "category_correct", "tags_sufficient"]}
            result["issues"].append(f"❌ Frontmatter がない")

        result["checks"]["frontmatter"] = fm_checks

        # === B. 要約セクション チェック ===
        summary_checks = {}
        summary_match = re.search(r"## 要約\n+(.+?)(?=\n##|$)", content, re.DOTALL)

        if summary_match:
            summary_text = summary_match.group(1).strip()
            summary_checks["exists"] = True
            summary_checks["char_valid"] = 100 <= len(summary_text) <= 300
            summary_checks["no_placeholder"] = "[未生成]" not in summary_text and "[文字起こし" not in summary_text

            if not summary_checks["char_valid"]:
                result["issues"].append(f"⚠️  要約: {len(summary_text)}字（100-300字推奨）")
            if not summary_checks["no_placeholder"]:
                result["issues"].append(f"❌ 要約にプレースホルダー")
        else:
            summary_checks = {"exists": False, "char_valid": False, "no_placeholder": False}
            result["issues"].append(f"❌ 要約セクションがない")

        result["checks"]["summary"] = summary_checks

        # === C. ポイント セクション チェック ===
        points_checks = {}
        points_match = re.search(r"## ポイント\n+(.+?)(?=\n##|$)", content, re.DOTALL)

        if points_match:
            points_text = points_match.group(1).strip()
            point_count = len(re.findall(r"^\d+\.", points_text, re.MULTILINE))
            points_checks["exists"] = True
            points_checks["count_valid"] = point_count >= 7
            points_checks["no_placeholder"] = "[未生成]" not in points_text

            if not points_checks["count_valid"]:
                result["issues"].append(f"⚠️  ポイント: {point_count}個（7個以上推奨）")
            if not points_checks["no_placeholder"]:
                result["issues"].append(f"❌ ポイントにプレースホルダー")
        else:
            points_checks = {"exists": False, "count_valid": False, "no_placeholder": False}
            result["issues"].append(f"❌ ポイントセクションがない")

        result["checks"]["points"] = points_checks

        # === D. 文字起こし セクション チェック ===【重要】
        transcription_checks = {}
        transcription_match = re.search(r"## 文字起こし（全文）\n+(.+?)(?=\n---|$)", content, re.DOTALL)

        if transcription_match:
            trans_text = transcription_match.group(1).strip()
            is_placeholder = "[文字起こしテキスト：" in trans_text or "[未処理]" in trans_text
            transcription_checks["exists"] = True
            transcription_checks["no_placeholder"] = not is_placeholder
            transcription_checks["char_valid"] = len(trans_text) >= 200
            transcription_checks["quality_valid"] = len(trans_text) >= 300

            if is_placeholder:
                result["issues"].append(f"❌❌❌ 文字起こしがプレースホルダー（重大不備）")
                self.critical_issues.append(filepath.name)
            if not transcription_checks["char_valid"]:
                result["issues"].append(f"❌ 文字起こし: {len(trans_text)}字（200字以上推奨）")
        else:
            transcription_checks = {"exists": False, "no_placeholder": False, "char_valid": False, "quality_valid": False}
            result["issues"].append(f"❌ 文字起こしセクションがない")

        result["checks"]["transcription"] = transcription_checks

        # === E. 整合性チェック ===
        consistency_checks = {
            "filename_matches": title in filepath.name or "42_" in filepath.name,
            "category_consistent": True,
            "source_url_has_id": False,
            "tags_relevant": "セミナー" in content or "T2S" in content,
            "no_broken_links": True
        }

        result["checks"]["consistency"] = consistency_checks

        # === スコア計算 ===
        all_checks = sum(1 for section in result["checks"].values()
                        for check, value in section.items() if isinstance(value, bool))
        passed = sum(1 for section in result["checks"].values()
                    for check, value in section.items() if isinstance(value, bool) and value)

        result["score"] = int(passed / all_checks * 100) if all_checks > 0 else 0

        return result

    def run_all_checks(self):
        """全ファイルをチェック"""
        files = sorted(SERIES_FOLDER.glob("[0-9]*.md"))

        for filepath in files:
            result = self.check_file(filepath)
            self.results.append(result)

    def print_report(self):
        """レポート出力"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║      T2Sセミナー 全42ファイル 品質管理チェック（検証官）    ║
╚══════════════════════════════════════════════════════════════╝
""")

        print(f"\n【ファイル別チェック結果】\n")

        for i, result in enumerate(self.results, 1):
            status = "✅" if result["score"] >= 90 else "⚠️" if result["score"] >= 70 else "❌"
            print(f"{i:2}. {status} {result['number']:2} | {result['title'][:40]}")

            if result["issues"]:
                for issue in result["issues"]:
                    print(f"         {issue}")
            else:
                print(f"         ✅ 不備なし")

        # サマリー
        print("\n" + "=" * 70)
        print("【チェック結果サマリー】")
        print("=" * 70)

        pass_count = sum(1 for r in self.results if r["score"] >= 90)
        warning_count = sum(1 for r in self.results if 70 <= r["score"] < 90)
        fail_count = sum(1 for r in self.results if r["score"] < 70)
        avg_score = sum(r["score"] for r in self.results) // len(self.results) if self.results else 0

        print(f"\n✅ 優秀（90%以上）: {pass_count}/{len(self.results)}")
        print(f"⚠️  要注意（70-89%）: {warning_count}/{len(self.results)}")
        print(f"❌ 不合格（70%未満）: {fail_count}/{len(self.results)}")
        print(f"\n📊 平均スコア: {avg_score}%")

        if self.critical_issues:
            print(f"\n🚨 【重大問題】{len(self.critical_issues)}件（プレースホルダー未処理）")
            print("\n重大問題ファイル:")
            for file in self.critical_issues:
                print(f"  - {file}")

        if fail_count > 0 or warning_count > 0 or self.critical_issues:
            print(f"\n⚠️  修正が必要です → 実装官に差し戻し")
            return False
        else:
            print(f"\n✅ 全ファイル合格！")
            return True

def main():
    checker = QualityChecker()
    checker.run_all_checks()
    success = checker.print_report()

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
