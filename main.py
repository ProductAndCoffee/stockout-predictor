from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

class PredictionResponse(BaseModel):
    item_id: str
    closing_stock: int
    sales_rate_per_day: float
    days_to_stockout: float

@app.get("/predict/{item_id}", response_model=PredictionResponse)
def predict_stockout(item_id: str):
    # Fetch inventory
    inv_resp = supabase.table("inventory").select("*").eq("item_id", item_id).execute()
    if not inv_resp.data:
        return {"error": "Item not found"}

    inventory = inv_resp.data[0]
    closing_stock = inventory["closing_stock"]

    # Fetch sales last 30 days
    start_date = (datetime.now() - timedelta(days=30)).date().isoformat()
    sales_resp = supabase.table("sales").select("quantity, sale_date").eq("item_id", item_id).gte("sale_date", start_date).execute()
    sales_data = sales_resp.data

    if not sales_data:
        return {
            "item_id": item_id,
            "closing_stock": closing_stock,
            "sales_rate_per_day": 0.0,
            "days_to_stockout": 9999
        }

    # Convert to DataFrame
    df = pd.DataFrame(sales_data)
    total_qty = df["quantity"].sum()
    sales_rate = total_qty / 30

    days_to_stockout = closing_stock / sales_rate if sales_rate > 0 else 9999

    return {
        "item_id": item_id,
        "closing_stock": closing_stock,
        "sales_rate_per_day": round(sales_rate, 2),
        "days_to_stockout": round(days_to_stockout, 1)
    }