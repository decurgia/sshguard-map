import argparse
import sqlite3

parser = argparse.ArgumentParser(description="Import blacklist into database.")
parser.add_argument(
    "-b",
    "--blacklist",
    default="/var/db/sshguard/blacklist.db",
    type=str,
    help="Path to sshguard blacklist.db file (default: /dev/db/sshguard/blacklist.db)",
)
args = parser.parse_args()

try:
    blacklist_file = open(args.blacklist)
except FileNotFoundError as err:
    print(err)
    parser.print_help()
    quit()

blacklist_db = sqlite3.connect("blacklist.sqlite")
blacklist_cursor = blacklist_db.cursor()

blacklist_cursor.execute(
    """CREATE TABLE IF NOT EXISTS Blacklist
            (ip_address TEXT PRIMARY KEY UNIQUE,
            updated_on TEXT,
            latitude REAL,
            longitude REAL,
            organization TEXT,
            iso_code TEXT)"""
)

blacklist_cursor.execute(
    """CREATE TRIGGER IF NOT EXISTS blacklist_record_inserted
            AFTER INSERT ON Blacklist
            BEGIN
                UPDATE Blacklist
                SET updated_on = DATETIME('now')
                WHERE ip_address = NEW.ip_address;
            END"""
)

blacklist_cursor.execute(
    """CREATE TRIGGER IF NOT EXISTS blacklist_record_updated
            AFTER UPDATE ON Blacklist
            BEGIN
                UPDATE Blacklist
                SET updated_on = DATETIME('now')
                WHERE ip_address = NEW.ip_address;
            END"""
)

for entry in blacklist_file:
    pieces = entry.split("|")
    ip_address = pieces[3].rstrip()

    blacklist_cursor.execute(
        """INSERT OR IGNORE INTO Blacklist (ip_address) VALUES (?)""",
        (ip_address,),
    )

blacklist_db.commit()
blacklist_cursor.close()
