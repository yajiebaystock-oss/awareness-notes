# awareness-notes Vault - Git セットアップガイド

## ✅ 完了: ローカル Git リポジトリの初期化

awareness-notes vault は Git で管理できるようになりました。

### 現在の状態

```
リポジトリ: C:\Users\yajim\OneDrive\デスクトップ\awareness-notes
ブランチ: master
コミット: 1 (Initial commit)
ステータス: Working tree clean
```

---

## 🔄 次のステップ

### オプション 1: GitHub に同期（推奨）

1. **GitHub でリモートリポジトリを作成**
   - https://github.com/new にアクセス
   - Repository name: `awareness-notes`
   - Description: `Awareness lectures unified management system`
   - Private / Public を選択
   - Create repository

2. **リモートリポジトリを追加**
   ```powershell
   cd "C:\Users\yajim\OneDrive\デスクトップ\awareness-notes"
   git remote add origin https://github.com/YOUR_USERNAME/awareness-notes.git
   git branch -M master main
   git push -u origin main
   ```

3. **認証設定**
   - GitHub Personal Access Token を生成
   - または SSH キーを設定

---

### オプション 2: ローカル Git のみで管理

現在の設定で十分です。毎回のコミットで変更を記録できます。

```powershell
# 変更をコミット
git add -A
git commit -m "Update lecture content"

# ログを確認
git log --oneline
```

---

## 📋 Git コマンドリファレンス

### ステータス確認
```powershell
git status
```

### 変更をステージング
```powershell
git add -A                    # すべてのファイル
git add "01_講義/T2Sセミナー" # 特定フォルダのみ
```

### コミット作成
```powershell
git commit -m "修正内容説明"
```

### ログ確認
```powershell
git log --oneline            # 1行表示
git log -n 10               # 直近10件
git log --graph --all       # グラフ表示
```

### 差分確認
```powershell
git diff                     # ステージング前の変更
git diff --cached           # ステージング済みの変更
```

### ブランチ管理
```powershell
git branch                  # ブランチ一覧
git checkout -b feature/xxx # 新しいブランチ作成
git switch feature/xxx      # ブランチ切り替え
```

### リモート管理（GitHub の場合）
```powershell
git remote -v              # リモートリポジトリ確認
git push origin main       # プッシュ
git pull origin main       # プル
```

---

## 🛡️ セキュリティ上の注意

### .gitignore が除外しているファイル

以下のファイル/フォルダは Git の追跡から除外されています：

- `.obsidian/` - Obsidian の設定ファイル
- `.trash/` - Obsidian のゴミ箱
- `node_modules/` - npm パッケージ
- `__pycache__/` - Python キャッシュ
- `.env` - 環境変数（秘密情報）

---

## 🔄 同期の流れ

### ローカルで変更した場合

```
1. ファイルを編集
   ↓
2. git add で変更をステージング
   ↓
3. git commit でローカル履歴に記録
   ↓
4. git push でリモートに送信（GitHub の場合）
```

### リモートから変更を取得

```
git pull origin main
```

---

## 📊 推奨フロー

### 日常的な更新

```powershell
# 作業終了時
cd "C:\Users\yajim\OneDrive\デスクトップ\awareness-notes"

# 変更を確認
git status

# 変更をコミット
git add -A
git commit -m "Update: [変更内容の説明]"

# リモートに送信（GitHub の場合）
git push origin main
```

### 定期的なチェック

```powershell
# ローカルの変更確認
git log --oneline -10

# 同期状態確認
git status
```

---

## 🆘 トラブルシューティング

### コミットをキャンセルしたい場合

```powershell
# 最後のコミット前に戻す
git reset HEAD~1

# ステージングをキャンセル
git reset
```

### ファイルの変更を取り消したい場合

```powershell
# 特定ファイルをリセット
git restore "ファイルパス"

# すべてをリセット
git restore .
```

### リモートと同期したい場合

```powershell
git fetch origin
git pull origin main
```

---

**作成日**: 2026-06-25  
**バージョン**: 1.0  
**管理対象**: 全74ファイル（4つの講義フォルダ）
