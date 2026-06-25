# Awareness.co.jp Brightcove 動画抽出 実装ガイド

## 📋 目次

1. [推奨方法の選定](#推奨方法の選定)
2. [実装スニペット](#実装スニペット)
3. [Fallback 戦略](#fallback-戦略)
4. [エラーハンドリング](#エラーハンドリング)
5. [セッション管理](#セッション管理)
6. [パフォーマンス最適化](#パフォーマンス最適化)

---

## 🎯 推奨方法の選定

### **結論：方法1 → 方法2 → 方法3 の段階的フォールバック**

| 方法 | 推奨度 | 実行可能性 | 複雑度 | 堅牢性 | 用途 |
|------|--------|---------|--------|--------|------|
| **方法1: HTML パース** | ⭐⭐⭐⭐⭐ | 5/5 | 1/5 | 2/5 | **第1選択肢** - 高速、シンプル |
| **方法2: yt-dlp** | ⭐⭐⭐⭐ | 5/5 | 2/5 | 5/5 | **第2選択肢** - 堅牢、既実装 |
| **方法3: Playwright** | ⭐⭐⭐ | 4/5 | 4/5 | 4/5 | **第3選択肢** - 最後の手段 |

---

## 💻 実装スニペット

### **方法1: HTML パース（推奨）**

```python
import re
import requests
from typing import Optional

def extract_video_id(url: str) -> Optional[str]:
    """
    HTML パースで videoId を抽出
    実行時間: 1-2秒
    """
    response = requests.get(url)
    html = response.text

    # パターンマッチ（複数対応）
    patterns = [
        r'data-video-id=["\'](\d+)["\']',
        r'"videoId"\s*:\s*["\'](\d+)["\']',
        r'bc-video-id=["\'](\d+)["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)

    return None


def get_mp4_url(video_id: str, referer: str) -> Optional[str]:
    """
    Brightcove Playback API から MP4 URL を取得
    実行時間: 0.5-1秒
    """
    url = f"https://edge.api.brightcove.com/playback/v1/accounts/6054371505001/videos/{video_id}"

    headers = {
        'Referer': referer,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # MP4 URL を検索
        for source in data.get('sources', []):
            if source.get('container') == 'video/mp4':
                return source.get('src')

        # フォールバック：HLS
        for source in data.get('sources', []):
            if source.get('container') == 'application/x-mpegURL':
                return source.get('src')

        return None

    except Exception as e:
        print(f"エラー: {e}")
        return None


# 使用例
video_id = extract_video_id("https://www.awareness.co.jp/mypage/...")
if video_id:
    mp4_url = get_mp4_url(video_id, "https://www.awareness.co.jp")
    print(f"MP4 URL: {mp4_url}")
```

**メリット:**
- 実行時間: 1-2秒
- 依存ツール最小
- CPU 使用率低い

**デメリット:**
- HTML 構造変更に弱い
- レート制限に弱い（ただし Brightcove API は緩い）

---

### **方法2: yt-dlp（堅牢性重視）**

```bash
#!/bin/bash
# Brightcove プレイヤーから MP4 取得

VIDEO_ID="6398801618112"
ACCOUNT_ID="6054371505001"
PLAYER_ID="hNf2KNmT85"

BRIGHTCOVE_URL="https://players.brightcove.net/${ACCOUNT_ID}/${PLAYER_ID}_default/index.html?videoId=${VIDEO_ID}"

# ダウンロード実行
yt-dlp \
  -f "best[ext=mp4]" \
  -o "%(title)s.%(ext)s" \
  --quiet \
  "${BRIGHTCOVE_URL}"

# JSON メタデータ取得
yt-dlp \
  -j \
  "${BRIGHTCOVE_URL}" | jq '.[] | {title, duration, ext}'
```

**Python 版:**

```python
import subprocess
import json

def download_with_ytdlp(video_id: str, output_dir: str = "videos") -> dict:
    """
    yt-dlp でダウンロード
    実行時間: 30秒～数分（ファイルサイズに依存）
    """
    brightcove_url = (
        f"https://players.brightcove.net/6054371505001/"
        f"hNf2KNmT85_default/index.html?videoId={video_id}"
    )

    cmd = [
        "yt-dlp",
        "-f", "best[ext=mp4]",
        "-o", f"{output_dir}/%(title)s.%(ext)s",
        "-j",  # JSON 出力
        "--quiet",
        brightcove_url
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            metadata = json.loads(result.stdout)
            return {
                'title': metadata.get('title'),
                'filename': metadata.get('filename'),
                'duration': metadata.get('duration'),
                'success': True
            }
        else:
            print(f"エラー: {result.stderr}")
            return {'success': False}

    except subprocess.TimeoutExpired:
        print("タイムアウト（ダウンロード中）")
        return {'success': False}
```

**メリット:**
- 最も堅牢（Brightcove 仕様変更に強い）
- 既存スキルで実装済み
- 署名付き URL の自動処理

**デメリット:**
- yt-dlp インストール必須
- 実行時間が長い（30秒～数分）
- HLS セグメント再結合のオーバーヘッド

---

### **方法3: Playwright（動的レンダリング）**

```python
from playwright.sync_api import sync_playwright

def extract_with_playwright(url: str, cookies: dict = None) -> dict:
    """
    Playwright でページレンダリング後に抽出
    実行時間: 5-10秒
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # セッションクッキー設定
        if cookies:
            page.context.add_cookies([
                {
                    'name': k,
                    'value': v,
                    'url': 'https://www.awareness.co.jp'
                }
                for k, v in cookies.items()
            ])

        # ページロード
        page.goto(url, wait_until='networkidle')

        # videoId 抽出
        video_id = page.evaluate(
            """() => {
                const video = document.querySelector('[data-video-id]');
                return video?.getAttribute('data-video-id') || null;
            }"""
        )

        # タイトル抽出
        title = page.evaluate(
            """() => {
                return document.querySelector('h1')?.textContent || document.title;
            }"""
        )

        browser.close()

        return {
            'video_id': video_id,
            'title': title
        }
```

**メリット:**
- ブラウザ完全シミュレーション
- JavaScript 実行後の DOM アクセス
- Cookie ベース認証対応

**デメリット:**
- Playwright インストール必須
- ブラウザプロセス起動コスト（1-2秒）
- メモリ使用量が多い

---

## 🔄 Fallback 戦略

### **3段階フォールバックロジック**

```python
def extract_video_info(url: str, video_id: str = None, cookies: dict = None):
    """
    統合抽出メソッド（自動フォールバック）
    """

    # ========== 段階1: HTML パース ==========
    try:
        video_id = extract_video_id(url)
        if video_id:
            mp4_url = get_mp4_url(video_id, url)
            if mp4_url:
                return {
                    'video_id': video_id,
                    'mp4_url': mp4_url,
                    'method': 'html_parse',  # ← 成功したメソッド
                    'status': 'success'
                }
    except Exception as e:
        print(f"[警告] HTML パース失敗: {e}")

    # ========== 段階2: yt-dlp ==========
    try:
        if video_id:  # videoId が取得できていれば
            result = download_with_ytdlp(video_id)
            if result['success']:
                return {
                    'video_id': video_id,
                    'title': result['title'],
                    'filename': result['filename'],
                    'method': 'ytdlp',  # ← 成功したメソッド
                    'status': 'success'
                }
    except Exception as e:
        print(f"[警告] yt-dlp 失敗: {e}")

    # ========== 段階3: Playwright ==========
    try:
        result = extract_with_playwright(url, cookies=cookies)
        if result['video_id']:
            mp4_url = get_mp4_url(result['video_id'], url)
            if mp4_url:
                return {
                    'video_id': result['video_id'],
                    'title': result['title'],
                    'mp4_url': mp4_url,
                    'method': 'playwright',  # ← 成功したメソッド
                    'status': 'success'
                }
    except Exception as e:
        print(f"[エラー] Playwright 失敗: {e}")

    # ========== 全て失敗 ==========
    return {
        'status': 'failed',
        'error': 'すべての抽出方法が失敗しました'
    }
```

---

## ⚠️ エラーハンドリング

### **一般的なエラーと対応方法**

| エラー | 原因 | 対応 |
|--------|------|------|
| **403 Forbidden** | Referer ヘッダーが無い | `Referer: https://www.awareness.co.jp` を設定 |
| **404 Not Found** | 削除済み動画 | 別の video_id を試す |
| **429 Too Many Requests** | レート制限 | バックオフ: 5秒待機後リトライ |
| **timeout** | ネットワーク遅延 | タイムアウト値を延長（30秒→60秒） |
| **HLS only** | MP4 が存在しない | HLS マニフェストから ffmpeg で変換 |

### **エラーハンドリング実装例**

```python
import time
from requests.exceptions import Timeout, ConnectionError

def get_mp4_url_with_retry(video_id: str, max_retries: int = 3) -> str:
    """
    エラーハンドリング付き MP4 URL 取得
    """
    for attempt in range(max_retries):
        try:
            url = f"https://edge.api.brightcove.com/playback/v1/accounts/6054371505001/videos/{video_id}"
            headers = {'Referer': 'https://www.awareness.co.jp'}

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 404:
                print(f"エラー: 動画が見つかりません (video_id={video_id})")
                return None

            if response.status_code == 429:
                # レート制限：バックオフ
                wait_time = (2 ** attempt)  # 1秒、2秒、4秒...
                print(f"レート制限。{wait_time}秒待機...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()

            data = response.json()
            for source in data.get('sources', []):
                if source.get('container') == 'video/mp4':
                    return source.get('src')

            return None

        except Timeout:
            print(f"試行 {attempt + 1}/{max_retries}: タイムアウト")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return None

        except ConnectionError as e:
            print(f"接続エラー: {e}")
            return None

    return None
```

---

## 🔐 セッション管理

### **認証クッキーの取得と永続化**

```python
import json
import requests
from pathlib import Path

class SessionManager:
    """Awareness.co.jp セッション管理"""

    def __init__(self, cookie_file: str = "awareness_cookies.json"):
        self.cookie_file = cookie_file
        self.session = requests.Session()

    def login(self, email: str, password: str) -> bool:
        """
        ログインしてセッションクッキー取得
        """
        try:
            # ログインURL（推定）
            login_url = "https://www.awareness.co.jp/api/auth/login"

            response = self.session.post(login_url, json={
                'email': email,
                'password': password
            })

            if response.status_code == 200:
                # クッキーを保存
                self.save_cookies()
                print("✓ ログイン成功")
                return True
            else:
                print(f"✗ ログイン失敗: {response.status_code}")
                return False

        except Exception as e:
            print(f"エラー: {e}")
            return False

    def save_cookies(self):
        """セッションクッキーをファイルに保存"""
        cookies_dict = dict(self.session.cookies)
        with open(self.cookie_file, 'w') as f:
            json.dump(cookies_dict, f, indent=2)
        print(f"✓ クッキーを保存: {self.cookie_file}")

    def load_cookies(self) -> bool:
        """ファイルからクッキーをロード"""
        if not Path(self.cookie_file).exists():
            return False

        try:
            with open(self.cookie_file, 'r') as f:
                cookies_dict = json.load(f)
            self.session.cookies.update(cookies_dict)
            print(f"✓ クッキーをロード: {self.cookie_file}")
            return True

        except Exception as e:
            print(f"エラー: {e}")
            return False

    def is_valid(self) -> bool:
        """セッション有効性を確認"""
        try:
            # ダミーリクエストで確認
            response = self.session.get(
                "https://www.awareness.co.jp/mypage/",
                timeout=10
            )
            # ログインページが返されたらセッション無効
            return "/login" not in response.url
        except:
            return False
```

### **使用例**

```python
# 初回：ログイン
manager = SessionManager()
manager.login("user@example.com", "password")

# 次回以降：クッキーをロード
manager = SessionManager()
if manager.load_cookies() and manager.is_valid():
    print("セッション有効")
    extractor = BrightcoveExtractor(session_cookies=dict(manager.session.cookies))
else:
    print("セッション無効。再ログイン必要")
    manager.login("user@example.com", "password")
```

---

## 🚀 パフォーマンス最適化

### **1. 並列処理（複数動画の一括処理）**

```python
from concurrent.futures import ThreadPoolExecutor
import time

def batch_extract(urls: list, max_workers: int = 5) -> list:
    """
    複数動画を並列処理
    実行時間: 1本あたり 1-2秒（HTML パース時）
    """
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(extract_video_info, url): url
            for url in urls
        }

        for future in futures:
            try:
                result = future.result(timeout=30)
                results.append(result)
            except Exception as e:
                print(f"エラー: {e}")
                results.append({'status': 'failed'})

    return results

# 使用例
urls = [
    "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216",
    "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5217",
    # ...
]

results = batch_extract(urls, max_workers=10)
print(f"処理完了: {len(results)}件")
```

### **2. キャッシング（重複処理の排除）**

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_mp4_url_cached(video_id: str) -> str:
    """
    MP4 URL をキャッシュ
    同じ video_id への2回目以降はメモリから取得
    """
    return get_mp4_url(video_id, "https://www.awareness.co.jp")

# 使用例
url1 = get_mp4_url_cached("6398801618112")  # API リクエスト
url2 = get_mp4_url_cached("6398801618112")  # キャッシュから取得
```

### **3. コネクションプーリング**

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retry() -> requests.Session:
    """
    リトライ機構付きセッション作成
    """
    session = requests.Session()

    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504]
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    return session
```

---

## 📊 実装チェックリスト

- [ ] **方法1: HTML パース** を実装
  - [ ] videoId 抽出正確性テスト
  - [ ] Brightcove API 接続確認
  - [ ] Referer ヘッダー設定確認

- [ ] **方法2: yt-dlp** をセットアップ
  - [ ] yt-dlp インストール確認
  - [ ] Brightcove プレイヤーURL 構築確認
  - [ ] MP4 ダウンロード テスト

- [ ] **方法3: Playwright** を準備（オプション）
  - [ ] Playwright インストール
  - [ ] ブラウザインストール（`playwright install`）
  - [ ] セッションクッキー管理

- [ ] **エラーハンドリング** を実装
  - [ ] タイムアウト処理
  - [ ] 403/404/429 エラー処理
  - [ ] ログ記録

- [ ] **パフォーマンス** を最適化
  - [ ] 並列処理実装
  - [ ] キャッシング実装
  - [ ] コネクションプーリング

---

## 📝 参考資料

- [Brightcove Playback API](https://docs.brightcove.com/en/video-cloud/playback-api/)
- [yt-dlp Brightcove Support](https://github.com/yt-dlp/yt-dlp#brightcove)
- [Playwright Documentation](https://playwright.dev/python/)
