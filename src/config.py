import sys
from configparser import ConfigParser
from pathlib import Path

from db_resolver import resolve_db_path_for_network

_SRC_DIR = Path(__file__).resolve().parent

if not getattr(sys, "frozen", False):
    src = str(_SRC_DIR)
    if src not in sys.path:
        sys.path.insert(0, src)


def get_app_root():

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return _SRC_DIR.parent


def resolve_app_path(path_value):

    path = Path(path_value)

    if path.is_absolute():
        return str(path)

    return str((get_app_root() / path).resolve())


class Config:

    def __init__(self):

        root_dir = get_app_root()
        ini_file = root_dir / "config.ini"

        if not ini_file.exists():
            raise RuntimeError(
                f"config.ini not found : {ini_file}"
            )

        cfg = ConfigParser()

        cfg.read(ini_file, encoding="utf-8")

        if "SCAN" not in cfg:
            raise RuntimeError(
                f"SCAN section not found : {ini_file}"
            )

        self.app_root = str(root_dir)
        self.ini_file = str(ini_file)

        self.network = cfg["SCAN"]["NETWORK"]

        self.days_per_cycle = int(
            cfg["SCAN"]["DAYS_PER_CYCLE"]
        )

        self.ping_timeout = int(
            cfg["SCAN"]["PING_TIMEOUT"]
        )

        self.parallel = int(
            cfg["SCAN"]["PARALLEL"]
        )

        self.ping_interval_ms = int(
            cfg["SCAN"].get(
                "PING_INTERVAL_MS",
                200,
            )
        )

        self.log_dir = resolve_app_path(
            cfg["SCAN"]["LOG_DIR"]
        )

        db_path = resolve_db_path_for_network(
            self.network,
            root_dir,
        )

        self.db_file = str(db_path)

        if "EXPORT" not in cfg:
            raise RuntimeError(
                f"EXPORT section not found : {ini_file}"
            )

        self.export_dir = resolve_app_path(
            cfg["EXPORT"]["CSV_DIR"]
        )
