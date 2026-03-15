import csv
from pathlib import Path
from db_util import execute, query_one

SEED_DATA_DIR = Path(__file__).parent / "seed_data"
USERS_CSV = SEED_DATA_DIR / "users.csv"
JOB_POSTINGS_CSV = SEED_DATA_DIR / "job_postings.csv"


def seed_users():
    with open(USERS_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            execute(
                """
                INSERT OR IGNORE INTO users (user_name, email, first_name, last_name, role, resume_url)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row["user_name"],
                    row["email"],
                    row["first_name"],
                    row["last_name"],
                    row["role"],
                    row["resume_url"] or None,
                )
            )
    print(f"Users seeded from {USERS_CSV}")


def seed_job_postings():
    with open(JOB_POSTINGS_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            recruiter = query_one(
                "SELECT id FROM users WHERE user_name = ?",
                (row["recruiter_user_name"],)
            )
            if not recruiter:
                print(f"Recruiter '{row['recruiter_user_name']}' not found, skipping row.")
                continue
            execute(
                """
                INSERT OR IGNORE INTO job_postings (recruiter_id, title, company, location, description, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    recruiter["id"],
                    row["title"],
                    row["company"],
                    row["location"],
                    row["description"],
                    row["status"],
                )
            )
    print(f"Job postings seeded from {JOB_POSTINGS_CSV}")


if __name__ == "__main__":
    seed_users()
    seed_job_postings()
