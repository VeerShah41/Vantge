from fastapi import APIRouter
from store import get_transactions
import pandas as pd
import numpy as np
import datetime
import traceback
# import matplotlib.pyplot as plt

router = APIRouter()

def get_transactions_df():
    txns = get_transactions()
    if not txns:
        return pd.DataFrame(columns=["id", "date", "description", "amount", "type", "category"])
    df = pd.DataFrame(txns)
    df['date'] = pd.to_datetime(df['date'])
    return df

@router.get("/summary")
def analytics_summary():
    try:
        df = get_transactions_df()
        if df.empty:
            return {
                "success": True,
                "data": {
                    "totalIncome": 0, "totalExpenses": 0, "netProfit": 0, "profitMargin": 0,
                    "cashFlow": 0, "monthIncome": 0, "monthExpenses": 0, "monthNetProfit": 0,
                    "transactionCount": 0
                }
            }
        
        income = float(df[df['type'] == 'income']['amount'].sum())
        expenses = float(df[df['type'] == 'expense']['amount'].sum())
        netProfit = income - expenses
        profitMargin = (netProfit / income * 100) if income > 0 else 0

        now = datetime.datetime.now()
        current_month = df[df['date'].dt.month == now.month]
        current_month = current_month[current_month['date'].dt.year == now.year]
        
        monthIncome = float(current_month[current_month['type'] == 'income']['amount'].sum())
        monthExpenses = float(current_month[current_month['type'] == 'expense']['amount'].sum())
        
        return {
            "success": True,
            "data": {
                "totalIncome": income,
                "totalExpenses": expenses,
                "netProfit": netProfit,
                "profitMargin": round(profitMargin, 1),
                "cashFlow": netProfit,
                "monthIncome": monthIncome,
                "monthExpenses": monthExpenses,
                "monthNetProfit": monthIncome - monthExpenses,
                "transactionCount": len(df),
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e), "trace": traceback.format_exc()}

