#!/usr/bin/env python3
"""
【品質管理】ユニーク度スコアリング & 改善提案エンジン

目的: Markdown ファイルの文字起こしセクションについて、
     実テキスト vs 自動生成コンテンツを判別し、
     改善の優先度を自動付与

使用方法:
    python quality_check_uniqueness_scorer.py

出力:
    - uniqueness_analysis_report.json: 詳細分析レポート
    - improvement_recommendations.txt: 改善提案書
"""

import re
import json
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict


@dataclass
class AnalysisMetrics:
    """分析メトリクス"""
    file_name: str
    title: str
    transcription_length: int

    # スコア
    template_probability: float
    uniqueness_score: float
    specificity_score: float
    diversity_score: float

    # 判定
    quality_level: str  # EXCELLENT, GOOD, FAIR, POOR
    improvement_priority: str  # P1, P2, P3, NONE

    # 改善提案
    issues: List[str]
    recommendations: List[str]


class UniquenessScorer:
    """ユニーク度スコアリングエンジン"""

    # 文字起こしに頻出する自動生成パターン
    AUTO_GENERATION_PATTERNS = [
        r"【.+?の本質的な意味】",
        r"【実生活への適用】",
        r"【心理学的背景】",
        r"【成功事例と失敗事例】",
        r"【具体的な実践方法】",
        r"【継続と習慣化】",
        r"【次のステップ】",
    ]

    def __init__(self):
        self.results = []

    def calculate_specificity_score(self, text: str, title: str) -> float:
        """
        タイトル固有性スコア (0.0-1.0)
        テキストがタイトルに固有の内容を含むかを判定
        """
        if not title:
            return 0.0

        title_words = [w for w in title.split() if len(w) >= 3]
        if not title_words:
            return 0.0

        # タイトル関連語の出現回数
        mentions = sum(text.count(word) for word in title_words)

        # 出現頻度から固有性を計算
        specificity = min(1.0, mentions / max(3, len(title_words)))
        return specificity

    def calculate_diversity_score(self, text: str) -> float:
        """
        多様性スコア (0.0-1.0)
        テキストの語彙の豊かさと多様性を測定
        """
        # 単語を抽出（長さ3以上のもののみ）
        words = re.findall(r'\b\w{3,}\b', text)
        if not words:
            return 0.0

        # ユニークな単語の割合
        unique_words = len(set(words))
        total_words = len(words)

        if total_words == 0:
            return 0.0

        diversity = unique_words / total_words
        return min(1.0, diversity)

    def calculate_auto_generation_probability(self, text: str) -> float:
        """
        自動生成確率 (0.0-1.0)
        テキストが自動生成コンテンツ（テンプレート）である確率
        """
        matches = sum(
            1 for pattern in self.AUTO_GENERATION_PATTERNS
            if re.search(pattern, text)
        )

        # マッチした自動生成パターンの割合
        probability = matches / len(self.AUTO_GENERATION_PATTERNS)
        return probability

    def detect_issues(self, text: str, title: str, specificity: float,
                     diversity: float, auto_prob: float) -> List[str]:
        """問題点を検出"""
        issues = []

        # 1. 長さチェック
        if len(text) < 1000:
            issues.append(f"文字数が少ない（{len(text)}字）")

        # 2. 固有性チェック
        if specificity < 0.3:
            issues.append(f"タイトル固有性が低い（スコア: {specificity:.2f}）")

        # 3. 多様性チェック
        if diversity < 0.4:
            issues.append(f"語彙の多様性が低い（スコア: {diversity:.2f}）")

        # 4. 自動生成パターン検出
        if auto_prob > 0.5:
            issues.append(f"自動生成パターンが多い（確率: {auto_prob:.0%}）")

        # 5. 構造化パターン検出
        has_sections = len(re.findall(r"【.+?】", text)) >= 3
        if not has_sections:
            issues.append("セクション構造化されていない")

        # 6. 具体例の不足
        if not re.search(r"例|事例|具体的", text):
            issues.append("具体例・事例が不足している")

        return issues

    def generate_recommendations(self, issues: List[str],
                                quality_level: str) -> List[str]:
        """改善提案を生成"""
        recommendations = []

        if quality_level in ["EXCELLENT", "GOOD"]:
            recommendations.append("現在のレベルを維持しつつ、定期的にレビュー")

        if "文字数が少ない" in str(issues):
            recommendations.append("1500字以上の詳細な説明を追加")

        if "タイトル固有性が低い" in str(issues):
            recommendations.append("タイトルに関連する専門用語・事例を追加")

        if "語彙の多様性が低い" in str(issues):
            recommendations.append("異なる観点や表現を含める")

        if "自動生成パターンが多い" in str(issues):
            recommendations.append("テンプレート構造を崩し、より自然な文体に")

        if "セクション構造化されていない" in str(issues):
            recommendations.append("段階的な説明構造を追加")

        if "具体例・事例が不足している" in str(issues):
            recommendations.append("実生活の具体例・研究データを追加")

        return recommendations if recommendations else ["良好です。定期メンテナンスのみ"]

    def determine_quality_level(self, uniqueness: float) -> str:
        """品質レベルを判定"""
        if uniqueness >= 0.85:
            return "EXCELLENT"
        elif uniqueness >= 0.75:
            return "GOOD"
        elif uniqueness >= 0.60:
            return "FAIR"
        else:
            return "POOR"

    def determine_improvement_priority(self, quality_level: str,
                                       issues: List[str]) -> str:
        """改善優先度を判定"""
        if quality_level in ["EXCELLENT", "GOOD"]:
            return "NONE"
        elif quality_level == "FAIR":
            if len(issues) >= 3:
                return "P2"
            else:
                return "P3"
        else:  # POOR
            return "P1"

    def analyze_file(self, filepath: Path) -> Dict:
        """1つのファイルを詳細分析"""
        result = {
            "file": filepath.name,
            "filepath": str(filepath),
            "status": "OK",
            "metrics": None,
            "error": None
        }

        try:
            content = filepath.read_text(encoding="utf-8")

            # タイトル抽出
            title_match = re.search(r'title: "【.+?】(.+?)（', content)
            title = title_match.group(1) if title_match else ""

            # 文字起こしセクション抽出
            trans_match = re.search(
                r"## 文字起こし（全文）\n+(.+?)(?=\n##|$)",
                content,
                re.DOTALL
            )

            if not trans_match:
                result["status"] = "MISSING"
                result["error"] = "文字起こしセクションなし"
                return result

            trans_text = trans_match.group(1).strip()
            length = len(trans_text)

            # 各種スコア計算
            specificity = self.calculate_specificity_score(trans_text, title)
            diversity = self.calculate_diversity_score(trans_text)
            auto_gen_prob = self.calculate_auto_generation_probability(trans_text)

            # ユニーク度スコア（複合スコア）
            uniqueness = (
                (1 - auto_gen_prob) * 0.4 +
                specificity * 0.3 +
                diversity * 0.3
            )

            # 品質判定
            quality_level = self.determine_quality_level(uniqueness)

            # 問題検出
            issues = self.detect_issues(trans_text, title, specificity,
                                       diversity, auto_gen_prob)

            # 改善優先度
            priority = self.determine_improvement_priority(quality_level, issues)

            # 改善提案
            recommendations = self.generate_recommendations(issues, quality_level)

            # メトリクス作成
            metrics = AnalysisMetrics(
                file_name=filepath.name,
                title=title,
                transcription_length=length,
                template_probability=auto_gen_prob,
                uniqueness_score=round(uniqueness, 3),
                specificity_score=round(specificity, 3),
                diversity_score=round(diversity, 3),
                quality_level=quality_level,
                improvement_priority=priority,
                issues=issues,
                recommendations=recommendations
            )

            result["metrics"] = asdict(metrics)
            result["status"] = quality_level

        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)

        return result

    def scan_folder(self, folder_path: Path) -> None:
        """フォルダをスキャン"""
        md_files = sorted(folder_path.glob("*.md"))

        print(f"Analyzing {len(md_files)} files...\n")

        for filepath in md_files:
            result = self.analyze_file(filepath)
            self.results.append(result)

            if result["metrics"]:
                metrics = result["metrics"]
                status_icon = {
                    "EXCELLENT": "[A+]",
                    "GOOD": "[A]",
                    "FAIR": "[B]",
                    "POOR": "[C]",
                    "ERROR": "[E]",
                    "MISSING": "[M]"
                }
                icon = status_icon.get(result["status"], "[?]")
                print(f"{icon} {metrics['file_name'][:50]:<50} | "
                      f"Quality: {metrics['quality_level']:<10} | "
                      f"Priority: {metrics['improvement_priority']}")

    def generate_detailed_report(self, output_path: Path) -> None:
        """詳細レポートを生成"""

        # JSON レポート
        report_path = output_path / "uniqueness_analysis_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] Detailed report: {report_path}")

        # 改善提案レポート
        improvement_path = output_path / "improvement_recommendations.txt"
        with open(improvement_path, "w", encoding="utf-8") as f:
            f.write("【品質改善提案書】\n")
            f.write("="*80 + "\n\n")

            # サマリー
            total = len([r for r in self.results if r["metrics"]])
            excellent = len([r for r in self.results
                           if r["metrics"] and r["metrics"]["quality_level"] == "EXCELLENT"])
            good = len([r for r in self.results
                       if r["metrics"] and r["metrics"]["quality_level"] == "GOOD"])
            fair = len([r for r in self.results
                       if r["metrics"] and r["metrics"]["quality_level"] == "FAIR"])
            poor = len([r for r in self.results
                       if r["metrics"] and r["metrics"]["quality_level"] == "POOR"])

            f.write(f"分析対象: {total}ファイル\n")
            f.write(f"EXCELLENT (A+): {excellent}\n")
            f.write(f"GOOD (A): {good}\n")
            f.write(f"FAIR (B): {fair}\n")
            f.write(f"POOR (C): {poor}\n\n")

            # 優先度別提案
            f.write("【改善優先度別 提案リスト】\n\n")

            for priority in ["P1", "P2", "P3"]:
                files = [r for r in self.results
                        if r["metrics"] and r["metrics"]["improvement_priority"] == priority]

                if files:
                    f.write(f"【{priority}（高優先）】\n")
                    for r in files:
                        metrics = r["metrics"]
                        f.write(f"\nFile: {metrics['file_name']}\n")
                        f.write(f"  Title: {metrics['title']}\n")
                        f.write(f"  Quality: {metrics['quality_level']}\n")
                        f.write(f"  Uniqueness Score: {metrics['uniqueness_score']}\n")
                        f.write(f"  Issues:\n")
                        for issue in metrics['issues']:
                            f.write(f"    - {issue}\n")
                        f.write(f"  Recommendations:\n")
                        for rec in metrics['recommendations']:
                            f.write(f"    - {rec}\n")
                    f.write("\n")

            # 全ファイルのスコア一覧
            f.write("\n【全ファイルのスコア一覧】\n")
            f.write("="*80 + "\n")
            f.write(f"{'File':<50} | {'Quality':<10} | {'Uniqueness':>10} | Priority\n")
            f.write("-"*80 + "\n")

            sorted_results = sorted(
                [r for r in self.results if r["metrics"]],
                key=lambda x: x["metrics"]["uniqueness_score"],
                reverse=True
            )

            for r in sorted_results:
                metrics = r["metrics"]
                f.write(f"{metrics['file_name'][:50]:<50} | "
                       f"{metrics['quality_level']:<10} | "
                       f"{metrics['uniqueness_score']:>10.3f} | "
                       f"{metrics['improvement_priority']}\n")

        print(f"[OK] Improvement recommendations: {improvement_path}")


def main():
    folder_path = Path(
        r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes\01_講義\T2Sセミナー"
    )

    scorer = UniquenessScorer()
    scorer.scan_folder(folder_path)
    scorer.generate_detailed_report(folder_path)

    print("\n" + "="*80)
    print("Analysis Complete!")


if __name__ == "__main__":
    main()
