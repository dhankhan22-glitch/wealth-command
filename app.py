import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="Wealth Command", layout="wide", initial_sidebar_state="expanded")
DATA_FILE = "expense_database.csv"

# --- CUSTOM CATEGORIES ---
CATEGORIES = [
    "1. Housing, Rent & EMIs",
    "2. Automated Strategic Savings (SIP)",
    "3. Convenience Apps (Zomato/Blinkit)",
    "4. Clinical & Academic Expenses",
    "5. Momo's Gift & Celebration Fund",
    "6. Daily Cash Micro-Friction",
    "7. Dining Out & Leisure",
    "8. Wardrobe & Grooming",
    "9. Medical & Healthcare"
]

# --- LOAD OR INITIALIZE DATA ---
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["Date", "Amount", "Category", "Notes"])

def save_transaction(date, amount, category, notes):
    df = load_data()
    new_data = pd.DataFrame({"Date": [date], "Amount": [amount], "Category": [category], "Notes": [notes]})
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Wealth Command")
page = st.sidebar.radio("Navigation", ["Dashboard", "Log Transaction"])

# --- PAGE 1: DASHBOARD ---
if page == "Dashboard":
    st.title("🎯 Monthly Command Center")
    
    if df.empty:
        st.info("No transactions logged yet. Head over to 'Log Transaction' to get started.")
    else:
        total_spend = df["Amount"].sum()
        
        # KPI Cards
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Monthly Income", "₹80,000")
        col2.metric("Total Expenses Logged", f"₹{total_spend:,.2f}")
        col3.metric("Remaining Balance", f"₹{80000 - total_spend:,.2f}")
        
        st.markdown("---")
        
        # Visual Analytics
        st.subheader("Compartmentalization Breakdown")
        category_sum = df.groupby("Category")["Amount"].sum().reset_index()
        fig = px.pie(category_sum, values='Amount', names='Category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)
        
        # Ledger View
        st.subheader("Recent Ledger Entries")
        st.dataframe(df.tail(10).sort_values(by="Date", ascending=False), use_container_width=True)

# --- PAGE 2: LOG TRANSACTION ---
elif page == "Log Transaction":
    st.title("📝 Quick Logger")
    
    with st.form("transaction_form"):
        t_date = st.date_input("Date", date.today())
        t_amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
        t_cat = st.selectbox("Category", CATEGORIES)
        t_notes = st.text_input("Notes / Vendor Name")
        
        submitted = st.form_submit_button("Save Transaction")
        
        if submitted:
            save_transaction(t_date, t_amount, t_cat, t_notes)
            st.success(f"Successfully logged ₹{t_amount} under '{t_cat}'!")
