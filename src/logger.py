import logging
import os
from datetime import datetime


def setup_logger(log_dir):

    os.makedirs(log_dir, exist_ok=True)

    logfile = os.path.join(
        log_dir,
        datetime.now().strftime("%Y%m%d") + ".log"
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(logfile, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger("PingScanner")