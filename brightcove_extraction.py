#!/usr/bin/env python3
"""
Awareness.co.jp Brightcove 動画情報抽出スクリプト
3段階アプローチ：HTML → yt-dlp → Playwright
"""

import os
import re
import json
import requests
import subprocess
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse
from pathlib import Path
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BrightcoveExtractor:
    """Brightcove 動画抽出マネージャー"""

    def __init__(self, session_cookies: Optional[Dict] = None):
        """
        初期化

        Args:
            session_cookies: awareness.co.jp のセッションクッキー
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # セッションクッキー設定（認証済みセッション用）
        if session_cookies:
            self.session.cookies.update(session_cookies)

        # Brightcove API 定数
        self.BRIGHTCOVE_ACCOUNT = "6054371505001"  # awareness.co.jp の Account ID
        self.BRIGHTCOVE_API = "https://edge.api.brightcove.com/playback/v1/accounts"

    # ==========================================
    # 方法1: HTML パース（第1選択肢）
    # ==========================================

    def extract_from_html(self, url: str) -> Optional[Dict]:
        """
        ページ HTML から videoId とメタデータを抽出

        Args:
            url: awareness.co.jp ページ URL

        Returns:
            {
                'video_id': str,
                'title': str,
                'mp4_url': str,
                'method': 'html_parse'
            }
        """
        try:
            logger.info(f"[方法1] HTML パース開始: {url}")

            # ページ取得
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # videoId 抽出（複数パターンに対応）
            video_id = self._extract_video_id_from_html(response.text)
            if not video_id:
                logger.warning("HTML から videoId を抽出できませんでした")
                return None

            logger.info(f"✓ videoId 抽出成功: {video_id}")

            # タイトル抽出
            title = self._extract_title_from_html(response.text)
            logger.info(f"✓ タイトル: {title}")

            # MP4 URL 取得（Brightcove API 経由）
            mp4_url = self.get_mp4_url(video_id)
            if not mp4_url:
                logger.warning("MP4 URL を取得できませんでした")
                return None

            logger.info(f"✓ MP4 URL 取得成功")

            return {
                'video_id': video_id,
                'title': title,
                'mp4_url': mp4_url,
                'method': 'html_parse',
                'source_url': url
            }

        except Exception as e:
            logger.error(f"HTML パース失敗: {e}")
            return None

    def _extract_video_id_from_html(self, html: str) -> Optional[str]:
        """
        HTML から videoId を抽出

        対応パターン：
        - data-video-id="6398801618112"
        - "videoId": "6398801618112"
        - bc-video-id="..."
        """
        patterns = [
            r'data-video-id=["\'](\d+)["\']',
            r'"videoId"\s*:\s*["\'](\d+)["\']',
            r'bc-video-id=["\'](\d+)["\']',
            r'<video[^>]*data-video-id=["\'](\d+)["\']',
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)

        return None

    def _extract_title_from_html(self, html: str) -> str:
        """
        HTML から動画タイトルを抽出

        優先順：
        1. og:title メタタグ
        2. <title> タグ
        3. h1 要素
        """
        # og:title
        match = re.search(r'<meta\s+property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', html)
        if match:
            return match.group(1).strip()

        # title タグ
        match = re.search(r'<title>([^<]+)</title>', html)
        if match:
            return match.group(1).strip()

        # h1 要素
        match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        if match:
            return match.group(1).strip()

        return "Unknown Title"

    # ==========================================
    # Brightcove API: MP4 URL 取得（共通）
    # ==========================================

    def get_mp4_url(self, video_id: str) -> Optional[str]:
        """
        Brightcove Playback API から MP4 URL を取得

        API: https://edge.api.brightcove.com/playback/v1/accounts/{account}/videos/{videoId}

        Args:
            video_id: Brightcove Video ID

        Returns:
            MP4 URL（有効期限付き）
        """
        try:
            url = f"{self.BRIGHTCOVE_API}/{self.BRIGHTCOVE_ACCOUNT}/videos/{video_id}"

            # API リクエスト（Referer ヘッダー必須）
            self.session.headers.update({
                'Referer': 'https://www.awareness.co.jp/'
            })

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # sources から MP4 URL を検索
            if 'sources' not in data:
                logger.warning(f"Response に sources がありません: {data}")
                return None

            for source in data.get('sources', []):
                if source.get('container') == 'video/mp4':
                    mp4_url = source.get('src')
                    logger.info(f"✓ MP4 URL 取得: {mp4_url[:80]}...")
                    return mp4_url

            # MP4 が無い場合は HLS URL を返す（フォールバック）
            for source in data.get('sources', []):
                if source.get('container') == 'application/x-mpegURL':
                    hls_url = source.get('src')
                    logger.warning(f"MP4 URL が見つかりません。HLS URL を使用します")
                    return hls_url

            logger.error("MP4 / HLS URL が見つかりません")
            return None

        except Exception as e:
            logger.error(f"Brightcove API エラー: {e}")
            return None

    # ==========================================
    # 方法2: yt-dlp（第2選択肢）
    # ==========================================

    def extract_with_ytdlp(self, video_id: str, output_path: str = "videos") -> Optional[Dict]:
        """
        yt-dlp を使用して動画ダウンロード＆情報抽出

        Args:
            video_id: Brightcove Video ID
            output_path: ダウンロード先ディレクトリ

        Returns:
            {
                'video_id': str,
                'title': str,
                'mp4_url': str,
                'local_path': str,
                'method': 'ytdlp'
            }
        """
        try:
            logger.info(f"[方法2] yt-dlp 実行開始: {video_id}")

            # yt-dlp URL 構築
            # Brightcove プレイヤー埋め込みURL
            brightcove_url = (
                f"https://players.brightcove.net/{self.BRIGHTCOVE_ACCOUNT}/"
                f"hNf2KNmT85_default/index.html?videoId={video_id}"
            )

            # ダウンロードディレクトリ作成
            Path(output_path).mkdir(parents=True, exist_ok=True)

            # yt-dlp コマンド
            output_template = os.path.join(output_path, "%(title)s.%(ext)s")

            cmd = [
                "yt-dlp",
                "--quiet",  # 静か実行
                "-f", "best[ext=mp4]",  # 最高品質 MP4
                "-o", output_template,
                "-j",  # JSON 出力（メタデータ）
                brightcove_url
            ]

            logger.info(f"実行コマンド: {' '.join(cmd[:5])}...")

            # yt-dlp 実行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分タイムアウト
            )

            if result.returncode != 0:
                logger.error(f"yt-dlp エラー: {result.stderr}")
                return None

            # JSON メタデータ解析
            metadata = json.loads(result.stdout)

            logger.info(f"✓ ダウンロード成功")
            logger.info(f"✓ タイトル: {metadata.get('title')}")
            logger.info(f"✓ ファイル: {metadata.get('filename')}")

            return {
                'video_id': video_id,
                'title': metadata.get('title', 'Unknown'),
                'mp4_url': metadata.get('url', ''),
                'local_path': metadata.get('filename', ''),
                'duration': metadata.get('duration', 0),
                'method': 'ytdlp'
            }

        except subprocess.TimeoutExpired:
            logger.error("yt-dlp タイムアウト（ダウンロード中）")
            return None
        except Exception as e:
            logger.error(f"yt-dlp エラー: {e}")
            return None

    # ==========================================
    # 方法3: Playwright（第3選択肢）
    # ==========================================

    def extract_with_playwright(self, url: str) -> Optional[Dict]:
        """
        Playwright でページレンダリング後に情報抽出

        Args:
            url: awareness.co.jp ページ URL

        Returns:
            {
                'video_id': str,
                'title': str,
                'mp4_url': str,
                'method': 'playwright'
            }
        """
        try:
            from playwright.sync_api import sync_playwright

            logger.info(f"[方法3] Playwright 実行開始: {url}")

            with sync_playwright() as p:
                # ブラウザ起動
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # セッションクッキー設定
                if self.session.cookies:
                    for cookie in self.session.cookies:
                        page.context.add_cookies([{
                            'name': cookie.name,
                            'value': cookie.value,
                            'url': 'https://www.awareness.co.jp'
                        }])

                # ページロード
                page.goto(url, wait_until='networkidle')
                logger.info("✓ ページロード完了")

                # videoId 抽出（data 属性）
                video_id = page.evaluate(
                    """() => {
                        const video = document.querySelector('[data-video-id]');
                        return video ? video.getAttribute('data-video-id') : null;
                    }"""
                )

                if not video_id:
                    logger.warning("Playwright で videoId を抽出できませんでした")
                    browser.close()
                    return None

                logger.info(f"✓ videoId 抽出: {video_id}")

                # タイトル抽出
                title = page.evaluate(
                    """() => {
                        return document.querySelector('h1')?.textContent
                            || document.title
                            || 'Unknown';
                    }"""
                )

                logger.info(f"✓ タイトル: {title}")

                # MP4 URL 取得（API 経由）
                mp4_url = self.get_mp4_url(video_id)

                browser.close()

                if not mp4_url:
                    logger.warning("MP4 URL を取得できませんでした")
                    return None

                return {
                    'video_id': video_id,
                    'title': title,
                    'mp4_url': mp4_url,
                    'method': 'playwright',
                    'source_url': url
                }

        except ImportError:
            logger.error("Playwright がインストールされていません: pip install playwright")
            return None
        except Exception as e:
            logger.error(f"Playwright エラー: {e}")
            return None

    # ==========================================
    # 統合メソッド（自動フォールバック）
    # ==========================================

    def extract(self, url: str, video_id: Optional[str] = None) -> Optional[Dict]:
        """
        統合抽出メソッド（3段階フォールバック機構）

        優先順：
        1. HTML パース（最速）
        2. yt-dlp（堅牢性重視）
        3. Playwright（最後の手段）

        Args:
            url: awareness.co.jp ページ URL
            video_id: 既知の場合は Video ID を指定

        Returns:
            抽出結果 or None
        """
        # 方法1: HTML パース
        logger.info("\n" + "="*60)
        logger.info("段階1: HTML パース (最速)")
        logger.info("="*60)
        result = self.extract_from_html(url)
        if result:
            return result

        # HTML パースで videoId 取得できたか確認
        if not video_id:
            try:
                response = self.session.get(url, timeout=10)
                video_id = self._extract_video_id_from_html(response.text)
            except:
                pass

        # 方法2: yt-dlp
        if video_id:
            logger.info("\n" + "="*60)
            logger.info("段階2: yt-dlp フォールバック (堅牢性重視)")
            logger.info("="*60)
            result = self.extract_with_ytdlp(video_id)
            if result:
                return result

        # 方法3: Playwright
        logger.info("\n" + "="*60)
        logger.info("段階3: Playwright フォールバック (最後の手段)")
        logger.info("="*60)
        result = self.extract_with_playwright(url)
        if result:
            return result

        logger.error("すべての方法が失敗しました")
        return None


# ==========================================
# 使用例
# ==========================================

if __name__ == "__main__":
    # セッションクッキー（事前に取得・保存したもの）
    session_cookies = {
        # 'session_id': 'xxxxx...',
        # 他のクッキー
    }

    # 抽出器初期化
    extractor = BrightcoveExtractor(session_cookies=session_cookies)

    # 例1: URL から抽出（HTML パース → yt-dlp → Playwright）
    url = "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"

    result = extractor.extract(url)

    if result:
        print("\n✅ 抽出成功")
        print(f"  Video ID: {result['video_id']}")
        print(f"  タイトル: {result['title']}")
        print(f"  MP4 URL: {result['mp4_url'][:80]}...")
        print(f"  方法: {result['method']}")
    else:
        print("\n❌ 抽出失敗")

    # 例2: Video ID が既知の場合（yt-dlp 直接実行）
    # result = extractor.extract_with_ytdlp("6398801618112")

    # 例3: MP4 URL のみ取得（API 利用）
    # mp4_url = extractor.get_mp4_url("6398801618112")
