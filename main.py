from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pandas as pd
import uvicorn
from pdf_parser import parse_pdf_to_csv

# Ensure CSV exists
csv_file = "transactions.csv"
parse_pdf_to_csv("STMT.ENT.BOOK1.pdf", csv_file)

# Load CSV into DataFrame
df = pd.read_csv(csv_file, dtype=str).fillna("")

app = FastAPI()

# ----------------- BASE HTML + CSS -----------------
def base_html(body: str) -> str:
    return f"""
    <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>D WATSON - Transaction Search</title>
      <style>
        :root {{
          --bg: #0b1220;
          --card: #11182a;
          --muted: #9fb0c3;
          --text: #e7eef8;
          --accent: #3aa1ff;
          --accent-2: #19c37d;
          --danger: #ff5b5b;
          --border: #21314a;
        }}
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0; padding: 20px;
          font-family: system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans";
          background: radial-gradient(1200px 800px at 10% -20%, #1a2850, transparent),
                      radial-gradient(1200px 800px at 90% 120%, #0c3c4c, transparent),
                      var(--bg);
          color: var(--text);
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .title {{ font-size: 26px; font-weight: 700; text-align: center; margin: 10px 0 18px; }}
        .subtitle {{ font-size: 16px; color: var(--muted); text-align: center; margin-bottom: 25px; }}
        .card {{
          background: linear-gradient(180deg, #121a2e 0%, #0f1729 100%);
          border: 1px solid var(--border);
          border-radius: 16px; padding: 20px;
        }}
        .grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
        .field {{ display: flex; flex-direction: column; gap: 8px; background: #0c1324; border: 1px solid var(--border); border-radius: 12px; padding: 14px; }}
        label {{ font-size: 13px; color: var(--muted); }}
        input[type="text"] {{
          width: 100%; padding: 12px 14px; border-radius: 10px;
          border: 1px solid #25324a; background: #0a1120;
          color: var(--text); outline: none; font-size: 14px;
        }}
        input[type="text"]::placeholder {{ color: #7f91a8; }}
        .btn {{
          display: inline-flex; align-items: center; justify-content: center;
          padding: 10px 14px; border-radius: 10px; font-weight: 600; font-size: 14px;
          border: 1px solid #264e7b; background: linear-gradient(180deg, #0d6efd 0%, #0b5ed7 100%);
          color: white; text-decoration: none; cursor: pointer;
        }}
        .btn.secondary {{ background: #141c31; border: 1px solid var(--border); color: #d3e2f4; }}
        .btn:hover {{ filter: brightness(1.06); }}
        .actions {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }}
        table {{
          width: 100%; border-collapse: collapse; margin-top: 18px;
          background: #0b1325; border: 1px solid var(--border);
        }}
        thead th {{ background: #0f1a32; color: #cbd8ea; padding: 10px; font-size: 13px; }}
        tbody td {{ padding: 10px; font-size: 14px; border-top: 1px solid #182642; }}
        tbody tr:hover {{ background: #0e1a33; }}
        .badge {{ padding: 3px 8px; border-radius: 999px; font-size: 12px; }}
        .badge.credit {{ background: rgba(25,195,125,.15); color: #86f3c4; border: 1px solid rgba(25,195,125,.35); }}
        .badge.debit  {{ background: rgba(255,91,91,.12); color: #ff9c9c; border: 1px solid rgba(255,91,91,.28); }}
        .footer {{ margin-top: 24px; color: var(--muted); font-size: 13px; text-align: center; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="title">💳 D WATSON - Transaction Search</div>
        <div class="subtitle">POWERED BY MR WASI</div>
        {body}
        <div class="footer">© 2025 D WATSON • Built with FastAPI</div>
      </div>
    </body>
    </html>
    """

