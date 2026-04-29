#!/bin/bash
set -e

echo "=== macOS Git セットアップスクリプト ==="
echo ""

# Homebrewのインストール確認
if ! command -v brew &>/dev/null; then
    echo "[1/4] Homebrewをインストールします..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Apple Silicon の場合PATHを通す
    if [[ "$(uname -m)" == "arm64" ]]; then
        echo "" >> ~/.zprofile
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
        echo "[Apple Silicon] ~/.zprofile にHomebrew PATHを追加しました"
    fi
else
    echo "[1/4] Homebrew は既にインストール済みです"
fi

# Apple Silicon で brew コマンドが使えるか確認
if [[ "$(uname -m)" == "arm64" ]] && [[ -f /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

echo "[2/4] gitをインストールします..."
brew install git

# 古い Intel 用 git バイナリを除去
if [[ -f /usr/local/bin/git ]]; then
    echo "[3/4] 古いIntel用 git (/usr/local/bin/git) を削除します..."
    sudo rm /usr/local/bin/git
    echo "      削除完了"
else
    echo "[3/4] /usr/local/bin/git は存在しないためスキップ"
fi

echo "[4/4] インストール確認..."
git --version

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ: git の初期設定"
echo "  git config --global user.name \"あなたの名前\""
echo "  git config --global user.email \"your@email.com\""
