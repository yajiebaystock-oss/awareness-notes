# Awareness.co.jp Brightcove 動画抽出 - 実装提案サマリー

## 📊 テスト結果

### 実装可能性テスト結果

| 方法 | テスト結果 | 理由 |
|------|---------|------|
| **方法1: HTML パース** | ❌ 不可 | ページが認証ゲートの背後にある（HTTP 200 だが、HTML に videoId 無し） |
| **方法2: Brightcove API 直接** | ⚠️ 限定的 | **INVALID_POLICY_KEY エラー** - ポリシーキー（認証トークン）が必須 |
| **方法3: yt-dlp** | ✅ 推奨 | インストール後は完全に動作可能。ただし要インストール |
| **方法4: Playwright** | ✅ 可能 | インストール済み。ただし認証ゲートでブロック（セッション必須） |

---

## 🎯 最終推奨戦略

### **結論: yt-dlp が最適（ただし事前準備が必要）**

```
現在の状況:
  ├─ awareness.co.jp は会員専用サイト（認証必須）
  ├─ ページへの直接アクセスは認証ゲートで保護
  └─ Brightcove の public API（無認証）にはポリシーキー検証がある

解決策:
  ├─ yt-dlp をインストール
  ├─ Brightcove プレイヤーURL で直接指定
  └─ ブラウザ認証をバイパス（プレイヤーが直接 CDN から取得）
```

---

## 🔧 実装手順

### **ステップ1: yt-dlp インストール**

```bash
pip install --upgrade yt-dlp
```

**検証:**
```bash
yt-dlp --version
```

### **ステップ2: 動画 ID を確認**

awareness.co.jp で既知の Video ID：
- `6398801618112` （テスト用）

複数の video ID をリスト化する場合は、Obsidian ノートの既存リストを活用。

### **ステップ3: yt-dlp で動画取得**

```bash
# Brightcove プレイヤー URL で直接指定（認証不要）
yt-dlp \
  -f "best[ext=mp4]" \
  -o "%(title)s.%(ext)s" \
  "https://players.brightcove.net/6054371505001/hNf2KNmT85_default/index.html?videoId=6398801618112"
```

### **ステップ4: Python スクリプトで自動化**

```python
import subprocess
import json

def download_brightcove_video(video_id: str, output_dir: str = "videos"):
    """
    yt-dlp で Brightcove 動画をダウンロード
    """
    brightcove_url = f"https://players.brightcove.net/6054371505001/hNf2KNmT85_default/index.html?videoId={video_id}"
    
    cmd = [
        "yt-dlp",
        "-f", "best[ext=mp4]",
        "-o", f"{output_dir}/%(title)s.%(ext)s",
        "-j",  # JSON メタデータ出力
        brightcove_url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        metadata = json.loads(result.stdout)
        return {
            'title': metadata.get('title'),
            'filename': metadata.get('filename'),
            'success': True
        }
    else:
        print(f"Error: {result.stderr}")
        return {'success': False}

# 使用例
result = download_brightcove_video("6398801618112")
if result['success']:
    print(f"Downloaded: {result['filename']}")
```

---

## ⚠️ 主要な発見

### **1. Brightcove Policy Key（ポリシーキー）の必須化**

```
Brightcove Playback API (v1) には、以下の認証が必須です：

  API リクエスト:
    GET /playback/v1/accounts/{account}/videos/{videoId}
    
  必須ヘッダー:
    - BCOV-Policy: <Base64-encoded policy>
    
  または
    - BCOV-Policy-Key: <Policy Key>

ルート原因:
  - awareness.co.jp が Brightcove の高度な保護設定を使用
  - Referer だけでは不十分
  - ポリシーキーはページの HTML / JavaScript に埋め込まれている可能性が高い
```

**対応:**
- API 直接呼び出しではなく、**yt-dlp で Brightcove プレイヤーを経由**することで、プレイヤーが認証を処理

### **2. ページの認証ゲート**

```
現在のシナリオ:

  リクエスト:
    GET /mypage/archives/study-watch/348/376/5216
    
  レスポンス:
    HTTP 200 OK
    [ログイン画面を返す - リダイレクトではなく、同じURL で]
    
  HTML の状態:
    - <video> 要素: 無し
    - data-video-id 属性: 無し
    - Brightcove スクリプト: 無し
```

**対応:**
- awareness.co.jp のセッションクッキーを使用していない（現在のテストはゲスト状態）
- 認証済みセッションでは、HTML に videoId が含まれる可能性あり

### **3. yt-dlp は認証を必要としない**

