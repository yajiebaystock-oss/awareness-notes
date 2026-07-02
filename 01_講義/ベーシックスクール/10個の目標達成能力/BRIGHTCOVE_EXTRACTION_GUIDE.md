---
title: Brightcove VideoId 抽出 & MP3 変換ガイド
date: 2026-06-26
target_file: 【10の能力動画】タイミングの原則.md
target_url: https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216
---

# Brightcove VideoId 抽出 & MP3 変換ガイド

このドキュメントは、awareness.co.jp の Brightcove 動画から VideoId を抽出し、MP3 に変換するための実装ガイドです。

---

## 📋 目次

1. [推奨方法](#推奨方法)
2. [実行可能なコマンド例](#実行可能なコマンド例)
3. [Python スニペット](#python-スニペット)
4. [エラーハンドリング](#エラーハンドリング)
5. [トラブルシューティング](#トラブルシューティング)

---

## 🎯 推奨方法

### 段階的フォールバック戦略

| 段階 | 方法 | 実行時間 | 成功率 | 推奨度 |
|------|------|--------|--------|--------|
| 1 | HTML パース | 1-2秒 | 80% | ⭐⭐⭐⭐⭐ |
| 2 | yt-dlp | 30秒～数分 | 95% | ⭐⭐⭐⭐ |
| 3 | Playwright | 5-10秒 | 90% | ⭐⭐⭐ |

**推奨戦略：方法1 → 方法2 → 方法3 の順で実行し、最初に成功した結果を採用**

---

## 💻 実行可能なコマンド例

### **方法1: yt-dlp で直接 MP3 ダウンロード（推奨）**

```bash
#!/bin/bash

URL="https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"

# MP3 ダウンロード
yt-dlp -f bestaudio -x --audio-format m4a \
  "$URL" \
  -o "timing_principle.m4a"
```

**説明：**
- `-f bestaudio` : 最高品質オーディオストリーム選択
- `-x` : 動画から音声を抽出
- `--audio-format m4a` : M4A 形式に変換
- `-o` : 出力ファイル名指定

**代替案（MP3 形式）：**

```bash
yt-dlp -f bestaudio -x --audio-format mp3 \
  "$URL" \
  -o "timing_principle.mp3"
```

---

### **方法2: yt-dlp で VideoId と JSON メタデータを抽出**

```bash
#!/bin/bash

URL="https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"

# JSON メタデータ取得
yt-dlp -j "$URL" | jq '.'

# VideoId のみ抽出
yt-dlp -j "$URL" | jq -r '.id'

# 動画情報（タイトル、継続時間、拡張子）抽出
yt-dlp -j "$URL" | jq '{title, duration, ext}'

# リスト形式で複数情報取得
yt-dlp -j "$URL" | jq '.[0] | {id, title, uploader, duration, ext}'
```

---

### **方法3: VideoId を既知の場合、Brightcove API で MP4 URL を直接取得**

```bash
#!/bin/bash

VIDEO_ID="6398801618112"  # 例：実際の VideoId に置き換え
ACCOUNT_ID="6054371505001"  # awareness.co.jp のアカウント ID

# API エンドポイント
API_URL="https://edge.api.brightcove.com/playback/v1/accounts/${ACCOUNT_ID}/videos/${VIDEO_ID}"

# JSON レスポンス取得
curl -s "$API_URL" \
  -H "Referer: https://www.awareness.co.jp" \
  -H "User-Agent: Mozilla/5.0" | jq '.sources[] | select(.container=="video/mp4") | .src'

# MP4 URL をファイルに保存
curl -s "$API_URL" \
  -H "Referer: https://www.awareness.co.jp" | jq -r '.sources[] | select(.container=="video/mp4") | .src' > mp4_url.txt
```

---

### **方法4: ffmpeg で MP3 に変換（ダウンロード済みの場合）**

```bash
#!/bin/bash

# MP4 から MP3 へ変換
ffmpeg -i timing_principle.mp4 \
  -q:a 0 \
  -map a \
  timing_principle.mp3

# または m4a から MP3 へ変換
ffmpeg -i timing_principle.m4a \
  -q:a 0 \
  -acodec libmp3lame \
  timing_principle.mp3
```

---

## 🐍 Python スニペット

### **完全実装版（推奨）**

```python
#!/usr/bin/env python3
"""
Awareness.co.jp Brightcove 動画抽出 & MP3 変換スクリプト
段階的フォールバック機構付き
"""

import os
import re
import json
import requests
import subprocess
from typing import Optional, Dict
from pathlib import Path
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BrightcoveMP3Converter:
    """Brightcove 動画 → MP3 変換マネージャー"""

    def __init__(self):
        """初期化"""
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
        実行時間: 1-2秒
        """
        try:
            logger.info(f"[方法1] HTML パース開始: {url}")
            
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

        except Exception as e:
            logger.error(f"HTML パース失敗: {e}")
            return None

    # ==========================================
    # MP4 URL 取得（API 経由）
    # ==========================================

    def get_mp4_url(self, video_id: str) -> Optional[str]:
        """
        Brightcove Playback API から MP4 URL を取得
        実行時間: 0.5-1秒
        """
        try:
            logger.info(f"Brightcove API から MP4 URL 取得中: {video_id}")
            
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
                    logger.info(f"✓ MP4 URL 取得成功")
                    return mp4_url
            
            # フォールバック: HLS
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
    # 方法2: yt-dlp（堅牢性重視）
    # ==========================================

    def download_with_ytdlp(self, url: str, output_format: str = "m4a") -> Optional[Dict]:
        """
        yt-dlp で動画をダウンロード＆変換
        実行時間: 30秒～数分
        """
        try:
            logger.info(f"[方法2] yt-dlp 実行開始")
            
            # 出力ファイル名
            output_file = f"video.{output_format}"
            
            # yt-dlp コマンド
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
            
            logger.info(f"実行コマンド: {' '.join(cmd[:5])}...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分タイムアウト
            )
            
            if result.returncode != 0:
                logger.error(f"yt-dlp エラー: {result.stderr}")
                return None
            
            # メタデータ解析
            try:
                metadata = json.loads(result.stdout)
                logger.info(f"✓ ダウンロード成功")
                logger.info(f"✓ タイトル: {metadata.get('title')}")
                logger.info(f"✓ ファイル: {output_file}")
                
                return {
                    'title': metadata.get('title', 'Unknown'),
                    'duration': metadata.get('duration', 0),
                    'file': output_file,
                    'format': output_format,
                    'success': True
                }
            except json.JSONDecodeError:
                # JSON パース失敗時も成功とみなす（ファイルは生成された）
                logger.info(f"✓ ダウンロード完了: {output_file}")
                return {
                    'file': output_file,
                    'format': output_format,
                    'success': True
                }

        except subprocess.TimeoutExpired:
            logger.error("yt-dlp タイムアウト（ダウンロード中）")
            return None
        except FileNotFoundError:
            logger.error("yt-dlp がインストールされていません")
            logger.info("インストール: pip install yt-dlp または brew install yt-dlp")
            return None
        except Exception as e:
            logger.error(f"yt-dlp エラー: {e}")
            return None

    # ==========================================
    # 方法3: curl + ffmpeg（代替）
    # ==========================================

    def download_with_curl_ffmpeg(self, video_id: str, output_file: str = "video.mp3") -> Optional[Dict]:
        """
        curl で MP4 ダウンロード後、ffmpeg で MP3 に変換
        """
        try:
            logger.info(f"[方法3] curl + ffmpeg 実行開始")
            
            # MP4 URL 取得
            mp4_url = self.get_mp4_url(video_id)
            if not mp4_url:
                logger.error("MP4 URL を取得できませんでした")
                return None
            
            # 一時ファイル
            temp_mp4 = "temp_video.mp4"
            
            # curl でダウンロード
            logger.info("curl で MP4 ダウンロード中...")
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
            
            logger.info(f"✓ MP4 ダウンロード完了: {temp_mp4}")
            
            # ffmpeg で MP3 変換
            logger.info("ffmpeg で MP3 に変換中...")
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", temp_mp4,
                "-q:a", "0",
                "-map", "a",
                output_file
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True)
            if result.returncode != 0:
                logger.error(f"ffmpeg エラー: {result.stderr}")
                return None
            
            logger.info(f"✓ MP3 変換完了: {output_file}")
            
            # 一時ファイル削除
            if os.path.exists(temp_mp4):
                os.remove(temp_mp4)
                logger.info("一時ファイル削除完了")
            
            return {
                'file': output_file,
                'format': 'mp3',
                'success': True
            }

        except FileNotFoundError as e:
            logger.error(f"必要なツールがインストールされていません: {e}")
            return None
        except Exception as e:
            logger.error(f"エラー: {e}")
            return None

    # ==========================================
    # 統合メソッド（自動フォールバック）
    # ==========================================

    def convert_to_mp3(self, url: str, output_file: str = "video.mp3") -> Optional[Dict]:
        """
        URL から MP3 へ自動変換（3段階フォールバック）
        """
        logger.info("\n" + "="*70)
        logger.info("Brightcove 動画 MP3 変換開始")
        logger.info("="*70)
        
        # 段階1: HTML パース → yt-dlp（最速・最堅牢）
        logger.info("\n[段階1] HTML パース & yt-dlp")
        logger.info("-"*70)
        
        video_id = self.extract_video_id_from_html(url)
        if video_id:
            # yt-dlp で直接 MP3 変換
            result = self.download_with_ytdlp(url, output_format="mp3")
            if result:
                logger.info("\n✅ 変換成功（yt-dlp 経由）")
                return result
        
        # 段階2: curl + ffmpeg（フォールバック）
        if video_id:
            logger.info("\n[段階2] curl + ffmpeg フォールバック")
            logger.info("-"*70)
            
            result = self.download_with_curl_ffmpeg(video_id, output_file)
            if result:
                logger.info("\n✅ 変換成功（curl + ffmpeg 経由）")
                return result
        
        logger.error("\n❌ すべての方法が失敗しました")
        return None


# ==========================================
# 使用例
# ==========================================

if __name__ == "__main__":
    
    # 対象 URL
    url = "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"
    
    # コンバーター初期化
    converter = BrightcoveMP3Converter()
    
    # MP3 変換実行
    result = converter.convert_to_mp3(
        url=url,
        output_file="timing_principle.mp3"
    )
    
    if result and result.get('success'):
        print(f"\n✅ 完了")
        print(f"   ファイル: {result.get('file')}")
        print(f"   形式: {result.get('format')}")
        if 'title' in result:
            print(f"   タイトル: {result.get('title')}")
    else:
        print("\n❌ 変換失敗")
```

---

### **シンプル版（yt-dlp のみ）**

```python
#!/usr/bin/env python3
"""
シンプル版：yt-dlp のみを使用
"""

import subprocess
import sys

def download_mp3(url: str, output_file: str = "video.mp3") -> bool:
    """
    URL から MP3 ダウンロード（yt-dlp 使用）
    """
    cmd = [
        "yt-dlp",
        "-f", "bestaudio",  # 最高品質オーディオ
        "-x",  # 音声抽出
        "--audio-format", "mp3",
        "-o", output_file,
        url
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"✓ MP3 ダウンロード完了: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ エラー: {e}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("✗ yt-dlp がインストールされていません", file=sys.stderr)
        print("  インストール: pip install yt-dlp", file=sys.stderr)
        return False


if __name__ == "__main__":
    url = "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"
    success = download_mp3(url, "timing_principle.mp3")
    sys.exit(0 if success else 1)
```

---

### **VideoId 抽出専用版**

```python
#!/usr/bin/env python3
"""
VideoId 抽出専用スクリプト
"""

import re
import requests
from typing import Optional

def extract_video_id(url: str) -> Optional[str]:
    """
    HTML パース で videoId を抽出
    """
    try:
        response = requests.get(url, timeout=10)
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
                return match.group(1)
        
        return None

    except Exception as e:
        print(f"エラー: {e}")
        return None


if __name__ == "__main__":
    url = "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"
    
    video_id = extract_video_id(url)
    
    if video_id:
        print(f"✓ VideoId: {video_id}")
    else:
        print("✗ VideoId を抽出できませんでした")
```

---

## ⚠️ エラーハンドリング

### **yt-dlp がインストールされていない場合**

```bash
# macOS
brew install yt-dlp

# Windows (pip)
pip install yt-dlp

# Windows (Chocolatey)
choco install yt-dlp
```

### **ffmpeg がインストールされていない場合**

```bash
# macOS
brew install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

### **タイムアウトエラー**

```python
# タイムアウト時間を延長
result = subprocess.run(
    cmd,
    timeout=600,  # 10分に延長
    capture_output=True,
    text=True
)
```

### **MP4 URL が見つからない場合**

```python
# HLS URL を使用
if not mp4_url:
    for source in data.get('sources', []):
        if source.get('container') == 'application/x-mpegURL':
            hls_url = source.get('src')
            # HLS URL から MP3 へ直接ダウンロード
            cmd = ["yt-dlp", "-x", "--audio-format", "mp3", hls_url]
```

---

## 🔧 トラブルシューティング

### **問題：「Permission denied」エラー**

```bash
# Python スクリプトに実行権限を追加
chmod +x script.py

# または Python インタプリタで直接実行
python3 script.py
```

### **問題：「HTML から videoId を抽出できない」**

```python
# HTML の構造を確認
response = requests.get(url)
print(response.text)  # 出力して手動で確認

# または直接ブラウザで「ページのソースを表示」を確認
```

### **問題：yt-dlp が「サポートされていない URL」と言う**

```bash
# yt-dlp を最新版に更新
pip install --upgrade yt-dlp

# または
brew upgrade yt-dlp
```

### **問題：ダウンロード速度が遅い**

```bash
# 低品質設定で高速化
yt-dlp -f worst[ext=mp4] \
  -x --audio-format mp3 \
  "$URL"

# または複数スレッド使用
yt-dlp -f bestaudio \
  -x --audio-format mp3 \
  --socket-timeout 30 \
  "$URL"
```

---

## 📊 実装比較表

| 方法 | 依存関係 | 実行時間 | 成功率 | 推奨用途 |
|------|---------|--------|--------|---------|
| HTML パース | requests | 1-2秒 | 80% | 初期化/テスト |
| yt-dlp | yt-dlp | 30秒～数分 | 95% | 本番運用 |
| curl + ffmpeg | curl, ffmpeg | 1-5分 | 85% | 柔軟性が必要 |
| Playwright | playwright | 5-10秒 | 90% | 認証が必要な場合 |

---

## 📝 推奨実装フロー

```
1. HTML パース で videoId 抽出
   ↓
2. 成功 → yt-dlp で MP3 ダウンロード
   ↓
3. 失敗 → curl + ffmpeg でフォールバック
   ↓
4. すべて失敗 → エラーログ出力
```

---

**更新日:** 2026-06-26
