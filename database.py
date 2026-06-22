"""SQLite database layer for NayePankh Foundation management."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "nayepankh.db"


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS volunteers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                city TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active',
                joined_on TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                city TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active',
                target_amount REAL NOT NULL DEFAULT 0,
                start_date TEXT NOT NULL,
                end_date TEXT
            );

            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donor_name TEXT NOT NULL,
                email TEXT,
                amount REAL NOT NULL,
                campaign_id INTEGER,
                payment_mode TEXT NOT NULL,
                receipt_80g INTEGER NOT NULL DEFAULT 0,
                donated_on TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
            );
            """
        )


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def seed_sample_data() -> None:
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM volunteers").fetchone()[0]
        if count:
            return

        campaigns = [
            ("Education for All", "Education", "Kanpur", "Active", 150000, "2025-01-15", "2025-12-31"),
            ("Food Relief Drive", "Food", "Ghaziabad", "Active", 80000, "2025-03-01", "2025-09-30"),
            ("Menstrual Hygiene Awareness", "Health", "Kanpur", "Completed", 50000, "2024-06-01", "2024-12-15"),
            ("Winter Clothing Drive", "Clothing", "Delhi", "Active", 60000, "2025-11-01", "2026-02-28"),
        ]
        conn.executemany(
            """
            INSERT INTO campaigns (name, category, city, status, target_amount, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            campaigns,
        )

        volunteers = [
            ("Ashant Shukla", "ashant@nayepankh.com", "8318500748", "Kanpur", "Coordinator", "Active", "2020-04-01"),
            ("Priya Sharma", "priya.sharma@example.com", "9876543210", "Kanpur", "Fundraising", "Active", "2024-08-12"),
            ("Rahul Verma", "rahul.v@example.com", "9123456780", "Ghaziabad", "Outreach", "Active", "2025-01-20"),
            ("Ananya Singh", "ananya.s@example.com", "9988776655", "Delhi", "Social Media", "Inactive", "2023-05-10"),
            ("Karan Mehta", "karan.m@example.com", "9012345678", "Kanpur", "Volunteer", "Active", "2025-06-01"),
        ]
        conn.executemany(
            """
            INSERT INTO volunteers (name, email, phone, city, role, status, joined_on)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            volunteers,
        )

        donations = [
            ("Amit Kapoor", "amit.k@example.com", 5000, 1, "UPI", 1, "2025-02-10", "Monthly supporter"),
            ("Neha Gupta", "neha.g@example.com", 2500, 2, "Bank Transfer", 1, "2025-03-05", ""),
            ("Anonymous Donor", None, 10000, 1, "Cash", 0, "2025-04-18", "School supplies"),
            ("Vikram Patel", "vikram.p@example.com", 1500, 4, "UPI", 1, "2025-11-22", "Winter drive"),
            ("Sunita Rao", "sunita.r@example.com", 7500, 3, "Cheque", 1, "2024-08-30", "Health camp"),
            ("Rohit Jain", "rohit.j@example.com", 3000, 2, "UPI", 1, "2025-05-14", ""),
        ]
        conn.executemany(
            """
            INSERT INTO donations (donor_name, email, amount, campaign_id, payment_mode, receipt_80g, donated_on, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            donations,
        )


def query_df(sql: str, params: tuple | list = ()) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(sql, params).fetchall()


def insert_volunteer(
    name: str,
    email: str,
    phone: str,
    city: str,
    role: str,
    status: str,
    joined_on: date,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO volunteers (name, email, phone, city, role, status, joined_on)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, email, phone, city, role, status, joined_on.isoformat()),
        )


def insert_campaign(
    name: str,
    category: str,
    city: str,
    status: str,
    target_amount: float,
    start_date: date,
    end_date: date | None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO campaigns (name, category, city, status, target_amount, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                category,
                city,
                status,
                target_amount,
                start_date.isoformat(),
                end_date.isoformat() if end_date else None,
            ),
        )


def insert_donation(
    donor_name: str,
    email: str | None,
    amount: float,
    campaign_id: int | None,
    payment_mode: str,
    receipt_80g: bool,
    donated_on: date,
    notes: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO donations (donor_name, email, amount, campaign_id, payment_mode, receipt_80g, donated_on, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                donor_name,
                email or None,
                amount,
                campaign_id,
                payment_mode,
                int(receipt_80g),
                donated_on.isoformat(),
                notes,
            ),
        )