# ----------------- HOME PAGE -----------------
@app.get("/", response_class=HTMLResponse)
def home():
    body = """
      <div class="card">
        <div class="grid">
          <form class="field" action="/search-date" method="get">
            <label>By Date (exact or partial)</label>
            <input name="date" placeholder="e.g. 02 JUL 24 or 2024-07-02">
            <div class="actions">
              <button class="btn" type="submit">Search by Date</button>
              <a class="btn secondary" href="/preview">Preview CSV</a>
            </div>
          </form>

          <form class="field" action="/search-amount" method="get">
            <label>By Amount (credit/debit)</label>
            <input name="amount" placeholder="e.g. 84695.00 or -84695.00">
            <div class="actions">
              <button class="btn" type="submit">Search by Amount</button>
            </div>
          </form>

          <form class="field" action="/search-id" method="get">
            <label>By Transaction ID</label>
            <input name="id" placeholder="e.g. 200515912587008">
            <div class="actions">
              <button class="btn" type="submit">Search by ID</button>
            </div>
          </form>
        </div>
      </div>
    """
    return base_html(body)

# ----------------- CSV PREVIEW WITH PAGINATION -----------------
@app.get("/preview", response_class=HTMLResponse)
def preview(page: int = 1, per_page: int = 100):
    total_rows = len(df)
    total_pages = (total_rows // per_page) + (1 if total_rows % per_page else 0)

    start = (page - 1) * per_page
    end = start + per_page
    chunk = df.iloc[start:end]

    rows_html = ""
    for _, r in chunk.iterrows():
        rows_html += f"""
          <tr>
            <td>{r.get('date','')}</td>
            <td>{r.get('date_iso','')}</td>
            <td>{r.get('description','')}</td>
            <td>{r.get('id','')}</td>
            <td>{r.get('value_date','')}</td>
            <td><span class="badge debit">{r.get('debit','')}</span></td>
            <td><span class="badge credit">{r.get('credit','')}</span></td>
            <td>{r.get('balance','')}</td>
          </tr>
        """

    pagination_html = f"<div class='actions'>"
    if page > 1:
        pagination_html += f"<a class='btn secondary' href='/preview?page={page-1}&per_page={per_page}'>← Prev</a>"
    if page < total_pages:
        pagination_html += f"<a class='btn secondary' href='/preview?page={page+1}&per_page={per_page}'>Next →</a>"
    pagination_html += f"<span style='margin:auto;color:#9fb0c3'>Page {page} of {total_pages}</span></div>"

    table = f"""
      <div class="title">📄 CSV Preview ({total_rows} rows)</div>
      <div class="card">
        <table>
          <thead>
            <tr>
              <th>date</th><th>date_iso</th><th>description</th><th>id</th>
              <th>value_date</th><th>debit</th><th>credit</th><th>balance</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
        {pagination_html}
        <div class="actions"><a class="btn secondary" href="/">← Back</a></div>
      </div>
    """
    return base_html(table)

# ----------------- RENDER RESULTS -----------------
def render_results(results: "pd.DataFrame") -> str:
    if results.empty:
        body = """
          <div class="title">No results found</div>
          <div class="card">
            Try a partial search (e.g. enter just the first 6 digits of the ID, or “02 JUL” for date).
            <div class="actions"><a class="btn secondary" href="/">← Back</a></div>
          </div>
        """
        return base_html(body)

    rows_html = ""
    for _, r in results.iterrows():
        rows_html += f"""
          <tr>
            <td>{r.get('date','')}</td>
            <td>{r.get('date_iso','')}</td>
            <td>{r.get('description','')}</td>
            <td>{r.get('id','')}</td>
            <td>{r.get('value_date','')}</td>
            <td><span class="badge debit">{r.get('debit','')}</span></td>
            <td><span class="badge credit">{r.get('credit','')}</span></td>
            <td>{r.get('balance','')}</td>
          </tr>
        """

    table = f"""
      <div class="title">🔎 Results ({len(results)} found)</div>
      <div class="card">
        <table>
          <thead>
            <tr>
              <th>date</th><th>date_iso</th><th>description</th><th>id</th>
              <th>value_date</th><th>debit</th><th>credit</th><th>balance</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
        <div class="actions"><a class="btn secondary" href="/">← Back</a></div>
      </div>
    """
    return base_html(table)

# ----------------- SEARCH ROUTES -----------------
@app.get("/search-date", response_class=HTMLResponse)
def get_by_date(date: str):
    results = df[df["date"].str.contains(date.strip(), case=False, na=False) |
                 df["date_iso"].str.contains(date.strip(), case=False, na=False)]
    return render_results(results)

@app.get("/search-amount", response_class=HTMLResponse)
def get_by_amount(amount: str):
    amount = amount.replace(",", "").strip()
    results = df[(df["debit"].str.contains(amount, na=False)) |
                 (df["credit"].str.contains(amount, na=False))]
    return render_results(results)

@app.get("/search-id", response_class=HTMLResponse)
def get_by_id(id: str):
    id = id.strip()
    results = df[df["id"].str.contains(id, na=False)]
    return render_results(results)

# ----------------- RUN SERVER -----------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)



















# from fastapi import FastAPI
# from fastapi.responses import HTMLResponse
# import pandas as pd
# import uvicorn
# from pdf_parser import parse_pdf_to_csv

# # Ensure CSV exists
# csv_file = "transactions.csv"
# parse_pdf_to_csv("STMT.ENT.BOOK1.pdf", csv_file)

# # Load CSV into DataFrame
# df = pd.read_csv(csv_file, dtype=str).fillna("")

# app = FastAPI()

# # --- add/replace these functions in main.py ---
# def base_html(body: str) -> str:
#     return f"""
#     <html>
#     <head>
#       <meta charset="utf-8" />
#       <meta name="viewport" content="width=device-width, initial-scale=1" />
#       <title>D WATSON - Transaction Search</title>
#       <style>
#         :root {{
#           --bg: #0b1220;
#           --card: #11182a;
#           --muted: #9fb0c3;
#           --text: #e7eef8;
#           --accent: #3aa1ff;
#           --accent-2: #19c37d;
#           --danger: #ff5b5b;
#           --border: #21314a;
#         }}
#         * {{ box-sizing: border-box; }}
#         body {{
#           margin: 0; padding: 20px;
#           font-family: system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans";
#           background: radial-gradient(1200px 800px at 10% -20%, #1a2850, transparent),
#                       radial-gradient(1200px 800px at 90% 120%, #0c3c4c, transparent),
#                       var(--bg);
#           color: var(--text);
#         }}
#         .container {{
#           max-width: 1000px; margin: 0 auto;
#         }}
#         .title {{
#           font-size: 26px; font-weight: 700; letter-spacing: 0.4px;
#           margin: 10px 0 18px; text-align: center;
#         }}
#         .subtitle {{
#           font-size: 16px; color: var(--muted); text-align: center; margin-bottom: 25px;
#         }}
#         .card {{
#           background: linear-gradient(180deg, #121a2e 0%, #0f1729 100%);
#           border: 1px solid var(--border);
#           border-radius: 16px;
#           padding: 20px;
#           box-shadow: 0 10px 30px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.04);
#         }}
#         .grid {{
#           display: grid; gap: 16px;
#           grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
#         }}
#         .field {{
#           display: flex; flex-direction: column; gap: 8px;
#           background: #0c1324; border: 1px solid var(--border);
#           border-radius: 12px; padding: 14px;
#         }}
#         label {{ font-size: 13px; color: var(--muted); }}
#         input[type="text"] {{
#           appearance: none;
#           width: 100%;
#           padding: 12px 14px;
#           border-radius: 10px;
#           border: 1px solid #25324a;
#           background: #0a1120;
#           color: var(--text);
#           outline: none;
#           font-size: 14px;
#         }}
#         input[type="text"]::placeholder {{ color: #7f91a8; }}
#         .btn {{
#           display: inline-flex; align-items: center; justify-content: center;
#           padding: 10px 14px; gap: 8px; border-radius: 10px;
#           border: 1px solid #264e7b; background: linear-gradient(180deg, #0d6efd 0%, #0b5ed7 100%);
#           color: white; text-decoration: none; cursor: pointer; font-weight: 600;
#           font-size: 14px;
#         }}
#         .btn.secondary {{
#           background: linear-gradient(180deg, #1a243c 0%, #141c31 100%);
#           border: 1px solid var(--border); color: #d3e2f4;
#         }}
#         .btn:hover {{ filter: brightness(1.06); }}
#         .actions {{ display: flex; gap: 10px; flex-wrap: wrap; }}
#         .hint {{
#           margin-top: 6px; color: var(--muted); font-size: 12px;
#         }}
#         table {{
#           width: 100%; border-collapse: collapse;
#           margin-top: 18px; background: #0b1325; border: 1px solid var(--border);
#           border-radius: 14px; overflow: hidden;
#         }}
#         thead th {{
#           background: #0f1a32; color: #cbd8ea; text-align: left; font-size: 13px;
#           padding: 12px 12px;
#         }}
#         tbody td {{
#           padding: 12px 12px; font-size: 14px; color: #eaf2ff; border-top: 1px solid #182642;
#         }}
#         tbody tr:hover {{ background: #0e1a33; }}
#         .badge {{
#           display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 12px;
#         }}
#         .badge.credit {{ background: rgba(25,195,125,.15); color: #86f3c4; border: 1px solid rgba(25,195,125,.35); }}
#         .badge.debit  {{ background: rgba(255,91,91,.12); color: #ff9c9c; border: 1px solid rgba(255,91,91,.28); }}
#         .footer {{
#           margin-top: 24px; color: var(--muted); font-size: 13px; text-align: center;
#         }}
#       </style>
#     </head>
#     <body>
#       <div class="container">
#         <div class="title">💳 D WATSON - Transaction Search</div>
#         <div class="subtitle">POWERED BY MR WASI</div>
#         {body}
#         <div class="footer">© 2025 D WATSON • Built with FastAPI</div>
#       </div>
#     </body>
#     </html>
#     """


# # def base_html(body: str) -> str:
# #     return f"""
# #     <html>
# #     <head>
# #       <meta charset="utf-8" />
# #       <meta name="viewport" content="width=device-width, initial-scale=1" />
# #       <title>PDF Transaction Search</title>
# #       <style>
# #         :root {{
# #           --bg: #0b1220;
# #           --card: #11182a;
# #           --muted: #9fb0c3;
# #           --text: #e7eef8;
# #           --accent: #3aa1ff;
# #           --accent-2: #19c37d;
# #           --danger: #ff5b5b;
# #           --border: #21314a;
# #         }}
# #         * {{ box-sizing: border-box; }}
# #         body {{
# #           margin: 0; padding: 24px;
# #           font-family: system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans";
# #           background: radial-gradient(1200px 800px at 10% -20%, #1a2850, transparent),
# #                       radial-gradient(1200px 800px at 90% 120%, #0c3c4c, transparent),
# #                       var(--bg);
# #           color: var(--text);
# #         }}
# #         .container {{
# #           max-width: 980px; margin: 0 auto;
# #         }}
# #         .title {{
# #           font-size: 28px; font-weight: 700; letter-spacing: 0.3px;
# #           margin: 6px 0 18px;
# #         }}
# #         .card {{
# #           background: linear-gradient(180deg, #121a2e 0%, #0f1729 100%);
# #           border: 1px solid var(--border);
# #           border-radius: 16px;
# #           padding: 20px;
# #           box-shadow: 0 10px 30px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.04);
# #         }}
# #         .grid {{
# #           display: grid; gap: 16px;
# #           grid-template-columns: repeat(3, 1fr);
# #         }}
# #         @media (max-width: 900px) {{
# #           .grid {{ grid-template-columns: 1fr; }}
# #         }}
# #         .field {{
# #           display: flex; flex-direction: column; gap: 8px;
# #           background: #0c1324; border: 1px solid var(--border);
# #           border-radius: 12px; padding: 14px;
# #         }}
# #         label {{ font-size: 13px; color: var(--muted); }}
# #         input[type="text"] {{
# #           appearance: none;
# #           width: 100%;
# #           padding: 12px 14px;
# #           border-radius: 10px;
# #           border: 1px solid #25324a;
# #           background: #0a1120;
# #           color: var(--text);
# #           outline: none;
# #         }}
# #         input[type="text"]::placeholder {{ color: #7f91a8; }}
# #         .btn {{
# #           display: inline-flex; align-items: center; justify-content: center;
# #           padding: 10px 14px; gap: 8px; border-radius: 10px;
# #           border: 1px solid #264e7b; background: linear-gradient(180deg, #0d6efd 0%, #0b5ed7 100%);
# #           color: white; text-decoration: none; cursor: pointer; font-weight: 600;
# #         }}
# #         .btn.secondary {{
# #           background: linear-gradient(180deg, #1a243c 0%, #141c31 100%);
# #           border: 1px solid var(--border); color: #d3e2f4;
# #         }}
# #         .btn:hover {{ filter: brightness(1.06); }}
# #         .actions {{ display: flex; gap: 10px; flex-wrap: wrap; }}
# #         .hint {{
# #           margin-top: 10px; color: var(--muted); font-size: 13px;
# #         }}
# #         table {{
# #           width: 100%; border-collapse: separate; border-spacing: 0;
# #           margin-top: 18px; background: #0b1325; border: 1px solid var(--border);
# #           border-radius: 14px; overflow: hidden;
# #         }}
# #         thead th {{
# #           background: #0f1a32; color: #cbd8ea; text-align: left; font-size: 13px;
# #           padding: 12px 12px; border-bottom: 1px solid var(--border);
# #         }}
# #         tbody td {{
# #           padding: 12px 12px; border-bottom: 1px solid #182642; font-size: 14px; color: #eaf2ff;
# #         }}
# #         tbody tr:hover {{ background: #0e1a33; }}
# #         .badge {{
# #           display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 12px;
# #         }}
# #         .badge.credit {{ background: rgba(25,195,125,.15); color: #86f3c4; border: 1px solid rgba(25,195,125,.35); }}
# #         .badge.debit  {{ background: rgba(255,91,91,.12); color: #ff9c9c; border: 1px solid rgba(255,91,91,.28); }}
# #         .footer {{
# #           margin-top: 20px; color: var(--muted); font-size: 12px; text-align: center;
# #         }}
# #       </style>
# #     </head>
# #     <body>
# #       <div class="container">
# #         {body}
# #         <div class="footer">Powered by FastAPI • CSV-backed search</div>
# #       </div>
# #     </body>
# #     </html>
# #     """

# @app.get("/", response_class=HTMLResponse)
# def home():
#     body = """
#       <div class="title">🔎 PDF Transaction Search</div>
#       <div class="card">
#         <div class="grid">
#           <form class="field" action="/search-date" method="get">
#             <label>By Date (exact or partial)</label>
#             <input name="date" placeholder="e.g. 02 JUL 24 or 2024-07-02">
#             <div class="actions">
#               <button class="btn" type="submit">Search by Date</button>
#               <a class="btn secondary" href="/preview">Preview CSV</a>
#             </div>
#             <div class="hint">Tip: Partial works too (e.g. “02 JUL”)</div>
#           </form>

#           <form class="field" action="/search-amount" method="get">
#             <label>By Amount (credit/debit)</label>
#             <input name="amount" placeholder="e.g. 84695.00 or -84695.00">
#             <div class="actions">
#               <button class="btn" type="submit">Search by Amount</button>
#             </div>
#             <div class="hint">No commas. Use minus for debit.</div>
#           </form>

#           <form class="field" action="/search-id" method="get">
#             <label>By Transaction ID</label>
#             <input name="id" placeholder="e.g. 200515912587008">
#             <div class="actions">
#               <button class="btn" type="submit">Search by ID</button>
#             </div>
#             <div class="hint">Partial ID works (e.g. first 6 digits).</div>
#           </form>
#         </div>
#       </div>
#     """
#     return base_html(body)

# @app.get("/preview", response_class=HTMLResponse)
# def preview():
#     # show first 20 rows so the user can see formats
#     head = df.head(20)
#     rows_html = ""
#     for _, r in head.iterrows():
#         rows_html += f"""
#           <tr>
#             <td>{r.get('date','')}</td>
#             <td>{r.get('date_iso','')}</td>
#             <td>{r.get('description','')}</td>
#             <td>{r.get('id','')}</td>
#             <td>{r.get('value_date','')}</td>
#             <td><span class="badge debit">{r.get('debit','')}</span></td>
#             <td><span class="badge credit">{r.get('credit','')}</span></td>
#             <td>{r.get('balance','')}</td>
#           </tr>
#         """
#     table = f"""
#       <div class="title">📄 CSV Preview (first 20 rows)</div>
#       <div class="card">
#         <table>
#           <thead>
#             <tr>
#               <th>date</th><th>date_iso</th><th>description</th><th>id</th>
#               <th>value_date</th><th>debit</th><th>credit</th><th>balance</th>
#             </tr>
#           </thead>
#           <tbody>{rows_html}</tbody>
#         </table>
#         <div class="actions" style="margin-top:12px"><a class="btn secondary" href="/">← Back</a></div>
#       </div>
#     """
#     return base_html(table)

# def render_results(results: "pd.DataFrame") -> str:
#     if results.empty:
#         body = """
#           <div class="title">No results found</div>
#           <div class="card">
#             Try a partial search (e.g. enter just the first 6 digits of the ID, or “02 JUL” for date).
#             <div class="actions" style="margin-top:12px"><a class="btn secondary" href="/">← Back</a></div>
#           </div>
#         """
#         return base_html(body)

#     rows_html = ""
#     for _, r in results.iterrows():
#         rows_html += f"""
#           <tr>
#             <td>{r.get('date','')}</td>
#             <td>{r.get('date_iso','')}</td>
#             <td>{r.get('description','')}</td>
#             <td>{r.get('id','')}</td>
#             <td>{r.get('value_date','')}</td>
#             <td><span class="badge debit">{r.get('debit','')}</span></td>
#             <td><span class="badge credit">{r.get('credit','')}</span></td>
#             <td>{r.get('balance','')}</td>
#           </tr>
#         """

#     table = f"""
#       <div class="title">🔎 Results ({len(results)} found)</div>
#       <div class="card">
#         <table>
#           <thead>
#             <tr>
#               <th>date</th><th>date_iso</th><th>description</th><th>id</th>
#               <th>value_date</th><th>debit</th><th>credit</th><th>balance</th>
#             </tr>
#           </thead>
#           <tbody>{rows_html}</tbody>
#         </table>
#         <div class="actions" style="margin-top:12px"><a class="btn secondary" href="/">← Back</a></div>
#       </div>
#     """
#     return base_html(table)

# # --- your CSS + base_html/home/preview/render_results functions go here ---
# # (the big block you pasted in the last message)


# # 🔎 SEARCH ENDPOINTS -------------------------

# @app.get("/search-date", response_class=HTMLResponse)
# def get_by_date(date: str):
#     # allow partial matching
#     results = df[df["date"].str.contains(date.strip(), case=False, na=False) |
#                  df["date_iso"].str.contains(date.strip(), case=False, na=False)]
#     return render_results(results)

# @app.get("/search-amount", response_class=HTMLResponse)
# def get_by_amount(amount: str):
#     amount = amount.replace(",", "").strip()
#     results = df[(df["debit"].str.contains(amount, na=False)) |
#                  (df["credit"].str.contains(amount, na=False))]
#     return render_results(results)

# @app.get("/search-id", response_class=HTMLResponse)
# def get_by_id(id: str):
#     id = id.strip()
#     results = df[df["id"].str.contains(id, na=False)]
#     return render_results(results)


# # 🔧 Run server
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
