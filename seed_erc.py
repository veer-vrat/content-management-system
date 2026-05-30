"""Seed exposures, resolutions, challenges, and sentence ERC metadata from CSVs."""
import csv
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "veervrat_cms.db"
DATA_PATH = Path(__file__).parent.parent


def lookup_sentence(c, text_en):
    row = c.execute("SELECT id FROM sentence WHERE text_en = ?", (text_en.strip(),)).fetchone()
    if not row:
        print(f"  WARNING: no sentence found for: {text_en[:60]!r}")
    return row[0] if row else None


def seed_erc():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    # Clear existing ERC data
    c.execute("DELETE FROM exposure")
    c.execute("DELETE FROM resolution")
    c.execute("DELETE FROM challenge")
    c.execute("DELETE FROM sentence_weakness")
    c.execute("UPDATE sentence SET source_file = NULL, notes = NULL")
    conn.commit()

    # sentence_erc_meta → update source_file/notes and seed sentence_weakness
    with open(DATA_PATH / "sentence_erc_meta.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = lookup_sentence(c, row["sentence_text_en"])
            if not sid:
                continue
            c.execute(
                "UPDATE sentence SET source_file = ?, notes = ? WHERE id = ?",
                (row.get("source_file", "").strip(), row.get("notes", "").strip(), sid),
            )
            for wname in row.get("weakness_names", "").split("|"):
                wname = wname.strip()
                if not wname:
                    continue
                wrow = c.execute("SELECT id FROM weakness WHERE name_en = ?", (wname,)).fetchone()
                if wrow:
                    c.execute(
                        "INSERT OR IGNORE INTO sentence_weakness (sentence_id, weakness_id) VALUES (?, ?)",
                        (sid, wrow[0]),
                    )
                else:
                    print(f"  WARNING: weakness not found: {wname!r}")

    with open(DATA_PATH / "exposures.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = lookup_sentence(c, row["sentence_text_en"])
            if sid:
                c.execute(
                    "INSERT INTO exposure (sentence_id, tier, title, description, sort_order) VALUES (?, ?, ?, ?, ?)",
                    (
                        sid,
                        row["tier"].strip(),
                        row["title"].strip(),
                        row.get("description", "").strip(),
                        int(row.get("sort_order", 0) or 0),
                    ),
                )

    with open(DATA_PATH / "resolutions.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = lookup_sentence(c, row["sentence_text_en"])
            if sid:
                dur = row.get("duration_weeks", "").strip()
                c.execute(
                    "INSERT INTO resolution (sentence_id, title, description, duration_weeks, sort_order) VALUES (?, ?, ?, ?, ?)",
                    (
                        sid,
                        row["title"].strip(),
                        row.get("description", "").strip(),
                        int(dur) if dur else None,
                        int(row.get("sort_order", 0) or 0),
                    ),
                )

    with open(DATA_PATH / "challenges.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = lookup_sentence(c, row["sentence_text_en"])
            if sid:
                dur = row.get("duration_days", "").strip()
                c.execute(
                    "INSERT INTO challenge (sentence_id, title, description, duration_days) VALUES (?, ?, ?, ?)",
                    (
                        sid,
                        row["title"].strip(),
                        row.get("description", "").strip(),
                        int(dur) if dur else None,
                    ),
                )

    conn.commit()

    for table in ["exposure", "resolution", "challenge", "sentence_weakness"]:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {n} rows")
    n = conn.execute("SELECT COUNT(*) FROM sentence WHERE source_file IS NOT NULL").fetchone()[0]
    print(f"  sentences with ERC metadata: {n}")

    conn.close()


if __name__ == "__main__":
    print("Seeding ERC from CSVs...")
    seed_erc()
    print("Done.")
