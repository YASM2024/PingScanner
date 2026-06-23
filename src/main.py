import sys

from pathlib import Path



if not getattr(sys, "frozen", False):

    _src_dir = Path(__file__).resolve().parent

    _src = str(_src_dir)

    if _src not in sys.path:

        sys.path.insert(0, _src)



import math



from config import Config, get_app_root

from db_resolver import prepare_database

from logger import setup_logger

from run_lock import RunLock, RunLockError

from scan_control import ScanAborted, StopController

from scanner import PingScanner



BATCH_COMMIT_SIZE = 100





def main():



    cfg = Config()



    Path(cfg.log_dir).mkdir(

        parents=True,

        exist_ok=True,

    )



    logger = setup_logger(cfg.log_dir)



    lock_path = (

        get_app_root()

        / "pingscanner.lock"

    )



    try:

        with RunLock(lock_path):

            _run_scan(cfg, logger)

    except RunLockError as exc:

        logger.error(str(exc))

        sys.exit(1)





def _abort_scan(

    db,

    logger,

    stop,

    current_index,

    processed,

    reason,

):



    db.commit()



    if processed > 0:

        db.set_current_index(

            current_index + processed

        )



    stop.consume_stop_file()



    logger.warning(

        f"ABORTED: {reason} "

        f"processed={processed} "

        f"next_index="

        f"{current_index + processed}"

    )



    db.close()





def _run_scan(cfg, logger):



    stop = StopController(

        get_app_root() / "pingscanner.stop"

    )

    stop.install_signal_handler()



    logger.info("START")

    logger.info(f"NETWORK={cfg.network}")



    db, scan_network = prepare_database(

        cfg.network,

        get_app_root(),

        logger,

    )



    total_ip = db.get_total_ip_count(

        scan_network

    )



    scan_count = math.ceil(

        total_ip / cfg.days_per_cycle

    )



    current_index = db.get_current_index()



    logger.info(f"TOTAL_IP={total_ip}")

    logger.info(f"SCAN_COUNT={scan_count}")

    logger.info(

        f"CURRENT_INDEX={current_index}"

    )

    logger.info(

        f"PING_INTERVAL_MS="

        f"{cfg.ping_interval_ms}"

    )



    ip_list = db.get_ip_range(

        current_index,

        scan_count,

        scan_network,

    )



    scanner = PingScanner(

        timeout_ms=cfg.ping_timeout,

        parallel=cfg.parallel,

        ping_interval_ms=(

            cfg.ping_interval_ms

        ),

        stop_controller=stop,

    )



    success_count = 0

    processed = 0



    try:



        for i, (

            ip,

            success,

            checked_at,

        ) in enumerate(

            scanner.scan_iter(ip_list)

        ):



            db.update_ping_result(

                ip,

                success,

                checked_at,

                commit=False,

            )



            processed += 1



            if success:

                success_count += 1



            logger.info(

                f"{ip} "

                f"{'SUCCESS' if success else 'FAIL'}"

            )



            if (

                (i + 1) % BATCH_COMMIT_SIZE

                == 0

            ):

                db.commit()



    except (KeyboardInterrupt, ScanAborted) as exc:



        reason = (

            "Ctrl+C"

            if isinstance(

                exc, KeyboardInterrupt

            )

            else "stop file"

        )



        _abort_scan(

            db,

            logger,

            stop,

            current_index,

            processed,

            reason,

        )



        sys.exit(130)



    db.commit()



    next_index = current_index + scan_count



    if next_index >= total_ip:

        next_index = 0



    db.set_current_index(next_index)



    logger.info(f"SUCCESS={success_count}")

    logger.info(

        f"FAIL={processed - success_count}"

    )

    logger.info(f"NEXT_INDEX={next_index}")



    db.close()



    logger.info("END")





if __name__ == "__main__":

    main()

