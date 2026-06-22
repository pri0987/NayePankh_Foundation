"""Report generation helpers for NayePankh Foundation."""

from __future__ import annotations

from datetime import datetime
from io import StringIO
from pathlib import Path

import pandas as pd

from database import query_df

REPORTS_DIR = Path(__file__).parent / "reports"


def _rows_to_dataframe(rows) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(row) for row in rows])


def get_dashboard_stats() -> dict:
    volunteers = query_df("SELECT COUNT(*) AS count FROM volunteers WHERE status = 'Active'")[0]["count"]
    campaigns = query_df("SELECT COUNT(*) AS count FROM campaigns WHERE status = 'Active'")[0]["count"]
    donation_stats = query_df(
        """
        SELECT COUNT(*) AS total_donations,
               COALESCE(SUM(amount), 0) AS total_amount,
               COALESCE(SUM(CASE WHEN receipt_80g = 1 THEN amount ELSE 0 END), 0) AS amount_with_80g
        FROM donations
        """
    )[0]
    return {
        "active_volunteers": volunteers,
        "active_campaigns": campaigns,
        "total_donations": donation_stats["total_donations"],
        "total_amount": donation_stats["total_amount"],
        "amount_with_80g": donation_stats["amount_with_80g"],
    }


def get_volunteers_df(city: str | None = None, role: str | None = None, status: str | None = None, search: str = "") -> pd.DataFrame:
    sql = "SELECT id, name, email, phone, city, role, status, joined_on FROM volunteers WHERE 1=1"
    params: list = []
    if city and city != "All":
        sql += " AND city = ?"
        params.append(city)
    if role and role != "All":
        sql += " AND role = ?"
        params.append(role)
    if status and status != "All":
        sql += " AND status = ?"
        params.append(status)
    if search.strip():
        sql += " AND (name LIKE ? OR email LIKE ? OR city LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term, term])
    sql += " ORDER BY joined_on DESC"
    return _rows_to_dataframe(query_df(sql, params))


def get_campaigns_df(category: str | None = None, city: str | None = None, status: str | None = None, search: str = "") -> pd.DataFrame:
    sql = """
        SELECT c.id, c.name, c.category, c.city, c.status, c.target_amount, c.start_date, c.end_date,
               COALESCE(SUM(d.amount), 0) AS raised_amount
        FROM campaigns c
        LEFT JOIN donations d ON d.campaign_id = c.id
        WHERE 1=1
    """
    params: list = []
    if category and category != "All":
        sql += " AND c.category = ?"
        params.append(category)
    if city and city != "All":
        sql += " AND c.city = ?"
        params.append(city)
    if status and status != "All":
        sql += " AND c.status = ?"
        params.append(status)
    if search.strip():
        sql += " AND (c.name LIKE ? OR c.city LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term])
    sql += " GROUP BY c.id ORDER BY c.start_date DESC"
    df = _rows_to_dataframe(query_df(sql, params))
    if not df.empty:
        df["progress_pct"] = (df["raised_amount"] / df["target_amount"].replace(0, 1) * 100).round(1)
    return df


def get_donations_df(
    campaign_id: int | None = None,
    payment_mode: str | None = None,
    receipt_only: bool = False,
    search: str = "",
    date_from: str | None = None,
    date_to: str | None = None,
) -> pd.DataFrame:
    sql = """
        SELECT d.id, d.donor_name, d.email, d.amount, c.name AS campaign,
               d.payment_mode, d.receipt_80g, d.donated_on, d.notes
        FROM donations d
        LEFT JOIN campaigns c ON c.id = d.campaign_id
        WHERE 1=1
    """
    params: list = []
    if campaign_id:
        sql += " AND d.campaign_id = ?"
        params.append(campaign_id)
    if payment_mode and payment_mode != "All":
        sql += " AND d.payment_mode = ?"
        params.append(payment_mode)
    if receipt_only:
        sql += " AND d.receipt_80g = 1"
    if date_from:
        sql += " AND d.donated_on >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND d.donated_on <= ?"
        params.append(date_to)
    if search.strip():
        sql += " AND (d.donor_name LIKE ? OR d.email LIKE ? OR d.notes LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term, term])
    sql += " ORDER BY d.donated_on DESC"
    df = _rows_to_dataframe(query_df(sql, params))
    if not df.empty:
        df["receipt_80g"] = df["receipt_80g"].map({1: "Yes", 0: "No"})
    return df


def get_filter_options() -> dict:
    cities = [row["city"] for row in query_df("SELECT DISTINCT city FROM volunteers UNION SELECT DISTINCT city FROM campaigns ORDER BY city")]
    roles = [row["role"] for row in query_df("SELECT DISTINCT role FROM volunteers ORDER BY role")]
    categories = [row["category"] for row in query_df("SELECT DISTINCT category FROM campaigns ORDER BY category")]
    campaigns = query_df("SELECT id, name FROM campaigns ORDER BY name")
    return {
        "cities": cities,
        "roles": roles,
        "categories": categories,
        "campaigns": campaigns,
    }


def save_csv_report(df: pd.DataFrame, prefix: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"{prefix}_{timestamp}.csv"
    df.to_csv(path, index=False)
    return path


def donations_summary_report() -> pd.DataFrame:
    return _rows_to_dataframe(
        query_df(
            """
            SELECT c.name AS campaign,
                   c.category,
                   c.city,
                   COUNT(d.id) AS donation_count,
                   COALESCE(SUM(d.amount), 0) AS total_raised,
                   c.target_amount,
                   ROUND(COALESCE(SUM(d.amount), 0) * 100.0 / NULLIF(c.target_amount, 0), 1) AS progress_pct
            FROM campaigns c
            LEFT JOIN donations d ON d.campaign_id = c.id
            GROUP BY c.id
            ORDER BY total_raised DESC
            """
        )
    )


def volunteers_by_city_report() -> pd.DataFrame:
    return _rows_to_dataframe(
        query_df(
            """
            SELECT city,
                   COUNT(*) AS total_volunteers,
                   SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) AS active_volunteers
            FROM volunteers
            GROUP BY city
            ORDER BY active_volunteers DESC
            """
        )
    )


def export_report_text(title: str, df: pd.DataFrame) -> str:
    buffer = StringIO()
    buffer.write(f"NayePankh Foundation Report\n")
    buffer.write(f"{title}\n")
    buffer.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    buffer.write("=" * 60 + "\n\n")
    buffer.write(df.to_string(index=False))
    return buffer.getvalue()
