import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="Wealth Command", layout="wide", initial_sidebar_state="expanded")
DATA_FILE = "expense_database.csv"
CAT_FILE = "categories.csv"

# --- DEFAULT SETTINGS ---
HOUSEHOLD_USERS = ["Dhanesh", "Yamini"]

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
    else:
        return pd.DataFrame({"Category": DEFAULT_CATEGORIES})

def save_categories(df_cat):
    df_cat.to_csv(CAT_FILE, index=False)

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Backward compatibility: if the User column doesn't exist yet, add it
        if "User" not in df.columns:
            df["User"] = "Dhanesh" # Default old transactions
        return df
    else:
        return pd.DataFrame(columns=["Date", "Amount", "Category", "Notes", "User"])

def save_transaction(date, amount, category, notes, user):
    df = load_data()
    new_data = pd.DataFrame({"Date": [date], "Amount": [amount], "Category": [category], "Notes": [notes], "User": [user]})
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

# --- APP NAVIGATION ---
st.sidebar.title("Wealth Command")
page = st.sidebar.radio("Navigation", ["Dashboard", "Log Transaction", "Manage Categories"])

# Load data into memory
df = load_data()
df_cat = load_categories()
category_list = df_cat["Category"].tolist()

# --- PAGE 1: DASHBOARD ---
if page == "Dashboard":
    st.title("🎯 Monthly Command Center")
    
    if df.empty:
        st.info("No transactions logged yet. Head over to 'Log Transaction' to get started.")
    else:
        # User Toggle
        st.write("### 👤 Select View")
        view_options = ["Combined Household"] + HOUSEHOLD_USERS
        selected_view = st.pills("Filter Dashboard", view_options, default="Combined Household")
        
        # Filter Data based on toggle
        if selected_view == "Combined Household":
            display_df = df
            income_budget = 160000  # Adjust combined income here if needed
        else:
            display_df = df[df["User"] == selected_view]
            income_budget = 80000   # Individual income baseline

        total_spend = display_df["Amount"].sum()
        
        # KPI Cards
        col1, col2, col3 = st.columns(3)
        col1.metric(f"Budget Baseline ({selected_view})", f"₹{income_budget:,}")
        col2.metric("Total Expenses Logged", f"₹{total_spend:,.2f}")
        col3.metric("Remaining Balance", f"₹{income_budget - total_spend:,.2f}")
        
        st.markdown("---")
        
        # Visual Analytics
        if not display_df.empty:
            st.subheader(f"Compartmentalization Breakdown: {selected_view}")
            category_sum = display_df.groupby("Category")["Amount"].sum().reset_index()
            fig = px.pie(category_sum, values='Amount', names='Category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No transactions found for {selected_view}.")
        
        # Ledger View
        st.subheader("Recent Ledger Entries")
        st.dataframe(display_df.tail(10).sort_values(by="Date", ascending=False), use_container_width=True)

# --- PAGE 2: LOG TRANSACTION ---
elif page == "Log Transaction":
    st.title("📝 Quick Logger")
    
    with st.form("transaction_form"):
        t_user = st.radio("Who made this transaction?", HOUSEHOLD_USERS, horizontal=True)
        t_date = st.date_input("Date", date.today())
        t_amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
        
        if not category_list:
            st.warning("You have no categories! Go to 'Manage Categories' to add some.")
            t_cat = None
        else:
            t_cat = st.selectbox("Category", category_list)
            
        t_notes = st.text_input("Notes / Vendor Name")
        
        submitted = st.form_submit_button("Save Transaction")
        
        if submitted and t_cat:
            save_transaction(t_date, t_amount, t_cat, t_notes, t_user)
            st.success(f"Successfully logged ₹{t_amount} for {t_user} under '{t_cat}'!")

# --- PAGE 3: MANAGE CATEGORIES ---
elif page == "Manage Categories":
    st.title("⚙️ Manage Categories")
    st.markdown("Double-click a cell to edit a name. Scroll to the bottom to add a new one. Select a row on the left to delete it.")
    
    edited_df = st.data_editor(df_cat, num_rows="dynamic", use_container_width=True)
    
    if st.button("Save Changes"):
        edited_df = edited_df.dropna(subset=["Category"])
        edited_df = edited_df[edited_df["Category"].str.strip() != ""]
        save_categories(edited_df)
        st.success("Categories updated successfully! The new list is now live in your Quick Logger.")
