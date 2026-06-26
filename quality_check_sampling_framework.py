#!/usr/bin/env python3
"""
【品質管理】サンプル点検フロー（月1回）

目的: 自動化チェックでは検出できない品質問題を
     月1回のサンプル点検で発見・改善

使用方法:
    python quality_check_sampling_framework.py

出力:
    - monthly_sampling_schedule.txt: 年間サンプル点検スケジュール
    - sampling_report_YYYY-MM.txt: 月別検証レポート
"""

import random
import json
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class SamplingFramework:
    """サンプル点検フレームワーク"""

    # サンプリング設定
    SAMPLE_SIZE_PER_MONTH = 5  # 月1回5ファイル
    SERIES_NAMES = ["10の能力動画", "スキマニT2S", "T2Sセミナー"]
    VERIFICATION_DIMENSIONS = [
        "タイトル固有性",
        "テンプレート検出",
        "実質性確認",
        "セクション構造",
        "具体例・事例",
    ]

    def __init__(self):
        self.current_date = datetime.now()

    def generate_annual_schedule(self) -> str:
        """年間サンプル点検スケジュール生成"""

        schedule = "【年間サンプル点検スケジュール】\n"
        schedule += "="*80 + "\n\n"

        schedule += "【目的】\n"
        schedule += "自動化チェックでは検出できない品質問題を発見・改善\n\n"

        schedule += "【ルール】\n"
        schedule += f"- 月1回、全ファイルからランダムに{self.SAMPLE_SIZE_PER_MONTH}ファイルを抽出\n"
        schedule += "- 3つのシリーズからバランス良くサンプリング\n"
        schedule += "- 検証担当者による目視確認\n"
        schedule += "- 問題検出時は即座に改善\n\n"

        schedule += "【月別スケジュール】\n"
        schedule += "-" * 80 + "\n"

        # 12ヶ月分のスケジュールを生成
        for month in range(1, 13):
            month_date = datetime(self.current_date.year, month, 1)
            month_str = month_date.strftime("%Y年%m月")

            schedule += f"\n【{month_str}】\n"
            schedule += f"  実施日: 毎月{15 if month % 2 == 1 else 28}日\n"
            schedule += f"  サンプル数: {self.SAMPLE_SIZE_PER_MONTH}ファイル\n"
            schedule += f"  内訳:\n"

            # シリーズごとのサンプル数
            for series in self.SERIES_NAMES:
                if series == "10の能力動画":
                    max_files = 12
                elif series == "スキマニT2S":
                    max_files = 18
                else:  # T2Sセミナー
                    max_files = 42

                sample_per_series = self.SAMPLE_SIZE_PER_MONTH // 3
                schedule += f"    - {series}: {sample_per_series}ファイル\n"

        return schedule

    def generate_verification_checklist(self) -> str:
        """検証チェックリスト生成"""

        checklist = "【サンプル点検 検証チェックリスト】\n"
        checklist += "="*80 + "\n\n"

        checklist += "【検証の5つの観点】\n\n"

        checks = {
            "1. タイトル固有性": [
                "タイトルの主要な概念が明確に説明されているか",
                "タイトル内の専門用語を含んでいるか",
                "タイトルと本文の内容が一致しているか",
            ],
            "2. テンプレート検出": [
                "「本セミナーでは...」などのテンプレート表現がないか",
                "定型句の繰り返しがないか",
                "自動生成的な構造になっていないか",
            ],
            "3. 実質性確認": [
                "プレースホルダーがないか",
                "具体的な知識・情報を含んでいるか",
                "実用的な内容であるか",
            ],
            "4. セクション構造": [
                "段階的な説明構造があるか",
                "理論→具体例→実践という流れがあるか",
                "読みやすく整理されているか",
            ],
            "5. 具体例・事例": [
                "実生活の具体例が含まれているか",
                "研究データや統計が含まれているか",
                "複数の視点からの説明があるか",
            ],
        }

        for dimension, items in checks.items():
            checklist += f"{dimension}\n"
            for item in items:
                checklist += f"  □ {item}\n"
            checklist += "\n"

        return checklist

    def generate_sampling_process(self) -> str:
        """サンプル点検プロセス生成"""

        process = "【月1回サンプル点検 実行プロセス】\n"
        process += "="*80 + "\n\n"

        steps = {
            "STEP 1: サンプル抽出": [
                "全72ファイルからランダムに5ファイルを抽出",
                "抽出方法: Python random.sample()を使用",
                "記録: 抽出日時・抽出ファイルリストを記録",
            ],
            "STEP 2: 詳細確認": [
                "チェックリストの5つの観点で検証",
                "各ファイルについて、5つの観点それぞれで評価",
                "問題箇所を記録",
            ],
            "STEP 3: 問題検出": [
                "3つ以上の観点で問題がないか確認",
                "問題がある場合、その内容を詳細に記録",
                "優先度を付与（Critical / High / Medium / Low）",
            ],
            "STEP 4: 改善対応": [
                "Critical / High 問題は即座に修正",
                "Medium 問題は翌月までに修正",
                "Low 問題は参考情報として蓄積",
            ],
            "STEP 5: レポート作成": [
                "点検レポートを作成・保存",
                "改善内容を記録",
                "次月への引き継ぎ事項をまとめる",
            ],
        }

        for step, details in steps.items():
            process += f"{step}\n"
            for detail in details:
                process += f"  • {detail}\n"
            process += "\n"

        return process

    def generate_implementation_guide(self) -> str:
        """実装ガイド生成"""

        guide = "【サンプル点検フロー 実装ガイド】\n"
        guide += "="*80 + "\n\n"

        guide += "【毎月の実行手順】\n\n"

        guide += "1. スケジュール確認\n"
        guide += "   月1回、指定日（毎月15日 or 28日）に実施\n\n"

        guide += "2. Pythonスクリプト実行\n"
        guide += "   $ python quality_check_sampling_framework.py\n\n"

        guide += "3. ランダムサンプル抽出\n"
        guide += "   全72ファイルから5ファイルを自動抽出\n\n"

        guide += "4. チェックリストに基づいて検証\n"
        guide += "   - タイトル固有性\n"
        guide += "   - テンプレート検出\n"
        guide += "   - 実質性確認\n"
        guide += "   - セクション構造\n"
        guide += "   - 具体例・事例\n\n"

        guide += "5. 問題があれば記録・改善\n"
        guide += "   Critical/High: 即座に修正\n"
        guide += "   Medium: 翌月までに修正\n"
        guide += "   Low: 参考情報として蓄積\n\n"

        guide += "6. レポート作成\n"
        guide += "   月別レポートをGit履歴に記録\n\n"

        guide += "【年間実績管理】\n\n"
        guide += "- 年間60ファイルをサンプル点検（12ヶ月 × 5ファイル）\n"
        guide += "- 全72ファイルの約83%を1年で検証\n"
        guide += "- 検出率: 自動チェック + 人間検証による二重チェック\n\n"

        return guide

    def generate_full_framework(self, output_path: Path) -> None:
        """完全なフレームワークを生成"""

        # 年間スケジュール
        schedule_text = self.generate_annual_schedule()
        schedule_path = output_path / "monthly_sampling_schedule.txt"
        with open(schedule_path, "w", encoding="utf-8") as f:
            f.write(schedule_text)

        # 検証チェックリスト
        checklist_text = self.generate_verification_checklist()
        checklist_path = output_path / "sampling_verification_checklist.txt"
        with open(checklist_path, "w", encoding="utf-8") as f:
            f.write(checklist_text)

        # プロセス
        process_text = self.generate_sampling_process()
        process_path = output_path / "sampling_process.txt"
        with open(process_path, "w", encoding="utf-8") as f:
            f.write(process_text)

        # 実装ガイド
        guide_text = self.generate_implementation_guide()
        guide_path = output_path / "sampling_implementation_guide.txt"
        with open(guide_path, "w", encoding="utf-8") as f:
            f.write(guide_text)

        print("[OK] Sampling framework documents generated:")
        print(f"  - {schedule_path}")
        print(f"  - {checklist_path}")
        print(f"  - {process_path}")
        print(f"  - {guide_path}")

    def generate_current_month_sampling(self, output_path: Path) -> None:
        """当月のサンプル抽出実施"""

        # ファイルパス定義
        files = []

        # 10の能力動画（12ファイル）
        ability_folder = Path(
            r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes\01_講義\10の能力動画"
        )
        if ability_folder.exists():
            files.extend([f for f in ability_folder.glob("*.md") if f.is_file()])

        # スキマニT2S（18ファイル）
        skimani_folder = Path(
            r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes\01_講義\スキマニT2S"
        )
        if skimani_folder.exists():
            files.extend([f for f in skimani_folder.glob("*.md") if f.is_file()])

        # T2Sセミナー（42ファイル）
        t2s_folder = Path(
            r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes\01_講義\T2Sセミナー"
        )
        if t2s_folder.exists():
            files.extend(
                [f for f in t2s_folder.glob("*_42_*.md") if f.is_file()]
            )

        # ランダムに5ファイルを抽出
        if len(files) >= 5:
            sampled_files = random.sample(files, 5)

            # レポート生成
            month_str = self.current_date.strftime("%Y-%m")
            report_path = output_path / f"sampling_report_{month_str}.txt"

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"【当月サンプル点検レポート】\n")
                f.write(f"実施日: {self.current_date.strftime('%Y年%m月%d日')}\n")
                f.write(f"サンプル数: 5ファイル\n\n")

                f.write("【抽出されたサンプルファイル】\n")
                f.write("-" * 80 + "\n")

                for i, file in enumerate(sampled_files, 1):
                    f.write(f"\n{i}. {file.name}\n")
                    f.write(f"   Path: {file}\n")

                f.write("\n\n【検証チェックリスト】\n")
                f.write("-" * 80 + "\n")

                f.write("""
各ファイルについて、以下の5つの観点で検証してください：

1. タイトル固有性
   □ タイトルの主要な概念が明確に説明されているか
   □ タイトル内の専門用語を含んでいるか

2. テンプレート検出
   □ テンプレート表現がないか
   □ 定型句の繰り返しがないか

3. 実質性確認
   □ プレースホルダーがないか
   □ 具体的な知識を含んでいるか

4. セクション構造
   □ 段階的な説明構造があるか
   □ 読みやすく整理されているか

5. 具体例・事例
   □ 実生活の具体例が含まれているか
   □ 複数の視点からの説明があるか

【問題検出時の対応】
Critical/High 問題: 即座に修正
Medium 問題: 翌月までに修正
Low 問題: 参考情報として蓄積
""")

            print(f"[OK] Monthly sampling report: {report_path}")


def main():
    output_path = Path(
        r"C:\Users\yajim\OneDrive\デスクトップ\awareness-notes"
    )

    framework = SamplingFramework()

    print("Generating P3: Sampling Framework...\n")

    # 年間フレームワーク生成
    framework.generate_full_framework(output_path)

    # 当月のサンプル抽出
    print("\nGenerating current month sampling...")
    framework.generate_current_month_sampling(output_path)

    print("\n" + "="*80)
    print("[OK] P3: Sampling Framework is ready!")
    print("\nYou can run monthly sampling inspections:")
    print(f"  Monthly schedule: {output_path / 'monthly_sampling_schedule.txt'}")
    print(f"  Verification checklist: {output_path / 'sampling_verification_checklist.txt'}")


if __name__ == "__main__":
    main()
