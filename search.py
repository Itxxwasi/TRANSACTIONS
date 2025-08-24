import pdfplumber
import re
import pandas as pd

def parse_pdf_to_csv(pdf_file="STMT.ENT.BOOK1.pdf", csv_file="transactions.csv"):
    transactions = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split("\n"):
                match = re.match(
                    r"(\d{2} \w{3} \d{2})\s+(.+?)\s+(\d+)?\s*(\d{2} \w{3} \d{2})?\s+(-?\d+[,\d]*\.\d{2}|0\.00)\s+(-?\d+[,\d]*\.\d{2}|0\.00)\s+([\d,]+\.\d{2})",
                    line
                )
                if match:
                    transactions.append({
                        "date": match.group(1),
                        "description": match.group(2).strip(),
                        "id": match.group(3),
                        "value_date": match.group(4),
                        "debit": match.group(5),
                        "credit": match.group(6),
                        "balance": match.group(7),
                    })
    # Save to CSV
    df = pd.DataFrame(transactions)
    df.to_csv(csv_file, index=False)
    return csv_file

if __name__ == "__main__":
    print("Parsing PDF to CSV...")
    parse_pdf_to_csv()
    print("CSV created: transactions.csv")
