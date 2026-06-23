import sqlite3
import ipaddress

from datetime import datetime

from models import (
    IP_STATUS_TABLE,
    PING_LOG_TABLE,
    SCAN_META_TABLE,
    SCAN_STATE_TABLE,
)


class Database:

    def __init__(self, dbfile):

        self.conn = sqlite3.connect(
            dbfile,
            check_same_thread=False
        )

        self.create_tables()

    # ----------------------------------------
    # テーブル生成
    # ----------------------------------------
    def create_tables(self):

        cur = self.conn.cursor()

        cur.execute(IP_STATUS_TABLE)
        cur.execute(PING_LOG_TABLE)
        cur.execute(SCAN_STATE_TABLE)
        cur.execute(SCAN_META_TABLE)

        self.conn.commit()

        cur.execute(
            "SELECT COUNT(*) FROM scan_state"
        )

        if cur.fetchone()[0] == 0:

            cur.execute(
                """
                INSERT INTO scan_state(
                    current_index
                )
                VALUES(0)
                """
            )

            self.conn.commit()

    # ----------------------------------------
    # scan_meta
    # ----------------------------------------
    def get_stored_network(self):

        cur = self.conn.cursor()

        cur.execute(
            """
            SELECT network
            FROM scan_meta
            LIMIT 1
            """
        )

        row = cur.fetchone()

        return row[0] if row else None

    def set_stored_network(self, network):

        cur = self.conn.cursor()

        cur.execute("DELETE FROM scan_meta")

        cur.execute(
            """
            INSERT INTO scan_meta(network)
            VALUES(?)
            """,
            (network,),
        )

        self.conn.commit()

    def infer_stored_network(self):

        count = self.count_ip_status()

        if count == 0:
            return None

        cur = self.conn.cursor()

        cur.execute(
            """
            SELECT ip
            FROM ip_status
            ORDER BY ip_index ASC
            LIMIT 1
            """
        )

        first_ip = ipaddress.ip_address(
            cur.fetchone()[0]
        )

        cur.execute(
            """
            SELECT ip
            FROM ip_status
            ORDER BY ip_index DESC
            LIMIT 1
            """
        )

        last_ip = ipaddress.ip_address(
            cur.fetchone()[0]
        )

        from network_utils import network_host_count

        for prefixlen in range(32, 0, -1):

            net = ipaddress.ip_network(
                (first_ip, prefixlen),
                strict=False,
            )

            if network_host_count(net) != count:
                continue

            if (
                first_ip in net
                and last_ip in net
            ):
                return str(net)

        return None

    def ensure_stored_network(self, logger=None):

        stored = self.get_stored_network()

        if stored:
            return stored

        inferred = self.infer_stored_network()

        if inferred:

            self.set_stored_network(inferred)

            if logger:
                logger.info(
                    "DB meta inferred: "
                    f"{inferred}"
                )

            return inferred

        return None

    def rebuild(self, network):

        cur = self.conn.cursor()

        cur.execute(
            "DROP TABLE IF EXISTS ip_status"
        )
        cur.execute(
            "DROP TABLE IF EXISTS ping_log"
        )
        cur.execute(
            "DROP TABLE IF EXISTS scan_state"
        )
        cur.execute(
            "DROP TABLE IF EXISTS scan_meta"
        )

        self.conn.commit()

        self.create_tables()

        self.initialize_ip_status(network)

        self.set_stored_network(network)

        self.set_current_index(0)

    # ----------------------------------------
    # scan_state
    # ----------------------------------------
    def get_current_index(self):

        cur = self.conn.cursor()

        cur.execute(
            """
            SELECT current_index
            FROM scan_state
            """
        )

        row = cur.fetchone()

        return row[0]

    def set_current_index(self, value):

        cur = self.conn.cursor()

        cur.execute(
            """
            UPDATE scan_state
            SET current_index=?
            """,
            (value,)
        )

        self.conn.commit()

    # ----------------------------------------
    # 初期投入
    # ----------------------------------------
    def count_ip_status(self):

        cur = self.conn.cursor()

        cur.execute(
            """
            SELECT COUNT(*)
            FROM ip_status
            """
        )

        return cur.fetchone()[0]

    def initialize_ip_status(
        self,
        network,
    ):

        if self.count_ip_status() > 0:
            return

        cur = self.conn.cursor()

        net = ipaddress.ip_network(
            network,
            strict=False,
        )

        rows = []

        for idx, ip in enumerate(net):

            rows.append(
                (
                    idx,
                    str(ip),
                )
            )

        cur.executemany(
            """
            INSERT INTO ip_status(
                ip_index,
                ip
            )
            VALUES(
                ?,
                ?
            )
            """,
            rows,
        )

        self.conn.commit()

    def _is_full_network_scan(
        self,
        scan_network,
    ):

        stored = self.get_stored_network()

        if not stored or not scan_network:
            return True

        return (
            ipaddress.ip_network(
                scan_network,
                strict=False,
            )
            == ipaddress.ip_network(
                stored,
                strict=False,
            )
        )

    def _get_scannable_rows(
        self,
        scan_network=None,
    ):

        cur = self.conn.cursor()

        cur.execute(
            """
            SELECT ip_index, ip
            FROM ip_status
            ORDER BY ip_index
            """
        )

        rows = cur.fetchall()

        if not scan_network:
            return rows

        net = ipaddress.ip_network(
            scan_network,
            strict=False,
        )

        return [
            (idx, ip)
            for idx, ip in rows
            if ipaddress.ip_address(ip) in net
        ]

    # ----------------------------------------
    # 件数取得
    # ----------------------------------------
    def get_total_ip_count(
        self,
        scan_network=None,
    ):

        if self._is_full_network_scan(
            scan_network
        ):

            cur = self.conn.cursor()

            cur.execute(
                """
                SELECT COUNT(*)
                FROM ip_status
                """
            )

            return cur.fetchone()[0]

        return len(
            self._get_scannable_rows(
                scan_network,
            )
        )

    # ----------------------------------------
    # 巡回対象取得
    # ----------------------------------------
    def get_ip_range(
        self,
        start_index,
        count,
        scan_network=None,
    ):

        if self._is_full_network_scan(
            scan_network
        ):

            return self._get_ip_range_full(
                start_index,
                count,
            )

        rows = self._get_scannable_rows(
            scan_network,
        )

        total = len(rows)

        if total == 0:
            return []

        if start_index >= total:
            start_index = 0

        selected = []

        for i in range(count):

            pos = (start_index + i) % total
            selected.append(rows[pos][1])

        return selected

    def _get_ip_range_full(
        self,
        start_index,
        count,
    ):

        total = self.get_total_ip_count()

        result = []

        cur = self.conn.cursor()

        if start_index + count <= total:

            cur.execute(
                """
                SELECT ip
                FROM ip_status
                WHERE ip_index >= ?
                ORDER BY ip_index
                LIMIT ?
                """,
                (
                    start_index,
                    count,
                ),
            )

            result.extend(
                [r[0] for r in cur.fetchall()]
            )

        else:

            first_count = (
                total - start_index
            )

            second_count = (
                count - first_count
            )

            cur.execute(
                """
                SELECT ip
                FROM ip_status
                WHERE ip_index >= ?
                ORDER BY ip_index
                """,
                (start_index,),
            )

            result.extend(
                [r[0] for r in cur.fetchall()]
            )

            cur.execute(
                """
                SELECT ip
                FROM ip_status
                WHERE ip_index < ?
                ORDER BY ip_index
                """,
                (second_count,),
            )

            result.extend(
                [r[0] for r in cur.fetchall()]
            )

        return result

    # ----------------------------------------
    # 結果更新
    # ----------------------------------------
    def _format_checked_at(self, checked_at):

        if isinstance(checked_at, datetime):
            return checked_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        return checked_at

    def update_ping_result(
        self,
        ip,
        success,
        checked_at,
        commit=True,
    ):

        now = self._format_checked_at(
            checked_at
        )

        cur = self.conn.cursor()

        # 履歴保存

        cur.execute(
            """
            INSERT INTO ping_log(
                check_time,
                ip,
                result
            )
            VALUES(
                ?,
                ?,
                ?
            )
            """,
            (
                now,
                ip,
                1 if success else 0
            )
        )

        # 応答あり

        if success:

            cur.execute(
                """
                UPDATE ip_status
                SET
                    last_check=?,
                    last_reply=?,
                    last_result=1,
                    consecutive_fail=0,
                    first_found=
                        COALESCE(
                            first_found,
                            ?
                        )
                WHERE ip=?
                """,
                (
                    now,
                    now,
                    now,
                    ip
                )
            )

        # 応答なし

        else:

            cur.execute(
                """
                UPDATE ip_status
                SET
                    last_check=?,
                    last_result=0,
                    consecutive_fail=
                        consecutive_fail + 1
                WHERE ip=?
                """,
                (
                    now,
                    ip
                )
            )

        if commit:
            self.conn.commit()

    def commit(self):

        self.conn.commit()

    # ----------------------------------------
    # remark
    # ----------------------------------------
    def get_ip_status(self, ip):

        cur = self.conn.cursor()

        cur.execute(
            """
            SELECT
                ip,
                remark,
                last_reply,
                first_found
            FROM ip_status
            WHERE ip=?
            """,
            (ip,)
        )

        row = cur.fetchone()

        if not row:
            return None

        return {
            "ip": row[0],
            "remark": row[1],
            "last_reply": row[2],
            "first_found": row[3],
        }

    def get_ips_by_index_range(
        self,
        start_ip,
        end_ip
    ):

        cur = self.conn.cursor()

        cur.execute(
            """
            SELECT ip_index
            FROM ip_status
            WHERE ip=?
            """,
            (start_ip,)
        )

        start_row = cur.fetchone()

        cur.execute(
            """
            SELECT ip_index
            FROM ip_status
            WHERE ip=?
            """,
            (end_ip,)
        )

        end_row = cur.fetchone()

        if not start_row or not end_row:
            missing = []

            if not start_row:
                missing.append(start_ip)

            if not end_row:
                missing.append(end_ip)

            return None, missing

        start_index = start_row[0]
        end_index = end_row[0]

        if start_index > end_index:
            start_index, end_index = (
                end_index,
                start_index
            )

        cur.execute(
            """
            SELECT
                ip,
                last_reply
            FROM ip_status
            WHERE ip_index >= ?
              AND ip_index <= ?
            ORDER BY ip_index
            """,
            (
                start_index,
                end_index
            )
        )

        return cur.fetchall(), []

    def update_remarks(
        self,
        ips,
        remark
    ):

        cur = self.conn.cursor()

        cur.executemany(
            """
            UPDATE ip_status
            SET remark=?
            WHERE ip=?
            """,
            [
                (remark, ip)
                for ip in ips
            ]
        )

        self.conn.commit()

        return len(ips)

    # ----------------------------------------
    # DBクローズ
    # ----------------------------------------
    def close(self):

        if self.conn:
            self.conn.close()