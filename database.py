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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS custom_brands (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS captcha_attempts (
            ip          TEXT PRIMARY KEY,
            attempts    INTEGER NOT NULL DEFAULT 0,
            locked_until REAL NOT NULL DEFAULT 0
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
    cur.execute("DELETE FROM custom_brands")
    conn.commit()
    conn.close()


def add_custom_brand(brand):
    """Uloží název vlastní značky telefonu."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO custom_brands (brand) VALUES (?)", (brand,))
    conn.commit()
    conn.close()


def get_captcha_state(ip):
    """Vrátí (attempts, locked_until) pro danou IP."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT attempts, locked_until FROM captcha_attempts WHERE ip = ?", (ip,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row["attempts"], row["locked_until"]
    return 0, 0.0


def record_captcha_failure(ip, max_attempts, lockout_seconds):
    """
    Zaznamená neúspěšný pokus pro IP.
    Pokud počet dosáhne max_attempts, nastaví locked_until.
    Vrátí (locked, locked_until, remaining_attempts).
    """
    import time
    now = time.time()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO captcha_attempts (ip, attempts, locked_until) VALUES (?, 1, 0) "
        "ON CONFLICT(ip) DO UPDATE SET attempts = attempts + 1",
        (ip,)
    )
    cur.execute("SELECT attempts FROM captcha_attempts WHERE ip = ?", (ip,))
    attempts = cur.fetchone()["attempts"]

    locked_until = 0.0
    if attempts >= max_attempts:
        locked_until = now + lockout_seconds
        cur.execute(
            "UPDATE captcha_attempts SET attempts = 0, locked_until = ? WHERE ip = ?",
            (locked_until, ip)
        )

    conn.commit()
    conn.close()
    locked = locked_until > 0
    remaining_attempts = max(0, max_attempts - attempts)
    return locked, locked_until, remaining_attempts


def clear_captcha_attempts(ip):
    """Vymaže záznamy po úspěšném ověření."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM captcha_attempts WHERE ip = ?", (ip,))
    conn.commit()
    conn.close()


def get_custom_brands():
    """Vrátí seznam vlastních značek."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT brand FROM custom_brands ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [row["brand"] for row in rows]
