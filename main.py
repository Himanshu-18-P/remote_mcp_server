import sqlite3
from datetime import date
from pathlib import Path
from fastmcp import FastMCP

DB_PATH = Path(__file__).parent / "expenses.db"

mcp = FastMCP(name="Expense Tracker")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                spent_on TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


init_db()


@mcp.tool
def add_expense(
    amount: float,
    category: str,
    description: str = "",
    spent_on: str | None = None,
) -> dict:
    """Add a new expense. spent_on is YYYY-MM-DD; defaults to today."""
    spent_on = spent_on or date.today().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO expenses (amount, category, description, spent_on) VALUES (?, ?, ?, ?)",
            (amount, category, description, spent_on),
        )
        return {
            "id": cur.lastrowid,
            "amount": amount,
            "category": category,
            "description": description,
            "spent_on": spent_on,
        }


@mcp.tool
def list_expenses(
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """List expenses, optionally filtered by category and/or date range (YYYY-MM-DD)."""
    query = "SELECT * FROM expenses WHERE 1=1"
    params: list = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if start_date:
        query += " AND spent_on >= ?"
        params.append(start_date)
    if end_date:
        query += " AND spent_on <= ?"
        params.append(end_date)
    query += " ORDER BY spent_on DESC, id DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


@mcp.tool
def get_expense(expense_id: int) -> dict | None:
    """Get a single expense by id."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
        return dict(row) if row else None


@mcp.tool
def update_expense(
    expense_id: int,
    amount: float | None = None,
    category: str | None = None,
    description: str | None = None,
    spent_on: str | None = None,
) -> dict | None:
    """Update fields on an existing expense. Only provided fields are changed."""
    fields = []
    params: list = []
    for name, value in (
        ("amount", amount),
        ("category", category),
        ("description", description),
        ("spent_on", spent_on),
    ):
        if value is not None:
            fields.append(f"{name} = ?")
            params.append(value)
    if not fields:
        return get_expense(expense_id)
    params.append(expense_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?", params)
    return get_expense(expense_id)


@mcp.tool
def delete_expense(expense_id: int) -> dict:
    """Delete an expense by id."""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return {"deleted": cur.rowcount > 0, "id": expense_id}


@mcp.tool
def summary_by_category(
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """Total spending grouped by category, optionally within a date range."""
    query = "SELECT category, SUM(amount) AS total, COUNT(*) AS count FROM expenses WHERE 1=1"
    params: list = []
    if start_date:
        query += " AND spent_on >= ?"
        params.append(start_date)
    if end_date:
        query += " AND spent_on <= ?"
        params.append(end_date)
    query += " GROUP BY category ORDER BY total DESC"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


@mcp.tool
def total_spent(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Total amount spent in a date range (or all-time if no range given)."""
    query = "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count FROM expenses WHERE 1=1"
    params: list = []
    if start_date:
        query += " AND spent_on >= ?"
        params.append(start_date)
    if end_date:
        query += " AND spent_on <= ?"
        params.append(end_date)
    with get_conn() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
