from . import adapt_nodered_mqtt as anm
import argparse
import json
import sys

def load_config(config_path):
    with open(config_path, 'r') as config_file:
        return json.load(config_file)

if __name__ == "__main__":
    config = load_config('./src/receiver/settings/config.json')

    parser = argparse.ArgumentParser()
    parser.add_argument("--export", help="Export the DB into CSV and quit (file path)", default=None)
    args = parser.parse_args()

    if args.export:
        db_conn = anm.init_db(config['database']['filename'])
        anm.export_csv(db_conn, args.export)
        db_conn.close()
        sys.exit(0)

    anm.main_mqtt()