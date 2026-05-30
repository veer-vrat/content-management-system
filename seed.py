"""Seed the CMS database from existing CSVs in data/."""
import csv
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "veervrat_cms.db"
DATA_PATH = Path(__file__).parent.parent


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    # ── Virtues ──────────────────────────────────────────────
    with open(DATA_PATH / "virtues.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            c.execute(
                "INSERT OR IGNORE INTO virtue (name_en, name_mr) VALUES (?, ?)",
                (row["name_en"].strip(), row.get("name_mr", "").strip()),
            )

    # ── Subvirtues ───────────────────────────────────────────
    with open(DATA_PATH / "subvirtues.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            virtue_name = row["virtue_name_en"].strip()
            vid = c.execute(
                "SELECT id FROM virtue WHERE name_en = ?", (virtue_name,)
            ).fetchone()
            if vid:
                c.execute(
                    "INSERT OR IGNORE INTO subvirtue (name_en, name_mr, virtue_id) VALUES (?, ?, ?)",
                    (row["name_en"].strip(), row.get("name_mr", "").strip(), vid[0]),
                )

    # ── Weaknesses ───────────────────────────────────────────
    with open(DATA_PATH / "weakness.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            c.execute(
                "INSERT OR IGNORE INTO weakness (name_en, name_mr, category) VALUES (?, ?, ?)",
                (row["name_en"].strip(), row.get("name_mr", "").strip(), row.get("category", "").strip()),
            )

    # ── Weakness ↔ Subvirtue links ───────────────────────────
    with open(DATA_PATH / "weakness_subvirtues.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            wname = row["weakness_name_en"].strip()
            svname = row["subvirtue_name_en"].strip()
            priority = int(row.get("priority", 0) or 0)
            wid = c.execute("SELECT id FROM weakness WHERE name_en = ?", (wname,)).fetchone()
            svid = c.execute("SELECT id FROM subvirtue WHERE name_en = ?", (svname,)).fetchone()
            if wid and svid:
                c.execute(
                    "INSERT OR IGNORE INTO weakness_subvirtue (weakness_id, subvirtue_id, priority) VALUES (?, ?, ?)",
                    (wid[0], svid[0], priority),
                )

    # ── Sentences ────────────────────────────────────────────
    with open(DATA_PATH / "sentences.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            svname = row["subvirtue_name_en"].strip()
            svid = c.execute("SELECT id FROM subvirtue WHERE name_en = ?", (svname,)).fetchone()
            if svid:
                c.execute(
                    "INSERT OR IGNORE INTO sentence (text_en, text_mr, subvirtue_id) VALUES (?, ?, ?)",
                    (row["text_en"].strip(), row.get("text_mr", "").strip(), svid[0]),
                )

    conn.commit()
    conn.close()

    # Summary
    conn = sqlite3.connect(DB_PATH)
    for table in ["virtue", "subvirtue", "weakness", "weakness_subvirtue", "sentence"]:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {n} rows")
    conn.close()


if __name__ == "__main__":
    from database import init_db
    print("Initialising schema...")
    init_db()
    print("Seeding from CSVs...")
    seed()
    print("Done.")
