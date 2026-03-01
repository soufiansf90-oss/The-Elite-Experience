import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import calendar

# --- 1. SETTINGS & ANIMATED UI ---
st.set_page_config(page_title="369 ELITE V30", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap');
    
    /* Animation Definition */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Apply Animation to all main containers */
    .stTabs [data-testid="stVerticalBlock"] > div {
        animation: fadeIn 0.5s ease-out forwards;
    }

    .stApp { background: #05070a; color: #e6edf3; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Orbitron'; color: #00ffcc; text-align: center; text-shadow: 0 0 20px rgba(0,255,204,0.4); padding: 20px; }
    
    /* Calendar Card Logic */
    .cal-card {
        border-radius: 8px; padding: 15px; text-align: center; min-height: 110px;
        transition: transform 0.3s ease, box-shadow 0.3s ease; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 10px;
    }
    .cal-card:hover { transform: scale(1.02); box-shadow: 0 5px 15px rgba(0,255,204,0.1); }
    .cal-win { background: linear-gradient(135deg, rgba(45, 101, 74, 0.9), rgba(20, 50, 40, 0.9)); border-top: 4px solid #34d399; }
    .cal-loss { background: linear-gradient(135deg, rgba(127, 45, 45, 0.9), rgba(60, 20, 20, 0.9)); border-top: 4px solid #ef4444; }
    .cal-be { background: linear-gradient(135deg, rgba(180, 130, 40, 0.9), rgba(80, 60, 20, 0.9)); border-top: 4px solid #fbbf24; }
    .cal-empty { background: #161b22; opacity: 0.3; }
    
    div[data-testid="stMetric"] { background: rgba(22, 27, 34, 0.7) !important; border: 1px solid #30363d !important; backdrop-filter: blur(5px); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
conn = sqlite3.connect('elite_final_v30.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS trades 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, pair TEXT, 
              outcome TEXT, pnl REAL, rr REAL, balance REAL, mindset TEXT, setup TEXT)''')
conn.commit()

# --- 3. DATA PREP ---
df = pd.read_sql_query("SELECT * FROM trades", conn)
if not df.empty:
    df['date_dt'] = pd.to_datetime(df['date'])
    df = df.sort_values('date_dt')
    df['cum_pnl'] = df['pnl'].cumsum()
    df['equity_curve'] = df['balance'].iloc[0] + df['cum_pnl']

# --- 4. HEADER ---
st.markdown('<h1 class="main-title">369 ELITE PRO V30</h1>', unsafe_allow_html=True)
tabs = st.tabs(["🚀 TERMINAL", "📅 CALENDAR LOG", "📊 MONTHLY %", "🧬 TRACKERS", "📜 JOURNAL"])

# --- TAB 1: TERMINAL ---
with tabs[0]:
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.form("entry_v30", clear_on_submit=True):
            bal_in = st.number_input("Account Amount ($)", value=1000.0, format="%.2f")
            d_in = st.date_input("Date", datetime.now())
            asset = st.text_input("Pair", "NAS100").upper()
            res = st.selectbox("Outcome", ["WIN", "LOSS", "BE"])
            p_val = st.number_input("P&L ($)", value=0.0, format="%.2f")
            r_val = st.number_input("RR Ratio", value=0.0, format="%.2f")
            setup = st.text_input("Setup Name").upper()
            mind = st.selectbox("Mindset", ["Focused", "Impulsive", "Revenge", "Bored"])
            if st.form_submit_button("LOCK TRADE"):
                c.execute("INSERT INTO trades (date, pair, outcome, pnl, rr, balance, mindset, setup) VALUES (?,?,?,?,?,?,?,?)",
                          (str(d_in), asset, res, p_val, r_val, bal_in, mind, setup))
                conn.commit()
                st.rerun()
    with col2:
        if not df.empty:
            st.metric("CURRENT EQUITY", f"${df['equity_curve'].iloc[-1]:.2f}", f"{df['pnl'].sum():.2f}")
            fig_eq = px.line(df, x='date_dt', y='equity_curve', title="📈 ACCOUNT EQUITY GROWTH")
            fig_eq.update_traces(line_color='#00ffcc', fill='tozeroy', fillcolor='rgba(0,255,204,0.1)', markers=True)
            fig_eq.update_layout(template="plotly_dark")
            st.plotly_chart(fig_eq, use_container_width=True)

# --- TAB 2: CALENDAR LOG ---
with tabs[1]:
    if not df.empty:
        today = datetime.now()
        cal = calendar.monthcalendar(today.year, today.month)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        cols_h = st.columns(7)
        for i, d_name in enumerate(days): cols_h[i].markdown(f"<p style='text-align:center; color:#8b949e'>{d_name}</p>", unsafe_allow_html=True)
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0: cols[i].markdown('<div class="cal-card cal-empty"></div>', unsafe_allow_html=True)
                else:
                    curr_d = datetime(today.year, today.month, day).date()
                    day_data = df[df['date_dt'].dt.date == curr_d]
                    pnl_s = day_data['pnl'].sum()
                    cnt = len(day_data)
                    style = "cal-win" if cnt > 0 and pnl_s > 0 else "cal-loss" if cnt > 0 and pnl_s < 0 else "cal-be" if cnt > 0 else "cal-empty"
                    pnl_txt = f"{'+' if pnl_s > 0 else ''}{pnl_s:.2f}" if cnt > 0 else ""
                    cols[i].markdown(f'<div class="cal-card {style}"><div class="cal-date">{day}</div><div class="cal-pnl">{pnl_txt}</div><div style="font-size:0.7rem">{cnt if cnt>0 else ""} Trades</div></div>', unsafe_allow_html=True)

# --- TAB 3: MONTHLY % ---
with tabs[2]:
    if not df.empty:
        df['month_year'] = df['date_dt'].dt.to_period('M').astype(str)
        m_stats = df.groupby('month_year').agg({'pnl': 'sum', 'balance': 'first'}).reset_index()
        m_stats['pct'] = (m_stats['pnl'] / m_stats['balance']) * 100
        fig_m = px.bar(m_stats, x='month_year', y='pct', title="Monthly Gain/Loss %", color='pct', color_continuous_scale=['#ef4444', '#34d399'])
        st.plotly_chart(fig_m, use_container_width=True)

# --- TAB 4: TRACKERS ---
with tabs[3]:
    if not df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### ⚖️ Risk Tracker")
            st.plotly_chart(px.scatter(df, x='rr', y='pnl', color='outcome', template="plotly_dark"), use_container_width=True)
        with col_b:
            st.markdown("### 🧠 Mindset Tracker")
            st.plotly_chart(px.bar(df.groupby('mindset')['pnl'].sum().reset_index(), x='mindset', y='pnl', template="plotly_dark"), use_container_width=True)
        st.write("---")
        wr = (len(df[df['outcome']=='WIN']) / len(df)) * 100
        st.metric("🏆 Consistency Win Rate", f"{wr:.1f}%")
        st.progress(wr/100)

# --- TAB 5: JOURNAL ---
with tabs[4]:
    if not df.empty:
        st.dataframe(df.sort_values('date_dt', ascending=False).style.format({"pnl": "{:.2f}", "rr": "{:.2f}"}), use_container_width=True)
