import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "veervrat_cms.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS virtue (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name_en TEXT NOT NULL UNIQUE,
            name_mr TEXT
        );

        CREATE TABLE IF NOT EXISTS subvirtue (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name_en     TEXT NOT NULL UNIQUE,
            name_mr     TEXT,
            virtue_id   INTEGER NOT NULL REFERENCES virtue(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS weakness (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name_en  TEXT NOT NULL UNIQUE,
            name_mr  TEXT,
            category TEXT CHECK(category IN ('A','B','C'))
        );

        CREATE TABLE IF NOT EXISTS weakness_subvirtue (
            weakness_id   INTEGER NOT NULL REFERENCES weakness(id) ON DELETE CASCADE,
            subvirtue_id  INTEGER NOT NULL REFERENCES subvirtue(id) ON DELETE CASCADE,
            priority      INTEGER DEFAULT 0,
            PRIMARY KEY (weakness_id, subvirtue_id)
        );

        CREATE TABLE IF NOT EXISTS sentence (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            text_en       TEXT NOT NULL,
            text_mr       TEXT,
            subvirtue_id  INTEGER NOT NULL REFERENCES subvirtue(id) ON DELETE CASCADE,
            source_file   TEXT,
            notes         TEXT
        );

        CREATE TABLE IF NOT EXISTS exposure (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            sentence_id   INTEGER NOT NULL REFERENCES sentence(id) ON DELETE CASCADE,
            tier          TEXT CHECK(tier IN ('local','national','international')),
            title         TEXT NOT NULL,
            description   TEXT,
            sort_order    INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS resolution (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            sentence_id    INTEGER NOT NULL REFERENCES sentence(id) ON DELETE CASCADE,
            title          TEXT NOT NULL,
            description    TEXT,
            duration_weeks INTEGER,
            sort_order     INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS challenge (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            sentence_id   INTEGER NOT NULL REFERENCES sentence(id) ON DELETE CASCADE,
            title         TEXT NOT NULL,
            description   TEXT,
            duration_days INTEGER
        );
    """)

    conn.commit()
    conn.close()
