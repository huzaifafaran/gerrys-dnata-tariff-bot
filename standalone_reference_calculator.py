"""Standalone Reference Tariff Calculator

An independent runner for the reference Gerry's / dnata calculation logic and CSV tables from `more docs/`.
Runs completely outside the main WhatsApp / FastAPI application.

Usage:
  1. Web Interface (opens browser form on port 5000):
     python standalone_reference_calculator.py --server --port 5000

  2. Command Line Interface (CLI):
     python standalone_reference_calculator.py --arrival 2026-10-01 --payment 2026-10-01 --category AFU --class GEN --weight 1000 --station KHI --oversize

  3. Interactive Terminal Prompt:
     python standalone_reference_calculator.py
"""

import sys
import os
import csv
import sqlite3
import math
from datetime import datetime, date
from decimal import Decimal
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "more docs")

TAX_RATES = {
    "KHI": 15.0,
    "ISB": 15.0,
    "LHE": 16.0,
    "MUX": 16.0,
    "PEW": 16.0,
}


def cargo_class_parser(cargo_class: str) -> str:
    """Class normalizer taken directly from reference/views.py."""
    if cargo_class == 'IDT (DR)':
        return 'IDT'
    elif cargo_class == 'RAD (RAM)':
        return 'RAD'
    elif cargo_class == 'DGR/AVI':
        return 'DGR'
    elif cargo_class == 'GEN (PIL)':
        return 'GEN'
    elif cargo_class == 'DGR (PDG)':
        return 'DGR'
    elif cargo_class in ['15 to 25 Degree Celsius (IRT)', '15 to 25 Degree Celsius (PRT)', '15 to 25 Degree Celsius (CRT)']:
        return '15 to 25 Degree Celsius'
    elif cargo_class in ['2 to 8 Degree Celsius (ICO)', '2 to 8 Degree Celsius (COL)', '2 to 8 Degree Celsius (PIC)']:
        return '2 to 8 Degree Celsius'
    elif cargo_class in ['Freezer (IRO)', 'Freezer (PRF)', 'Freezer (FRO)']:
        return 'Freezer'
    return cargo_class


def safe_float(val, default=0.0):
    if val is None:
        return default
    s = str(val).strip()
    if not s or s.upper() == 'NULL':
        return default
    try:
        return float(s)
    except ValueError:
        return default


