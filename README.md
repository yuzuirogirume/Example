# airline-sale-watcher

毎週火曜の朝4時にANA / JAL のタイムセールページを巡回し、現在進行中のセールがあれば
Google カレンダーに終日予定として登録します。

## 巡回先

| キー | URL |
| --- | --- |
| ANA 国内線 | https://www.ana.co.jp/ja/jp/domestic/theme/timesale/sale/ |
| ANA SUPER VALUE | https://www.ana.co.jp/ja/jp/domestic/theme/timesale/sv/ |
| ANA 国際線 | https://www.ana.co.jp/ja/jp/international/theme/special_prj/ |
| JAL 国内線 | https://www.jal.co.jp/jp/ja/dom/special/timesale/ |
| JAL 国際線 | https://www.jal.co.jp/jp/ja/inter/special/sale/ |

ページ本文に「販売期間」「申込期間」などのキーワードがあり、その近くに今日を含む
日付範囲があれば「セール開催中」と判定します。誤検知を抑えるため、キーワード周辺の
240文字を見て、`YYYY年M月D日 〜 ...`、`YYYY/M/D 〜 ...`、`M/D 〜 M/D` の3形式を抽出します。

## セットアップ

### 1. 依存パッケージ

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### 2. Google Calendar API の認可

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成し、
   「Google Calendar API」を有効化。
2. 「OAuth 同意画面」を設定し、テストユーザーに自分のGmailアドレスを追加。
3. 「認証情報」→「OAuth クライアント ID」を作成。種別は **デスクトップアプリ**。
4. JSON をダウンロードし、リポジトリ直下に `client_secret.json` として保存。
5. 初回認可フローを実行：

   ```bash
   GCAL_CALENDAR_ID=your.email@gmail.com python init_oauth.py
   ```

   ブラウザが開くので、対象の Gmail アカウントでログイン → カレンダー権限を許可。
   `token.json` が作成されます（refresh token 付き、以降は自動更新）。

### 3. 環境変数

`.env.example` を `.env` にコピーしてカレンダーIDを記入。`.env` は git 管理外です。

```env
GCAL_CALENDAR_ID=your.email@gmail.com
GCAL_OAUTH_CLIENT_FILE=./client_secret.json
GCAL_TOKEN_FILE=./token.json
```

### 4. 動作確認

```bash
set -a && . .env && set +a
.venv/bin/python check_airline_sales.py
```

セールが進行中なら `created event ...` が、なければ `no active sale` が出力されます。

## cron 登録（毎週火曜 4:00 JST）

```cron
# crontab -e
TZ=Asia/Tokyo
0 4 * * 2 cd /path/to/repo && set -a && . ./.env && set +a && ./.venv/bin/python check_airline_sales.py >> ./run.log 2>&1
```

サーバー時刻が JST でない場合は `TZ=Asia/Tokyo` を必ず付与してください。マシンが
火曜4時に必ず起動している必要があります（ノートPCなどで休止していると当該回はスキップ
される点に注意）。常時稼働させたくない場合は systemd の OnCalendar + Persistent=true
を使うと、復帰後に取りこぼしを実行できます。

## 補足

- イベントは `summary` を一致条件として重複登録を回避します（同じ販売期間内に再実行しても二重登録しない）。
- ANA / JAL のページ構造が変わると検出精度が落ちる可能性があります。`no active sale` が
  続くようなら HTML を確認して `SALE_KEYWORDS` や正規表現を調整してください。
- JS で動的に生成される本文がある場合は requests / BeautifulSoup では取れません。
  必要に応じて Playwright に置き換える前提で `fetch_page_text` を分離してあります。
