#!/usr/bin/env python3
"""
【品質管理】テンプレート検出エンジン

目的: Markdown ファイルの文字起こしセクションから
     テンプレート的な表現を検出し、実テキストとの区別を支援

使用方法:
    python quality_check_template_detector.py [folder_path]

出力:
    - template_detection_report.json: 詳細レポート
    - template_suspicious_files.txt: 疑わしいファイルリスト
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict


@dataclass
class TemplatePattern:
    """テンプレートパターン定義"""
    name: str
    regex: str
    risk_level: str  # HIGH, MEDIUM, LOW
    description: str


class TemplateDetector:
    """テンプレート検出エンジン"""

    # 既知のテンプレートパターン
    KNOWN_PATTERNS = [
        TemplatePattern(
            name="T2S_TEMPLATE_A",
            regex=r"本セミナーの「(.+?)」では、人生を豊かにするための重要な原則",
            risk_level="HIGH",
            description="T2Sセミナー テンプレートA（旧式）"
        ),
        TemplatePattern(
            name="T2S_TEMPLATE_B",
            regex=r"本セミナーの「(.+?)」では、重要な概念と実践的なアプローチ",
            risk_level="HIGH",
            description="T2Sセミナー テンプレートB（旧式）"
        ),
        TemplatePattern(
            name="GENERIC_SEMINAR",
            regex=r"このセミナーの内容を実生活で活かすために：",
            risk_level="MEDIUM",
            description="汎用セミナーテンプレート"
        ),
        TemplatePattern(
            name="PLACEHOLDER_PATTERN",
            regex=r"\[文字起こしテキスト：",
            risk_level="CRITICAL",
            description="プレースホルダー形式"
        ),
        TemplatePattern(
            name="UNGENERATED_MARKER",
            regex=r"\[未生成\]|\[未処理\]",
            risk_level="CRITICAL",
            description="未生成マーカー"
        ),
    ]

    def __init__(self):
        self.results = {
            "files_scanned": 0,
            "files_with_templates": 0,
            "critical_issues": 0,
            "warnings": 0,
            "file_details": []
        }

    def detect_in_text(self, text: str) -> Dict:
        """テキストからテンプレートパターンを検出"""
        detected = {
            "matched_patterns": [],
            "risk_level": "SAFE",
            "template_probability": 0.0,
            "confidence": 0.0
        }

        high_risk_count = 0
        medium_risk_count = 0

        for pattern in self.KNOWN_PATTERNS:
            if re.search(pattern.regex, text):
                detected["matched_patterns"].append({
                    "name": pattern.name,
                    "risk": pattern.risk_level,
                    "description": pattern.description
                })

                if pattern.risk_level == "CRITICAL":
                    detected["risk_level"] = "CRITICAL"
                    detected["confidence"] = 0.99
                elif pattern.risk_level == "HIGH":
                    high_risk_count += 1
                elif pattern.risk_level == "MEDIUM":
                    medium_risk_count += 1

        # リスクレベルの判定
        if detected["matched_patterns"]:
            if detected["risk_level"] == "CRITICAL":
                detected["template_probability"] = 0.95
            elif high_risk_count >= 2:
                detected["risk_level"] = "HIGH"
                detected["template_probability"] = 0.85
                detected["confidence"] = 0.85
            elif high_risk_count >= 1:
                detected["risk_level"] = "MEDIUM"
                detected["template_probability"] = 0.70
                detected["confidence"] = 0.70
            elif medium_risk_count >= 2:
                detected["risk_level"] = "MEDIUM"
                detected["template_probability"] = 0.60
                detected["confidence"] = 0.60

        return detected

    def calculate_generic_phrase_density(self, text: str) -> float:
        """定型句の密度を計算（0.0-1.0）"""
        generic_phrases = [
            "本セミナーでは",
            "詳しく解説",
            "実践的な",
            "日常生活で",
            "このセミナーの内容を",
            "セミナーで強調",
            "セミナーで述べられた",
            "中心的な内容",
            "ポイント",
            "重要な",
            "について述べられています",
        ]

        total_phrases = 0
        for phrase in generic_phrases:
            count = text.count(phrase)
            total_phrases += count

        # 100文字あたりの定型句数で密度を計算
        text_length = len(text)
        if text_length == 0:
            return 0.0

        density = (total_phrases / (text_length / 100)) / len(generic_phrases)
        return min(1.0, density)

    def calculate_uniqueness_score(self, text: str, title: str = "") -> float:
        """
        文字起こしの一意性を測定（0.0-1.0）

        1.0 = 完全にユニーク（実テキスト可能性高い）
        0.0 = テンプレート的（実内容なし）
        """

        # 1. 定型フレーズ密度
        phrase_density = self.calculate_generic_phrase_density(text)
        density_score = max(0, 1.0 - phrase_density)

        # 2. タイトル関連語の出現度
        title_relevance = 0.0
        if title:
            title_words = [w for w in title.split() if len(w) > 2]
            title_mentions = sum(
                text.count(word) for word in title_words
            )
            title_relevance = min(1.0, title_mentions / max(3, len(title_words)))

        # 3. 文章長（短いほどテンプレート的）
        length_score = min(1.0, len(text) / 2000)  # 2000字以上なら満点

        # 4. 最終スコア（加重平均）
        uniqueness = (
            density_score * 0.4 +
            title_relevance * 0.3 +
            length_score * 0.3
        )

        return min(1.0, max(0.0, uniqueness))

    def scan_file(self, filepath: Path) -> Dict:
        """1つのMarkdownファイルをスキャン"""

        result = {
            "file": filepath.name,
            "filepath": str(filepath),
            "status": "OK",
            "transcription": {
                "exists": False,
                "length": 0,
                "template_detection": None,
                "uniqueness_score": 0.0,
                "recommendation": "UNKNOWN"
            }
        }

        try:
            content = filepath.read_text(encoding="utf-8")
            self.results["files_scanned"] += 1

            # タイトルを抽出
            title_match = re.search(
                r'title: "【.+?】(.+?)（',
                content
            )
            title = title_match.group(1) if title_match else ""

            # 文字起こしセクションを抽出
            trans_match = re.search(
                r"## 文字起こし（全文）\n+(.+?)(?=\n##|$)",
                content,
                re.DOTALL
            )

            if not trans_match:
                result["transcription"]["exists"] = False
                result["status"] = "MISSING"
                result["transcription"]["recommendation"] = "文字起こしセクションなし"
                self.results["critical_issues"] += 1
                return result

            trans_text = trans_match.group(1).strip()
            result["transcription"]["exists"] = True
            result["transcription"]["length"] = len(trans_text)

            # テンプレート検出
            template_detection = self.detect_in_text(trans_text)
            result["transcription"]["template_detection"] = template_detection

            # ユニーク度スコア計算
            uniqueness = self.calculate_uniqueness_score(trans_text, title)
            result["transcription"]["uniqueness_score"] = round(uniqueness, 3)

            # 推奨事項の判定
            if template_detection["risk_level"] == "CRITICAL":
                result["status"] = "CRITICAL"
                result["transcription"]["recommendation"] = "プレースホルダー/未処理 → 即座の修正が必須"
                self.results["critical_issues"] += 1
            elif template_detection["risk_level"] == "HIGH":
                result["status"] = "WARNING"
                result["transcription"]["recommendation"] = "テンプレート検出 → 修正推奨"
                self.results["warnings"] += 1
            elif uniqueness < 0.5:
                result["status"] = "WARNING"
                result["transcription"]["recommendation"] = f"テンプレート可能性高い（スコア: {uniqueness:.2f}） → 確認推奨"
                self.results["warnings"] += 1
            elif uniqueness < 0.7:
                result["status"] = "CAUTION"
                result["transcription"]["recommendation"] = f"若干テンプレート傾向（スコア: {uniqueness:.2f}） → サンプル点検対象"
            else:
                result["status"] = "OK"
                result["transcription"]["recommendation"] = f"実テキスト判定（スコア: {uniqueness:.2f}） → OK"

            if result["status"] != "OK":
                self.results["files_with_templates"] += 1

        except Exception as e:
            result["status"] = "ERROR"
            result["transcription"]["recommendation"] = f"スキャンエラー: {str(e)}"
            self.results["critical_issues"] += 1

        return result

    def scan_folder(self, folder_path: Path) -> None:
        """フォルダ内の全Markdownファイルをスキャン"""

        md_files = sorted(folder_path.glob("*.md"))

        print(f"Scanning {len(md_files)} files in {folder_path}\n")

        for filepath in md_files:
            result = self.scan_file(filepath)
            self.results["file_details"].append(result)

            # 進捗表示
            status_icon = {
                "OK": "[OK]",
                "CAUTION": "[!]",
                "WARNING": "[!]",
                "CRITICAL": "[X]",
                "ERROR": "[E]",
                "MISSING": "[M]"
            }

            icon = status_icon.get(result["status"], "[?]")
            print(f"{icon} {result['file'][:50]:<50} | {result['status']:<10} | Score: {result['transcription'].get('uniqueness_score', 0):.2f}")

    def generate_report(self, output_path: Path) -> None:
        """JSON形式でレポートを生成"""

        # JSON レポート出力
        report_path = output_path / "template_detection_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] JSON report saved: {report_path}")

        # テキストサマリー出力
        summary_path = output_path / "template_detection_summary.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("【テンプレート検出レポート - サマリー】\n")
            f.write("="*80 + "\n\n")

            f.write(f"スキャンファイル数: {self.results['files_scanned']}\n")
            f.write(f"テンプレート検出: {self.results['files_with_templates']}\n")
            f.write(f"重大問題: {self.results['critical_issues']}\n")
            f.write(f"警告: {self.results['warnings']}\n\n")

            # 問題ファイル一覧
            critical_files = [d for d in self.results["file_details"]
                            if d["status"] in ["CRITICAL", "ERROR", "MISSING"]]
            warning_files = [d for d in self.results["file_details"]
                           if d["status"] in ["WARNING", "CAUTION"]]

            if critical_files:
                f.write("【重大問題ファイル】\n")
                for d in critical_files:
                    f.write(f"- {d['file']}: {d['transcription']['recommendation']}\n")
                f.write("\n")

            if warning_files:
                f.write("【警告ファイル】\n")
                for d in warning_files:
                    f.write(f"- {d['file']}: {d['transcription']['recommendation']}\n")
                f.write("\n")

            # ユニーク度スコア一覧
            f.write("【ユニーク度スコア一覧】\n")
            sorted_by_score = sorted(
                self.results["file_details"],
                key=lambda x: x["transcription"].get("uniqueness_score", 0)
            )

            for d in sorted_by_score:
                score = d["transcription"].get("uniqueness_score", 0)
                f.write(f"{d['file'][:50]:<50} | {score:.3f}\n")

        print(f"[OK] Summary report saved: {summary_path}")


def main():
    import sys

    # フォルダパスの指定
    if len(sys.argv) > 1:
        folder_path = Path(sys.argv[1])
    else:
        folder_path = Path(
            r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes\01_講義\T2Sセミナー"
        )

    if not folder_path.exists():
        print(f"Error: Folder not found: {folder_path}")
        sys.exit(1)

    # 検出エンジン実行
    detector = TemplateDetector()
    detector.scan_folder(folder_path)
    detector.generate_report(folder_path)

    # 結果表示
    print("\n" + "="*80)
    print("【検出結果】")
    print(f"スキャンファイル: {detector.results['files_scanned']}")
    print(f"テンプレート検出: {detector.results['files_with_templates']}")
    print(f"重大問題: {detector.results['critical_issues']}")
    print(f"警告: {detector.results['warnings']}")

    if detector.results["critical_issues"] == 0 and detector.results["warnings"] == 0:
        print("\n[OK] テンプレート問題なし！")
    else:
        print("\n[!] 問題あり → レポートを確認してください")


if __name__ == "__main__":
    main()
