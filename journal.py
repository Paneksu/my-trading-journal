import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import json
from streamlit_gsheets import GSheetsConnection

# --- KONFIGURACJA POCZĄTKOWA ---
st.set_page_config(page_title="NQPaneksu Journal", layout="wide")

# --- ZARZĄDZANIE MOTYWEM I STANEM ---
if 'theme' not in st.session_state:
    st.session_state.theme = "Dark"

if 'menu_nav' not in st.session_state:
    st.session_state.menu_nav = "📊 Dashboard"

if st.session_state.get('navigate_to_history'):
    st.session_state.menu_nav = "📜 Trades History"
    st.session_state.navigate_to_history = False

if 'bt_nav_section' not in st.session_state:
    st.session_state.bt_nav_section = "Dashboard"

# --- DEFINICJA KOLORÓW DLA MOTYWÓW (ROZJAŚNIONE) ---
themes = {
    "Dark": {
        "bg_app": "#16161e",
        "bg_sidebar": "#121218",
        "bg_card": "#1d1d27",
        "bg_metric": "linear-gradient(135deg, #1d1d27 0%, #251d30 100%)",
        "border": "#3a3a4a",
        "text_primary": "#eaeaea",
        "text_secondary": "#b4b4b4",
        "accent": "#ff007f",
        "popover_bg": "#1d1d27",
        "card_shadow": "0 2px 4px rgba(0,0,0,0.3)",
        "input_bg": "#1d1d27"
    },
    "Light": {
        "bg_app": "#f4f7fa",
        "bg_sidebar": "#ffffff",
        "bg_card": "#ffffff",
        "bg_metric": "linear-gradient(135deg, #ffffff 0%, #eadaff 100%)",
        "border": "#d2dbe3",
        "text_primary": "#202538",
        "text_secondary": "#5a627a",
        "accent": "#6c5ce7",
        "popover_bg": "#ffffff",
        "card_shadow": "0 4px 6px rgba(0,0,0,0.08)",
        "input_bg": "#ffffff"
    }
}

current_theme = themes[st.session_state.theme]

# --- UI: PRZYCISK ZMIANY MOTYWU ---
top_col1, top_col2 = st.columns([20, 1])
with top_col2:
    btn_icon = "☀️" if st.session_state.theme == "Dark" else "🌙"
    if st.button(btn_icon, key="theme_toggle"):
        st.session_state.theme = "Light" if st.session_state.theme == "Dark" else "Dark"
        st.rerun()

