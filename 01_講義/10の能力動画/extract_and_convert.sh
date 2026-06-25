#!/bin/bash

################################################################################
# Awareness.co.jp Brightcove 動画抽出 & MP3 変換スクリプト
#
# 使用方法:
#     bash extract_and_convert.sh <URL> [output_file] [format]
#
# 例:
#     bash extract_and_convert.sh "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"
#     bash extract_and_convert.sh <URL> timing_principle.mp3 mp3
#     bash extract_and_convert.sh <URL> output.m4a m4a
#
# 依存ツール:
#     - curl
#     - jq (JSON パース)
#     - yt-dlp (推奨)
#     - ffmpeg (フォールバック用)
#
################################################################################

set -e

# ==========================================
# 設定
# ==========================================

URL="${1:-}"
OUTPUT_FILE="${2:-}"
OUTPUT_FORMAT="${3:-mp3}"

BRIGHTCOVE_ACCOUNT="6054371505001"
BRIGHTCOVE_API="https://edge.api.brightcove.com/playback/v1/accounts"

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# ==========================================
# ユーティリティ関数
# ==========================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_debug() {
    if [ "$VERBOSE" = "true" ]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# ==========================================
# 入力検証
# ==========================================

if [ -z "$URL" ]; then
    log_error "URL を指定してください"
    echo ""
    echo "使用方法: $0 <URL> [output_file] [format]"
    echo ""
    echo "例:"
    echo "  $0 \"https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216\""
    echo "  $0 \"https://...\" timing_principle.mp3 mp3"
    echo "  $0 \"https://...\" output.m4a m4a"
    exit 1
fi

