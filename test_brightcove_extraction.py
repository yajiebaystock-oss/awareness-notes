#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Brightcove 抽出スクリプトの検証テスト
各方法の実行可能性を検証
"""

import subprocess
import sys
import os

# Windows環境でのエンコーディング問題を回避
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# テスト対象リソース
TEST_VIDEO_ID = "6398801618112"
TEST_URL = "https://www.awareness.co.jp/mypage/archives/study-watch/348/376/5216"
BRIGHTCOVE_ACCOUNT = "6054371505001"


def test_requirements():
    """必要なツール/ライブラリの確認"""
    print("\n" + "="*60)
    print("1. Environment Check")
    print("="*60)

    requirements = {
        'python': ('python', '--version'),
        'pip': ('pip', '--version'),
        'requests': (sys.executable, '-c', 'import requests; print(requests.__version__)'),
        'yt-dlp': ('yt-dlp', '--version'),
    }

    results = {}

    for name, cmd in requirements.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout.strip()
                print("[OK] {}: {}".format(name, output))
                results[name] = True
            else:
                print("[NG] {}: Optional".format(name))
                results[name] = False
        except FileNotFoundError:
            print("[NG] {}: Install required".format(name))
            results[name] = False
        except Exception as e:
            print("[NG] {}: Error - {}".format(name, e))
            results[name] = False

    return results


def test_brightcove_api():
    """Brightcove API の接続確認"""
    print("\n" + "="*60)
    print("2. Brightcove API Connection Test")
    print("="*60)

    try:
        import requests
    except ImportError:
        print("[NG] requests library not installed")
        return False

    try:
        url = "https://edge.api.brightcove.com/playback/v1/accounts/{}/videos/{}".format(
            BRIGHTCOVE_ACCOUNT, TEST_VIDEO_ID)

        headers = {
            'Referer': 'https://www.awareness.co.jp',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }

        print("API Endpoint: {}".format(url))
        print("Referer: {}".format(headers['Referer']))
        print("Requesting...")

        response = requests.get(url, headers=headers, timeout=10)

        print("Status Code: {}".format(response.status_code))

        if response.status_code == 200:
            data = response.json()
            print("[OK] API connection successful")
            print("  Title: {}".format(data.get('name', 'N/A')))
            print("  Video ID: {}".format(data.get('id', 'N/A')))
            print("  Duration: {:.1f} min".format(data.get('duration', 0) / 1000 / 60))

            # Source check
            sources = data.get('sources', [])
            print("  Available Sources: {} items".format(len(sources)))

            for i, source in enumerate(sources):
                container = source.get('container', 'unknown')
                src = source.get('src', '')
                print("    - {}. {} ({} bytes)".format(i + 1, container, len(src)))

            return True

        elif response.status_code == 403:
            print("[NG] 403 Forbidden - Referer header required")
            return False

        elif response.status_code == 404:
            print("[NG] 404 Not Found - Video not found")
            return False

        else:
            print("[NG] Error: {}".format(response.status_code))
            print("  Response: {}".format(response.text[:200]))
            return False

    except requests.exceptions.Timeout:
        print("[NG] Timeout")
        return False

    except Exception as e:
        print("[NG] Error: {}".format(e))
        return False


def test_html_parse():
    """HTML パース方法の実行可能性テスト"""
    print("\n" + "="*60)
    print("3. HTML Parse Method Test")
    print("="*60)

    try:
        import requests
        import re
    except ImportError:
        print("[NG] Required libraries not installed")
        return False

    try:
        print("URL: {}".format(TEST_URL))
        print("Requesting...")

        response = requests.get(TEST_URL, timeout=10)

        print("Status Code: {}".format(response.status_code))

        if response.status_code == 200:
            # videoId extraction test
            patterns = [
                r'data-video-id=["\'](\d+)["\']',
                r'"videoId"\s*:\s*["\'](\d+)["\']',
                r'bc-video-id=["\'](\d+)["\']',
            ]

            found = False
            for i, pattern in enumerate(patterns, 1):
                match = re.search(pattern, response.text)
                if match:
                    video_id = match.group(1)
                    print("[OK] videoId extraction success (Pattern {})".format(i))
                    print("  Extracted ID: {}".format(video_id))
                    found = True
                    break

            if not found:
                print("[NG] Could not extract videoId")
                print("  Possible: Behind auth gate or different HTML structure")
                return False

            # Title extraction test
            title_match = re.search(r'<title>([^<]+)</title>', response.text)
            if title_match:
                print("[OK] Title extraction success")
                print("  Title: {}".format(title_match.group(1)[:50]))

            return True

        else:
            print("[NG] Page access failed: {}".format(response.status_code))
            if response.status_code == 403:
                print("  Possible: Authentication required (set session cookie)")
            elif response.status_code == 404:
                print("  Possible: Page not found (check URL)")
            return False

    except requests.exceptions.Timeout:
        print("[NG] Timeout")
        return False

    except Exception as e:
        print("[NG] Error: {}".format(e))
        return False


def test_ytdlp():
    """yt-dlp 方法の実行可能性テスト"""
    print("\n" + "="*60)
    print("4. yt-dlp Method Test")
    print("="*60)

    brightcove_url = (
        "https://players.brightcove.net/{}/hNf2KNmT85_default/index.html?videoId={}".format(
            BRIGHTCOVE_ACCOUNT, TEST_VIDEO_ID))

    print("Brightcove URL: {}".format(brightcove_url))

    try:
        # yt-dlp version check
        result = subprocess.run(
            ['yt-dlp', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            print("[NG] yt-dlp not installed")
            print("  Install: pip install yt-dlp")
            return False

        print("[OK] yt-dlp version: {}".format(result.stdout.strip()))

        # Metadata retrieval test
        print("\nMetadata retrieval test...")

        result = subprocess.run(
            ['yt-dlp', '-j', '--quiet', brightcove_url],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            import json
            metadata = json.loads(result.stdout)

            print("[OK] Metadata retrieval success")
            print("  Title: {}".format(metadata.get('title', 'N/A')))
            print("  Duration: {:.1f} min".format(metadata.get('duration', 0) / 60))
            print("  Extension: {}".format(metadata.get('ext', 'N/A')))

            return True

        else:
            print("[NG] yt-dlp error")
            print("  Error message: {}".format(result.stderr[:200]))
            return False

    except FileNotFoundError:
        print("[NG] yt-dlp command not found")
        print("  Install: pip install yt-dlp")
        return False

    except Exception as e:
        print("[NG] Error: {}".format(e))
        return False


def test_playwright():
    """Playwright 方法の実行可能性テスト"""
    print("\n" + "="*60)
    print("5. Playwright Method Test")
    print("="*60)

    try:
        from playwright.sync_api import sync_playwright
        print("[OK] Playwright installed")

    except ImportError:
        print("[NG] Playwright not installed")
        print("  Install: pip install playwright && playwright install")
        return False

    try:
        print("\nLaunching browser...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            print("Loading page...")
            page.goto(TEST_URL, wait_until='networkidle', timeout=30000)

            # videoId extraction
            video_id = page.evaluate(
                """() => {
                    const video = document.querySelector('[data-video-id]');
                    return video?.getAttribute('data-video-id') || null;
                }"""
            )

            # Title extraction
            title = page.evaluate(
                """() => {
                    return document.querySelector('h1')?.textContent
                        || document.title
                        || 'Unknown';
                }"""
            )

            browser.close()

            if video_id:
                print("[OK] Playwright test success")
                print("  Extracted videoId: {}".format(video_id))
                print("  Extracted title: {}".format(title[:50]))
                return True
            else:
                print("[NG] Could not extract videoId")
                print("  Possible: Behind authentication gate")
                return False

    except Exception as e:
        print("[NG] Playwright error: {}".format(e))
        return False


def generate_report(results):
    """テスト結果レポート生成"""
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)

    print("\n[Available Methods]\n")

    methods = [
        ("HTML Parse", results.get('html_parse', False), "Fastest, Recommended"),
        ("Brightcove API", results.get('brightcove_api', False), "Reliable"),
        ("yt-dlp", results.get('ytdlp', False), "Most Robust"),
        ("Playwright", results.get('playwright', False), "Full Automation"),
    ]

    for method, status, note in methods:
        icon = "[OK]" if status else "[NG]"
        print("{} {:20} {}".format(icon, method, note))

    # Recommended steps
    print("\n[Recommended Implementation Steps]\n")

    if results.get('html_parse') or results.get('brightcove_api'):
        print("[1] Method 1: HTML Parse (Primary)")
        print("    Available. Fast and stable.")

    if results.get('ytdlp'):
        print("[2] Method 2: yt-dlp (Fallback)")
        print("    Installed. Most robust.")
    else:
        print("[2] Method 2: yt-dlp (Fallback)")
        print("    Recommended: pip install yt-dlp")

    if results.get('playwright'):
        print("[3] Method 3: Playwright (Last Resort)")
        print("    Available.")
    else:
        print("[3] Method 3: Playwright (Last Resort)")
        print("    Optional: pip install playwright")

    print("\n" + "="*60)


def main():
    """メイン実行"""
    print("\n")
    print("="*60)
    print("Awareness.co.jp Brightcove Extraction Method Test")
    print("="*60)

    results = {}

    # Run tests
    results['requirements'] = test_requirements()
    results['brightcove_api'] = test_brightcove_api()
    results['html_parse'] = test_html_parse()
    results['ytdlp'] = test_ytdlp()
    results['playwright'] = test_playwright()

    # Generate report
    generate_report(results)

    print("\n[TESTS COMPLETED]\n")


if __name__ == "__main__":
    main()
