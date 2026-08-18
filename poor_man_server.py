import glob
import json
import logging
import os
import sqlite3
import sys
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("poor_man.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
logger.addHandler(file_handler)


class PoorManServer:
    def __init__(self, config_path):
        self.config_path = config_path
        self.read_config()
        self._last_status = None

    def read_config(self):
        with open(self.config_path) as f:
            config = json.load(f)
            logger.info(f"Read config from {config}")
        self.root_dir = config["poor_man_message_queue_root"]
        self.init_config_path = config["poor_man_message_init_config"]
        self.db_path = config["poor_man_db_path"]

    def setup_db(self):
        with open(self.init_config_path) as f:
            init_config = json.load(f)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS labs (
                    name TEXT PRIMARY KEY,
                    occupant TEXT,
                    checked_out_at TEXT
                )
                """
            )
            for lab in init_config["labs"]:
                conn.execute(
                    "INSERT OR IGNORE INTO labs (name, occupant, checked_out_at) VALUES (?, NULL, NULL)",
                    (lab,),
                )
        conn.close()
        logger.info(f"Set up db with labs: {init_config['labs']}")

    def poll_root(self):
        pattern = os.path.join(self.root_dir, "req_*.json")
        return sorted(glob.glob(pattern))

    def process_message(self, path):
        with open(path) as f:
            message = json.load(f)

        action = message.get("action")
        user = message.get("user")
        lab = message.get("lab")

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT occupant FROM labs WHERE name = ?", (lab,)).fetchone()

            if row is None:
                logger.info(f"Rejected '{action}' for unknown lab '{lab}' from {user}")
            elif action not in ("checkout", "release"):
                logger.info(f"Ignored unsupported action '{action}' from {user}")
            elif action == "checkout":
                cursor = conn.execute(
                    "UPDATE labs SET occupant = ?, checked_out_at = ? WHERE name = ? AND occupant IS NULL",
                    (user, message.get("timestamp"), lab),
                )
                if cursor.rowcount == 1:
                    logger.info(f"{user} checked out {lab}")
                else:
                    logger.info(f"{user} lost the race for {lab} (already occupied by {row[0]})")
            else:
                cursor = conn.execute(
                    "UPDATE labs SET occupant = NULL, checked_out_at = NULL WHERE name = ? AND occupant = ?",
                    (lab, user),
                )
                if cursor.rowcount == 1:
                    logger.info(f"{user} released {lab}")
                else:
                    logger.info(f"{user} could not release {lab} (not the current occupant)")

        conn.close()
        os.remove(path)

    def export_snapshot(self):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT name, occupant FROM labs").fetchall()
        conn.close()

        status = {name: occupant for name, occupant in rows}
        if status == self._last_status:
            return

        tmp_path = os.path.join(self.root_dir, ".status.json.tmp")
        final_path = os.path.join(self.root_dir, "status.json")
        with open(tmp_path, "w") as f:
            json.dump(status, f)
        os.replace(tmp_path, final_path)
        self._last_status = status

    def run(self, poll_interval=3):
        self.setup_db()
        while True:
            for path in self.poll_root():
                try:
                    self.process_message(path)
                except Exception:
                    logger.exception(f"Failed to process {path}, will retry next poll")
            try:
                self.export_snapshot()
            except Exception:
                logger.exception("Failed to export snapshot, will retry next poll")
            time.sleep(poll_interval)


if __name__ == "__main__":
    PoorManServer(sys.argv[1]).run()