@router.get("/trend")
def trend():
    try:
        df = get_transactions_df()
        if df.empty:
            return {"success": True, "data": []}
            
        # Last 6 months trend using pandas Grouper
        now = datetime.datetime.now()
        six_months_ago = now - pd.DateOffset(months=5)
        six_months_ago = six_months_ago.replace(day=1)
        
        recent_df = df[df['date'] >= six_months_ago]
        
        # We need all 6 months even if empty
        months_list = pd.date_range(start=six_months_ago, end=now, freq='MS')
        results = []
        for m in months_list:
            m_df = recent_df[(recent_df['date'].dt.month == m.month) & (recent_df['date'].dt.year == m.year)]
            inc = float(m_df[m_df['type'] == 'income']['amount'].sum())
            exp = float(m_df[m_df['type'] == 'expense']['amount'].sum())
            results.append({
                "month": m.strftime("%b %Y"),
                "income": inc,
                "expenses": exp,
                "profit": inc - exp
            })

        return {"success": True, "data": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/categories")
def categories():
    try:
        df = get_transactions_df()
        if df.empty:
            return {"success": True, "data": []}
            
        exp_df = df[df['type'] == 'expense']
        if exp_df.empty:
            return {"success": True, "data": []}
            
        grouped = exp_df.groupby('category')['amount'].sum().reset_index()
        data = [{"name": row['category'], "value": float(row['amount'])} for _, row in grouped.iterrows()]
        return {"success": True, "data": data}
    except Exception as e:
         return {"success": False, "error": str(e)}

@router.get("/anomalies")
def anomalies():
    try:
        df = get_transactions_df()
        anomalies_list = []
        
        if not df.empty:
            exp_df = df[df['type'] == 'expense']
            if not exp_df.empty:
                # Group by category using pandas and find spikes (mean + deviation)
                grouped = exp_df.groupby('category')['amount'].agg(['mean', 'last', 'count']).reset_index()
                for _, row in grouped.iterrows():
                    if row['count'] < 2: continue
                    avg = row['mean']
                    latest = row['last']
                    if latest > avg * 1.4:
                        sev = "high" if latest > avg * 1.8 else "medium"
                        anomalies_list.append({
                            "type": "expense_spike",
                            "category": row['category'],
                            "message": f"{row['category']} spending is {round(((latest - avg) / avg) * 100)}% above average",
                            "severity": sev,
                            "amount": float(latest),
                            "average": float(round(avg))
                        })

            income = float(df[df['type'] == 'income']['amount'].sum())
            expenses = float(df[df['type'] == 'expense']['amount'].sum())
            if income > 0 and expenses > income * 0.85:
                 anomalies_list.append({
                    "type": "low_margin",
                    "category": "Cash Flow",
                    "message": f"Expenses are {round((expenses / income) * 100)}% of revenue — profit margin is very thin",
                    "severity": "high"
                })

        return {"success": True, "data": anomalies_list}
    except Exception as e:
        return {"success": False, "error": str(e), "trace": traceback.format_exc()}

@router.get("/recommendations")
def recommendations():
    try:
        df = get_transactions_df()
        recs = []
        
        if not df.empty:
            income = float(df[df['type'] == 'income']['amount'].sum())
            expenses = float(df[df['type'] == 'expense']['amount'].sum())
            
            exp_df = df[df['type'] == 'expense']
            if not exp_df.empty and expenses > 0:
                grouped = exp_df.groupby('category')['amount'].sum().reset_index()
                for _, row in grouped.iterrows():
                    pct = (row['amount'] / expenses) * 100
                    if pct > 30:
                        recs.append({
                            "icon": '⚠️',
                            "priority": 'high',
                            "title": f"High {row['category']} Spend",
                            "description": f"{row['category']} is {round(pct)}% of total expenses. Consider reviewing contracts or finding alternatives."
                        })
            
            if income > 0 and expenses / income > 0.7:
                recs.append({
                    "icon": '📊',
                    "priority": 'high',
                    "title": 'Improve Profit Margin',
                    "description": 'Your profit margin is below 30%. Focus on reducing top expense categories or increasing pricing.',
                })
                
        recs.append({
            "icon": '💡',
            "priority": 'medium',
            "title": 'Diversify Revenue',
            "description": 'Consider adding a new product line or service offering to reduce dependency on single revenue streams.'
        })

        recs.append({
            "icon": '📅',
            "priority": 'low',
            "title": 'Build an Emergency Fund',
            "description": 'Aim to maintain 3 months of operating expenses as a cash reserve for business continuity.'
        })

        return {"success": True, "data": recs}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/health-score")
def health_score():
    try:
        df = get_transactions_df()
        score = 50
        profitMargin = 0
        if not df.empty:
            income = float(df[df['type'] == 'income']['amount'].sum())
            expenses = float(df[df['type'] == 'expense']['amount'].sum())
            
            if income > 0:
                profitMargin = (income - expenses) / income
                
            if profitMargin > 0.3: score += 30
            elif profitMargin > 0.15: score += 15
            elif profitMargin < 0: score -= 20
            
            inc_df = df[df['type'] == 'income']
            inc_cats = inc_df['category'].nunique()
            if inc_cats >= 3: score += 15
            elif inc_cats == 2: score += 8

        score = min(100, max(0, score))
        if score >= 80: grade = 'Excellent'
        elif score >= 60: grade = 'Good'
        elif score >= 40: grade = 'Fair'
        else: grade = 'Critical'
        
        return {"success": True, "data": {"score": score, "grade": grade, "profitMargin": f"{profitMargin * 100:.1f}"}}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/stats")
def stats():
    try:
        df = get_transactions_df()
        if df.empty:
            return {
                "success": True,
                "data": {
                    "totalTransactions": 0, "totalIncome": 0, "totalExpenses": 0,
                    "netProfit": 0, "uniqueCategories": 0, "healthyBalance": True
                }
            }
            
        income = float(df[df['type'] == 'income']['amount'].sum())
        expenses = float(df[df['type'] == 'expense']['amount'].sum())
        
        return {
            "success": True,
            "data": {
                "totalTransactions": len(df),
                "totalIncome": income,
                "totalExpenses": expenses,
                "netProfit": income - expenses,
                "uniqueCategories": df['category'].nunique(),
                "healthyBalance": income > expenses
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
