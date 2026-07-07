"""
The Corporate Tax and Subsidy Optimizer - Backend
--------------------------------------------------
A Flask REST API that:
  1. Accepts company financial details
  2. Computes corporate tax liability under simplified slab rules
  3. Applies eligible subsidies / incentives (investment, employment, green energy)
  4. Stores every calculation in a built-in SQLite database (no external DB server needed)
  5. Serves history + summary statistics back to the frontend

NOTE: The tax/subsidy rules here are simplified for teaching / demo purposes.
They are NOT meant to be used for real tax filing or financial advice.
"""

import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allows the separately-served frontend (different port) to call this API

DB_PATH = "tax_optimizer.db"


# ---------------------------------------------------------------------------
# Database helpers (SQLite is part of Python's standard library -> "inbuilt")
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            sector TEXT NOT NULL,
            turnover REAL NOT NULL,
            net_profit REAL NOT NULL,
            investment REAL NOT NULL,
            new_jobs INTEGER NOT NULL,
            base_tax REAL NOT NULL,
            investment_subsidy REAL NOT NULL,
            employment_subsidy REAL NOT NULL,
            green_subsidy REAL NOT NULL,
            total_subsidy REAL NOT NULL,
            net_tax_payable REAL NOT NULL,
            effective_rate REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Core optimizer logic
# ---------------------------------------------------------------------------
def compute_base_tax(turnover, net_profit, sector):
    """Simplified slab-based corporate tax rate."""
    if sector == "Manufacturing (New Unit)":
        rate = 0.15
    elif turnover <= 400:  # in Crores
        rate = 0.25
    else:
        rate = 0.30
    return round(net_profit * rate, 2), rate


def compute_subsidies(sector, investment, new_jobs, base_tax):
    """Returns (investment_subsidy, employment_subsidy, green_subsidy)."""
    investment_subsidy = 0.0
    employment_subsidy = 0.0
    green_subsidy = 0.0

    # 1. Capital investment incentive - manufacturing sector only
    if sector in ("Manufacturing", "Manufacturing (New Unit)") and investment >= 10:
        investment_subsidy = investment * 0.05  # 5% of qualifying investment
        investment_subsidy = min(investment_subsidy, base_tax * 0.20)  # capped at 20% of base tax

    # 2. Employment generation incentive (loosely modeled on Sec 80JJAA)
    if new_jobs >= 10:
        employment_subsidy = new_jobs * 0.003  # Rs 30,000 per employee, expressed in Crores
        employment_subsidy = min(employment_subsidy, base_tax * 0.15)

    # 3. Green / renewable energy rebate
    if sector == "Renewable Energy":
        green_subsidy = base_tax * 0.10

    return (
        round(investment_subsidy, 2),
        round(employment_subsidy, 2),
        round(green_subsidy, 2),
    )


@app.route("/api/optimize", methods=["POST"])
def optimize():
    data = request.get_json(force=True)

    try:
        company_name = str(data["company_name"]).strip() or "Unnamed Company"
        sector = str(data["sector"])
        turnover = float(data["turnover"])
        net_profit = float(data["net_profit"])
        investment = float(data.get("investment", 0))
        new_jobs = int(data.get("new_jobs", 0))
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Invalid or missing input fields"}), 400

    if net_profit < 0 or turnover < 0:
        return jsonify({"error": "Turnover and profit cannot be negative"}), 400

    base_tax, rate = compute_base_tax(turnover, net_profit, sector)
    inv_sub, emp_sub, green_sub = compute_subsidies(sector, investment, new_jobs, base_tax)
    total_subsidy = round(inv_sub + emp_sub + green_sub, 2)
    net_tax_payable = max(round(base_tax - total_subsidy, 2), 0)
    effective_rate = round((net_tax_payable / net_profit) * 100, 2) if net_profit > 0 else 0

    result = {
        "company_name": company_name,
        "sector": sector,
        "turnover": turnover,
        "net_profit": net_profit,
        "investment": investment,
        "new_jobs": new_jobs,
        "base_tax_rate": rate,
        "base_tax": base_tax,
        "investment_subsidy": inv_sub,
        "employment_subsidy": emp_sub,
        "green_subsidy": green_sub,
        "total_subsidy": total_subsidy,
        "net_tax_payable": net_tax_payable,
        "effective_rate": effective_rate,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    db = get_db()
    db.execute(
        """INSERT INTO records
           (company_name, sector, turnover, net_profit, investment, new_jobs,
            base_tax, investment_subsidy, employment_subsidy, green_subsidy,
            total_subsidy, net_tax_payable, effective_rate, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            company_name, sector, turnover, net_profit, investment, new_jobs,
            base_tax, inv_sub, emp_sub, green_sub,
            total_subsidy, net_tax_payable, effective_rate, result["created_at"],
        ),
    )
    db.commit()

    return jsonify(result), 200


@app.route("/api/history", methods=["GET"])
def history():
    db = get_db()
    rows = db.execute("SELECT * FROM records ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows]), 200

from flask import send_from_directory

app = Flask(__name__, static_folder="../frontend", static_url_path="")

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

    
@app.route("/api/history/<int:record_id>", methods=["DELETE"])
def delete_record(record_id):
    db = get_db()
    db.execute("DELETE FROM records WHERE id = ?", (record_id,))
    db.commit()
    return jsonify({"deleted": record_id}), 200


@app.route("/api/stats", methods=["GET"])
def stats():
    db = get_db()
    row = db.execute(
        """SELECT COUNT(*) as total_companies,
                  COALESCE(SUM(base_tax), 0) as total_base_tax,
                  COALESCE(SUM(total_subsidy), 0) as total_subsidy,
                  COALESCE(SUM(net_tax_payable), 0) as total_net_tax
           FROM records"""
    ).fetchone()
    return jsonify(dict(row)), 200


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "Corporate Tax and Subsidy Optimizer API is running.",
        "endpoints": ["/api/optimize [POST]", "/api/history [GET]",
                      "/api/history/<id> [DELETE]", "/api/stats [GET]"]
    })


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
