import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from store import get_transactions
from groq import Groq

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str
    
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

def get_groq_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_model():
    return os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

def build_financial_context():
    txns = get_transactions()
    income = sum(t["amount"] for t in txns if t["type"] == "income")
    expenses = sum(t["amount"] for t in txns if t["type"] == "expense")
    net_profit = income - expenses
    profit_margin = ((net_profit / income) * 100) if income > 0 else 0

    cat_map = {}
    for t in txns:
        if t["type"] == "expense":
            cat_map[t["category"]] = cat_map.get(t["category"], 0) + t["amount"]
            
    top_expenses = sorted(cat_map.items(), key=lambda x: x[1], reverse=True)[:5]
    top_expenses_str = ", ".join([f"{k}: ₹{v:,.2f}" for k, v in top_expenses])
    
    recent_txns = sorted(txns, key=lambda x: x["date"], reverse=True)[:8]
    recent_txns_str = "\n".join([f"{t['date']} | {'+' if t['type']=='income' else '-'}₹{t['amount']} | {t['description']} ({t['category']})" for t in recent_txns])
    
    return f"""You are Vantge's AI financial advisor for a small/medium Indian business.
Here is their current financial data:

FINANCIAL SUMMARY:
- Total Revenue: ₹{income:,.2f}
- Total Expenses: ₹{expenses:,.2f}
- Net Profit: ₹{net_profit:,.2f}
- Profit Margin: {profit_margin:.1f}%
- Total Transactions: {len(txns)}

TOP EXPENSE CATEGORIES:
{top_expenses_str}

RECENT TRANSACTIONS:
{recent_txns_str}

Your role: Give concise, actionable, friendly financial advice. Use Indian business context (₹ currency, GST awareness, Indian market conditions). Keep answers short (3-5 sentences max unless asked otherwise). Be encouraging but honest about financial risks."""

@router.post("/chat")
def chat_with_ai(req: ChatRequest):
    try:
        system_prompt = build_financial_context()
        messages = [{"role": "system", "content": system_prompt}]
        for h in req.history[-10:]:
            messages.append({"role": h.role, "content": h.content})
        
        messages.append({"role": "user", "content": req.message})
        
        client = get_groq_client()
        completion = client.chat.completions.create(
            model=get_model(),
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        reply = completion.choices[0].message.content or "Sorry, I could not generate a response."
        return {"success": True, "reply": reply}
    except Exception as e:
        return {"success": False, "message": "AI service error", "error": str(e)}

@router.get("/quick-insights")
def quick_insights():
    try:
        system_prompt = build_financial_context()
        client = get_groq_client()
        completion = client.chat.completions.create(
            model=get_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Analyze this business data and give me 4 key insights: 1 about revenue, 1 about top expense risk, 1 about profit margin, 1 actionable recommendation. Format each as a short bullet point starting with an emoji."}
            ],
            max_tokens=400,
            temperature=0.6,
        )
        insights = completion.choices[0].message.content or ""
        return {"success": True, "insights": insights}
    except Exception as e:
        return {"success": False, "message": str(e)}
