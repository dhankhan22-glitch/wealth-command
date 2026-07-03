import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
from datetime import datetime, date

# --- CONFIGURATION ---
# "centered" layout is much better for mobile phones than "wide"
st.set_page_config(page_title="Wealth Command", page_icon="🏦", layout="centered", initial_sidebar_state="collapsed")
DATA_FILE = "expense_database.csv"
CAT_FILE = "categories.csv"
INCOMES_FILE = "incomes.json"

# --- DEFAULT SETTINGS ---
DEFAULT_CATEGORIES = [
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

DEFAULT_INCOMES = {"Dhanesh": 80000, "Yamini": 80000}

# --- DATA HANDLING ---
def load_incomes():
    if os.path.exists(INCOMES_FILE):
        with open(INCOMES_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_INCOMES

def save_incomes(incomes_dict):
    with open(INCOMES_FILE, "w") as f:
        json.dump(incomes_dict, f)

def load_categories():
    if os.path.exists(CAT_FILE):
        return pd.read_csv(CAT_FILE)
    return pd.DataFrame({"Category": DEFAULT_CATEGORIES})

def save_categories(df_cat):
    df_cat.to_csv(CAT_FILE, index=False)

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if "User" not in df.columns: df["User"] = "Dhanesh"
        if "ID" not in df.columns: df.insert(0, "ID", range(1, len(df) + 1))
        df['Date'] = pd.to_datetime(df['Date']) 
        return df
    return pd.DataFrame(columns=["ID", "Date", "Amount", "Category", "Notes", "User"])

def save_data(df):
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    df.to_csv(DATA_FILE, index=False)

def save_transaction(t_date, amount, category, notes, user):
    df = load_data()
    new_id = 1 if df.empty else df["ID"].max() + 1
    new_data = pd.DataFrame({
        "ID": [new_id], "Date": [pd.to_datetime(t_date)], 
        "Amount": [amount], "Category": [category], 
        "Notes": [notes], "User": [user]
    })
    df = pd.concat([df, new_data], ignore_index=True)
    save_data(df)

def delete_transaction(tx_id):
    df = load_data()
    df = df[df["ID"] != tx_id]
    save_data(df)

# --- LOAD CORE DATA ---
df = load_data()
df_cat = load_categories()
category_list = df_cat["Category"].tolist()
incomes = load_incomes()

# --- APP HEADER & GLOBAL PROFILE SWITCHER ---
st.markdown("<h2 style='text-align: center; color: #1F4E78;'>🏦 Wealth Command</h2>", unsafe_allow_html=True)

# This radio button dictates what the ENTIRE app sees
active_profile = st.radio(
    "👤 Select Active Profile", 
    ["Dhanesh", "Yamini", "Household (Combined)"], 
    horizontal=True
)
st.markdown("---")

# --- FILTER GLOBAL DATA BASED ON PROFILE ---
if active_profile == "Household (Combined)":
    profile_df = df.copy()
    current_budget = sum(incomes.values())
else:
    profile_df = df[df["User"] == active_profile].copy()
    current_budget = incomes.get(active_profile, 80000)

# --- TOP NAVIGATION TABS ---
tab_dash, tab_log, tab_ledger, tab_settings = st.tabs([
    "📊 Dash", 
    "📝 Log", 
    "📂 Ledger", 
    "⚙️ Settings"
])

# ==========================================
# TAB 1: DASHBOARD
# ==========================================
with tab_dash:
    if profile_df.empty:
        st.info(f"No transactions found for {active_profile}.")
    else:
        profile_df['Month_Year'] = profile_df['Date'].dt.strftime('%b %Y')
        month_options = profile_df['Month_Year'].unique().tolist()
        
        current_my = datetime.now().strftime('%b %Y')
        default_my = current_my if current_my in month_options else month_options[0]

        selected_month = st.selectbox("📅 Filter by Month", month_options, index=month_options.index(default_my))
        
        month_df = profile_df[profile_df['Month_Year'] == selected_month]
        total_spent = month_df["Amount"].sum()
        remaining = current_budget - total_spent
        percent_spent = min((total_spent / current_budget) * 100, 100) if current_budget > 0 else 0

        # KPIs (Mobile optimized layout)
        kpi1, kpi2 = st.columns(2)
        kpi1.metric("Budget Ceiling", f"₹{current_budget:,}")
        kpi2.metric("Total Spent", f"₹{total_spent:,.2f}")
        
        st.metric("Remaining Pool", f"₹{remaining:,.2f}", delta=f"{-total_spent:,.0f} spent", delta_color="inverse")

        st.write(f"**Budget Consumed:** {percent_spent:.1f}%")
        st.progress(int(percent_spent))

        st.markdown("<br>", unsafe_allow_html=True)
        st.write(f"### 📍 Where {active_profile}'s money went")
        if not month_df.empty:
            cat_sum = month_df.groupby("Category")["Amount"].sum().reset_index()
            fig_pie = px.pie(cat_sum, values='Amount', names='Category', hole=0.4)
            fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5))
            st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# TAB 2: LOG EXPENSE (Mobile Friendly Layout)
