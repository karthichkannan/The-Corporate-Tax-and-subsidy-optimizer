const API_BASE = ""; // relative path — frontend is served from same origin as Flask (127.0.0.1:5000)

const form = document.getElementById("optimize-form");
const formError = document.getElementById("form-error");
const resultEmpty = document.getElementById("result-empty");
const resultBody = document.getElementById("result-body");
const historyBody = document.getElementById("history-body");
const statsBar = document.getElementById("stats-bar");

function currency(value) {
  return "₹" + Number(value).toFixed(2) + " Cr";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  formError.textContent = "";

  const payload = {
    company_name: document.getElementById("company_name").value,
    sector: document.getElementById("sector").value,
    turnover: document.getElementById("turnover").value,
    net_profit: document.getElementById("net_profit").value,
    investment: document.getElementById("investment").value || 0,
    new_jobs: document.getElementById("new_jobs").value || 0,
  };

  try {
    const res = await fetch(`${API_BASE}/api/optimize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) {
      formError.textContent = data.error || "Something went wrong.";
      return;
    }

    renderResult(data);
    form.reset();
    loadHistory();
  } catch (err) {
    formError.textContent = "Could not reach the backend. Is app.py running on port 5000?";
  }
});

function renderResult(r) {
  resultEmpty.classList.add("hidden");
  resultBody.classList.remove("hidden");

  document.getElementById("r-company").textContent = `${r.company_name} — ${r.sector}`;
  document.getElementById("r-rate").textContent = `${(r.base_tax_rate * 100).toFixed(0)}%`;
  document.getElementById("r-base").textContent = currency(r.base_tax);
  document.getElementById("r-inv").textContent = "-" + currency(r.investment_subsidy);
  document.getElementById("r-emp").textContent = "-" + currency(r.employment_subsidy);
  document.getElementById("r-green").textContent = "-" + currency(r.green_subsidy);
  document.getElementById("r-net").textContent = currency(r.net_tax_payable);
  document.getElementById("r-effective").textContent = `${r.effective_rate}%`;
}

async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/history`);
    const rows = await res.json();
    historyBody.innerHTML = "";

    rows.forEach((r) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${r.company_name}</td>
        <td>${r.sector}</td>
        <td class="mono">${currency(r.base_tax)}</td>
        <td class="subsidy-cell">${currency(r.total_subsidy)}</td>
        <td class="net-cell">${currency(r.net_tax_payable)}</td>
        <td class="mono">${r.effective_rate}%</td>
        <td>${r.created_at}</td>
        <td><button class="delete-btn" data-id="${r.id}">Remove</button></td>
      `;
      historyBody.appendChild(tr);
    });

    document.querySelectorAll(".delete-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await fetch(`${API_BASE}/api/history/${btn.dataset.id}`, { method: "DELETE" });
        loadHistory();
      });
    });

    loadStats();
  } catch (err) {
    historyBody.innerHTML = `<tr><td colspan="8">Could not load history. Is the backend running?</td></tr>`;
  }
}

async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/api/stats`);
    const s = await res.json();
    statsBar.innerHTML = `
      <span>Companies: <b>${s.total_companies}</b></span>
      <span>Total Base Tax: <b>${currency(s.total_base_tax)}</b></span>
      <span>Total Subsidy Given: <b>${currency(s.total_subsidy)}</b></span>
      <span>Total Net Tax: <b>${currency(s.total_net_tax)}</b></span>
    `;
  } catch (err) {
    statsBar.textContent = "";
  }
}

loadHistory();