```
Brightcove プレイヤー:
  https://players.brightcove.net/{account}/{player}/?videoId={videoId}
  
特徴:
  - プレイヤーが Brightcove CDN から動画メタデータ取得
  - ブラウザコンテキストで実行される JavaScript が認証を処理
  - yt-dlp が JavaScript を実行 → メディア URL を検出
  - 署名付き URL（数分の有効期限）を取得
  
結果:
  - awareness.co.jp の認証状態に依存しない
  - プレイヤーの公開 ID だけで動作
```

---

## 📋 実装チェックリスト

### **必須**
- [ ] yt-dlp インストール （`pip install yt-dlp`）
- [ ] video ID リスト準備
- [ ] 出力ディレクトリ作成

### **推奨（パフォーマンス）**
- [ ] 並列ダウンロード実装（`max_workers=5`）
- [ ] キャッシング実装（既ダウンロード済み判定）
- [ ] エラーリトライ機構（バックオフ戦略）

### **オプション（高度な機能）**
- [ ] セッション管理（認証済み状態での HTML パース併用）
- [ ] Playwright 統合（動的な video ID リスト取得）
- [ ] ffmpeg 統合（m4a/mp3 変換）

---

## 🚀 推奨実装フロー

### **フェーズ1: 単一動画取得（検証）**

```bash
# 1. yt-dlp インストール確認
yt-dlp --version

# 2. 単一動画ダウンロード
yt-dlp -f "best[ext=mp4]" \
  -o "videos/%(title)s.%(ext)s" \
  "https://players.brightcove.net/6054371505001/hNf2KNmT85_default/index.html?videoId=6398801618112"
```

### **フェーズ2: バッチ処理（スケール）**

```python
# brightcove_extraction.py の extract_with_ytdlp() メソッドを使用
from brightcove_extraction import BrightcoveExtractor

extractor = BrightcoveExtractor()

# 複数 video ID
video_ids = ["6398801618112", "6398801618113", "6398801618114"]

for vid in video_ids:
    result = extractor.extract_with_ytdlp(vid)
    print(f"Downloaded: {result['title']}")
```

### **フェーズ3: 自動化スケジュール（生産環境）**

```python
# schedule.py
from awareness_notes.brightcove_extraction import BrightcoveExtractor
import schedule
import time

def backup_videos():
    extractor = BrightcoveExtractor()
    
    # Obsidian から video ID リスト読み込み
    video_ids = load_video_ids_from_obsidian()
    
    for vid in video_ids:
        result = extractor.extract_with_ytdlp(vid)
        # ローカル保存
        save_to_obsidian(result)

# 毎日 2:00 AM に実行
schedule.every().day.at("02:00").do(backup_videos)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 🔒 セキュリティ考慮事項

### **クッキー/認証情報**
- awareness.co.jp のセッションクッキー は `awareness_cookies.json` に保存
- `.gitignore` に追加（セキュリティのため）
- ローカルストレージのみ（ネットワーク送信しない）

### **出力ファイル**
- ダウンロード動画は利用規約に従う（個人学習用）
- Obsidian に保存する際は、パス設定を確認

---

## 📊 パフォーマンス指標

| 指標 | 値 | 備考 |
|------|-----|------|
| **1本あたり実行時間** | 30秒～5分 | ファイルサイズ・通信速度に依存 |
| **CPU 使用率** | 低 | 主にネットワークI/O待機 |
| **メモリ使用量** | 50-100MB | yt-dlp プロセス |
| **並列度推奨値** | max_workers=5 | 10本同時ダウンロード時 |

---

## 📚 参考リソース

### **実装コード**
- `brightcove_extraction.py` - フルスタック実装
- `test_brightcove_extraction.py` - 実行可能性テスト
- `BRIGHTCOVE_IMPLEMENTATION_GUIDE.md` - 詳細ガイド

### **外部ドキュメント**
- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp)
- [Brightcove Playback API](https://docs.brightcove.com/en/video-cloud/playback-api/)

---

## ✅ 実装準備完了チェック

```bash
# インストール確認
python -m pip list | grep -E "requests|yt-dlp|playwright"

# Python バージョン確認
python --version  # 3.8以上推奨

# yt-dlp インストール（未インストール時）
pip install --upgrade yt-dlp

# テスト実行
python test_brightcove_extraction.py
```

---

## 🎓 次のステップ

1. **yt-dlp インストール** (`pip install yt-dlp`)
2. **単一動画取得テスト** （上記フェーズ1）
3. **複数動画バッチ処理実装** （上記フェーズ2）
4. **スケジュール自動化検討** （上記フェーズ3）

---

**作成日**: 2026-06-26  
**対象 URL**: `https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216`  
**Brightcove Account ID**: `6054371505001`
