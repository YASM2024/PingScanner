IP_STATUS_TABLE = """
CREATE TABLE IF NOT EXISTS ip_status (

    ip_index INTEGER PRIMARY KEY,

    ip TEXT UNIQUE,

    hostname TEXT,

    remark TEXT,

    first_found DATETIME,

    last_check DATETIME,

    last_reply DATETIME,

    last_result INTEGER,

    consecutive_fail INTEGER DEFAULT 0
);
"""


PING_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS ping_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    check_time DATETIME,

    ip TEXT,

    result INTEGER
);
"""


SCAN_STATE_TABLE = """
CREATE TABLE IF NOT EXISTS scan_state (
    current_index INTEGER
);
"""


SCAN_META_TABLE = """
CREATE TABLE IF NOT EXISTS scan_meta (
    network TEXT NOT NULL
);
"""