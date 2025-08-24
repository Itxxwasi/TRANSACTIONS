# pdf_parser.py
import re
import sys
import pdfplumber
import pandas as pd
from datetime import datetime
import os

DATE_RX = re.compile(r"^\s*(\d{2}\s+[A-Z]{3}\s+\d{2})\b")
AMOUNT_RX = re.compile(r"-?\d{1,3}(?:,\d{3})*\.\d{2}")
ID_RX = re.compile(r"\b(\d{8,18})\b")  # picks up IDs like 19828166 or 200515912587008

def _norm_amount(s: str) -> str:
    """Normalize amount string: remove commas, keep sign, keep 2 decimals as string."""
    s = s.strip()
    s = s.replace(",", "")
    if not re.fullmatch(r"-?\d+(\.\d{2})", s):
        return s
    return s

def _to_iso(date_txt: str) -> str:
    """Convert '02 JUL 24' -> '2024-07-02' (assumes 20xx)."""
    date_txt = date_txt.strip().upper()
    try:
        d = datetime.strptime(date_txt, "%d %b %y")
        return d.strftime("%Y-%m-%d")
    except Exception:
        return ""

def _clean_line(line: str) -> str:
    return " ".join(line.split())

def parse_pdf_to_rows(pdf_file: str) -> list[dict]:
    rows = []
    current = None

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=1, y_tolerance=1) or ""
            for raw_line in text.split("\n"):
                line = _clean_line(raw_line)

                if not line or any(h in line.upper() for h in [
                    "DATE", "DESCRIPTION", "VALUE DATE", "DEBIT", "CREDIT", "BALANCE",
                    "ACCOUNT", "STATEMENT", "PAGE", "OPENING BALANCE", "CLOSING BALANCE"
                ]):
                    continue

                m_date = DATE_RX.match(line)
                if m_date:
                    if current:
                        rows.append(_parse_record(current))
                    current = {
                        "date_txt": m_date.group(1).strip(),
                        "raw": line
                    }
                else:
                    if current:
                        current["raw"] += " " + line

        if current:
            rows.append(_parse_record(current))

    rows = [r for r in rows if r.get("date") or r.get("description")]
    return rows

def _parse_record(block: dict) -> dict:
    raw = block.get("raw", "").strip()

    date_txt = block.get("date_txt", "").strip()
    date_iso = _to_iso(date_txt)

    amounts = AMOUNT_RX.findall(raw)
    debit = credit = balance = ""
    if len(amounts) >= 3:
        debit, credit, balance = amounts[-3], amounts[-2], amounts[-1]
        debit, credit, balance = _norm_amount(debit), _norm_amount(credit), _norm_amount(balance)

        tmp = raw
        for a in [balance, credit, debit]:
            tmp = tmp[::-1].replace(a[::-1], "", 1)[::-1]
        stripped = tmp.strip()
    else:
        stripped = raw

    desc_part = DATE_RX.sub("", stripped, count=1).strip()

    value_date = ""
    other_dates = re.findall(r"\b\d{2}\s+[A-Z]{3}\s+\d{2}\b", desc_part)
    if other_dates:
        value_date = other_dates[-1]
        desc_part = re.sub(r"\b" + re.escape(value_date) + r"\b", "", desc_part).strip()

    trans_id = ""
    m_id = ID_RX.search(desc_part)
    if m_id:
        trans_id = m_id.group(1)

    description = _clean_line(desc_part)

    return {
        "date": date_txt,
        "date_iso": date_iso,
        "description": description,
        "id": trans_id,
        "value_date": value_date,
        "debit": debit,
        "credit": credit,
        "balance": balance,
        "raw": raw
    }

def parse_pdf_to_csv(pdf_file: str = "STMT.ENT.BOOK1.pdf", csv_file: str = "transactions.csv") -> str:
    rows = parse_pdf_to_rows(pdf_file)
    new_df = pd.DataFrame(rows, columns=[
        "date", "date_iso", "description", "id", "value_date", "debit", "credit", "balance", "raw"
    ]).fillna("")

    for col in new_df.columns:
        new_df[col] = new_df[col].astype(str).str.strip()

    if os.path.exists(csv_file):
        old_df = pd.read_csv(csv_file, dtype=str).fillna("")
        existing_rows = len(old_df)

        # Only keep new rows
        new_rows = new_df.iloc[existing_rows:]
        if new_rows.empty:
            print("✅ No new rows found. Already up-to-date.")
        else:
            new_rows.to_csv(csv_file, mode="a", header=False, index=False)
            print(f"✅ Added {len(new_rows)} new rows -> {csv_file} (now {existing_rows+len(new_rows)} total)")
    else:
        new_df.to_csv(csv_file, index=False)
        print(f"✅ Created {csv_file} with {len(new_df)} rows")

    return csv_file

if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else "STMT.ENT.BOOK1.pdf"
    csv = sys.argv[2] if len(sys.argv) > 2 else "transactions.csv"
    parse_pdf_to_csv(pdf, csv)










# # pdf_parser.py
# import re
# import sys
# import pdfplumber
# import pandas as pd
# from datetime import datetime

# DATE_RX = re.compile(r"^\s*(\d{2}\s+[A-Z]{3}\s+\d{2})\b")
# AMOUNT_RX = re.compile(r"-?\d{1,3}(?:,\d{3})*\.\d{2}")
# ID_RX = re.compile(r"\b(\d{8,18})\b")  # picks up IDs like 19828166 or 200515912587008

# def _norm_amount(s: str) -> str:
#     """Normalize amount string: remove commas, keep sign, keep 2 decimals as string."""
#     s = s.strip()
#     s = s.replace(",", "")
#     # sanity check
#     if not re.fullmatch(r"-?\d+(\.\d{2})", s):
#         return s  # leave as-is if unexpected
#     return s

