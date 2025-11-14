import pandas as pd
from PyQt5.QtSql import QSqlDatabase, QSqlQuery

# ---- Temporary database logic ----

def init_db(logger, db_path):
    '''Initializes the SQLite DB and creates the table if necessary using PyQt5.'''
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(db_path)

    if not db.open():
        logger.error("Failed to open database: %s", db.lastError().text())
        return None

    query = QSqlQuery(db)
    query.exec(f'''
    CREATE TABLE IF NOT EXISTS RawMeasurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_eui TEXT,
        timestamp TEXT,
        relay_id TEXT,
        gateway_id TEXT,
        fcnt INTEGER,
        a0 REAL,
        a1 REAL,
        a2 REAL,
        a3 REAL,
        a4 REAL,
        a5 REAL
    )
    ''')
    if query.lastError().isValid():
        logger.error("Failed to create table: %s", query.lastError().text())
    else:
        logger.info("Table '%s' initialized in DB '%s'", "RawMeasurements", db_path)
    return db


def insert_record(logger, db, rec):
    '''Insert a record into the database using PyQt5.'''
    query = QSqlQuery(db)
    query.prepare(f'''
        INSERT INTO RawMeasurements (
            device_eui, timestamp, relay_id, gateway_id, fcnt, a0, a1, a2, a3, a4, a5
        ) VALUES (:device_eui, :timestamp, :relay_id, :gateway_id, :fcnt, :a0, :a1, :a2, :a3, :a4, :a5)
    ''')

    query.bindValue(":device_eui", rec.get("device_eui"))
    query.bindValue(":timestamp", rec.get("timestamp"))
    query.bindValue(":relay_id", rec.get("relay_id"))
    query.bindValue(":gateway_id", rec.get("gateway_id"))
    query.bindValue(":fcnt", rec.get("fcnt"))
    query.bindValue(":a0", rec.get("a0"))
    query.bindValue(":a1", rec.get("a1"))
    query.bindValue(":a2", rec.get("a2"))
    query.bindValue(":a3", rec.get("a3"))
    query.bindValue(":a4", rec.get("a4"))
    query.bindValue(":a5", rec.get("a5"))

    if not query.exec():
        logger.error("Failed to insert record: %s", query.lastError().text())
    else:
        logger.info("Record inserted successfully.")

    return query.lastInsertId()


def export_csv(logger, conn, out_path):
    query = QSqlQuery(conn)
    if not query.exec(f"SELECT * FROM RawMeasurements"):
        logger.error("Failed to execute SELECT for export: %s", query.lastError().text())
        return False
    
    rec = query.record()
    cols = [rec.fieldName(i) for i in range(rec.count())]
    rows = []

    while query.next():
        rows.append([query.value(i) for i in range(rec.count())])

    try:
        df = pd.DataFrame(rows, columns=cols)
        df.to_csv(out_path, index=False, encoding='utf-8')
        logger.info("Export CSV done: %s (rows: %d, cols: %d)", out_path, len(rows), len(cols))
        return True
    except Exception as e:
        logger.exception("Failed to write CSV: %s", e)
        return False