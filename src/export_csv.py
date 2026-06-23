import sys
from pathlib import Path

if not getattr(sys, "frozen", False):
    _src_dir = Path(__file__).resolve().parent
    _src = str(_src_dir)
    if _src not in sys.path:
        sys.path.insert(0, _src)

import csv
import sqlite3
from datetime import datetime

from config import Config


def main():

    cfg = Config()

    #
    # DB接続
    #
    db_file = Path(cfg.db_file)

    print(f"DB_FILE={db_file}")

    if not db_file.exists():

        print("ERROR: DB file not found")

        return

    conn = sqlite3.connect(
        str(db_file)
    )

    cur = conn.cursor()

    #
    # 出力先
    #
    export_dir = Path(cfg.export_dir)

    export_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    csv_file = (
        export_dir /
        f"{timestamp}_ip_status.csv"
    )

    #
    # データ取得
    #
    cur.execute(
        """
        SELECT
            ip,
            hostname,
            remark,
            first_found,
            last_check,
            last_reply,
            last_result,
            consecutive_fail
        FROM ip_status
        ORDER BY ip_index
        """
    )

    rows = cur.fetchall()

    #
    # CSV出力
    #
    with open(
        csv_file,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.writer(f)

        writer.writerow(
            [
                "IP",
                "Hostname",
                "Remark",
                "FirstFound",
                "LastCheck",
                "LastReply",
                "LastResult",
                "ConsecutiveFail"
            ]
        )

        writer.writerows(rows)

    conn.close()

    print(
        f"Export Complete : {csv_file}"
    )

    print(
        f"Rows : {len(rows)}"
    )


if __name__ == "__main__":
    main()