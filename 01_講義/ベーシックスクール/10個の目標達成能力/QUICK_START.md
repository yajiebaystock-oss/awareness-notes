# Brightcove 動画抽出 & MP3 変換 クイックスタート

対象 URL: https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216

---

## 🚀 最短5秒での実行

### **最も簡単：yt-dlp で直接 MP3 ダウンロード**

```bash
yt-dlp -f bestaudio -x --audio-format mp3 \
  "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"
```

**結果：** カレントディレクトリに `【10の能力動画】タイミングの原則.mp3` が作成される

---

## 💻 3つの実行方法

### **方法A: Python スクリプト（推奨）**

```bash
# 最も簡単
python3 extract_and_convert.py "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"

# 出力ファイル名を指定
python3 extract_and_convert.py "https://..." --output timing_principle.mp3

# M4A 形式で変換
python3 extract_and_convert.py "https://..." --format m4a --output output.m4a

# 詳細ログを表示
python3 extract_and_convert.py "https://..." -v
```

### **方法B: Bash スクリプト**

```bash
# 最も簡単
bash extract_and_convert.sh "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"

# 出力ファイル名を指定
bash extract_and_convert.sh "https://..." timing_principle.mp3
```

### **方法C: yt-dlp コマンド直接実行**

```bash
# MP3 で保存（推奨）
yt-dlp -f bestaudio -x --audio-format mp3 \
  "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216" \
  -o "timing_principle.mp3"

# M4A で保存
yt-dlp -f bestaudio -x --audio-format m4a \
  "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216" \
  -o "timing_principle.m4a"

# JSON メタデータを取得
yt-dlp -j "https://..." | jq '.title, .duration'

# VideoId のみ抽出
yt-dlp -j "https://..." | jq -r '.id'
```

---

## 📋 コマンド詳細

### **yt-dlp オプション解説**

| オプション | 意味 | 例 |
|-----------|------|-----|
| `-f bestaudio` | 最高品質オーディオ選択 | `-f bestaudio` |
| `-x` | 動画から音声抽出 | `-x` |
| `--audio-format FORMAT` | 出力形式指定 | `--audio-format mp3` |
| `-o FILE` | 出力ファイル名 | `-o "output.mp3"` |
| `-j` | JSON メタデータ出力 | `-j` |
| `--quiet` | 静か実行 | `--quiet` |

### **出力形式の比較**

| 形式 | 容量 | 品質 | 互換性 | 推奨用途 |
|------|------|------|--------|---------|
| **MP3** | 中 | 低～中 | 最高 | 一般的な使用（推奨） |
| **M4A** | 小 | 高 | 高 | Apple デバイス / 高品質 |
| **OPUS** | 最小 | 高 | 中 | Web アプリ / 低容量 |

---

## 🔧 インストール

### **yt-dlp のインストール**

```bash
# macOS
brew install yt-dlp

# Windows (PowerShell)
pip install yt-dlp

# Linux (Ubuntu/Debian)
sudo apt-get install yt-dlp
```

### **ffmpeg のインストール（オプション：フォールバック用）**

```bash
# macOS
brew install ffmpeg

# Windows
choco install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

### **jq のインストール（JSON パース用）**

```bash
# macOS
brew install jq

# Windows
choco install jq

# Linux
sudo apt-get install jq
```

---

## ✅ 動作確認

### **yt-dlp のバージョン確認**

```bash
yt-dlp --version
```

### **VideoId の抽出確認**

```bash
yt-dlp -j "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216" | jq '.id'
```

期待される出力：
```
"6398801618112"
```

### **JSON メタデータ全体表示**

```bash
yt-dlp -j "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216" | jq '.'
```

---

## ⚠️ よくあるエラーと解決方法

| エラー | 原因 | 解決方法 |
|--------|------|--------|
| `yt-dlp: command not found` | yt-dlp がインストールされていない | `pip install yt-dlp` でインストール |
| `ERROR: This video is only available for registered users` | 認証が必要 | Cookie 付きでリクエスト（スクリプト内で自動処理） |
| `ERROR: requested format not available` | 形式が利用不可 | `-f best` で最高品質を自動選択 |
| `Connection timeout` | ネットワーク接続エラー | インターネット接続を確認 |

---

## 📊 実行例

### **例1: MP3 ダウンロード（最も一般的）**

```bash
$ yt-dlp -f bestaudio -x --audio-format mp3 \
  "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"

[generic] mypage/archives/study-watch/348/376/5216: Downloading webpage
...
[download] Destination: 【10の能力動画】タイミングの原則.mp3
[download] 100% of 12.34 MiB in 00:34

$ ls -lh *.mp3
-rw-r--r--  1 user  staff  12M Jun 26 12:34 【10の能力動画】タイミングの原則.mp3
```

### **例2: JSON メタデータ取得**

```bash
$ yt-dlp -j "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216" | jq '{title, duration, ext}'

{
  "title": "【10の能力動画】タイミングの原則",
  "duration": 600,
  "ext": "mp3"
}
```

### **例3: Python スクリプト実行**

```bash
$ python3 extract_and_convert.py \
  "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216" \
  --output timing.mp3

2026-06-26 12:34:56 - INFO - Brightcove 動画 MP3 変換開始
2026-06-26 12:34:56 - INFO - URL: https://www.awareness.co.jp/...
2026-06-26 12:35:02 - INFO - [方法1] HTML パース開始
2026-06-26 12:35:02 - INFO - ✓ videoId 抽出成功: 6398801618112
2026-06-26 12:35:04 - INFO - [方法2] yt-dlp 実行開始
2026-06-26 12:35:45 - INFO - ✓ ダウンロード & 変換成功
2026-06-26 12:35:45 - INFO - 
======================================================================
✅ 変換成功（yt-dlp 経由）
======================================================================

$ ls -lh timing.mp3
-rw-r--r--  1 user  staff  12M Jun 26 12:35 timing.mp3
```

---

## 🎯 推奨ワークフロー

### **シナリオ1: 単発で MP3 が欲しい**

```bash
yt-dlp -f bestaudio -x --audio-format mp3 \
  "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"
```

**所要時間：** 30秒～2分

### **シナリオ2: 複数の動画を一括ダウンロード**

```bash
# URL リストをファイルに作成
cat > urls.txt << 'EOF'
https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216
https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5217
https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5218
EOF

# 一括処理
while read url; do
  python3 extract_and_convert.py "$url"
done < urls.txt
```

### **シナリオ3: VideoId を取得してから処理**

```bash
# VideoId を抽出
VIDEO_ID=$(yt-dlp -j "https://www.awareness.co.jp/..." | jq -r '.id')

# API から MP4 URL を取得
curl -s "https://edge.api.brightcove.com/playback/v1/accounts/6054371505001/videos/$VIDEO_ID" \
  -H "Referer: https://www.awareness.co.jp/" | jq '.sources[] | select(.container=="video/mp4") | .src'
```

---

## 📖 参考リンク

- **yt-dlp GitHub:** https://github.com/yt-dlp/yt-dlp
- **yt-dlp ドキュメント:** https://github.com/yt-dlp/yt-dlp#readme
- **Brightcove API:** https://apis.support.brightcove.com/playback/

---

**最終更新:** 2026-06-26