# --- INJECT CSS ---
st.markdown(f"""
    <style>
    /* UKRYCIE DOMYŚLNEGO NAGŁÓWKA STREAMLIT */
    [data-testid="stHeader"] {{ display: none !important; }}

    .block-container {{ padding-top: 1.5rem; padding-bottom: 1rem; }}

    .stApp {{ background-color: {current_theme['bg_app']}; color: {current_theme['text_primary']}; }}
    [data-testid="stSidebar"] {{ background-color: {current_theme['bg_sidebar']}; border-right: 1px solid {current_theme['border']}; }}

    .stMetric {{ background: {current_theme['bg_metric']}; padding: 10px 15px; border-radius: 12px; border: 1px solid {current_theme['border']}; color: {current_theme['text_primary']}; box-shadow: {current_theme['card_shadow']}; }}
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{ color: {current_theme['text_primary']} !important; }}

    h1, h2, h3, h4, p, span, div, label {{ color: {current_theme['text_primary']}; }}
    .stMarkdown p {{ color: {current_theme['text_primary']} !important; }}
    div[data-testid="stButton"] button {{ border: 1px solid {current_theme['border']}; background-color: {current_theme['bg_card']}; color: {current_theme['text_primary']}; font-weight: bold; box-shadow: {current_theme['card_shadow']}; }}
    div[data-testid="column"] div[data-testid="stButton"] button {{ border-radius: 50%; width: 45px; height: 45px; }}

    [data-testid="stImage"] {{ overflow: visible !important; position: relative !important; }}
    button[title="View fullscreen"] {{ display: flex !important; visibility: visible !important; opacity: 1 !important; background-color: rgba(0, 0, 0, 0.6) !important; border: 1px solid rgba(255, 255, 255, 0.3) !important; width: 2.5rem !important; height: 2.5rem !important; right: 0.5rem !important; top: 0.5rem !important; z-index: 999999 !important; cursor: pointer !important; border-radius: 8px !important; align-items: center !important; justify-content: center !important; transition: background-color 0.2s !important; }}
    button[title="View fullscreen"]:hover {{ background-color: rgba(0, 0, 0, 0.9) !important; border-color: {current_theme['accent']} !important; transform: scale(1.05); }}
    button[title="View fullscreen"] svg {{ fill: white !important; width: 1.2rem !important; height: 1.2rem !important; }}

    .day-card {{ height: 95px; width: 100%; border-radius: 12px; padding: 10px; display: flex; flex-direction: column; justify-content: space-between; border: 1px solid {current_theme['border']}; transition: transform 0.2s, box-shadow 0.2s; box-sizing: border-box; background-color: {current_theme['bg_card']}; box-shadow: {current_theme['card_shadow']}; }}
    .weekly-summary-title {{ font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px; opacity: 0.7; }}
    .weekly-summary-value {{ font-size: 1.1em; font-weight: bold; line-height: 1.2; }}

    div[data-testid="stPopover"] > button {{ height: 95px !important; width: 100% !important; background-color: transparent !important; border: none !important; border-radius: 12px !important; color: transparent !important; margin-top: -95px !important; position: relative; z-index: 5; }}
    div[data-testid="stPopover"] > button:hover {{ background-color: rgba(128, 128, 128, 0.05) !important; border: 2px solid {current_theme['accent']} !important; }}
    div[data-testid="column"] {{ padding: 2px !important; }}

    div[data-testid="stPopoverBody"] {{ 
        border: 1px solid {current_theme['border']} !important; 
        background-color: {current_theme['popover_bg']} !important; 
        color: {current_theme['text_primary']} !important; 
        min-width: 1200px !important; 
        max-width: 95vw !important;
    }}

    .highlight-box {{ 
        background-color: {'#1e1e26' if st.session_state.theme == 'Dark' else '#f8faff'}; 
        padding: 10px; 
        border-radius: 5px; 
        border-left: 5px solid #00ff7f; 
        margin-bottom: 10px; 
        color: {current_theme['text_primary']};
        border: 1px solid {current_theme['border']};
        white-space: pre-wrap;
    }}

    .streamlit-expanderHeader {{ background-color: {current_theme['bg_card']}; color: {current_theme['text_primary']}; border-radius: 5px; border: 1px solid {current_theme['border']}; }}
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"], input, textarea, select {{ background-color: {current_theme['input_bg']} !important; color: {current_theme['text_primary']} !important; border-color: {current_theme['border']} !important; }}
    div[data-baseweb="select"] svg, div[data-baseweb="input"] svg {{ fill: {current_theme['text_secondary']} !important; }}
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)


def load_data_from_gsheets():
    try:
        df = conn.read(ttl=0)
        df = df.fillna("")
        if df.empty: return []
        data = df.to_dict(orient="records")
        processed_data = []
        for row in data:
            if isinstance(row.get('htf_links'), str) and row['htf_links']:
                row['htf_links'] = row['htf_links'].split('|||')
            else:
                row['htf_links'] = []
            if isinstance(row.get('ltf_links'), str) and row['ltf_links']:
                row['ltf_links'] = row['ltf_links'].split('|||')
            else:
                row['ltf_links'] = []
            if isinstance(row.get('checklist'), str) and row['checklist']:
                try:
                    row['checklist'] = json.loads(row['checklist'])
                except:
                    row['checklist'] = [False] * 6
            else:
                row['checklist'] = [False] * 6

            try:
                pnl_str = str(row.get('pnl', 0)).replace(',', '.')
                row['pnl'] = float(pnl_str) if pnl_str else 0.0
            except:
                row['pnl'] = 0.0

            # Pobieranie i rzutowanie nowej zmiennej RR
            try:
                rr_str = str(row.get('rr', 0)).replace(',', '.')
                row['rr'] = float(rr_str) if rr_str else 0.0
            except:
                row['rr'] = 0.0

            # Wsteczna kompatybilność: domyślnie 'Funded' dla starych danych
            row['account_type'] = row.get('account_type') if row.get('account_type') else 'Funded'

            # Nowe pola dla Backtestingu (i ujednoliconego Journala)
            row['is_backtest'] = str(row.get('is_backtest', 'False')).lower() == 'true'
            row['notes'] = row.get('notes', "")
            row['model_mistakes'] = row.get('model_mistakes', "")
            row['mental_mistakes'] = row.get('mental_mistakes', "")

            if isinstance(row.get('confluences'), str) and row.get('confluences'):
                try:
                    row['confluences'] = json.loads(row['confluences'])
                except:
                    row['confluences'] = []
            else:
                if not isinstance(row.get('confluences'), list):
                    row['confluences'] = []

            if row.get('date'): row['date'] = str(row['date'])
            processed_data.append(row)
        return processed_data
    except Exception as e:
        return []


def save_all_data(data):
    # Dodano kolumnę 'rr'
    columns = ['date', 'asset', 'direction', 'time', 'trade_type', 'account_type', 'outcome', 'pnl', 'rr',
               'general_notes', 'mood', 'interfered', 'interfered_how', 'htf_desc', 'htf_keypoints',
               'htf_links', 'ltf_desc', 'ltf_keypoints', 'ltf_links', 'checklist',
               'is_backtest', 'notes', 'model_mistakes', 'mental_mistakes', 'confluences']
    if not data:
        df = pd.DataFrame(columns=columns)
        conn.update(data=df)
        return
    data_to_save = []
    for row in data:
        new_row = row.copy()
        new_row['htf_links'] = "|||".join(row.get('htf_links', []))
        new_row['ltf_links'] = "|||".join(row.get('ltf_links', []))
        new_row['checklist'] = json.dumps(row.get('checklist', [False] * 6))
        new_row['confluences'] = json.dumps(row.get('confluences', []))

        # Zabezpieczenie brakujących kolumn
        for col in columns:
            if col not in new_row:
                new_row[col] = "" if col not in ['is_backtest', 'confluences', 'checklist', 'htf_links',
                                                 'ltf_links'] else False if col == 'is_backtest' else []

        data_to_save.append(new_row)

    df = pd.DataFrame(data_to_save)
    df = df[columns]
    conn.update(data=df)


if 'all_trades' not in st.session_state:
    with st.spinner("Ładowanie bazy danych..."):
        st.session_state.all_trades = load_data_from_gsheets()

all_trades = st.session_state.all_trades


# --- FUNKCJE CALLBACK ---
def go_to_edit_mode(index):
    st.session_state.editing_index = index
    if st.session_state.all_trades[index].get('is_backtest', False):
        st.session_state.menu_nav = "⏪ Backtesting"
        st.session_state.bt_nav_section = "Trade Entry"
    else:
        st.session_state.menu_nav = "📝 Daily Journal"


def go_to_history_for_day(target_date):
    if isinstance(target_date, str):
        try:
            target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        except:
            target_date_obj = date.today()
    else:
        target_date_obj = target_date
    st.session_state.history_filter_date = target_date_obj
    st.session_state.menu_nav = "📜 Trades History"


def back_to_dashboard():
    if 'history_filter_date' in st.session_state:
        del st.session_state.history_filter_date
    st.session_state.menu_nav = "📊 Dashboard"


# --- SIDEBAR MENU ---
with st.sidebar:
    st.title("📘 NQPaneksu Journal")
    menu = st.radio("MAIN MENU", ["📊 Dashboard", "📝 Daily Journal", "📜 Trades History", "⏪ Backtesting"],
                    key="menu_nav")
    st.divider()
    if st.button("🗑️ Delete Last Entry"):
        if st.session_state.all_trades:
            st.session_state.all_trades.pop()
            save_all_data(st.session_state.all_trades)
            st.rerun()

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    with top_col1:
        st.title("Dashboard Performance")

    filter_col1, filter_col2 = st.columns([1, 4])
    account_filter = filter_col1.radio("📂 Filter by Account:", ["All", "Funded", "Evaluation"], horizontal=True)

    if all_trades:
        # Filtrowanie tablicy omijające Backtesty
        base_trades = [t for t in all_trades if not t.get('is_backtest', False)]

        if account_filter == "All":
            filtered_trades = base_trades
        else:
            filtered_trades = [t for t in base_trades if t.get('account_type', 'Funded') == account_filter]

        df = pd.DataFrame(filtered_trades)

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])

            total_pnl = df['pnl'].sum()
            total_valid = len(df[df['direction'] != 'No Trade'])

            wins_df = df[df['pnl'] > 0]
            losses_df = df[df['pnl'] < 0]

            wins_count = len(wins_df)
            losses_count = len(losses_df)

            gross_profit = wins_df['pnl'].sum()
            gross_loss = abs(losses_df['pnl'].sum())

            wr = (wins_count / total_valid * 100) if total_valid > 0 else 0
            avg_win = (gross_profit / wins_count) if wins_count > 0 else 0
            avg_loss = (gross_loss / losses_count) if losses_count > 0 else 0

            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (
                float('inf') if gross_profit > 0 else 0.0)

            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("Net P&L", f"{total_pnl:+.1f} $")
            c2.metric("Win Rate", f"{wr:.1f}%")
            c3.metric("Avg Win", f"{avg_win:+.1f} $")
            c4.metric("Avg Loss", f"{-avg_loss:+.1f} $")

            pf_display = "∞" if profit_factor == float('inf') else f"{profit_factor:.2f}"
            c5.metric("Profit Factor", pf_display)
            c6.metric("Trades", total_valid)
        else:
            st.info(f"Brak danych dla wybranego filtru: {account_filter}")

        st.divider()
        st.subheader("Trading Calendar")
        col_y, col_m, _ = st.columns([1, 1, 4])
        view_year = col_y.selectbox("Year", range(2024, 2030), index=range(2024, 2030).index(datetime.now().year),
                                    label_visibility="collapsed")
        view_month = col_m.selectbox("Month", range(1, 13), index=datetime.now().month - 1,
                                     label_visibility="collapsed")

        cal = calendar.monthcalendar(view_year, view_month)

        cols = st.columns(7)
        days_header = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, d in enumerate(days_header):
            cols[i].markdown(f"<center><b style='color:{current_theme['text_secondary']}'>{d}</b></center>",
                             unsafe_allow_html=True)

        for week in cal:
            ref_day = next((d for d in week if d != 0), None)
            weekly_pnl = 0.0
            weekly_rr = 0.0
            week_end_date = None
            if ref_day:
                ref_date = date(view_year, view_month, ref_day)
                day_idx = week.index(ref_day)
                week_start_date = ref_date - timedelta(days=day_idx)
                week_end_date = week_start_date + timedelta(days=6)
                week_trades = [t for t in filtered_trades if
                               week_start_date <= datetime.strptime(t['date'], '%Y-%m-%d').date() <= week_end_date]
                weekly_pnl = sum(t['pnl'] for t in week_trades)
                weekly_rr = sum(t.get('rr', 0.0) for t in week_trades)

            cols = st.columns(7)
            for i, day in enumerate(week):
                if i == 6:  # Niedziela
                    bg_c, bor_c, txt_c, pnl_c = current_theme['bg_card'], current_theme['border'], current_theme[
                        'text_primary'], current_theme['text_secondary']
                    if weekly_pnl > 0:
                        bg_c, bor_c, pnl_c = (
                            "rgba(0, 255, 127, 0.15)" if st.session_state.theme == "Dark" else "#dcfce7"), (
                            "#00ff7f" if st.session_state.theme == "Dark" else "#22c55e"), (
                            "#00ff7f" if st.session_state.theme == "Dark" else "#15803d")
                    elif weekly_pnl < 0:
                        bg_c, bor_c, pnl_c = (
                            "rgba(255, 69, 58, 0.15)" if st.session_state.theme == "Dark" else "#fee2e2"), (
                            "#ff453a" if st.session_state.theme == "Dark" else "#ef4444"), (
                            "#ff453a" if st.session_state.theme == "Dark" else "#b91c1c")

                    card_html = f"""<div class="day-card" style="background-color: {bg_c}; border-color: {bor_c}; justify-content: center; align-items: center;"><div class="weekly-summary-title" style="color: {txt_c};">Weekly PnL</div><div class="weekly-summary-value" style="color: {pnl_c}; text-align: center;">{weekly_pnl:+.1f} $<br><span style="font-size: 0.85em; color: {txt_c}; font-weight: normal;">RR: {weekly_rr:.2f}</span></div></div>"""
                    cols[i].markdown(card_html, unsafe_allow_html=True)

                    curr_date_sunday = date(view_year, view_month, day) if day != 0 else (
                        week_end_date if ref_day else None)
                    with cols[i].popover(label=" ", use_container_width=True):
                        if curr_date_sunday:
                            st.header(f"📅 {curr_date_sunday.strftime('%A, %d %B %Y')}")
                            st.button(f"🔎 Go to History ({curr_date_sunday})", key=f"gth_sun_{i}_{day}_{view_month}",
                                      use_container_width=True, on_click=go_to_history_for_day,
                                      args=(curr_date_sunday,))
                            st.divider()
                            sunday_trades = [t for t in filtered_trades if t['date'] == str(curr_date_sunday)]
                            if sunday_trades:
                                for t in sunday_trades:
                                    with st.container():
                                        h1, h2 = st.columns([3, 1])
                                        h1.markdown(f"### {t['asset']} ({t['direction']})")
                                        pnl_c = "green" if t['pnl'] > 0 else ("red" if t['pnl'] < 0 else "gray")
                                        h2.markdown(f"<h3 style='color:{pnl_c}'>{t['pnl']:+.1f} $</h3>",
                                                    unsafe_allow_html=True)
                                        st.caption(
                                            f"🕒 {t['time']} | 🔄 {t['trade_type']} | 🎯 {t['outcome']} | 💼 {t.get('account_type', 'Funded')} | RR: {t.get('rr', 0.0)}")
                                        if t.get('notes'): st.info(f"📝 {t['notes']}")
                                        st.markdown("---")
                                        c_htf, c_ltf = st.columns(2)
                                        with c_htf:
                                            st.markdown("#### 🏛️ HTF Links")
                                            for l in t.get('htf_links', []):
                                                if "http" in l: st.image(l.strip(), use_container_width=True)
                                        with c_ltf:
                                            st.markdown("#### ⚡ LTF Links")
                                            for l in t.get('ltf_links', []):
                                                if "http" in l: st.image(l.strip(), use_container_width=True)
                                        st.divider()
                            else:
                                st.write("Brak tradów.")
                                st.info(f"**Weekly Total:** {weekly_pnl:+.1f} $ | RR: {weekly_rr:.2f}")
                else:
                    if day == 0:
                        cols[i].write("")
                    else:
                        curr_date = date(view_year, view_month, day)
                        day_trades = [t for t in filtered_trades if t['date'] == str(curr_date)]
                        day_pnl = sum([t['pnl'] for t in day_trades])
                        day_rr = sum([t.get('rr', 0.0) for t in day_trades])
                        has_no_trade = any(t['direction'] == 'No Trade' for t in day_trades)
                        valid_trades_count = sum(1 for t in day_trades if t['direction'] != 'No Trade')

                        bg_c, bor_c, txt_c, pnl_c = current_theme['bg_card'], current_theme['border'], current_theme[
                            'text_primary'], current_theme['text_secondary']
                        pnl_disp, badge = "", ""

                        if day_trades:
                            if valid_trades_count > 0:
                                b_bg = "#2d2d3a" if st.session_state.theme == "Dark" else "#e0e7ff"
                                b_txt = "#ccc" if st.session_state.theme == "Dark" else "#4338ca"
                                badge = f"<span style='font-size:0.8em;color:{b_txt};background:{b_bg};padding:2px 6px;border-radius:4px;'>{valid_trades_count}x</span>"

                            if has_no_trade and day_pnl == 0:
                                bg_c, bor_c, pnl_c, pnl_disp = (
                                    "rgba(142, 142, 147, 0.15)" if st.session_state.theme == "Dark" else "#f3f4f6"), "#8e8e93", "#8e8e93", "⚪ No Trade"
                            elif day_pnl > 0:
                                bg_c, bor_c, pnl_c, pnl_disp = (
                                    "rgba(0, 255, 127, 0.15)" if st.session_state.theme == "Dark" else "#dcfce7"), (
                                    "#00ff7f" if st.session_state.theme == "Dark" else "#22c55e"), (
                                    "#00ff7f" if st.session_state.theme == "Dark" else "#15803d"), f"🟢 +{day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"
                            elif day_pnl < 0:
                                bg_c, bor_c, pnl_c, pnl_disp = (
                                    "rgba(255, 69, 58, 0.15)" if st.session_state.theme == "Dark" else "#fee2e2"), (
                                    "#ff453a" if st.session_state.theme == "Dark" else "#ef4444"), (
                                    "#ff453a" if st.session_state.theme == "Dark" else "#b91c1c"), f"🔴 {day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"
                            else:
                                bg_c, bor_c, pnl_c, pnl_disp = "rgba(142, 142, 147, 0.15)", "#8e8e93", "#8e8e93", f"⚪ {day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"

                        card_html = f"""<div class="day-card" style="background-color: {bg_c}; border-color: {bor_c};"><div style="display:flex;justify-content:space-between;align-items:flex-start;"><div style="font-weight:bold;font-size:1.1em;color:{txt_c};">{day}</div><div>{badge}</div></div><div style="font-weight:bold;font-size:1em;color:{pnl_c};text-align:center;line-height:1.2;">{pnl_disp}</div></div>"""
                        cols[i].markdown(card_html, unsafe_allow_html=True)

                        with cols[i].popover(label=" ", use_container_width=True):
                            if day_trades:
                                st.header(f"📅 {curr_date.strftime('%A, %d %B %Y')}")
                                st.button(f"🔎 Go to History ({curr_date})", key=f"gth_{curr_date}",
                                          use_container_width=True, on_click=go_to_history_for_day, args=(curr_date,))
                                st.markdown(
                                    f"**Daily Net PnL:** :{'green' if day_pnl > 0 else 'red'}[{day_pnl:+.1f} $] | **RR:** {day_rr:.2f}")
                                st.divider()
                                for t in day_trades:
                                    with st.container():
                                        h1, h2 = st.columns([3, 1])
                                        h1.markdown(f"### {t['asset']} ({t['direction']})")
                                        pnl_c = "green" if t['pnl'] > 0 else ("red" if t['pnl'] < 0 else "gray")
                                        h2.markdown(f"<h3 style='color:{pnl_c}'>{t['pnl']:+.1f} $</h3>",
                                                    unsafe_allow_html=True)
                                        st.caption(
                                            f"🕒 {t['time']} | 🔄 {t['trade_type']} | 🎯 {t['outcome']} | 💼 {t.get('account_type', 'Funded')} | RR: {t.get('rr', 0.0)}")
                                        if t.get('notes'): st.info(f"📝 {t['notes']}")
                                        st.markdown("---")
                                        c_htf, c_ltf = st.columns(2)
                                        with c_htf:
                                            st.markdown("#### 🏛️ HTF Links")
                                            for l in t.get('htf_links', []):
                                                if "http" in l: st.image(l.strip(), use_container_width=True)
                                        with c_ltf:
                                            st.markdown("#### ⚡ LTF Links")
                                            for l in t.get('ltf_links', []):
                                                if "http" in l: st.image(l.strip(), use_container_width=True)
                                        st.divider()
                            else:
                                st.write("Brak wpisów.")
    else:
        st.info("Brak danych.")

# --- DAILY JOURNAL ---
elif menu == "📝 Daily Journal":
    with top_col1:
        st.title("Daily Trade Entry")

    if 'editing_index' not in st.session_state: st.session_state.editing_index = None
    curr = all_trades[st.session_state.editing_index] if st.session_state.editing_index is not None and not all_trades[
        st.session_state.editing_index].get('is_backtest') else None

    # Ładowanie confluences do tymczasowej listy przy wchodzeniu w tryb edycji
    if 'dj_current_edit_idx' not in st.session_state or st.session_state.dj_current_edit_idx != st.session_state.editing_index:
        st.session_state.dj_current_edit_idx = st.session_state.editing_index
        st.session_state.dj_temp_conf = curr.get('confluences', []).copy() if curr else []

    st.subheader("📌 Trade Details")
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    asset = r1c1.selectbox("Asset", ["NQ", "MNQ", "ES", "MES", "XAUUSD"],
                           index=0 if not curr else ["NQ", "MNQ", "ES", "MES", "XAUUSD"].index(curr['asset']),
                           key="dj_asset")
    direction = r1c2.selectbox("Direction", ["Long", "Short", "Both", "No Trade"],
                               index=0 if not curr else ["Long", "Short", "Both", "No Trade"].index(
                                   curr.get('direction', 'Long')), key="dj_dir")
    tt_l = ["Internal -> External", "External -> Internal", "Internal -> Internal", "External -> External", "-"]
    trade_type = r1c3.selectbox("Type", tt_l, index=0 if not curr or curr.get('trade_type') not in tt_l else tt_l.index(
        curr['trade_type']), key="dj_tt")
    acc_type_idx = 0 if not curr else ["Funded", "Evaluation"].index(curr.get('account_type', 'Funded'))
    account_type = r1c4.selectbox("Account Type", ["Funded", "Evaluation"], index=acc_type_idx, key="dj_acc")

    r2c1, r2c2, r2c3, r2c4, r2c5 = st.columns(5)
    trade_date = r2c1.date_input("Date",
                                 date.today() if not curr else datetime.strptime(curr['date'], '%Y-%m-%d').date(),
                                 key="dj_date")
    exec_time = r2c2.text_input("Time", value="" if not curr else curr['time'], key="dj_time")
    outcome = r2c3.selectbox("Outcome", ["Win", "Loss", "Breakeven", "No Trade"],
                             index=0 if not curr else ["Win", "Loss", "Breakeven", "No Trade"].index(curr['outcome']),
                             key="dj_out")
    pnl_val = r2c4.number_input("PnL ($)", value=0.0 if not curr else float(curr['pnl']), key="dj_pnl")
    rr_val = r2c5.number_input("RR", value=0.0 if not curr else float(curr.get('rr', 0.0)), key="dj_rr")

    st.divider()
    st.subheader("🔗 Analysis Links")
    lc1, lc2 = st.columns(2)
    htf_links = lc1.text_area("HTF Links (one link per line)",
                              value="" if not curr else "\n".join(curr.get('htf_links', [])), key="dj_htf", height=100)
    ltf_links = lc2.text_area("LTF Links (one link per line)",
                              value="" if not curr else "\n".join(curr.get('ltf_links', [])), key="dj_ltf", height=100)

    st.divider()
    st.subheader("🧩 Confluences")
    cc1, cc2, cc3 = st.columns([2, 2, 1])
    sel_tf = cc1.selectbox("Timeframe", ["30s", "1m", "2m", "3m", "4m", "5m", "15m", "30m", "1h", "4h", "d"],
                           key="dj_sel_tf")
    sel_conf = cc2.selectbox("Confluence", ["Liq Sweep", "SMT", "FVG", "iFVG", "CISD", "EQ"], key="dj_sel_conf")

    if cc3.button("➕ Add", use_container_width=True, key="dj_add_conf"):
        st.session_state.dj_temp_conf.append(f"{sel_tf} - {sel_conf}")
        st.rerun()

    if st.session_state.dj_temp_conf:
        st.write("**Dodane Konfluencje:**")
        for i, c in enumerate(st.session_state.dj_temp_conf):
            cx1, cx2 = st.columns([5, 1])
            cx1.markdown(f"✅ **{c}**")
            if cx2.button("❌", key=f"dj_del_conf_{i}"):
                st.session_state.dj_temp_conf.pop(i)
                st.rerun()

    st.divider()
    st.subheader("📝 Reviews & Mistakes")
    nc1, nc2, nc3 = st.columns(3)
    notes = nc1.text_area("Notes", value="" if not curr else curr.get('notes', ''), key="dj_notes", height=150)
    model_mistakes = nc2.text_area("Model Mistakes", value="" if not curr else curr.get('model_mistakes', ''),
                                   key="dj_mod_mist", height=150)
    mental_mistakes = nc3.text_area("Mental Mistakes", value="" if not curr else curr.get('mental_mistakes', ''),
                                    key="dj_men_mist", height=150)

    st.divider()

    if st.button("💾 SAVE RECORD", use_container_width=True, key="dj_save"):
        new_data = {
            "date": str(trade_date), "asset": asset, "direction": direction, "time": exec_time,
            "trade_type": trade_type, "account_type": account_type,
            "is_backtest": False,
            "notes": notes, "model_mistakes": model_mistakes, "mental_mistakes": mental_mistakes,
            "confluences": st.session_state.dj_temp_conf.copy(),
            "checklist": [False] * 6,  # Przekazanie pustej listy, by nie zepsuć struktury bazy
            "outcome": outcome, "pnl": pnl_val, "rr": rr_val,
            "htf_links": [x.strip() for x in htf_links.split('\n') if x.strip()],
            "ltf_links": [x.strip() for x in ltf_links.split('\n') if x.strip()],
            # Zachowujemy puste stare pola by nie zepsuć bazy
            "general_notes": "", "mood": "", "interfered": "No", "interfered_how": "",
            "htf_desc": "", "htf_keypoints": "", "ltf_desc": "", "ltf_keypoints": ""
        }
        if st.session_state.editing_index is not None:
            st.session_state.all_trades[st.session_state.editing_index] = new_data
            st.session_state.editing_index = None
        else:
            st.session_state.all_trades.append(new_data)

        save_all_data(st.session_state.all_trades)
        st.session_state.dj_temp_conf = []
        st.success("Zapisano!")
        st.session_state.navigate_to_history = True
        st.rerun()

# --- BACKTESTING ---
elif menu == "⏪ Backtesting":
    with top_col1:
        st.title("⏪ Backtesting")

    bt_section_idx = 1 if st.session_state.get('bt_nav_section') == "Trade Entry" else 0
    bt_menu = st.radio("Sekcja:", ["Dashboard", "Trade Entry"], horizontal=True, index=bt_section_idx,
                       key="bt_main_nav")
    st.session_state.bt_nav_section = bt_menu
    st.divider()

    if bt_menu == "Dashboard":
        bt_trades = [t for t in all_trades if t.get('is_backtest', True)]
        df_bt = pd.DataFrame(bt_trades)

        if not df_bt.empty:
            df_bt['date'] = pd.to_datetime(df_bt['date'])

            total_pnl = df_bt['pnl'].sum()
            total_valid = len(df_bt[df_bt['direction'] != 'No Trade'])

            wins_df = df_bt[df_bt['pnl'] > 0]
            losses_df = df_bt[df_bt['pnl'] < 0]

            wins_count = len(wins_df)
            losses_count = len(losses_df)

            gross_profit = wins_df['pnl'].sum()
            gross_loss = abs(losses_df['pnl'].sum())

            wr = (wins_count / total_valid * 100) if total_valid > 0 else 0
            avg_win = (gross_profit / wins_count) if wins_count > 0 else 0
            avg_loss = (gross_loss / losses_count) if losses_count > 0 else 0
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (
                float('inf') if gross_profit > 0 else 0.0)

            unique_days = df_bt['date'].nunique()

            c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
            c1.metric("Net P&L", f"{total_pnl:+.1f} $")
            c2.metric("Win Rate", f"{wr:.1f}%")
            c3.metric("Avg Win", f"{avg_win:+.1f} $")
            c4.metric("Avg Loss", f"{-avg_loss:+.1f} $")
            pf_display = "∞" if profit_factor == float('inf') else f"{profit_factor:.2f}"
            c5.metric("Profit Factor", pf_display)
            c6.metric("Trades", total_valid)
            c7.metric("Days Backtested", unique_days)

            # --- BT CALENDAR ---
            st.divider()
            st.subheader("Backtesting Calendar")
            min_y = df_bt['date'].dt.year.min()
            max_y = df_bt['date'].dt.year.max()
            view_year = col_y.selectbox("Year", range(min_y, max_y + 2), index=range(min_y, max_y + 2).index(
                datetime.now().year) if datetime.now().year in range(min_y, max_y + 2) else 0,
                                        label_visibility="collapsed", key="bt_cal_y")
            view_month = col_m.selectbox("Month", range(1, 13), index=datetime.now().month - 1,
                                         label_visibility="collapsed", key="bt_cal_m")

            cal = calendar.monthcalendar(view_year, view_month)

            cols = st.columns(7)
            days_header = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for i, d in enumerate(days_header):
                cols[i].markdown(f"<center><b style='color:{current_theme['text_secondary']}'>{d}</b></center>",
                                 unsafe_allow_html=True)

            for week in cal:
                ref_day = next((d for d in week if d != 0), None)
                weekly_pnl = 0.0
                weekly_rr = 0.0
                week_end_date = None
                if ref_day:
                    ref_date = date(view_year, view_month, ref_day)
                    day_idx = week.index(ref_day)
                    week_start_date = ref_date - timedelta(days=day_idx)
                    week_end_date = week_start_date + timedelta(days=6)
                    week_trades = [t for t in bt_trades if
                                   week_start_date <= datetime.strptime(t['date'], '%Y-%m-%d').date() <= week_end_date]
                    weekly_pnl = sum(t['pnl'] for t in week_trades)
                    weekly_rr = sum(t.get('rr', 0.0) for t in week_trades)

                cols = st.columns(7)
                for i, day in enumerate(week):
                    if i == 6:
                        bg_c, bor_c, txt_c, pnl_c = current_theme['bg_card'], current_theme['border'], current_theme[
                            'text_primary'], current_theme['text_secondary']
                        if weekly_pnl > 0:
                            bg_c, bor_c, pnl_c = (
                                "rgba(0, 255, 127, 0.15)" if st.session_state.theme == "Dark" else "#dcfce7"), (
                                "#00ff7f" if st.session_state.theme == "Dark" else "#22c55e"), (
                                "#00ff7f" if st.session_state.theme == "Dark" else "#15803d")
                        elif weekly_pnl < 0:
                            bg_c, bor_c, pnl_c = (
                                "rgba(255, 69, 58, 0.15)" if st.session_state.theme == "Dark" else "#fee2e2"), (
                                "#ff453a" if st.session_state.theme == "Dark" else "#ef4444"), (
                                "#ff453a" if st.session_state.theme == "Dark" else "#b91c1c")

                        card_html = f"""<div class="day-card" style="background-color: {bg_c}; border-color: {bor_c}; justify-content: center; align-items: center;"><div class="weekly-summary-title" style="color: {txt_c};">Weekly PnL</div><div class="weekly-summary-value" style="color: {pnl_c}; text-align: center;">{weekly_pnl:+.1f} $<br><span style="font-size: 0.85em; color: {txt_c}; font-weight: normal;">RR: {weekly_rr:.2f}</span></div></div>"""
                        cols[i].markdown(card_html, unsafe_allow_html=True)

                        curr_date_sunday = date(view_year, view_month, day) if day != 0 else (
                            week_end_date if ref_day else None)
                        with cols[i].popover(label=" ", use_container_width=True):
                            if curr_date_sunday:
                                st.header(f"📅 {curr_date_sunday.strftime('%A, %d %B %Y')}")
                                st.button(f"🔎 Go to History ({curr_date_sunday})",
                                          key=f"gth_sun_bt_{i}_{day}_{view_month}", use_container_width=True,
                                          on_click=go_to_history_for_day, args=(curr_date_sunday,))
                                st.divider()
                                sunday_trades = [t for t in bt_trades if t['date'] == str(curr_date_sunday)]
                                if sunday_trades:
                                    for t in sunday_trades:
                                        with st.container():
                                            h1, h2 = st.columns([3, 1])
                                            h1.markdown(f"### {t['asset']} ({t['direction']})")
                                            pnl_c = "green" if t['pnl'] > 0 else ("red" if t['pnl'] < 0 else "gray")
                                            h2.markdown(f"<h3 style='color:{pnl_c}'>{t['pnl']:+.1f} $</h3>",
                                                        unsafe_allow_html=True)
                                            st.caption(
                                                f"🕒 {t['time']} | 🔄 {t['trade_type']} | 🎯 {t['outcome']} | 💼 Backtesting | RR: {t.get('rr', 0.0)}")
                                            if t.get('notes'): st.info(f"📝 {t['notes']}")
                                            st.write(f"**Model Mistakes:** {t.get('model_mistakes', '-')}")
                                            st.write(f"**Mental Mistakes:** {t.get('mental_mistakes', '-')}")
                                            st.divider()
                                else:
                                    st.write("Brak tradów.")
                                    st.info(f"**Weekly Total:** {weekly_pnl:+.1f} $ | RR: {weekly_rr:.2f}")
                    else:
                        if day == 0:
                            cols[i].write("")
                        else:
                            curr_date = date(view_year, view_month, day)
                            day_trades = [t for t in bt_trades if t['date'] == str(curr_date)]
                            day_pnl = sum([t['pnl'] for t in day_trades])
                            day_rr = sum([t.get('rr', 0.0) for t in day_trades])
                            has_no_trade = any(t['direction'] == 'No Trade' for t in day_trades)
                            valid_trades_count = sum(1 for t in day_trades if t['direction'] != 'No Trade')

                            bg_c, bor_c, txt_c, pnl_c = current_theme['bg_card'], current_theme['border'], \
                            current_theme['text_primary'], current_theme['text_secondary']
                            pnl_disp, badge = "", ""

                            if day_trades:
                                if valid_trades_count > 0:
                                    b_bg = "#2d2d3a" if st.session_state.theme == "Dark" else "#e0e7ff"
                                    b_txt = "#ccc" if st.session_state.theme == "Dark" else "#4338ca"
                                    badge = f"<span style='font-size:0.8em;color:{b_txt};background:{b_bg};padding:2px 6px;border-radius:4px;'>{valid_trades_count}x</span>"

                                if has_no_trade and day_pnl == 0:
                                    bg_c, bor_c, pnl_c, pnl_disp = (
                                        "rgba(142, 142, 147, 0.15)" if st.session_state.theme == "Dark" else "#f3f4f6"), "#8e8e93", "#8e8e93", "⚪ No Trade"
                                elif day_pnl > 0:
                                    bg_c, bor_c, pnl_c, pnl_disp = (
                                        "rgba(0, 255, 127, 0.15)" if st.session_state.theme == "Dark" else "#dcfce7"), (
                                        "#00ff7f" if st.session_state.theme == "Dark" else "#22c55e"), (
                                        "#00ff7f" if st.session_state.theme == "Dark" else "#15803d"), f"🟢 +{day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"
                                elif day_pnl < 0:
                                    bg_c, bor_c, pnl_c, pnl_disp = (
                                        "rgba(255, 69, 58, 0.15)" if st.session_state.theme == "Dark" else "#fee2e2"), (
                                        "#ff453a" if st.session_state.theme == "Dark" else "#ef4444"), (
                                        "#ff453a" if st.session_state.theme == "Dark" else "#b91c1c"), f"🔴 {day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"
                                else:
                                    bg_c, bor_c, pnl_c, pnl_disp = "rgba(142, 142, 147, 0.15)", "#8e8e93", "#8e8e93", f"⚪ {day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"

                            card_html = f"""<div class="day-card" style="background-color: {bg_c}; border-color: {bor_c};"><div style="display:flex;justify-content:space-between;align-items:flex-start;"><div style="font-weight:bold;font-size:1.1em;color:{txt_c};">{day}</div><div>{badge}</div></div><div style="font-weight:bold;font-size:1em;color:{pnl_c};text-align:center;line-height:1.2;">{pnl_disp}</div></div>"""
                            cols[i].markdown(card_html, unsafe_allow_html=True)

                            with cols[i].popover(label=" ", use_container_width=True):
                                if day_trades:
                                    st.header(f"📅 {curr_date.strftime('%A, %d %B %Y')}")
                                    st.button(f"🔎 Go to History ({curr_date})", key=f"gth_bt_{curr_date}",
                                              use_container_width=True, on_click=go_to_history_for_day,
                                              args=(curr_date,))
                                    st.markdown(
                                        f"**Daily Net PnL:** :{'green' if day_pnl > 0 else 'red'}[{day_pnl:+.1f} $] | **RR:** {day_rr:.2f}")
                                    st.divider()
                                    for t in day_trades:
                                        with st.container():
                                            h1, h2 = st.columns([3, 1])
                                            h1.markdown(f"### {t['asset']} ({t['direction']})")
                                            pnl_c = "green" if t['pnl'] > 0 else ("red" if t['pnl'] < 0 else "gray")
                                            h2.markdown(f"<h3 style='color:{pnl_c}'>{t['pnl']:+.1f} $</h3>",
                                                        unsafe_allow_html=True)
                                            st.caption(
                                                f"🕒 {t['time']} | 🔄 {t['trade_type']} | 🎯 {t['outcome']} | 💼 Backtesting | RR: {t.get('rr', 0.0)}")
                                            if t.get('notes'): st.info(f"📝 {t['notes']}")
                                            st.write(f"**Model Mistakes:** {t.get('model_mistakes', '-')}")
                                            st.write(f"**Mental Mistakes:** {t.get('mental_mistakes', '-')}")
                                            st.divider()
                                else:
                                    st.write("Brak wpisów.")
        else:
            st.info("Brak danych z Backtestingu.")

    elif bt_menu == "Trade Entry":
        if 'editing_index' not in st.session_state: st.session_state.editing_index = None
        curr = all_trades[st.session_state.editing_index] if st.session_state.editing_index is not None and all_trades[
            st.session_state.editing_index].get('is_backtest') else None

        if 'bt_current_edit_idx' not in st.session_state or st.session_state.bt_current_edit_idx != st.session_state.editing_index:
            st.session_state.bt_current_edit_idx = st.session_state.editing_index
            st.session_state.bt_temp_conf = curr.get('confluences', []).copy() if curr else []

        st.subheader("📌 Trade Details")
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        asset = r1c1.selectbox("Asset", ["NQ", "MNQ", "ES", "MES", "XAUUSD"],
                               index=0 if not curr else ["NQ", "MNQ", "ES", "MES", "XAUUSD"].index(curr['asset']),
                               key="bt_asset")
        direction = r1c2.selectbox("Direction", ["Long", "Short", "Both", "No Trade"],
                                   index=0 if not curr else ["Long", "Short", "Both", "No Trade"].index(
                                       curr.get('direction', 'Long')), key="bt_dir")
        tt_l = ["Internal -> External", "External -> Internal", "Internal -> Internal", "External -> External", "-"]
        trade_type = r1c3.selectbox("Type", tt_l,
                                    index=0 if not curr or curr.get('trade_type') not in tt_l else tt_l.index(
                                        curr['trade_type']), key="bt_tt")
        account_type = r1c4.selectbox("Account Type", ["Backtesting"], disabled=True, key="bt_acc")

        r2c1, r2c2, r2c3, r2c4, r2c5 = st.columns(5)
        trade_date = r2c1.date_input("Date",
                                     date.today() if not curr else datetime.strptime(curr['date'], '%Y-%m-%d').date(),
                                     key="bt_date")
        exec_time = r2c2.text_input("Time", value="" if not curr else curr['time'], key="bt_time")
        outcome = r2c3.selectbox("Outcome", ["Win", "Loss", "Breakeven", "No Trade"],
                                 index=0 if not curr else ["Win", "Loss", "Breakeven", "No Trade"].index(
                                     curr['outcome']), key="bt_out")
        pnl_val = r2c4.number_input("PnL ($)", value=0.0 if not curr else float(curr['pnl']), key="bt_pnl")
        rr_val = r2c5.number_input("RR", value=0.0 if not curr else float(curr.get('rr', 0.0)), key="bt_rr")

        st.divider()
        st.subheader("🔗 Analysis Links")
        lc1, lc2 = st.columns(2)
        htf_links = lc1.text_area("HTF Links (one link per line)",
                                  value="" if not curr else "\n".join(curr.get('htf_links', [])), key="bt_htf",
                                  height=100)
        ltf_links = lc2.text_area("LTF Links (one link per line)",
                                  value="" if not curr else "\n".join(curr.get('ltf_links', [])), key="bt_ltf",
                                  height=100)

        st.divider()
        st.subheader("🧩 Confluences")
        cc1, cc2, cc3 = st.columns([2, 2, 1])
        sel_tf = cc1.selectbox("Timeframe", ["30s", "1m", "2m", "3m", "4m", "5m", "15m", "30m", "1h", "4h", "d"],
                               key="bt_sel_tf")
        sel_conf = cc2.selectbox("Confluence", ["Liq Sweep", "SMT", "FVG", "iFVG", "CISD", "EQ"], key="bt_sel_conf")

        if cc3.button("➕ Add", use_container_width=True, key="bt_add_conf"):
            st.session_state.bt_temp_conf.append(f"{sel_tf} - {sel_conf}")
            st.rerun()

        if st.session_state.bt_temp_conf:
            st.write("**Dodane Konfluencje:**")
            for i, c in enumerate(st.session_state.bt_temp_conf):
                cx1, cx2 = st.columns([5, 1])
                cx1.markdown(f"✅ **{c}**")
                if cx2.button("❌", key=f"bt_del_conf_{i}"):
                    st.session_state.bt_temp_conf.pop(i)
                    st.rerun()

        st.divider()
        st.subheader("📝 Reviews & Mistakes")
        nc1, nc2, nc3 = st.columns(3)
        notes = nc1.text_area("Notes", value="" if not curr else curr.get('notes', ''), key="bt_notes", height=150)
        model_mistakes = nc2.text_area("Model Mistakes", value="" if not curr else curr.get('model_mistakes', ''),
                                       key="bt_mod_mist", height=150)
        mental_mistakes = nc3.text_area("Mental Mistakes", value="" if not curr else curr.get('mental_mistakes', ''),
                                        key="bt_men_mist", height=150)

        st.divider()

        if st.button("💾 SAVE BACKTEST RECORD", use_container_width=True, key="bt_save"):
            new_data = {
                "date": str(trade_date), "asset": asset, "direction": direction, "time": exec_time,
                "trade_type": trade_type, "account_type": account_type,
                "is_backtest": True,
                "notes": notes, "model_mistakes": model_mistakes, "mental_mistakes": mental_mistakes,
                "confluences": st.session_state.bt_temp_conf.copy(),
                "checklist": [False] * 6,  # Przekazanie pustej listy, by nie zepsuć struktury bazy
                "outcome": outcome, "pnl": pnl_val, "rr": rr_val,
                "htf_links": [x.strip() for x in htf_links.split('\n') if x.strip()],
                "ltf_links": [x.strip() for x in ltf_links.split('\n') if x.strip()],
                "general_notes": "", "mood": "", "interfered": "No", "interfered_how": "",
                "htf_desc": "", "htf_keypoints": "", "ltf_desc": "", "ltf_keypoints": ""
            }

            if st.session_state.editing_index is not None:
                st.session_state.all_trades[st.session_state.editing_index] = new_data
                st.session_state.editing_index = None
            else:
                st.session_state.all_trades.append(new_data)

            save_all_data(st.session_state.all_trades)
            st.session_state.bt_temp_conf = []
            st.success("Zapisano Backtest!")
            st.session_state.navigate_to_history = True
            st.rerun()

# --- TRADES HISTORY ---
elif menu == "📜 Trades History":
    with top_col1:
        st.title("Trade History")

    preset_date = st.session_state.get('history_filter_date')
    if preset_date:
        st.button("⬅️ Back to Dashboard", use_container_width=True, on_click=back_to_dashboard)

    if all_trades:
        df = pd.DataFrame(all_trades)
        df['date'] = pd.to_datetime(df['date'])
        df['original_index'] = df.index

        with st.expander("🔍 Filter & Sort Options", expanded=bool(preset_date)):
            c_f1, c_f2, c_f3, c_f4 = st.columns(4)
            sel_asset = c_f1.multiselect("Asset", options=df['asset'].unique())
            sel_outcome = c_f2.multiselect("Outcome", options=df['outcome'].unique())

            if 'account_type' in df.columns:
                sel_account = c_f3.multiselect("Account Type", options=df['account_type'].unique())
            else:
                sel_account = []

            min_date, max_date = df['date'].min().date(), df['date'].max().date()
            default_val = (preset_date, preset_date) if preset_date else (min_date, max_date)
            sel_date = c_f4.date_input("Date Range", value=default_val)
            st.markdown("---")
            sort_opt = st.selectbox("Sort By",
                                    ["Date (Newest)", "Date (Oldest)", "PnL (High -> Low)", "PnL (Low -> High)"])

        if sel_asset: df = df[df['asset'].isin(sel_asset)]
        if sel_outcome: df = df[df['outcome'].isin(sel_outcome)]
        if sel_account: df = df[df['account_type'].isin(sel_account)]

        if isinstance(sel_date, tuple):
            if len(sel_date) == 2:
                df = df[(df['date'].dt.date >= sel_date[0]) & (df['date'].dt.date <= sel_date[1])]
            elif len(sel_date) == 1:
                df = df[df['date'].dt.date == sel_date[0]]
        elif isinstance(sel_date, date):
            df = df[df['date'].dt.date == sel_date]

        if sort_opt == "Date (Newest)":
            df = df.sort_values(by='date', ascending=False)
        elif sort_opt == "Date (Oldest)":
            df = df.sort_values(by='date', ascending=True)
        elif sort_opt == "PnL (High -> Low)":
            df = df.sort_values(by='pnl', ascending=False)
        elif sort_opt == "PnL (Low -> High)":
            df = df.sort_values(by='pnl', ascending=True)

        st.divider()
        st.write(f"Showing **{len(df)}** trades.")

        for _, row in df.iterrows():
            t = all_trades[int(row['original_index'])]
            idx = int(row['original_index'])
            acc_label = f" | 💼 {t.get('account_type', 'Funded')} | RR: {t.get('rr', 0.0)}"

            with st.expander(
                    f"#{idx + 1} | {t['date']} | {t['asset']} | {t.get('direction', 'Long')} | {t['pnl']} ${acc_label}"):
                st.button(f"✏️ Edit #{idx + 1}", key=f"ed_{idx}", on_click=go_to_edit_mode, args=(idx,))

                # Ujednolicony podgląd dla nowego formatu Daily Journal oraz Backtesting
                if t.get('is_backtest') or t.get('notes') or t.get('confluences'):
                    if t.get('notes'): st.info(f"**Notes:** {t['notes']}")
                    cm1, cm2 = st.columns(2)
                    cm1.error(f"**Model Mistakes:**\n{t.get('model_mistakes', '-')}")
                    cm2.warning(f"**Mental Mistakes:**\n{t.get('mental_mistakes', '-')}")

                    if t.get('confluences'):
                        st.markdown(f"**Confluences:** {', '.join(t.get('confluences', []))}")
                    st.write("---")

                    cl1, cl2 = st.columns(2)
                    with cl1:
                        st.markdown("### 🏛️ HTF Links")
                        for l in t.get('htf_links', []):
                            if "http" in l: st.image(l.strip(), use_container_width=True)
                    with cl2:
                        st.markdown("### ⚡ LTF Links")
                        for l in t.get('ltf_links', []):
                            if "http" in l: st.image(l.strip(), use_container_width=True)

                # Kompatybilność wsteczna - zachowujemy podgląd dla starych wpisów przed zmianami
                if t.get('general_notes') or t.get('htf_desc') or t.get('ltf_desc') or t.get('mood'):
                    st.markdown("---")
                    if t.get('general_notes'): st.info(f"**General Notes:** {t['general_notes']}")
                    ch1, ch2 = st.columns(2)
                    ch1.write(f"**🧠 Mood:** {t.get('mood', '-')}")
                    if t.get('interfered') == 'Yes':
                        ch2.markdown(f"**⚠️ Interfered:** :red[{t.get('interfered_how', '-')}]")
                    else:
                        ch2.write("**🛡️ Interfered:** No")
                    st.write("---")
                    ca, cb = st.columns(2)
                    with ca:
                        st.markdown("### 🏛️ HTF Analysis")
                        if t.get('htf_keypoints'):
                            st.markdown(
                                f"<div class='highlight-box'><b>HTF Key Points:</b><br>{t.get('htf_keypoints', 'N/A')}</div>",
                                unsafe_allow_html=True)
                        if t.get('htf_desc'):
                            st.write(f"**HTF Notes:** {t['htf_desc']}")
                    with cb:
                        st.markdown("### ⚡ LTF Analysis")
                        if t.get('ltf_keypoints'):
                            st.markdown(
                                f"<div class='highlight-box'><b>LTF Key Points:</b><br>{t.get('ltf_keypoints', 'N/A')}</div>",
                                unsafe_allow_html=True)
                        if t.get('ltf_desc'):
                            st.write(f"**LTF Notes:** {t['ltf_desc']}")
    else:
        st.info("Brak tradów w historii.")