def init_db() -> sqlite3.Connection:
    """Load CSV tables into an in-memory SQLite database mimicking MS SQL."""
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()

    # Tariff_Doc
    cur.execute('''
        CREATE TABLE Tariff_Doc (
            ID INTEGER, Tariff_ID INTEGER, Effective_Date TEXT, Expiry_Date TEXT,
            Category TEXT, Charges_DO_Fee REAL, Charges_D_Console REAL, Charges_Doc REAL
        )
    ''')
    doc_path = os.path.join(DOCS_DIR, "Tariff_Doc.csv")
    if os.path.exists(doc_path):
        with open(doc_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                cur.execute(
                    "INSERT INTO Tariff_Doc VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (r["ID"], r["Tariff_ID"], r["Effective_Date"], r["Expiry_Date"],
                     r["Category"], safe_float(r.get("Charges_DO_Fee")), safe_float(r.get("Charges_D_Console")), safe_float(r.get("Charges_Doc")))
                )

    # Tariff_Handling
    cur.execute('''
        CREATE TABLE Tariff_Handling (
            ID INTEGER, Tariff_ID INTEGER, Effective_Date TEXT, Expiry_Date TEXT,
            Category TEXT, Cargo_Class TEXT, Wt_Min REAL, Wt_Max REAL, Charges_PKR REAL, Charges_Per TEXT
        )
    ''')
    h_path = os.path.join(DOCS_DIR, "Tariff_Handling.csv")
    if os.path.exists(h_path):
        with open(h_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                cur.execute(
                    "INSERT INTO Tariff_Handling VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (r["ID"], r["Tariff_ID"], r["Effective_Date"], r["Expiry_Date"],
                     r["Category"], r["Cargo_Class"], safe_float(r.get("Wt_Min")), safe_float(r.get("Wt_Max")),
                     safe_float(r.get("Charges_PKR")), r.get("Charges_Per"))
                )

    # Tariff_Godown
    cur.execute('''
        CREATE TABLE Tariff_Godown (
            ID INTEGER, Tariff_ID INTEGER, Effective_Date TEXT, Expiry_Date TEXT,
            Category TEXT, Cargo_Class TEXT, Wt_Min REAL, Wt_Max REAL,
            Dwell_Min REAL, Dwell_Max REAL, Free_Days REAL, Charges_PKR REAL, Charges_Per TEXT
        )
    ''')
    g_path = os.path.join(DOCS_DIR, "Tariff_Godown.csv")
    if os.path.exists(g_path):
        with open(g_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                cur.execute(
                    "INSERT INTO Tariff_Godown VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (r["ID"], r["Tariff_ID"], r["Effective_Date"], r["Expiry_Date"],
                     r["Category"], r["Cargo_Class"], safe_float(r.get("Wt_Min")), safe_float(r.get("Wt_Max")),
                     safe_float(r.get("Dwell_Min")), safe_float(r.get("Dwell_Max")), safe_float(r.get("Free_Days")),
                     safe_float(r.get("Charges_PKR")), r.get("Charges_Per"))
                )

    # Tariff_Oversized
    cur.execute('''
        CREATE TABLE Tariff_Oversized (
            ID INTEGER, Tariff_ID INTEGER, Effective_Date TEXT, Expiry_Date TEXT,
            Category TEXT, Wt_Min REAL, Wt_Max REAL, Charges_PKR REAL, Charges_Per TEXT
        )
    ''')
    ov_path = os.path.join(DOCS_DIR, "Tariff_Oversized.csv")
    if os.path.exists(ov_path):
        with open(ov_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                cur.execute(
                    "INSERT INTO Tariff_Oversized VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (r["ID"], r["Tariff_ID"], r["Effective_Date"], r["Expiry_Date"],
                     r["Category"], safe_float(r.get("Wt_Min")), safe_float(r.get("Wt_Max")),
                     safe_float(r.get("Charges_PKR")), r.get("Charges_Per"))
                )

    # Tariff_Tax
    cur.execute('''
        CREATE TABLE Tariff_Tax (
            Station TEXT, Tax_Rate REAL
        )
    ''')
    for st, rate in TAX_RATES.items():
        cur.execute("INSERT INTO Tariff_Tax VALUES (?, ?)", (st, rate))

    conn.commit()
    return conn