# ==========================================
with tab_log:
    st.subheader(f"Log Expense for {active_profile}")
    
    if active_profile == "Household (Combined)":
        st.warning("⚠️ You are in Household view. Please select 'Dhanesh' or 'Yamini' at the top to log a personal expense.")
    else:
        with st.form("transaction_form", clear_on_submit=True):
            # Thumb-friendly vertical stacking (no columns)
            t_date = st.date_input("Date", date.today())
            t_amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            t_cat = st.selectbox("Category", category_list) if category_list else None
            t_notes = st.text_input("Notes / Vendor Name")
            
            # Big submit button
            submitted = st.form_submit_button("Save Transaction", type="primary", use_container_width=True)
            
            if submitted:
                if t_amount > 0 and t_cat:
                    save_transaction(t_date, t_amount, t_cat, t_notes, active_profile) # Auto-assigns to the active profile!
                    st.success(f"✅ Saved ₹{t_amount} to {active_profile}'s ledger!")
                    st.rerun()
                else:
                    st.error("Please enter an amount greater than 0.")

# ==========================================
# TAB 3: MANAGE LEDGER
# ==========================================
with tab_ledger:
    st.subheader(f"{active_profile}'s Ledger")
    if profile_df.empty:
        st.info("Ledger is empty.")
    else:
        # Show only relevant records
        df_clean = profile_df.copy()
        df_clean['Date'] = df_clean['Date'].dt.strftime('%Y-%m-%d')
        df_sorted = df_clean.sort_values(by=["Date", "ID"], ascending=[False, False])
        
        st.dataframe(df_sorted.drop(columns=["Month_Year"], errors='ignore'), use_container_width=True)
        
        st.markdown("### Delete a Record")
        def format_tx(row):
            # Shortened format for mobile screens
            return f"{row.Date} | ₹{row.Amount} | {row.Category[:15]}..."
            
        tx_options = {row.ID: format_tx(row) for row in df_sorted.itertuples()}
        selected_id = st.selectbox("Select Transaction to Delete", options=list(tx_options.keys()), format_func=lambda x: tx_options[x])
        
        if st.button("Delete Selected Transaction", type="primary", use_container_width=True):
            delete_transaction(selected_id)
            st.success("Transaction permanently removed!")
            st.rerun()

# ==========================================
# TAB 4: SETTINGS
# ==========================================
with tab_settings:
    st.subheader("💰 Monthly Income Baselines")
    
    new_dhanesh = st.number_input("Dhanesh (₹)", min_value=0, step=1000, value=incomes.get("Dhanesh", 80000))
    new_yamini = st.number_input("Yamini (₹)", min_value=0, step=1000, value=incomes.get("Yamini", 80000))
        
    if st.button("Save Incomes", type="primary", use_container_width=True):
        save_incomes({"Dhanesh": new_dhanesh, "Yamini": new_yamini})
        st.success("Incomes updated!")
        st.rerun()

    st.markdown("---")
    st.subheader("⚙️ Categories")
    edited_df = st.data_editor(df_cat, num_rows="dynamic", use_container_width=True)
    
    if st.button("Save Categories", type="primary", use_container_width=True):
        edited_df = edited_df.dropna(subset=["Category"])
        edited_df = edited_df[edited_df["Category"].str.strip() != ""]
        save_categories(edited_df)
        st.success("Categories updated!")
        st.rerun()
