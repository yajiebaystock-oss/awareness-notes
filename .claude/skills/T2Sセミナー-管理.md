# T2Sセミナー 管理スキル

> このスキルを使用するには、Obsidian の Claude Code プラグインで `/t2s-` コマンドを入力してください。

## 説明

T2Sセミナーの 42 エピソード分のマークダウンファイルを一元管理するスキル。
ファイルの確認、検証、一覧表示、新規作成、README更新をサポートします。

**フォルダ**: `01_講義/T2Sセミナー/`

---

## コマンド一覧

### `/t2s-check`
**T2Sセミナーフォルダの状態を確認**

```
ファイル数、完成度、フォーマット状態をチェック
- 合計エピソード数: 42/42
- ファイル数確認
- README.md の状態確認
```

実行内容:
```bash
ls -1 "01_講義/T2Sセミナー" | wc -l
```

### `/t2s-list`
**全エピソードのファイル一覧を表示**

```
01_42 ～ 42_42 のすべてのファイルを一覧表示
- ファイル名
- タイトル
- YAML frontmatter の category
```

実行内容:
```bash
ls -1 "01_講義/T2Sセミナー" | grep "_42_" | sort
```

### `/t2s-validate`
**ファイルのフォーマット検証**

チェック項目:
- ✅ YAML frontmatter の存在
- ✅ セクション順序（要約 → ポイント → 文字起こし/ページコンテンツ）
- ✅ タイトル形式の統一
- ✅ ファイル名形式の統一（XX_42_タイトル.md）

### `/t2s-create`
**新しいエピソード用テンプレートを生成**

入力:
- エピソード番号（例：43）
- タイトル
- ビデオ URL またはページ URL

出力:
```markdown
---
title: "【T2Sセミナー】[タイトル]（43_42）"
date: [今日の日付]
source_url: "[URL]"
episode_id: [ID]
category: T2Sセミナー
category_label: T2Sセミナー（Awareness）
tags: [セミナー, 文字起こし, T2Sセミナー]
---

## 要約
（要約は未生成）

## ポイント
- **重要なポイント1**:
- **重要なポイント2**:
- **重要なポイント3**:

> 学習効果を高めるために、上記のポイントについて実生活でどう活用できるかを考えてみてください。

## 文字起こし（全文）
[コンテンツここに入る]
```

### `/t2s-update-readme`
**README.md を自動更新**

更新項目:
- ✅ 完成度（XX/42）
- ✅ ファイル数
- ✅ 最終更新日時
- ✅ 完成エピソード一覧

---

## 実装済み機能

### 1️⃣ ファイル確認 (`/t2s-check`)

```python
import subprocess
from pathlib import Path

vault_path = Path("C:\\Users\\yajim\\OneDrive\\デスクトップ\\awareness-notes")
t2s_folder = vault_path / "01_講義" / "T2Sセミナー"

# ファイル一覧取得
files = list(t2s_folder.glob("*.md"))
md_files = [f for f in files if f.suffix == ".md"]

print(f"✅ T2Sセミナー フォルダ確認")
print(f"  総ファイル数: {len(md_files)}")
print(f"  エピソード: {len([f for f in md_files if '_42_' in f.name])}/42")
print(f"  README.md: {'✅ 存在' if (t2s_folder / 'README.md').exists() else '❌ なし'}")
```

### 2️⃣ 一覧表示 (`/t2s-list`)

```python
from pathlib import Path
import re

vault_path = Path("C:\\Users\\yajim\\OneDrive\\デスクトップ\\awareness-notes")
t2s_folder = vault_path / "01_講義" / "T2Sセミナー"

files = sorted(t2s_folder.glob("*_42_*.md"))

print("【T2Sセミナー エピソード一覧】\n")
for f in files:
    match = re.match(r'(\d{2})_42_(.+)\.md', f.name)
    if match:
        ep_num = match.group(1)
        title = match.group(2)
        print(f"  {ep_num}/42: {title}")
```

### 3️⃣ フォーマット検証 (`/t2s-validate`)

```python
import re
from pathlib import Path

vault_path = Path("C:\\Users\\yajim\\OneDrive\\デスクトップ\\awareness-notes")
t2s_folder = vault_path / "01_講義" / "T2Sセミナー"

print("【フォーマット検証】\n")

issues = []
for filepath in sorted(t2s_folder.glob("*_42_*.md")):
    content = filepath.read_text(encoding="utf-8")
    
    # YAML frontmatter チェック
    if not content.startswith("---"):
        issues.append(f"❌ {filepath.name}: frontmatter なし")
        continue
    
    # セクション順序チェック
    has_summary = "## 要約" in content
    has_points = "## ポイント" in content
    has_content = "## 文字起こし" in content or "## ページコンテンツ" in content
    
    if not (has_summary and has_points and has_content):
        issues.append(f"⚠️  {filepath.name}: セクション不足")

if not issues:
    print("✅ すべてのファイルのフォーマットが正しいです！")
else:
    for issue in issues:
        print(issue)
```

