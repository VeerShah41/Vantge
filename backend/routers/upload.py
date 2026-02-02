from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import csv
import io
import re
import pdfplumber
import datetime
from store import add_transactions

router = APIRouter()

def parse_amount(raw):
    if not raw: return 0
    cleaned = re.sub(r'[₹$€£,\s]', '', str(raw))
    try:
        return float(cleaned)
    except:
        return 0

def guess_category(desc):
    desc = (desc or '').lower()
    if re.search(r'rent|lease|property', desc): return 'Rent'
    if re.search(r'salary|salari|payroll|wages', desc): return 'Salaries'
    if re.search(r'material|inventory|stock|purchase', desc): return 'Inventory'
    if re.search(r'util|electric|water|gas|internet|broadband', desc): return 'Utilities'
    if re.search(r'market|advertis|promo', desc): return 'Marketing'
    if re.search(r'software|saas|subscription|license', desc): return 'Software'
    if re.search(r'equip|machin|tool|hardware', desc): return 'Equipment'
    if re.search(r'transport|logistic|delivery|courier|fuel', desc): return 'Transport'
    if re.search(r'tax|gst|tds|income tax', desc): return 'Taxes'
    if re.search(r'sales|revenue|invoice|receipt|payment received', desc): return 'Sales'
    if re.search(r'service|consult|professional', desc): return 'Services'
    return 'Uncategorized'

def parse_date(raw):
    raw = raw.strip()
    # DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r'^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})$', raw)
    if m:
        d, mo, y = m.groups()
        if len(y) == 2: y = '20' + y
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
        
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', raw)
    if m: return raw
    
    MONTHS = {'jan':'01','feb':'02','mar':'03','apr':'04','may':'05','jun':'06',
              'jul':'07','aug':'08','sep':'09','oct':'10','nov':'11','dec':'12'}
    m = re.match(r'^(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})$', raw)
    if m:
        d, mon_str, y = m.groups()
        mo = MONTHS.get(mon_str[:3].lower())
        if mo:
            return f"{y}-{mo}-{d.zfill(2)}"
    return None

def extract_transactions_from_text(text: str):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    results = []
    
    date_regex = re.compile(r'\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,}\s+\d{4}|\d{4}-\d{2}-\d{2})\b')
    amt_regex = re.compile(r'₹?\s*([\d,]+\.?\d*)')
    
    for line in lines:
        m_date = date_regex.search(line)
        if not m_date: continue
        raw_date = m_date.group(1)
        parsed_date = parse_date(raw_date)
        if not parsed_date: continue
        
        rest = line.replace(m_date.group(0), '', 1).strip()
        amounts_str = amt_regex.findall(rest)
        amounts = [parse_amount(a) for a in amounts_str if parse_amount(a) > 0]
        
        if not amounts: continue
        
        desc = rest.replace(m_date.group(0), '')
        desc = re.sub(r'₹?\s*[\d,]+\.?\d*', '', desc)
        desc = re.sub(r'\b(Dr|Cr|DR|CR|debit|credit)\b', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'\s{2,}', ' ', desc).strip()
        
        if len(desc) < 3: continue
        
        t_type = 'expense'
        if re.search(r'\b(Cr|CR|credit|credited|received|inward|deposit)\b', line, re.IGNORECASE):
            t_type = 'income'
        if re.search(r'\b(Dr|DR|debit|debited|paid|charge|withdrawal)\b', line, re.IGNORECASE):
            t_type = 'expense'
            
        amt = amounts[0]
        
        results.append({
            "date": parsed_date,
            "description": desc[:120],
            "amount": amt,
            "type": t_type,
            "category": guess_category(desc)
        })
    return results


@router.post("/csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    contents = await file.read()
    decoded = contents.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    
    results = []
    for row in reader:
        date = row.get("Date", row.get("date", row.get("DATE", "")))
        desc = row.get("Description", row.get("description", row.get("Narration", row.get("narration", ""))))
        amt_raw = row.get("Amount", row.get("amount", row.get("Credit", row.get("Debit", 0))))
        amount = abs(parse_amount(amt_raw))
        
        t_type = "expense"
        if row.get("Type") or row.get("type"):
            t_type = str(row.get("Type", row.get("type", ""))).lower()
        elif row.get("Credit"):
            t_type = "income"
            
        category = row.get("Category", row.get("category", "")) or guess_category(desc)
        if date and desc and amount:
            results.append({
                "date": date,
                "description": desc,
                "amount": amount,
                "type": t_type,
                "category": category
            })
            
    added = add_transactions(results)
    return {"success": True, "message": f"{len(added)} transactions imported", "data": added}

@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    if not (file.filename.endswith('.pdf') or file.content_type == 'application/pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
        
    contents = await file.read()
    try:
        raw_text = ""
        n_pages = 0
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            n_pages = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    raw_text += page_text + "\n"
        
        if len(raw_text.strip()) < 50:
            return {"success": False, "message": "Could not extract text from PDF. It may be a scanned/image-based PDF. Please try a text-based bank statement PDF."}
            
        transactions = extract_transactions_from_text(raw_text)
        if not transactions:
            return {"success": False, "message": "No transactions found in this PDF.", "rawTextPreview": raw_text[:500]}
            
        added = add_transactions(transactions)
        return {
            "success": True,
            "message": f"{len(added)} transactions extracted from PDF",
            "data": added,
            "pages": n_pages
        }
    except Exception as e:
        return {"success": False, "message": "Failed to parse PDF", "error": str(e)}

@router.post("/pdf/preview")
async def preview_pdf(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        raw_text = ""
        n_pages = 0
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            n_pages = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    raw_text += page_text + "\n"
                    
        transactions = extract_transactions_from_text(raw_text)
        return {
            "success": True,
            "rawText": raw_text[:2000],
            "detected": transactions[:20],
            "pages": n_pages
        }
    except Exception as e:
         return {"success": False, "message": str(e)}
