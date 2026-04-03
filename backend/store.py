import json
import os
import random
from datetime import datetime

# Build path to the JSON file
# Use /tmp for writable storage on Render (ephemeral but works within session)
DB_FILE = os.path.join("/tmp", "vantge_transactions.json")

# Make sure directory exists
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

transactions = []

def seed_data():
    generated = []
    start = datetime(2025, 9, 1).timestamp()
    end = datetime(2026, 3, 25).timestamp()
    exp_cats = ['Rent', 'Salaries', 'Inventory', 'Marketing', 'Utilities', 'Software']
    inc_cats = ['Sales', 'Services', 'Consulting']

    for i in range(115):
        time_ts = start + random.random() * (end - start)
        date_str = datetime.fromtimestamp(time_ts).strftime('%Y-%m-%d')
        is_income = random.random() > 0.65
        t_type = 'income' if is_income else 'expense'
        amount = random.randint(1500, 81500)
        
        if is_income:
            category = random.choice(inc_cats)
            description = f"Invoice #{random.randint(1000, 9999)} Payment"
        else:
            category = random.choice(exp_cats)
            description = f"Expense - {category} {random.randint(0, 99)}"
            
        generated.append({
            "id": str(int(datetime.now().timestamp() * 1000)) + str(i) + str(random.random())[2:8],
            "date": date_str,
            "description": description,
            "amount": amount,
            "type": t_type,
            "category": category
        })
        
    generated.sort(key=lambda x: x['date'])
    return generated

def load_data():
    global transactions
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if len(data) > 0:
                    transactions = data
                    return
        except Exception as e:
            print("Error reading DB:", e)
    
    transactions = seed_data()
    save_data()

def save_data():
    global transactions
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, indent=2)
    except Exception as e:
        print("Error saving DB:", e)

# Initial load
load_data()

def get_transactions():
    return transactions

def clear_transactions():
    global transactions
    transactions = []
    save_data()

def add_transaction(txn: dict):
    global transactions
    new_txn = txn.copy()
    new_txn["id"] = str(int(datetime.now().timestamp() * 1000)) + str(random.random())[2:8]
    transactions.append(new_txn)
    save_data()
    return new_txn

def add_transactions(txns: list):
    global transactions
    new_txns = []
    for t in txns:
        new_txn = t.copy()
        new_txn["id"] = str(int(datetime.now().timestamp() * 1000)) + str(random.random())[2:8]
        new_txns.append(new_txn)
    transactions.extend(new_txns)
    save_data()
    return new_txns

def delete_transaction(tid: str):
    global transactions
    for i, t in enumerate(transactions):
        if t["id"] == tid:
            del transactions[i]
            save_data()
            return True
    return False

def update_transaction(tid: str, updates: dict):
    global transactions
    for i, t in enumerate(transactions):
        if t["id"] == tid:
            transactions[i].update(updates)
            save_data()
            return transactions[i]
    return None