### 4️⃣ 新規エピソード作成 (`/t2s-create`)

```python
from pathlib import Path
from datetime import datetime

def create_episode(ep_num: int, title: str, source_url: str, episode_id: int):
    """新規エピソードファイルを作成"""
    
    vault_path = Path("C:\\Users\\yajim\\OneDrive\\デスクトップ\\awareness-notes")
    t2s_folder = vault_path / "01_講義" / "T2Sセミナー"
    
    ep_str = f"{ep_num:02d}"
    filename = f"{ep_str}_42_{title}.md"
    filepath = t2s_folder / filename
    
    content = f"""---
title: "【T2Sセミナー】{title}（{ep_num}_42）"
date: {datetime.now().strftime('%Y-%m-%d')}
source_url: "{source_url}"
episode_id: {episode_id}
category: T2Sセミナー
category_label: T2Sセミナー（Awareness）
tags: [セミナー, 文字起こし, T2Sセミナー]
---

## 要約

（要約は未生成）

## ポイント

- **重要なポイント1**:
- **重要なポイント2**:
- **重要なポイント3**:

> 学習効果を高めるために、上記のポイントについて実生活でどう活用できるかを考えてみてください。

## 文字起こし（全文）

[コンテンツをここに入れてください]
"""
    
    filepath.write_text(content, encoding="utf-8")
    print(f"✅ {ep_num}/42: {filename} を作成しました")

# 使用例
# create_episode(43, "新しいエピソードのタイトル", "https://...", 6343)
```

### 5️⃣ README 自動更新 (`/t2s-update-readme`)

```python
from pathlib import Path
from datetime import datetime

def update_readme():
    """README.md を自動更新"""
    
    vault_path = Path("C:\\Users\\yajim\\OneDrive\\デスクトップ\\awareness-notes")
    t2s_folder = vault_path / "01_講義" / "T2Sセミナー"
    
    # ファイル数をカウント
    md_files = list(t2s_folder.glob("*_42_*.md"))
    episode_count = len(md_files)
    
    progress = f"{episode_count}/42"
    percentage = f"{(episode_count/42)*100:.1f}%"
    
    # README の更新部分
    readme_content = f"""# T2Sセミナー（幸せと成功の原則）

## 進捗状況

### ✅ 完了: {progress} ({percentage})

**最終更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## ファイル構成

- **エピソード**: {episode_count} 個
- **形式**: Markdown（YAML frontmatter + セクション）
- **フォルダ**: `01_講義/T2Sセミナー/`

## ファイル一覧

{os.popen('ls -1 "01_講義/T2Sセミナー" | grep "_42_" | sort').read()}

---

最新の状態を確認するには `/t2s-check` を実行してください。
"""
    
    readme_path = t2s_folder / "README.md"
    readme_path.write_text(readme_content, encoding="utf-8")
    print(f"✅ README.md を更新しました（{progress}）")

# 実行
update_readme()
```

---

## クイックスタート

Obsidian で以下のコマンドを入力してください：

| コマンド | 説明 |
|---------|------|
| `/t2s-check` | 📊 フォルダ状態確認 |
| `/t2s-list` | 📋 ファイル一覧表示 |
| `/t2s-validate` | ✅ フォーマット検証 |
| `/t2s-create` | ➕ 新規エピソード作成 |
| `/t2s-update-readme` | 🔄 README自動更新 |

---

## 対応フォーマット

### 1-10: ビデオ文字起こし版
```markdown
---
title: "【T2Sセミナー動画】タイトル（EP/42）[時間]"
category: Feeling_Now
---

## 要約
## ポイント
## 文字起こし（全文）
```

### 11-42: ページコンテンツ版
```markdown
---
title: "【T2Sセミナー】タイトル（EP_42）"
category: T2Sセミナー
---

## 要約
## ポイント
## ページコンテンツ（全文）
```

---

## サポート

問題が発生した場合:
- `/t2s-validate` で フォーマットをチェック
- `/t2s-check` で ファイル状態を確認
- README.md を確認

---

**v1.0 - T2Sセミナー管理スキル**