# def _to_iso(date_txt: str) -> str:
#     """Convert '02 JUL 24' -> '2024-07-02' (assumes 20xx)."""
#     date_txt = date_txt.strip().upper()
#     try:
#         # Fast path: DD MON YY
#         d = datetime.strptime(date_txt, "%d %b %y")
#         return d.strftime("%Y-%m-%d")
#     except Exception:
#         return ""

# def _clean_line(line: str) -> str:
#     return " ".join(line.split())  # collapse whitespace

# def parse_pdf_to_rows(pdf_file: str) -> list[dict]:
#     """
#     Parses the PDF into transaction rows.
#     Strategy:
#       - Build records by detecting lines that START with a date.
#       - Merge following wrapped lines into the current record's 'raw' text.
#       - From the raw, extract:
#            date, description, (optional) value_date, debit, credit, balance, id
#     """
#     rows = []
#     current = None

#     with pdfplumber.open(pdf_file) as pdf:
#         for page in pdf.pages:
#             text = page.extract_text(x_tolerance=1, y_tolerance=1) or ""
#             for raw_line in text.split("\n"):
#                 line = _clean_line(raw_line)

#                 # Skip obvious headers/footers
#                 if not line or any(h in line.upper() for h in [
#                     "DATE", "DESCRIPTION", "VALUE DATE", "DEBIT", "CREDIT", "BALANCE",
#                     "ACCOUNT", "STATEMENT", "PAGE", "OPENING BALANCE", "CLOSING BALANCE"
#                 ]):
#                     continue

#                 m_date = DATE_RX.match(line)
#                 if m_date:
#                     # Close previous record
#                     if current:
#                         rows.append(_parse_record(current))

#                     # Start new record block
#                     current = {
#                         "date_txt": m_date.group(1).strip(),
#                         "raw": line
#                     }
#                 else:
#                     # Continuation of description (wrapped lines)
#                     if current:
#                         current["raw"] += " " + line
#                     else:
#                         # stray line before first date — ignore
#                         pass

#         # close last record
#         if current:
#             rows.append(_parse_record(current))

#     # Filter out empty/failed parses
#     rows = [r for r in rows if r.get("date") or r.get("description")]
#     return rows

# def _parse_record(block: dict) -> dict:
#     raw = block.get("raw", "").strip()

#     # 1) Date (text + ISO)
#     date_txt = block.get("date_txt", "").strip()
#     date_iso = _to_iso(date_txt)

#     # 2) Amounts: expect the last three monetary numbers to be Debit, Credit, Balance
#     amounts = AMOUNT_RX.findall(raw)
#     debit = credit = balance = ""
#     if len(amounts) >= 3:
#         # Take the LAST three
#         debit, credit, balance = amounts[-3], amounts[-2], amounts[-1]
#         debit, credit, balance = _norm_amount(debit), _norm_amount(credit), _norm_amount(balance)

#         # Remove those trailing amounts from the raw to isolate description/value_date
#         # (Remove in reverse order to avoid shifting)
#         tmp = raw
#         for a in [balance, credit, debit]:
#             # remove only once, from the right
#             tmp = tmp[::-1].replace(a[::-1], "", 1)[::-1]
#         stripped = tmp.strip()
#     else:
#         stripped = raw

#     # 3) Remove the leading date from the description part
#     desc_part = DATE_RX.sub("", stripped, count=1).strip()

#     # 4) Optional value_date (often another DD MON YY right after description)
#     #    If present near the end of the description chunk, lift it out.
#     value_date = ""
#     # Look for a second date anywhere; prefer the LAST one that isn't the first date
#     other_dates = re.findall(r"\b\d{2}\s+[A-Z]{3}\s+\d{2}\b", desc_part)
#     if other_dates:
#         value_date = other_dates[-1]
#         # Remove that from desc
#         desc_part = re.sub(r"\b" + re.escape(value_date) + r"\b", "", desc_part).strip()

#     # 5) Try to extract an ID from the remaining description
#     trans_id = ""
#     m_id = ID_RX.search(desc_part)
#     if m_id:
#         trans_id = m_id.group(1)

#     # Clean multiple spaces again
#     description = _clean_line(desc_part)

#     return {
#         "date": date_txt,         # e.g., "02 JUL 24"
#         "date_iso": date_iso,     # e.g., "2024-07-02"
#         "description": description,
#         "id": trans_id,
#         "value_date": value_date,
#         "debit": debit,
#         "credit": credit,
#         "balance": balance,
#         "raw": raw  # keep raw for debugging if needed
#     }

# def parse_pdf_to_csv(pdf_file: str = "STMT.ENT.BOOK1.pdf", csv_file: str = "transactions.csv") -> str:
#     rows = parse_pdf_to_rows(pdf_file)

#     # Build DataFrame as strings to keep formats consistent for searching
#     df = pd.DataFrame(rows, columns=[
#         "date", "date_iso", "description", "id", "value_date", "debit", "credit", "balance", "raw"
#     ]).fillna("")

#     # Final tidy: strip spaces
#     for col in df.columns:
#         df[col] = df[col].astype(str).str.strip()

#     # Save
#     df.to_csv(csv_file, index=False)
#     print(f"✅ Parsed {len(df)} rows -> {csv_file}")
#     return csv_file

# if __name__ == "__main__":
#     # Allow: python pdf_parser.py [PDF] [CSV]
#     pdf = sys.argv[1] if len(sys.argv) > 1 else "STMT.ENT.BOOK1.pdf"
#     csv = sys.argv[2] if len(sys.argv) > 2 else "transactions.csv"
#     parse_pdf_to_csv(pdf, csv)
