# The Corporate Tax and Subsidy Optimizer

A mini full-stack project:
- **Backend:** Python (Flask) + a built-in SQLite database (no separate DB server to install)
- **Frontend:** Plain HTML, CSS, and JavaScript (a "ledger" styled dashboard)

```
CorporateTaxOptimizer/
├── backend/
│   ├── app.py              # Flask API + SQLite database logic
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Dashboard page
│   ├── style.css           # Styling
│   └── script.js           # Calls the backend API
└── README.md
```

## What it does
You enter a company's turnover, net profit, sector, new investment, and new jobs
created. The backend:
1. Applies a simplified corporate tax slab (15% / 25% / 30% depending on sector & turnover).
2. Applies eligible subsidies: investment incentive, employment-generation incentive,
   and a green-energy rebate.
3. Saves every calculation to a local SQLite file (`tax_optimizer.db`), created automatically.
4. Returns the net tax payable, which the frontend displays as a stamped ledger entry,
   plus a running history table.

*(Rules are simplified for learning purposes — this is not real tax advice.)*

---

## Step-by-step setup in VS Code

### 1. Get the folder into VS Code
- Download/unzip `CorporateTaxOptimizer` anywhere on your computer.
- Open VS Code → `File` → `Open Folder...` → select the `CorporateTaxOptimizer` folder.

### 2. Install the Python extension (if you don't have it)
- In VS Code, go to the Extensions panel (`Ctrl+Shift+X` / `Cmd+Shift+X`).
- Search for **Python** (by Microsoft) and install it.

### 3. Open a terminal in VS Code
- `Terminal` → `New Terminal` (or `` Ctrl+` ``).

### 4. Set up the backend
```bash
cd backend
python -m venv venv
```
Activate the virtual environment:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

Install dependencies:
```bash
pip install -r requirements.txt
```

### 5. Run the backend server
```bash
python app.py
```
You should see something like:
```
 * Running on http://127.0.0.1:5000
```
Leave this terminal running — it's your live backend. The SQLite database file
(`tax_optimizer.db`) is created automatically in the `backend` folder the first
time you run this.

### 6. Run the frontend
Open a **second terminal** in VS Code (`Terminal` → `Split Terminal`), then:
```bash
cd frontend
python -m http.server 5500
```
Now open your browser at:
```
http://127.0.0.1:5500
```

> Tip: If you have the **Live Server** VS Code extension installed, you can instead
> right-click `index.html` → "Open with Live Server" — either method works, since
> the backend already allows cross-origin requests (CORS is enabled in `app.py`).

### 7. Use the app
- Fill in the company details on the left and click **Calculate & File Entry**.
- The result ledger on the right shows the base tax, each subsidy applied, and the
  final net tax payable — with an "OPTIMIZED" stamp.
- Every entry is saved and appears in the **Filed Entries** table below, along
  with running totals (companies filed, total tax, total subsidy given).
- Click **Remove** on any row to delete that record from the database.

### 8. Where the data lives
All records are stored in `backend/tax_optimizer.db`, a single SQLite file —
Python's `sqlite3` module (used in `app.py`) is part of the standard library,
so no extra database software needs to be installed. You can inspect this
file anytime with the free **SQLite Viewer** extension in VS Code, or the
`sqlite3` command-line tool.

---

## Customizing the tax/subsidy rules
All the calculation logic lives in `backend/app.py` inside:
- `compute_base_tax()` — the slab rates
- `compute_subsidies()` — the three subsidy rules

Change the percentages or thresholds there, restart `python app.py`, and the
frontend will immediately reflect the new rules — no frontend changes needed.

## API reference (for reference / testing with Postman etc.)
| Method | Endpoint              | Purpose                          |
|--------|-----------------------|-----------------------------------|
| POST   | `/api/optimize`       | Submit company data, get result   |
| GET    | `/api/history`        | Get all saved records             |
| DELETE | `/api/history/<id>`   | Delete one record                 |
| GET    | `/api/stats`          | Get aggregate totals              |
