<p align="center">
  <img src="logo.png" alt="PingScanner" width="200">
</p>

# PingScanner

設定した IP ネットワーク（CIDR 形式）に対して定期的に ICMP Echo（PING）を送信し、生存確認・最終応答日時・連続失敗回数・履歴・備考（Remark）を管理する Windows 向けツールです。

Windows タスクスケジューラから `main.exe` を毎日実行することを前提としています。

## システム構成

ビルド後は次の 3 つの実行ファイルで構成されます。

| 実行ファイル | 用途 |
|---|---|
| `main.exe` | PING 巡回スキャン（タスクスケジューラ実行対象） |
| `export_csv.exe` | `ip_status` を CSV 出力 |
| `remark_ui.exe` | Remark 登録 GUI |

### 配置ファイル・データ

EXE と同じディレクトリ（または `config.ini` で指定したパス）に配置します。

```
dist\
├─ main.exe
├─ export_csv.exe
├─ remark_ui.exe
├─ config.ini              … ローカル設定（Git 管理外）
├─ config.sample.ini       … 設定テンプレート
├─ 192.168.1.0_26.db       … SQLite DB（NETWORK から自動命名）
├─ logs\                   … 日次ログ
└─ exports\                … CSV 出力先
```

SQLite DB・ログ・CSV は EXE 外部に配置します。`LOG_DIR` / `CSV_DIR` には相対パスまたは絶対パスを指定できます。

DB ファイル名は `NETWORK` 設定から自動決定されます（例: `192.168.1.0/26` → `192.168.1.0_26.db`）。

---

## config.ini の作り方

### 1. テンプレートをコピーする

`config.sample.ini` を `config.ini` にコピーします。

```bat
copy config.sample.ini config.ini
```

`config.ini` は環境ごとの設定のため Git 管理しません。配布・開発時は `config.sample.ini` をテンプレートとして使います。

### 2. 設定を編集する

`config.ini` の例:

```ini
[SCAN]

NETWORK=192.168.1.0/26

DAYS_PER_CYCLE=1

PING_TIMEOUT=5000

PARALLEL=4

PING_INTERVAL_MS=200

LOG_DIR=logs

[EXPORT]

CSV_DIR=exports
```

### 設定項目

#### [SCAN]

| 項目 | 説明 |
|---|---|
| `NETWORK` | スキャン対象ネットワーク（CIDR 形式）。例: `10.50.0.0/16`（65536 IP）、`192.168.1.0/26`（64 IP） |
| `DAYS_PER_CYCLE` | 全 IP を 1 周するのに要する日数 |
| `PING_TIMEOUT` | `ping -w` のタイムアウト（ミリ秒） |
| `PARALLEL` | 並列 PING 数（デフォルト 4） |
| `PING_INTERVAL_MS` | PING 送信間隔（ミリ秒、省略時 200） |
| `LOG_DIR` | ログ出力ディレクトリ（相対パスは EXE 配置ディレクトリ基準） |

#### [EXPORT]

| 項目 | 説明 |
|---|---|
| `CSV_DIR` | CSV エクスポート先ディレクトリ（相対パスは EXE 配置ディレクトリ基準） |

### 配置場所

- **EXE 実行時**: 各 EXE と同じディレクトリに `config.ini` を置く
- **開発時（`python src/main.py` など）**: プロジェクトルートに `config.ini` を置く

`config.ini` が見つからない場合、起動時にエラーになります。

---

## ビルド方法（PyInstaller）

### 前提

プロジェクトルートに Python 仮想環境 `pyenv` を用意し、PyInstaller をインストールしておきます。

```bat
python -m venv pyenv
pyenv\Scripts\activate
pip install pyinstaller
```

### ビルド実行

プロジェクトルートで `build.bat` を実行します。

```bat
build.bat
```

内部では次のコマンドが実行されます。

```bat
pyenv\Scripts\pyinstaller.exe --clean --noconfirm pingscanner.spec
```

### 成果物

```
dist\main.exe
dist\export_csv.exe
dist\remark_ui.exe
```