# 出力ファイル名の自動生成
if [ -z "$OUTPUT_FILE" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    OUTPUT_FILE="video_${TIMESTAMP}.${OUTPUT_FORMAT}"
    log_info "出力ファイル: $OUTPUT_FILE (自動生成)"
else
    log_info "出力ファイル: $OUTPUT_FILE"
fi

# ==========================================
# 方法1: HTML パース で videoId 抽出
# ==========================================

extract_video_id() {
    local url="$1"

    log_info "[方法1] HTML パース開始"

    # HTML を取得
    html=$(curl -s "$url" || echo "")

    if [ -z "$html" ]; then
        log_error "ページを取得できませんでした"
        return 1
    fi

    # videoId を抽出
    video_id=$(echo "$html" | grep -oP 'data-video-id="\K[0-9]+(?=")' | head -1)

    if [ -z "$video_id" ]; then
        video_id=$(echo "$html" | grep -oP '"videoId"\s*:\s*"\K[0-9]+(?=")' | head -1)
    fi

    if [ -z "$video_id" ]; then
        video_id=$(echo "$html" | grep -oP 'bc-video-id="\K[0-9]+(?=")' | head -1)
    fi

    if [ -z "$video_id" ]; then
        log_warn "HTML から videoId を抽出できませんでした"
        return 1
    fi

    log_info "✓ videoId 抽出成功: $video_id"
    echo "$video_id"
    return 0
}

# ==========================================
# タイトル抽出
# ==========================================

extract_title() {
    local url="$1"

    html=$(curl -s "$url" || echo "")

    # og:title を試す
    title=$(echo "$html" | grep -oP '<meta\s+property="og:title"\s+content="\K[^"]+' | head -1)

    if [ -z "$title" ]; then
        # title タグを試す
        title=$(echo "$html" | grep -oP '<title>\K[^<]+' | head -1)
    fi

    if [ -z "$title" ]; then
        # h1 を試す
        title=$(echo "$html" | grep -oP '<h1[^>]*>\K[^<]+' | head -1)
    fi

    if [ -n "$title" ]; then
        log_info "タイトル: $title"
    fi
}

# ==========================================
# MP4 URL 取得（API 経由）
# ==========================================

get_mp4_url() {
    local video_id="$1"

    log_debug "Brightcove API から MP4 URL 取得中"

    url="${BRIGHTCOVE_API}/${BRIGHTCOVE_ACCOUNT}/videos/${video_id}"

    # API リクエスト
    response=$(curl -s "$url" \
        -H "Referer: https://www.awareness.co.jp/" \
        -H "User-Agent: Mozilla/5.0" || echo "{}")

    if [ -z "$response" ] || [ "$response" = "{}" ]; then
        log_error "Brightcove API レスポンスが無効です"
        return 1
    fi

    # MP4 URL を抽出
    mp4_url=$(echo "$response" | jq -r '.sources[]? | select(.container=="video/mp4") | .src' | head -1)

    if [ -z "$mp4_url" ] || [ "$mp4_url" = "null" ]; then
        log_debug "MP4 URL が見つかりません。HLS をフォールバック"
        mp4_url=$(echo "$response" | jq -r '.sources[]? | select(.container=="application/x-mpegURL") | .src' | head -1)
    fi

    if [ -z "$mp4_url" ] || [ "$mp4_url" = "null" ]; then
        log_error "MP4 / HLS URL が見つかりません"
        return 1
    fi

    log_debug "✓ URL 取得成功"
    echo "$mp4_url"
    return 0
}

# ==========================================
# 方法2: yt-dlp でダウンロード
# ==========================================

download_with_ytdlp() {
    local url="$1"
    local output_file="$2"
    local format="$3"

    if ! check_command yt-dlp; then
        log_error "yt-dlp がインストールされていません"
        log_info "インストール方法:"
        log_info "  macOS: brew install yt-dlp"
        log_info "  Windows: pip install yt-dlp"
        log_info "  Linux: sudo apt-get install yt-dlp"
        return 1
    fi

    log_info "[方法2] yt-dlp で動画ダウンロード中"

    yt-dlp \
        -f bestaudio \
        -x \
        --audio-format "$format" \
        -o "$output_file" \
        --quiet \
        "$url"

    if [ $? -eq 0 ]; then
        log_info "✓ ダウンロード & 変換成功: $output_file"
        return 0
    else
        log_error "yt-dlp に失敗しました"
        return 1
    fi
}

# ==========================================
# 方法3: curl + ffmpeg でダウンロード
# ==========================================

download_with_curl_ffmpeg() {
    local video_id="$1"
    local output_file="$2"

    if ! check_command curl; then
        log_error "curl がインストールされていません"
        return 1
    fi

    if ! check_command ffmpeg; then
        log_error "ffmpeg がインストールされていません"
        log_info "インストール方法:"
        log_info "  macOS: brew install ffmpeg"
        log_info "  Windows: choco install ffmpeg"
        log_info "  Linux: sudo apt-get install ffmpeg"
        return 1
    fi

    log_info "[方法3] curl + ffmpeg でダウンロード"

    # MP4 URL 取得
    mp4_url=$(get_mp4_url "$video_id")
    if [ $? -ne 0 ]; then
        return 1
    fi

    log_debug "MP4 URL: ${mp4_url:0:80}..."

    # 一時ファイル
    temp_mp4=".temp_${video_id}.mp4"

    # curl でダウンロード
    log_info "curl で動画をダウンロード中"
    curl -L -o "$temp_mp4" --progress-bar "$mp4_url"

    if [ ! -f "$temp_mp4" ]; then
        log_error "curl ダウンロード失敗"
        return 1
    fi

    log_info "✓ ダウンロード完了"

    # ffmpeg で変換
    log_info "ffmpeg で MP3 に変換中"
    ffmpeg -i "$temp_mp4" -q:a 0 -map a "$output_file" -loglevel quiet

    if [ $? -ne 0 ]; then
        log_error "ffmpeg 変換失敗"
        rm -f "$temp_mp4"
        return 1
    fi

    log_info "✓ 変換完了: $output_file"

    # 一時ファイル削除
    rm -f "$temp_mp4"
    log_debug "一時ファイル削除"

    return 0
}

# ==========================================
# メイン処理
# ==========================================

main() {
    echo ""
    echo "======================================================================"
    echo "Brightcove 動画 MP3 変換スクリプト"
    echo "======================================================================"
    echo "URL: $URL"
    echo "出力: $OUTPUT_FILE"
    echo ""

    # タイトル抽出
    extract_title "$URL"

    # VideoId 抽出
    video_id=$(extract_video_id "$URL")
    if [ $? -ne 0 ]; then
        log_error "VideoId を抽出できませんでした"
        exit 1
    fi

    echo ""
    echo "======================================================================"
    echo "[段階1] yt-dlp"
    echo "======================================================================"

    # 方法2: yt-dlp
    download_with_ytdlp "$URL" "$OUTPUT_FILE" "$OUTPUT_FORMAT"
    if [ $? -eq 0 ]; then
        echo ""
        echo "======================================================================"
        echo "✅ 変換成功（yt-dlp 経由）"
        echo "======================================================================"
        return 0
    fi

    echo ""
    echo "======================================================================"
    echo "[段階2] curl + ffmpeg フォールバック"
    echo "======================================================================"

    # 方法3: curl + ffmpeg
    download_with_curl_ffmpeg "$video_id" "$OUTPUT_FILE"
    if [ $? -eq 0 ]; then
        echo ""
        echo "======================================================================"
        echo "✅ 変換成功（curl + ffmpeg 経由）"
        echo "======================================================================"
        return 0
    fi

    echo ""
    echo "======================================================================"
    log_error "すべての方法が失敗しました"
    echo "======================================================================"
    return 1
}

# メイン実行
main
exit $?
