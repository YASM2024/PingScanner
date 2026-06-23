import sqlite3
from pathlib import Path

import ipaddress

from network_utils import (
    network_to_db_filename,
    parse_network,
)


def _read_stored_network(db_path):

    try:

        conn = sqlite3.connect(
            f"file:{db_path}?mode=ro",
            uri=True,
        )

        cur = conn.cursor()

        cur.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
              AND name='scan_meta'
            """
        )

        if not cur.fetchone():
            conn.close()
            return None

        cur.execute(
            """
            SELECT network
            FROM scan_meta
            LIMIT 1
            """
        )

        row = cur.fetchone()
        conn.close()

        return row[0] if row else None

    except sqlite3.Error:
        return None


def _read_ip_count(db_path):

    try:

        conn = sqlite3.connect(
            f"file:{db_path}?mode=ro",
            uri=True,
        )

        cur = conn.cursor()

        cur.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
              AND name='ip_status'
            """
        )

        if not cur.fetchone():
            conn.close()
            return 0

        cur.execute(
            """
            SELECT COUNT(*)
            FROM ip_status
            """
        )

        count = cur.fetchone()[0]
        conn.close()

        return count

    except sqlite3.Error:
        return 0


def _infer_network_from_db(db_path):

    count = _read_ip_count(db_path)

    if count == 0:
        return None

    try:

        conn = sqlite3.connect(
            f"file:{db_path}?mode=ro",
            uri=True,
        )

        cur = conn.cursor()

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

        conn.close()

    except (sqlite3.Error, TypeError):
        return None

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


def find_containing_db(ini_net, app_root):

    candidates = []

    for path in sorted(app_root.glob("*.db")):

        stored = _read_stored_network(path)

        if stored:

            stored_net = parse_network(stored)

            if (
                ini_net.subnet_of(stored_net)
                or ini_net == stored_net
            ):
                candidates.append(
                    (path, stored_net)
                )

            continue

        inferred = _infer_network_from_db(path)

        if not inferred:
            continue

        inferred_net = parse_network(inferred)

        if (
            ini_net.subnet_of(inferred_net)
            or ini_net == inferred_net
        ):
            candidates.append(
                (path, inferred_net)
            )

    if not candidates:
        return None

    for path, net in candidates:

        if net == ini_net:
            return path

    candidates.sort(
        key=lambda item: item[1].prefixlen,
        reverse=True,
    )

    return candidates[0][0]


def resolve_db_path_for_network(
    network,
    app_root,
):

    ini_net = parse_network(network)
    app_root = Path(app_root)

    ini_path = (
        app_root
        / network_to_db_filename(network)
    )

    if ini_path.exists():
        return ini_path

    containing = find_containing_db(
        ini_net,
        app_root,
    )

    if containing:
        return containing

    return ini_path


def prepare_database(
    network,
    app_root,
    logger,
):

    from database import Database

    ini_net = parse_network(network)
    app_root = Path(app_root)

    ini_path = (
        app_root
        / network_to_db_filename(network)
    )

    ini_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    containing_path = find_containing_db(
        ini_net,
        app_root,
    )

    if (
        containing_path
        and containing_path != ini_path
        and not ini_path.exists()
    ):

        db = Database(str(containing_path))

        stored = db.ensure_stored_network(
            logger
        )

        logger.info(f"DB={containing_path}")
        logger.info(f"DB_NETWORK={stored}")
        logger.info(
            "SCAN_NETWORK="
            f"{network} (subset)"
        )

        return db, network

    if ini_path.exists():

        db = Database(str(ini_path))

        stored = db.ensure_stored_network(
            logger
        )

        stored_net = parse_network(stored)

        if (
            ini_net.subnet_of(stored_net)
            or ini_net == stored_net
        ):

            logger.info(f"DB={ini_path}")
            logger.info(
                f"DB_NETWORK={stored}"
            )

            if ini_net != stored_net:
                logger.info(
                    "SCAN_NETWORK="
                    f"{network} (subset)"
                )
            else:
                logger.info(
                    f"SCAN_NETWORK={network}"
                )

            return db, network

        logger.warning(
            "DB rebuild: "
            f"ini={network} "
            f"db={stored}"
        )

        db.rebuild(network)

        logger.info(
            f"SCAN_NETWORK={network}"
        )

        return db, network

    db = Database(str(ini_path))

    logger.info(f"DB create: {ini_path}")

    db.rebuild(network)

    logger.info(f"SCAN_NETWORK={network}")

    return db, network
