# Git インストール手順

このガイドでは、主要な OS ごとに Git をインストールする方法を説明します。

## 目次

- [Windows](#windows)
- [macOS](#macos)
- [Linux](#linux)
- [インストール後の初期設定](#インストール後の初期設定)
- [動作確認](#動作確認)
- [トラブルシューティング](#トラブルシューティング)

---

## Windows

### 方法 1: 公式インストーラー (推奨)

1. 公式サイトにアクセスします: <https://git-scm.com/download/win>
2. 自動的にインストーラー (`Git-x.xx.x-64-bit.exe`) のダウンロードが始まります。
3. ダウンロードした `.exe` を実行します。
4. ウィザードに従ってインストールします。基本的にはデフォルト設定のままで問題ありません。特に重要な選択肢は次のとおりです:
   - **Select Components**: `Git Bash Here` と `Git GUI Here` を有効にしておくと便利です。
   - **Default editor**: 普段使っているエディタ (VS Code など) を選択します。
   - **Adjusting your PATH environment**: `Git from the command line and also from 3rd-party software` を選択します。
   - **Line ending conversions**: Windows の場合は `Checkout Windows-style, commit Unix-style line endings` を推奨します。
5. インストールが完了したら、スタートメニューから `Git Bash` を起動できることを確認します。

### 方法 2: winget (Windows 10/11)

PowerShell またはコマンドプロンプトで次を実行します:

```powershell
winget install --id Git.Git -e --source winget
```

### 方法 3: Chocolatey

```powershell
choco install git
```

---

## macOS

### 方法 1: Homebrew (推奨)

[Homebrew](https://brew.sh/) がインストール済みであれば、ターミナルで次を実行します:

```bash
brew install git
```

Homebrew が未インストールの場合は、先に以下を実行してください:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 方法 2: Xcode Command Line Tools

ターミナルで `git` を初めて実行すると、Xcode Command Line Tools のインストールを促すダイアログが表示されます。または明示的に次を実行します:

```bash
xcode-select --install
```

### 方法 3: 公式インストーラー

<https://git-scm.com/download/mac> から `.dmg` をダウンロードしてインストールします。

---

## Linux

### Debian / Ubuntu 系

```bash
sudo apt update
sudo apt install -y git
```

### Fedora / RHEL / CentOS Stream 系

```bash
sudo dnf install -y git
```

古い RHEL/CentOS の場合:

```bash
sudo yum install -y git
```

### Arch Linux / Manjaro

```bash
sudo pacman -S git
```

### openSUSE

```bash
sudo zypper install git
```

### Alpine Linux

```bash
sudo apk add git
```

---

## インストール後の初期設定

インストール後は最低限、ユーザー名とメールアドレスを設定します。これらはコミットの著者情報として記録されます。

```bash
git config --global user.name "あなたの名前"
git config --global user.email "you@example.com"
```

その他の推奨設定:

```bash
# デフォルトブランチ名を main にする
git config --global init.defaultBranch main

# pull のデフォルト挙動を rebase ではなく merge にする (好みで)
git config --global pull.rebase false

# 改行コードの自動変換 (Windows のみ推奨)
git config --global core.autocrlf true

# macOS / Linux の場合
git config --global core.autocrlf input

# 認証情報を OS のキャッシュに保存
# Windows
git config --global credential.helper manager
# macOS
git config --global credential.helper osxkeychain
# Linux (一時キャッシュ)
git config --global credential.helper cache
```

設定内容は次のコマンドで確認できます:

```bash
git config --list
```

---

## 動作確認

ターミナル (Windows なら Git Bash や PowerShell) で次を実行します:

```bash
git --version
```

例:

```text
git version 2.45.2
```

バージョン番号が表示されれば、インストールは成功です。

簡単な動作確認として、空のリポジトリを作ってみます:

```bash
mkdir hello-git
cd hello-git
git init
echo "# Hello Git" > README.md
git add README.md
git commit -m "first commit"
git log --oneline
```

`first commit` が表示されれば、Git は正しく動作しています。

---

## トラブルシューティング

### `git: command not found` と表示される

- **Windows**: PATH が通っていない可能性があります。インストーラーを再実行し、`Git from the command line...` を選択してください。
- **macOS/Linux**: ターミナルを再起動するか、`hash -r` を実行して PATH を再読み込みしてください。

### HTTPS で push/pull すると認証に失敗する

GitHub などは 2021 年以降、パスワード認証を廃止しています。代わりに [Personal Access Token (PAT)](https://docs.github.com/ja/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) または SSH 鍵を使用してください。

### SSL 証明書エラー

社内プロキシ環境などで証明書エラーが出る場合は、社内 CA 証明書を Git に登録します:

```bash
git config --global http.sslCAInfo /path/to/ca-bundle.crt
```

検証を一時的に無効化することもできますが (`http.sslVerify=false`)、セキュリティ上推奨されません。

### 改行コード関連の警告 (`LF will be replaced by CRLF`)

`core.autocrlf` の設定を見直してください。チームで開発する場合は、リポジトリのルートに `.gitattributes` を置いて統一するのが理想です。

---

## 参考リンク

- 公式サイト: <https://git-scm.com/>
- 公式ドキュメント (日本語): <https://git-scm.com/book/ja/v2>
- Pro Git book: <https://git-scm.com/book/en/v2>
