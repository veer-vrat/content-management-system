"""Seed plans, exposures, resolutions, and challenges from CSVs in data/."""
import csv
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "veervrat_cms.db"
DATA_PATH = Path(__file__).parent.parent


def seed_plans():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    # Clear existing plan data (cascade deletes exposures/resolutions/challenges)
    c.execute("DELETE FROM plan")
    conn.commit()

    # plan_id in CSV → actual DB id mapping
    plan_id_map = {}

    with open(DATA_PATH / "plans.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            csv_id = int(row["id"])
            virtue_name = row["virtue_name"].strip()
            vid = c.execute("SELECT id FROM virtue WHERE name_en = ?", (virtue_name,)).fetchone()
            virtue_id = vid[0] if vid else None

            c.execute(
                "INSERT INTO plan (title, framing, virtue_id, source_file, notes) VALUES (?, ?, ?, ?, ?)",
                (
                    row["title"].strip(),
                    row.get("framing", "").strip(),
                    virtue_id,
                    row.get("source_file", "").strip(),
                    row.get("notes", "").strip(),
                ),
            )
            plan_id_map[csv_id] = c.lastrowid

    with open(DATA_PATH / "exposures.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            db_plan_id = plan_id_map.get(int(row["plan_id"]))
            if not db_plan_id:
                continue
            c.execute(
                "INSERT INTO exposure (plan_id, tier, title, description, sort_order) VALUES (?, ?, ?, ?, ?)",
                (
                    db_plan_id,
                    row["tier"].strip(),
                    row["title"].strip(),
                    row.get("description", "").strip(),
                    int(row.get("sort_order", 0) or 0),
                ),
            )

    with open(DATA_PATH / "resolutions.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            db_plan_id = plan_id_map.get(int(row["plan_id"]))
            if not db_plan_id:
                continue
            duration = row.get("duration_weeks", "").strip()
            c.execute(
                "INSERT INTO resolution (plan_id, title, description, duration_weeks, sort_order) VALUES (?, ?, ?, ?, ?)",
                (
                    db_plan_id,
                    row["title"].strip(),
                    row.get("description", "").strip(),
                    int(duration) if duration else None,
                    int(row.get("sort_order", 0) or 0),
                ),
            )

    with open(DATA_PATH / "challenges.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            db_plan_id = plan_id_map.get(int(row["plan_id"]))
            if not db_plan_id:
                continue
            duration = row.get("duration_days", "").strip()
            c.execute(
                "INSERT INTO challenge (plan_id, title, description, duration_days) VALUES (?, ?, ?, ?)",
                (
                    db_plan_id,
                    row["title"].strip(),
                    row.get("description", "").strip(),
                    int(duration) if duration else None,
                ),
            )

    conn.commit()

    for table in ["plan", "exposure", "resolution", "challenge"]:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {n} rows")

    conn.close()


if __name__ == "__main__":
    print("Seeding plans from CSVs...")
    seed_plans()
    print("Done.")