def calculate(arrival_date_str: str, payment_date_str: str, category: str,
              cargo_class: str, weight: float, station: str, is_oversize: bool = False) -> dict:
    """Execute reference tariff calculation logic."""
    normalized_class = cargo_class_parser(cargo_class)
    d_arr = date.fromisoformat(arrival_date_str)
    d_pay = date.fromisoformat(payment_date_str)
    dwell_days = max(1, (d_pay - d_arr).days + 1)
    rounded_wt = round(weight)

    conn = init_db()
    cur = conn.cursor()

    # 1. Handling
    cur.execute('''
        SELECT Charges_PKR, Charges_Per FROM Tariff_Handling
        WHERE Category = ? AND Cargo_Class = ? AND ? >= Wt_Min AND ? <= Wt_Max
        LIMIT 1
    ''', (category, normalized_class, rounded_wt, rounded_wt))
    h_row = cur.fetchone()
    if h_row:
        h_rate, h_per = h_row
        if str(h_per).strip().lower() == 'per kg':
            handling = math.ceil(h_rate * weight)
        else:
            handling = math.ceil(h_rate)
    else:
        handling = 0

    # 2. Storage / Godown
    cur.execute('''
        SELECT Free_Days, Charges_PKR, Charges_Per FROM Tariff_Godown
        WHERE Category = ? AND Cargo_Class = ? AND ? >= Wt_Min AND ? <= Wt_Max
          AND ? >= Dwell_Min AND ? <= Dwell_Max
        LIMIT 1
    ''', (category, normalized_class, rounded_wt, rounded_wt, dwell_days, dwell_days))
    g_row = cur.fetchone()
    if g_row:
        free_days, g_rate, g_per = g_row
        chargeable_days = max(0, dwell_days - math.floor(free_days))
        if str(g_per).strip().lower() == 'per day':
            storage = math.ceil(chargeable_days * g_rate)
        else:
            storage = math.ceil(chargeable_days * g_rate * weight)
    else:
        storage = 0

    # 3. Documentation & Deconsole
    cur.execute('''
        SELECT Charges_D_Console, Charges_Doc, Charges_DO_Fee FROM Tariff_Doc
        WHERE Category = ? LIMIT 1
    ''', (category,))
    doc_row = cur.fetchone()
    if doc_row:
        deconsole = math.ceil(doc_row[0])
        doc_charges = math.ceil(doc_row[1])
        do_fee = 0  # Per official rule: D/O and D/Console are the same fee applied once
    else:
        deconsole = 9828
        doc_charges = 1226
        do_fee = 0

    # 4. Oversize
    oversize = 0
    if is_oversize:
        cur.execute('''
            SELECT Charges_PKR FROM Tariff_Oversized
            WHERE Category = ? AND ? >= Wt_Min AND ? <= Wt_Max
            LIMIT 1
        ''', (category, rounded_wt, rounded_wt))
        ov_row = cur.fetchone()
        if ov_row:
            oversize = math.ceil(ov_row[0])

    # 5. Station Tax
    tax_rate = TAX_RATES.get(station.upper(), 15.0)

    # Total & Tax
    subtotal = deconsole + doc_charges + handling + storage + oversize
    tax = round((tax_rate / 100.0) * subtotal)
    grand_total = subtotal + tax

    conn.close()

    return {
        "inputs": {
            "arrival_date": arrival_date_str,
            "payment_date": payment_date_str,
            "category": category,
            "cargo_class": cargo_class,
            "normalized_class": normalized_class,
            "weight": weight,
            "station": station,
            "is_oversize": is_oversize,
        },
        "dwell_days": dwell_days,
        "breakdown": {
            "handling": handling,
            "storage": storage,
            "deconsole": deconsole,
            "documentation": doc_charges,
            "do_fee": do_fee,
            "oversize": oversize,
        },
        "subtotal": subtotal,
        "tax_rate_percent": tax_rate,
        "tax": tax,
        "grand_total": grand_total,
    }


