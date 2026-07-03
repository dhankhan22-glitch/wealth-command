import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, date
import calendar

# --- CONFIGURATION ---
st.set_page_config(page_title="Wealth Command", page_icon="🏦", layout="wide", initial_sidebar_state="collapsed")
DATA_FILE = "expense_database.csv"
CAT_FILE = "categories.csv"

# --- DEFAULT SETTINGS ---
HOUSEHOLD_USERS = ["Dhanesh", "Yamini"]
INCOME_HOUSEHOLD = 160000
INCOME_INDIVIDUAL = 80000

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

# --- DATA HANDLING ---
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
        df['Date'] = pd.to_datetime(df['Date']) # Ensure date format
        return df
    return pd.DataFrame(columns=["ID", "Date", "Amount", "Category", "Notes", "User"])

def save_data(df):
    # Convert dates back to string for clean CSV saving
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

# --- HEADER ---
st.markdown("<h1 style='text-align: center; color: #1F4E78;'>🏦 Wealth Command</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- TOP NAVIGATION TABS ---
tab_dash, tab_log, tab_ledger, tab_settings = st.tabs([
    "📊 Monthly Dashboard", 
    "📝 Log Expense", 
    "📂 Manage Ledger", 
    "⚙️ Settings & Categories"
])

# ==========================================
# TAB 1: DASHBOARD
# ==========================================
with tab_dash:
    if df.empty:
        st.info("No data yet! Go to 'Log Expense' to make your first entry.")
    else:
        # --- Filters ---
        col_f1, col_f2, col_f3 = st.columns(3)
        
        # Get unique months and years for filtering
        df['Month_Year'] = df['Date'].dt.strftime('%b %Y')
        month_options = df['Month_Year'].unique().tolist()
        
        # Default to current month if it exists in data, else latest
        current_my = datetime.now().strftime('%b %Y')
        default_my = current_my if current_my in month_options else month_options[0]

        with col_f1:
            selected_month = st.selectbox("📅 Select Month", month_options, index=month_options.index(default_my))
        with col_f2:
            view_options = ["Combined Household"] + HOUSEHOLD_USERS
            selected_view = st.selectbox("👤 Select View", view_options)
        
        # Apply Filters
        filtered_df = df[df['Month_Year'] == selected_month]
        if selected_view != "Combined Household":
            filtered_df = filtered_df[filtered_df["User"] == selected_view]
            budget_baseline = INCOME_INDIVIDUAL
        else:
            budget_baseline = INCOME_HOUSEHOLD
            
        total_spent = filtered_df["Amount"].sum()
        remaining = budget_baseline - total_spent
        percent_spent = min((total_spent / budget_baseline) * 100, 100)

        # --- High-Level KPIs ---
        st.markdown("<br>", unsafe_allow_html=True)
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Budget Ceiling", f"₹{budget_baseline:,}")
        kpi2.metric("Total Spent", f"₹{total_spent:,.2f}")
        kpi3.metric("Remaining Pool", f"₹{remaining:,.2f}", delta=f"{-total_spent:,.0f} spent", delta_color="inverse")

        # --- Progress Bar ---
        st.write(f"**Monthly Budget Consumption:** {percent_spent:.1f}%")
        st.progress(int(percent_spent))
        st.markdown("<br>", unsafe_allow_html=True)

        # --- Visual Analytics ---
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.write("### Spending by Compartment")
            if not filtered_df.empty:
                cat_sum = filtered_df.groupby("Category")["Amount"].sum().reset_index()
                fig_pie = px.pie(cat_sum, values='Amount', names='Category', hole=0.4)
                fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.write("No spending this month.")

        with chart_col2:
            st.write("### Daily Spending Trend")
            if not filtered_df.empty:
                daily_sum = filtered_df.groupby(filtered_df['Date'].dt.day)["Amount"].sum().reset_index()
                daily_sum.rename(columns={'Date': 'Day of Month'}, inplace=True)
                fig_bar = px.bar(daily_sum, x='Day of Month', y='Amount', text_auto='.2s')
                fig_bar.update_layout(margin=dict(t=0, b=0, l=0, r=0), xaxis_title="Day of the Month", yaxis_title="Amount Spent (₹)")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.write("No daily trend data available.")

# ==========================================
# TAB 2: LOG EXPENSE
# ==========================================
with tab_log:
    st.subheader("Add a New Transaction")
    with st.form("transaction_form", clear_on_submit=True): # Form clears automatically!
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            t_user = st.radio("Spender", HOUSEHOLD_USERS, horizontal=True)
            t_date = st.date_input("Date", date.today())
        with col_l2:
            t_amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            t_cat = st.selectbox("Category", category_list) if category_list else None
            
        t_notes = st.text_input("Notes / Vendor Name")
        submitted = st.form_submit_button("Save Transaction", type="primary", use_container_width=True)
        
        if submitted:
            if t_amount > 0 and t_cat:
                save_transaction(t_date, t_amount, t_cat, t_notes, t_user)
                st.success(f"✅ Successfully logged ₹{t_amount} for {t_user}!")
                st.rerun()
            else:
                st.error("Please enter an amount greater than 0.")

# ==========================================
# TAB 3: MANAGE LEDGER
# ==========================================
with tab_ledger:
    st.subheader("Audit & Delete Transactions")
    if df.empty:
        st.info("Ledger is empty.")
    else:
        # Display clean dataframe
        df_clean = df.copy()
        df_clean['Date'] = df_clean['Date'].dt.strftime('%Y-%m-%d') # Format for display
        df_sorted = df_clean.sort_values(by=["Date", "ID"], ascending=[False, False])
        
        st.dataframe(df_sorted.drop(columns=["Month_Year"], errors='ignore'), use_container_width=True)
        
        st.markdown("### Delete a Record")
        def format_tx(row):
            return f"{row.Date} | {row.User} | ₹{row.Amount} | {row.Category} | {row.Notes}"
            
        tx_options = {row.ID: format_tx(row) for row in df_sorted.itertuples()}
        selected_id = st.selectbox("Select Transaction to Delete", options=list(tx_options.keys()), format_func=lambda x: tx_options[x])
        
        if st.button("Delete Selected Transaction", type="primary"):
            delete_transaction(selected_id)
            st.success("Transaction permanently removed!")
            st.rerun()

# ==========================================
# TAB 4: SETTINGS
# ==========================================
with tab_settings:
    st.subheader("Customize Categories")
    st.info("Double-click a cell to rename. Scroll to the bottom to add. Select the row number on the left and press delete on your keyboard to remove.")
    
    edited_df = st.data_editor(df_cat, num_rows="dynamic", use_container_width=True)
    
    if st.button("Save Categories", type="primary"):
        edited_df = edited_df.dropna(subset=["Category"])
        edited_df = edited_df[edited_df["Category"].str.strip() != ""]
        save_categories(edited_df)
        st.success("Categories updated! The changes are now live.")
        st.rerun()
    