ビルド後は `dist\` に `config.ini`（`config.sample.ini` からコピー）を配置して使用します。

---

## 動作の説明

### main.exe（PING 巡回スキャン）

毎日起動時に、前回の続きから未巡回の IP をスキャンします。

#### 巡回方式

1. DB の `scan_state` テーブルで `current_index`（巡回位置）を保持
2. 1 日あたりの巡回数を自動計算:

   ```
   scan_count = ceil(総 IP 数 ÷ DAYS_PER_CYCLE)
   ```

   例: 65536 IP、`DAYS_PER_CYCLE=100` → 656 IP/日

3. `current_index` から `scan_count` 件の IP を PING
4. ネットワーク末尾を超える場合は先頭にラップアラウンドして連続取得
5. 1 周完了時（`next_index >= 総 IP 数`）は `current_index = 0` に戻る

#### 初回起動

DB が存在しない、または対象ネットワークの `ip_status` が空の場合:

- テーブル自動生成（`ip_status` / `ping_log` / `scan_state` / `scan_meta`）
- `NETWORK` から全 IP を `ip_index` 付きで `ip_status` に登録
- `scan_state` に `current_index = 0` を設定

DB ファイル・ログ・エクスポート先ディレクトリは存在しなければ自動生成されます。

#### PING 仕様

- Windows 標準 `ping` を subprocess で実行: `ping -n 1 -w {PING_TIMEOUT} {IP}`
- stdout に `ttl=` が含まれる → **SUCCESS**、それ以外 → **FAIL**
- `PARALLEL` で指定した数だけ `ThreadPoolExecutor` により並列実行

#### 記録内容（ip_status）

| 項目 | 内容 |
|---|---|
| `last_check` | 最後に PING した日時 |
| `last_reply` | 最後に応答があった日時 |
| `last_result` | 1=成功、0=失敗 |
| `consecutive_fail` | 連続失敗回数（成功時 0 にリセット） |
| `first_found` | 初回 PING 成功日時 |
| `remark` | 備考（`remark_ui.exe` で登録） |

PING 結果は `ping_log` テーブルにも履歴として永久保存されます。

#### ログ

`{LOG_DIR}\YYYYMMDD.log` に日次で出力します（標準出力にも同一内容を出力）。

```
2026-06-04 01:00:00 INFO START
2026-06-04 01:00:00 INFO NETWORK=10.50.0.0/16
2026-06-04 01:00:00 INFO TOTAL_IP=65536
2026-06-04 01:00:00 INFO SCAN_COUNT=656
2026-06-04 01:00:00 INFO CURRENT_INDEX=0
2026-06-04 01:00:01 INFO 10.50.0.1 SUCCESS
2026-06-04 01:00:02 INFO 10.50.0.2 FAIL
2026-06-04 01:03:10 INFO SUCCESS=120
2026-06-04 01:03:10 INFO FAIL=536
2026-06-04 01:03:10 INFO NEXT_INDEX=656
2026-06-04 01:03:10 INFO END
```

#### 同時実行の防止・中断

- `pingscanner.lock`: 二重起動を防止（既に実行中の場合はエラー終了）
- `pingscanner.stop`: このファイルを作成するとスキャンを安全に中断（処理済み分は DB に保存）
- `Ctrl+C` でも同様に中断可能

#### タスクスケジューラ（推奨）

毎日 01:00 などに `main.exe` を登録して自動実行します。`export_csv.exe` / `remark_ui.exe` は必要に応じて手動実行します。

---

### export_csv.exe（CSV エクスポート）

手動実行。`ip_status` 全件を CSV 出力します。

- 出力先: `{CSV_DIR}\{YYYYMMDD_HHMMSS}_ip_status.csv`
- 文字コード: UTF-8（BOM 付き）
- 出力列: `IP`, `Hostname`, `Remark`, `FirstFound`, `LastCheck`, `LastReply`, `LastResult`, `ConsecutiveFail`
- `ip_index` 順でソート

---

### remark_ui.exe（Remark 登録 GUI）

手動実行。Tkinter ベースの GUI で IP の備考を登録します。

- **個別登録**: 1 IP を指定して remark を設定
- **範囲一括登録**: 開始 IP〜終了 IP の範囲に同一 remark を設定
- PING 未応答（`last_reply` が NULL）の IP に登録する場合は警告ダイアログを表示

`remark` のみ更新します（`hostname` は未対応）。

---

## 開発時のソース構成

```
pingscanner\
├─ build.bat
├─ config.sample.ini
├─ pingscanner.spec
├─ src\
│   ├─ main.py         … スキャン本体
│   ├─ export_csv.py   … CSV エクスポート
│   ├─ remark_ui.py    … Remark GUI
│   ├─ config.py       … config.ini 読み込み
│   ├─ database.py     … DB アクセス
│   ├─ scanner.py      … PING 実行
│   └─ ...
└─ pyenv\              … ローカル仮想環境（Git 管理外）
```

開発時の実行例:

```bat
pyenv\Scripts\activate
python src\main.py
python src\export_csv.py
python src\remark_ui.py
```

---

## 参考

詳細な仕様は `定期PING監視ツール仕様書 v1.1.txt` を参照してください。
