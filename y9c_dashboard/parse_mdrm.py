# parse_mdrm.py
import pandas as pd
import os
import requests
import streamlit as st
from datetime import datetime

def load_mnemonic_mapping():
    SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise EnvironmentError("❌ Supabase environment variables are not set.")

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    # Fetch up to 10,000 rows in pages of 2,000
    rows = []
    page_size = 2000
    offset = 0

    while True:
        url = f"{SUPABASE_URL}/rest/v1/mdrm_mapping?select=*&offset={offset}&limit={page_size}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"❌ Failed to load MDRM data: {response.text}")

        page = response.json()
        if not page:
            break

        rows.extend(page)
        if len(page) < page_size:
            break
        offset += page_size

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError("⚠️ MDRM table in Supabase is empty.")

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")

    df = df[df["reporting_form"].str.contains("FR Y-9C", na=False)]
    df = df[df["end_date"].isna() | (df["end_date"] >= datetime.today())]

    df["key"] = df["mnemonic"].str.upper() + df["item_code"].astype(str)
    df = df.sort_values(by="start_date", ascending=False)
    df = df.drop_duplicates(subset="key", keep="first")

    return {row["key"]: row["item_name"].strip() for _, row in df.iterrows()}
