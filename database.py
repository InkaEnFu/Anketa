import sqlite3
import config


def get_connection():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Vytvoří tabulku hlasů, pokud ještě neexistuje, a doplní chybějící možnosti."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            option_id TEXT PRIMARY KEY,
            count     INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Zajistí, že každá možnost z konfigurace má v DB řádek
    for opt in config.OPTIONS:
        cur.execute(
            "INSERT OR IGNORE INTO votes (option_id, count) VALUES (?, 0)",
            (opt["id"],)
        )
    conn.commit()
    conn.close()


def get_results():
    """Vrátí slovník {option_id: count} pro všechny možnosti."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT option_id, count FROM votes")
    rows = cur.fetchall()
    conn.close()
    return {row["option_id"]: row["count"] for row in rows}


def add_vote(option_id):
    """Přidá jeden hlas ke zvolené možnosti. Vrátí False, pokud option_id neexistuje."""
    valid_ids = {opt["id"] for opt in config.OPTIONS}
    if option_id not in valid_ids:
        return False
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE votes SET count = count + 1 WHERE option_id = ?",
        (option_id,)
    )
    conn.commit()
    conn.close()
    return True


def reset_votes():
    """Vynuluje všechny hlasy."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE votes SET count = 0")
    conn.commit()
    conn.close()
