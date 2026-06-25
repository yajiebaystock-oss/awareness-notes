#!/usr/bin/env python3
"""
Awareness.co.jp Brightcove 動画抽出 & MP3 変換スクリプト
段階的フォールバック機構付き

使用方法:
    python3 extract_and_convert.py <URL> [--output <filename>] [--format <mp3|m4a|opus>]

例:
    python3 extract_and_convert.py "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"
    python3 extract_and_convert.py "https://www.awareness.co.jp/..." --output my_video.mp3 --format mp3

依存ツール:
    - requests (pip install requests)
    - yt-dlp (pip install yt-dlp または brew install yt-dlp)
"""

import os
import re
import json
import sys
import argparse
import requests
import subprocess
from typing import Optional, Dict
from pathlib import Path
import logging
from datetime import datetime

# ==========================================
# ロギング設定
# ==========================================

class ColoredFormatter(logging.Formatter):
    """カラー出力対応ロギングフォーマッター"""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
    }
    RESET = '\033[0m'

    def format(self, record):
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


# ログハンドラ設定
handler = logging.StreamHandler()
formatter = ColoredFormatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


# ==========================================
# Brightcove MP3 コンバーター
# ==========================================

class BrightcoveMP3Converter:
    """Brightcove 動画 → MP3 変換マネージャー"""

    def __init__(self, verbose: bool = False):
        """
        初期化

        Args:
            verbose: 詳細ログを出力するかどうか
        """
        if verbose:
            logger.setLevel(logging.DEBUG)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Brightcove 定数
        self.BRIGHTCOVE_ACCOUNT = "6054371505001"
        self.BRIGHTCOVE_API = "https://edge.api.brightcove.com/playback/v1/accounts"

    # ==========================================
    # 方法1: HTML パース（最速）
    # ==========================================

    def extract_video_id_from_html(self, url: str) -> Optional[str]:
        """
        ページ HTML から videoId を抽出

        Args:
            url: awareness.co.jp ページ URL

        Returns:
            videoId (例: "6398801618112") または None
        """
        try:
            logger.info(f"[方法1] HTML パース開始")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # videoId 抽出パターン
            patterns = [
                r'data-video-id=["\'](\d+)["\']',
                r'"videoId"\s*:\s*["\'](\d+)["\']',
                r'bc-video-id=["\'](\d+)["\']',
            ]

            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    video_id = match.group(1)
                    logger.info(f"✓ videoId 抽出成功: {video_id}")
                    return video_id

            logger.warning("HTML から videoId を抽出できませんでした")
            return None

        except requests.exceptions.Timeout:
            logger.error("タイムアウト: ページの読み込みが時間切れになりました")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("接続エラー: インターネット接続を確認してください")
            return None
        except Exception as e:
            logger.error(f"HTML パース失敗: {e}")
            return None

    def extract_title_from_html(self, url: str) -> Optional[str]:
        """
        ページ HTML からタイトルを抽出

        Args:
            url: awareness.co.jp ページ URL

        Returns:
            タイトルテキスト或いは None
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # og:title メタタグ
            match = re.search(r'<meta\s+property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', response.text)
            if match:
                return match.group(1).strip()

            # title タグ
            match = re.search(r'<title>([^<]+)</title>', response.text)
            if match:
                return match.group(1).strip()

            # h1 要素
            match = re.search(r'<h1[^>]*>([^<]+)</h1>', response.text)
            if match:
                return match.group(1).strip()

            return None

        except Exception as e:
            logger.debug(f"タイトル抽出失敗: {e}")
            return None

    # ==========================================
    # MP4 URL 取得（API 経由）
    # ==========================================

    def get_mp4_url(self, video_id: str) -> Optional[str]:
        """
        Brightcove Playback API から MP4 URL を取得

        Args:
            video_id: Brightcove Video ID

        Returns:
            MP4 URL 或いは None
        """
        try:
            logger.debug(f"Brightcove API から MP4 URL 取得中: {video_id}")

            url = f"{self.BRIGHTCOVE_API}/{self.BRIGHTCOVE_ACCOUNT}/videos/{video_id}"

            self.session.headers.update({
                'Referer': 'https://www.awareness.co.jp/'
            })

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # MP4 URL を検索
            for source in data.get('sources', []):
                if source.get('container') == 'video/mp4':
                    mp4_url = source.get('src')
                    logger.debug(f"✓ MP4 URL 取得成功")
                    return mp4_url

            # フォールバック: HLS
            for source in data.get('sources', []):
                if source.get('container') == 'application/x-mpegURL':
                    hls_url = source.get('src')
                    logger.debug(f"HLS URL を使用します")
                    return hls_url

            logger.warning("MP4 / HLS URL が見つかりません")
            return None

        except Exception as e:
            logger.debug(f"Brightcove API エラー: {e}")
            return None

    # ==========================================
    # 方法2: yt-dlp（堅牢性重視）
    # ==========================================

    def download_with_ytdlp(
        self,
        url: str,
        output_file: str,
        output_format: str = "mp3"
    ) -> Optional[Dict]:
        """
        yt-dlp で動画をダウンロード＆変換

        Args:
            url: 動画 URL
            output_file: 出力ファイルパス
            output_format: 出力形式 (mp3, m4a, opus)

        Returns:
            変換結果情報 或いは None
        """
        try:
            logger.info(f"[方法2] yt-dlp 実行開始")

            # yt-dlp コマンド構築
            cmd = [
                "yt-dlp",
                "-f", "bestaudio",  # 最高品質オーディオ
                "-x",  # 音声抽出
                "--audio-format", output_format,
                "-o", output_file,
                "-j",  # JSON メタデータ出力
                "--quiet",
                url
            ]

            logger.debug(f"実行コマンド: {' '.join(cmd[:6])}...")

            # yt-dlp 実行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分タイムアウト
            )

            if result.returncode != 0:
                logger.error(f"yt-dlp エラー: {result.stderr[:200]}")
                return None

            # メタデータ解析
            try:
                metadata = json.loads(result.stdout)
                logger.info(f"✓ ダウンロード & 変換成功")
                logger.info(f"  タイトル: {metadata.get('title', 'Unknown')}")
                logger.info(f"  ファイル: {output_file}")

                return {
                    'title': metadata.get('title', 'Unknown'),
                    'duration': metadata.get('duration', 0),
                    'file': output_file,
                    'format': output_format,
                    'success': True,
                    'method': 'yt-dlp'
                }
            except json.JSONDecodeError:
                # JSON パース失敗時も成功とみなす
                logger.info(f"✓ ダウンロード & 変換完了: {output_file}")
                return {
                    'file': output_file,
                    'format': output_format,
                    'success': True,
                    'method': 'yt-dlp'
                }

        except subprocess.TimeoutExpired:
            logger.error("yt-dlp タイムアウト（ダウンロード中）")
            return None
        except FileNotFoundError:
            logger.error("yt-dlp がインストールされていません")
            logger.info("インストール方法:")
            logger.info("  macOS: brew install yt-dlp")
            logger.info("  Windows: pip install yt-dlp")
            logger.info("  Linux: sudo apt-get install yt-dlp")
            return None
        except Exception as e:
            logger.error(f"yt-dlp エラー: {e}")
            return None

    # ==========================================
    # 方法3: curl + ffmpeg（代替）
    # ==========================================

    def download_with_curl_ffmpeg(
        self,
        video_id: str,
        output_file: str = "video.mp3"
    ) -> Optional[Dict]:
        """
        curl で MP4 ダウンロード後、ffmpeg で変換

        Args:
            video_id: Brightcove Video ID
            output_file: 出力ファイルパス

        Returns:
            変換結果情報 或いは None
        """
        try:
            logger.info(f"[方法3] curl + ffmpeg 実行開始")

            # MP4 URL 取得
            mp4_url = self.get_mp4_url(video_id)
            if not mp4_url:
                logger.error("MP4 URL を取得できませんでした")
                return None

            # 一時ファイル
            temp_mp4 = ".temp_video.mp4"

            # curl でダウンロード
            logger.info("curl で動画ダウンロード中...")
            curl_cmd = [
                "curl",
                "-L",
                "-o", temp_mp4,
                "--progress-bar",
                mp4_url
            ]

            result = subprocess.run(curl_cmd, timeout=600)
            if result.returncode != 0:
                logger.error("curl ダウンロード失敗")
                return None

            logger.info(f"✓ ダウンロード完了")

            # ffmpeg で変換
            logger.info("ffmpeg で変換中...")
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", temp_mp4,
                "-q:a", "0",
                "-map", "a",
                output_file,
                "-loglevel", "quiet"  # 静か実行
            ]

            result = subprocess.run(ffmpeg_cmd, capture_output=True)
            if result.returncode != 0:
                logger.error(f"ffmpeg エラー: {result.stderr.decode()[:200]}")
                if os.path.exists(temp_mp4):
                    os.remove(temp_mp4)
                return None

            logger.info(f"✓ 変換完了: {output_file}")

            # 一時ファイル削除
            if os.path.exists(temp_mp4):
                os.remove(temp_mp4)
                logger.debug("一時ファイル削除")

            return {
                'file': output_file,
                'format': 'mp3',
                'success': True,
                'method': 'curl+ffmpeg'
            }

        except FileNotFoundError as e:
            logger.error(f"必要なツールがインストールされていません: {e}")
            logger.info("インストール方法:")
            logger.info("  macOS: brew install curl ffmpeg")
            logger.info("  Windows: choco install curl ffmpeg")
            logger.info("  Linux: sudo apt-get install curl ffmpeg")
            return None
        except Exception as e:
            logger.error(f"エラー: {e}")
            return None

    # ==========================================
    # 統合メソッド（自動フォールバック）
    # ==========================================

    def convert_to_mp3(
        self,
        url: str,
        output_file: Optional[str] = None,
        output_format: str = "mp3"
    ) -> Optional[Dict]:
        """
        URL から MP3 へ自動変換（段階的フォールバック）

        Args:
            url: 動画 URL
            output_file: 出力ファイルパス（未指定時は自動生成）
            output_format: 出力形式 (mp3, m4a, opus)

        Returns:
            変換結果情報 或いは None
        """
        logger.info("\n" + "="*70)
        logger.info("Brightcove 動画 MP3 変換開始")
        logger.info("="*70)
        logger.info(f"URL: {url}")

        # 出力ファイル名の自動生成
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"video_{timestamp}.{output_format}"
            logger.info(f"出力ファイル: {output_file} (自動生成)")
        else:
            logger.info(f"出力ファイル: {output_file}")

        # 段階1: HTML パース & yt-dlp（最速・最堅牢）
        logger.info("\n" + "-"*70)
        logger.info("[段階1] HTML パース & yt-dlp")
        logger.info("-"*70)

        # タイトル抽出
        title = self.extract_title_from_html(url)
        if title:
            logger.info(f"タイトル: {title}")

        # VideoId 抽出
        video_id = self.extract_video_id_from_html(url)
        if video_id:
            # yt-dlp で直接 MP3 変換
            result = self.download_with_ytdlp(url, output_file, output_format)
            if result:
                logger.info("\n" + "="*70)
                logger.info("✅ 変換成功（yt-dlp 経由）")
                logger.info("="*70)
                return result

        # 段階2: curl + ffmpeg（フォールバック）
        if video_id:
            logger.info("\n" + "-"*70)
            logger.info("[段階2] curl + ffmpeg フォールバック")
            logger.info("-"*70)

            result = self.download_with_curl_ffmpeg(video_id, output_file)
            if result:
                logger.info("\n" + "="*70)
                logger.info("✅ 変換成功（curl + ffmpeg 経由）")
                logger.info("="*70)
                return result

        logger.info("\n" + "="*70)
        logger.error("❌ すべての方法が失敗しました")
        logger.error("トラブルシューティング:")
        logger.error("  1. URL が正しいか確認")
        logger.error("  2. インターネット接続を確認")
        logger.error("  3. yt-dlp が最新版か確認: yt-dlp --version")
        logger.info("="*70)
        return None


# ==========================================
# CLI インターフェース
# ==========================================

def main():
    """メインエントリーポイント"""

    parser = argparse.ArgumentParser(
        description="Awareness.co.jp Brightcove 動画 MP3 変換スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python3 extract_and_convert.py "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"
  python3 extract_and_convert.py <URL> --output timing_principle.mp3
  python3 extract_and_convert.py <URL> --format m4a --output output.m4a
  python3 extract_and_convert.py <URL> -v  # 詳細ログ出力
        """
    )

    parser.add_argument(
        "url",
        help="動画 URL"
    )
    parser.add_argument(
        "-o", "--output",
        help="出力ファイル名 (デフォルト: video_YYYYMMDDhhmmss.{format})",
        default=None
    )
    parser.add_argument(
        "-f", "--format",
        choices=["mp3", "m4a", "opus"],
        default="mp3",
        help="出力形式 (デフォルト: mp3)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="詳細ログを出力"
    )

    args = parser.parse_args()

    # コンバーター初期化
    converter = BrightcoveMP3Converter(verbose=args.verbose)

    # 変換実行
    result = converter.convert_to_mp3(
        url=args.url,
        output_file=args.output,
        output_format=args.format
    )

    # 結果出力
    if result and result.get('success'):
        print(f"\n✅ 完了")
        print(f"   ファイル: {result.get('file')}")
        print(f"   形式: {result.get('format')}")
        print(f"   方法: {result.get('method')}")
        if 'title' in result:
            print(f"   タイトル: {result.get('title')}")
        if 'duration' in result and result.get('duration'):
            minutes = int(result.get('duration') // 60)
            seconds = int(result.get('duration') % 60)
            print(f"   継続時間: {minutes}:{seconds:02d}")

        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