def print_cli_result(res: dict):
    inp = res["inputs"]
    b = res["breakdown"]
    print("=" * 60)
    print("       GERRY'S / DNATA — STANDALONE REFERENCE CALCULATOR")
    print("=" * 60)
    print(f"Arrival Date:    {inp['arrival_date']}")
    print(f"Payment Date:    {inp['payment_date']}")
    print(f"Category:        {inp['category']}")
    print(f"Cargo Class:     {inp['cargo_class']} (normalized: {inp['normalized_class']})")
    print(f"Weight:          {inp['weight']} kg")
    print(f"Station:         {inp['station']} ({res['tax_rate_percent']}% tax)")
    print(f"Oversize Cargo:  {'Yes' if inp['is_oversize'] else 'No'}")
    print(f"Dwell Period:    {res['dwell_days']} day(s)")
    print("-" * 60)
    print(f"• Handling Charges:          PKR {b['handling']:,}")
    print(f"• Storage Charges:           PKR {b['storage']:,}")
    print(f"• D/O & Deconsole Fee:       PKR {b['deconsole']:,}")
    print(f"• Documentation Charges:     PKR {b['documentation']:,}")
    if b["oversize"] > 0:
        print(f"• Oversize Charges:          PKR {b['oversize']:,}")
    print("-" * 60)
    print(f"Subtotal:                    PKR {res['subtotal']:,}")
    print(f"Station Tax ({res['tax_rate_percent']}%):           PKR {res['tax']:,}")
    print("=" * 60)
    print(f"GRAND TOTAL:                 PKR {res['grand_total']:,}")
    print("=" * 60)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Gerry's / dnata Reference Calculator</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 30px; }
    .container { max-width: 900px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 28px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); }
    h1 { color: #38bdf8; margin-top: 0; font-size: 24px; border-bottom: 2px solid #334155; padding-bottom: 12px; }
    .subtitle { color: #94a3b8; font-size: 14px; margin-top: -8px; margin-bottom: 20px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .form-group { display: flex; flex-direction: column; }
    label { font-size: 13px; font-weight: 600; color: #cbd5e1; margin-bottom: 6px; }
    input, select { background: #0f172a; border: 1px solid #475569; color: #f8fafc; padding: 10px 12px; border-radius: 6px; font-size: 14px; outline: none; }
    input:focus, select:focus { border-color: #38bdf8; }
    .checkbox-group { display: flex; align-items: center; gap: 10px; margin-top: 24px; }
    .btn { background: #2563eb; color: #fff; border: none; padding: 12px 24px; border-radius: 6px; font-size: 15px; font-weight: 600; cursor: pointer; width: 100%; margin-top: 20px; }
    .btn:hover { background: #1d4ed8; }
    .result-card { margin-top: 30px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 20px; }
    .result-title { font-size: 18px; color: #38bdf8; font-weight: 700; margin-bottom: 15px; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid #1e293b; font-size: 14px; }
    th { color: #94a3b8; font-weight: 600; }
    .total-row { font-size: 18px; font-weight: 700; color: #4ade80; border-top: 2px solid #334155; }
    .badge { background: #0369a1; color: #e0f2fe; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Gerry’s / dnata — Standalone Reference Tariff Calculator</h1>
    <div class="subtitle">Direct emulator for reference Python script and rate sheets from <code>more docs/</code>. Compare results side-by-side with WhatsApp bot.</div>
    <form method="POST">
      <div class="grid">
        <div class="form-group">
          <label>Arrival Date (YYYY-MM-DD):</label>
          <input type="date" name="arrival_date" value="{arrival_date}" required>
        </div>
        <div class="form-group">
          <label>Payment Date (YYYY-MM-DD):</label>
          <input type="date" name="payment_date" value="{payment_date}" required>
        </div>
        <div class="form-group">
          <label>Cargo Category:</label>
          <select name="category" id="category">
            <option value="AFU" {cat_AFU}>AFU (Air Freight Unit)</option>
            <option value="PHARMA" {cat_PHARMA}>PHARMA (Pharmaceuticals)</option>
            <option value="ICG" {cat_ICG}>ICG (Import Cargo General)</option>
            <option value="ICG COLD" {cat_ICG_COLD}>ICG COLD (Cold Storage)</option>
          </select>
        </div>
        <div class="form-group">
          <label>Cargo Class:</label>
          <select name="cargo_class">
            <option value="GEN" {cls_GEN}>GEN (General Cargo)</option>
            <option value="DGR" {cls_DGR}>DGR (Dangerous Goods)</option>
            <option value="2 to 8 Degree Celsius" {cls_2_8}>2 to 8 Degree Celsius</option>
            <option value="15 to 25 Degree Celsius" {cls_15_25}>15 to 25 Degree Celsius</option>
            <option value="Freezer" {cls_Freezer}>Freezer</option>
            <option value="VAL" {cls_VAL}>VAL (Valuable Cargo)</option>
            <option value="VUN" {cls_VUN}>VUN (Vulnerable Cargo)</option>
          </select>
        </div>
        <div class="form-group">
          <label>Gross Weight (kg):</label>
          <input type="number" step="any" name="weight" value="{weight}" required>
        </div>
        <div class="form-group">
          <label>Delivery Station:</label>
          <select name="station">
            <option value="KHI" {st_KHI}>Karachi — KHI (15% Tax)</option>
            <option value="ISB" {st_ISB}>Islamabad — ISB (15% Tax)</option>
            <option value="LHE" {st_LHE}>Lahore — LHE (16% Tax)</option>
            <option value="MUX" {st_MUX}>Multan — MUX (16% Tax)</option>
            <option value="PEW" {st_PEW}>Peshawar — PEW (16% Tax)</option>
          </select>
        </div>
      </div>
      <div class="checkbox-group">
        <input type="checkbox" id="oversize" name="is_oversize" value="1" {ov_checked}>
        <label for="oversize" style="margin:0; cursor:pointer;">Consignment is Oversize / Over-dimensional</label>
      </div>
      <button type="submit" class="btn">Calculate Reference Tariff</button>
    </form>

    {result_section}
  </div>
</body>
</html>
"""


class StandaloneServer(BaseHTTPRequestHandler):
    def do_GET(self):
        html = self._render_form(
            arrival_date="2026-10-01",
            payment_date="2026-10-01",
            category="AFU",
            cargo_class="GEN",
            weight="1000",
            station="KHI",
            is_oversize=True,
            result_section=""
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        params = urllib.parse.parse_qs(body)

        arr = params.get("arrival_date", ["2026-10-01"])[0]
        pay = params.get("payment_date", ["2026-10-01"])[0]
        cat = params.get("category", ["AFU"])[0]
        cls_ = params.get("cargo_class", ["GEN"])[0]
        wt_str = params.get("weight", ["1000"])[0]
        st = params.get("station", ["KHI"])[0]
        is_ov = "is_oversize" in params

        try:
            wt = float(wt_str)
            res = calculate(arr, pay, cat, cls_, wt, st, is_ov)
            result_html = self._build_result_card(res)
        except Exception as e:
            result_html = f'<div class="result-card" style="border-color:#ef4444;"><div class="result-title" style="color:#ef4444;">Error</div><p>{str(e)}</p></div>'

        html = self._render_form(
            arrival_date=arr,
            payment_date=pay,
            category=cat,
            cargo_class=cls_,
            weight=wt_str,
            station=st,
            is_oversize=is_ov,
            result_section=result_html
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _render_form(self, arrival_date, payment_date, category, cargo_class, weight, station, is_oversize, result_section):
        t = HTML_TEMPLATE
        t = t.replace("{arrival_date}", arrival_date)
        t = t.replace("{payment_date}", payment_date)
        t = t.replace("{cat_AFU}", "selected" if category == "AFU" else "")
        t = t.replace("{cat_PHARMA}", "selected" if category == "PHARMA" else "")
        t = t.replace("{cat_ICG}", "selected" if category == "ICG" else "")
        t = t.replace("{cat_ICG_COLD}", "selected" if category == "ICG COLD" else "")
        t = t.replace("{cls_GEN}", "selected" if cargo_class == "GEN" else "")
        t = t.replace("{cls_DGR}", "selected" if cargo_class == "DGR" else "")
        t = t.replace("{cls_2_8}", "selected" if "2 to 8" in cargo_class else "")
        t = t.replace("{cls_15_25}", "selected" if "15 to 25" in cargo_class else "")
        t = t.replace("{cls_Freezer}", "selected" if "Freezer" in cargo_class else "")
        t = t.replace("{cls_VAL}", "selected" if cargo_class == "VAL" else "")
        t = t.replace("{cls_VUN}", "selected" if cargo_class == "VUN" else "")
        t = t.replace("{weight}", str(weight))
        t = t.replace("{st_KHI}", "selected" if station == "KHI" else "")
        t = t.replace("{st_ISB}", "selected" if station == "ISB" else "")
        t = t.replace("{st_LHE}", "selected" if station == "LHE" else "")
        t = t.replace("{st_MUX}", "selected" if station == "MUX" else "")
        t = t.replace("{st_PEW}", "selected" if station == "PEW" else "")
        t = t.replace("{ov_checked}", "checked" if is_oversize else "")
        t = t.replace("{result_section}", result_section)
        return t

    def _build_result_card(self, res: dict) -> str:
        b = res["breakdown"]
        ov_row = f"<tr><td>Oversize Consignment Charges</td><td>PKR {b['oversize']:,}</td></tr>" if b['oversize'] > 0 else ""
        return f"""
        <div class="result-card">
          <div class="result-title">Reference Calculation Result <span class="badge">Dwell: {res['dwell_days']} Day(s)</span></div>
          <table>
            <tr><th>Fee Description</th><th>Amount (PKR)</th></tr>
            <tr><td>Handling Charges</td><td>PKR {b['handling']:,}</td></tr>
            <tr><td>Storage Charges</td><td>PKR {b['storage']:,}</td></tr>
            <tr><td>D/O & Deconsole Fee</td><td>PKR {b['deconsole']:,}</td></tr>
            <tr><td>Documentation Charges</td><td>PKR {b['documentation']:,}</td></tr>
            {ov_row}
            <tr><td><strong>Subtotal</strong></td><td><strong>PKR {res['subtotal']:,}</strong></td></tr>
            <tr><td>Station Tax ({res['tax_rate_percent']}%)</td><td>PKR {res['tax']:,}</td></tr>
            <tr class="total-row"><td>GRAND TOTAL</td><td>PKR {res['grand_total']:,}</td></tr>
          </table>
        </div>
        """


def run_interactive():
    print("=" * 60)
    print("   GERRY'S / DNATA — STANDALONE REFERENCE CALCULATOR")
    print("=" * 60)
    arr = input("Cargo Arrival Date (YYYY-MM-DD) [2026-10-01]: ").strip() or "2026-10-01"
    pay = input("Cargo Payment Date (YYYY-MM-DD) [2026-10-01]: ").strip() or "2026-10-01"
    cat = input("Cargo Category (AFU/PHARMA/ICG/ICG COLD) [AFU]: ").strip().upper() or "AFU"
    cls_ = input("Cargo Class (GEN/DGR/2 to 8/Freezer/etc.) [GEN]: ").strip() or "GEN"
    wt_s = input("Gross Weight in kg [1000]: ").strip() or "1000"
    st = input("Station (KHI/ISB/LHE/MUX/PEW) [KHI]: ").strip().upper() or "KHI"
    ov_s = input("Oversize? (yes/no) [yes]: ").strip().lower()
    is_ov = ov_s in ["yes", "y", "1", "true"]

    res = calculate(arr, pay, cat, cls_, float(wt_s), st, is_ov)
    print_cli_result(res)


def main():
    parser = argparse.ArgumentParser(description="Standalone Gerry's/dnata Tariff Calculator")
    parser.add_argument("--server", action="store_true", help="Start standalone Web UI server")
    parser.add_argument("--port", type=int, default=5000, help="Port for standalone Web UI (default: 5000)")
    parser.add_argument("--arrival", type=str, help="Arrival date (YYYY-MM-DD)")
    parser.add_argument("--payment", type=str, help="Payment date (YYYY-MM-DD)")
    parser.add_argument("--category", type=str, help="Category (AFU, PHARMA, ICG, ICG COLD)")
    parser.add_argument("--class", dest="cargo_class", type=str, help="Cargo class (GEN, DGR, etc.)")
    parser.add_argument("--weight", type=float, help="Gross weight in kg")
    parser.add_argument("--station", type=str, help="Station code (KHI, ISB, LHE, MUX, PEW)")
    parser.add_argument("--oversize", action="store_true", help="Mark as oversize")

    args = parser.parse_args()

    if args.server:
        server_addr = ("", args.port)
        httpd = HTTPServer(server_addr, StandaloneServer)
        print(f"[STANDALONE] Web UI running at http://127.0.0.1:{args.port}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[STANDALONE] Server stopped.")
        return

    if args.arrival and args.payment and args.category and args.cargo_class and args.weight and args.station:
        res = calculate(args.arrival, args.payment, args.category, args.cargo_class, args.weight, args.station, args.oversize)
        print_cli_result(res)
    else:
        run_interactive()


if __name__ == "__main__":
    main()
