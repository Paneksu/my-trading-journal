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

# --- DEFINICJA KOLORÓW DLA MOTYWÓW ---
themes = {
    "Dark": {
        "bg_app": "#0e0e12",
        "bg_sidebar": "#09090b",
        "bg_card": "#16161d",
        "bg_metric": "linear-gradient(135deg, #16161d 0%, #1c1624 100%)",
        "border": "#2d2d3a",
        "text_primary": "#e0e0e0",
        "text_secondary": "#aaaaaa",
        "accent": "#ff007f",
        "popover_bg": "#16161d",
        "card_shadow": "0 2px 4px rgba(0,0,0,0.2)",
        "input_bg": "#16161d"
    },
    "Light": {
        "bg_app": "#eef2f6",
        "bg_sidebar": "#ffffff",
        "bg_card": "#ffffff",
        "bg_metric": "linear-gradient(135deg, #ffffff 0%, #e0c3fc 100%)",
        "border": "#c7d2dd",
        "text_primary": "#1a1f36",
        "text_secondary": "#4f566b",
        "accent": "#6c5ce7",
        "popover_bg": "#ffffff",
        "card_shadow": "0 4px 6px rgba(0,0,0,0.05)",
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
    .stApp {{ background-color: {current_theme['bg_app']}; color: {current_theme['text_primary']}; }}
    [data-testid="stSidebar"] {{ background-color: {current_theme['bg_sidebar']}; border-right: 1px solid {current_theme['border']}; }}
    .stMetric {{ background: {current_theme['bg_metric']}; padding: 20px; border-radius: 12px; border: 1px solid {current_theme['border']}; color: {current_theme['text_primary']}; box-shadow: {current_theme['card_shadow']}; }}
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{ color: {current_theme['text_primary']} !important; }}
    h1, h2, h3, h4, p, span, div, label {{ color: {current_theme['text_primary']}; }}
    .stMarkdown p {{ color: {current_theme['text_primary']} !important; }}
    div[data-testid="stButton"] button {{ border: 1px solid {current_theme['border']}; background-color: {current_theme['bg_card']}; color: {current_theme['text_primary']}; font-weight: bold; box-shadow: {current_theme['card_shadow']}; }}
    div[data-testid="column"] div[data-testid="stButton"] button {{ border-radius: 50%; width: 45px; height: 45px; }}

    [data-testid="stImage"] {{ overflow: visible !important; position: relative !important; }}
    button[title="View fullscreen"] {{ display: flex !important; visibility: visible !important; opacity: 1 !important; background-color: rgba(0, 0, 0, 0.6) !important; border: 1px solid rgba(255, 255, 255, 0.3) !important; width: 2.5rem !important; height: 2.5rem !important; right: 0.5rem !important; top: 0.5rem !important; z-index: 999999 !important; cursor: pointer !important; border-radius: 8px !important; align-items: center !important; justify-content: center !important; transition: background-color 0.2s !important; }}
    button[title="View fullscreen"]:hover {{ background-color: rgba(0, 0, 0, 0.9) !important; border-color: {current_theme['accent']} !important; transform: scale(1.05); }}
    button[title="View fullscreen"] svg {{ fill: white !important; width: 1.2rem !important; height: 1.2rem !important; }}

    .day-card {{ height: 120px; width: 100%; border-radius: 12px; padding: 10px; display: flex; flex-direction: column; justify-content: space-between; border: 1px solid {current_theme['border']}; transition: transform 0.2s, box-shadow 0.2s; box-sizing: border-box; background-color: {current_theme['bg_card']}; box-shadow: {current_theme['card_shadow']}; }}
    .weekly-summary-title {{ font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px; opacity: 0.7; }}
    .weekly-summary-value {{ font-size: 1.2em; font-weight: bold; }}
    div[data-testid="stPopover"] > button {{ height: 120px !important; width: 100% !important; background-color: transparent !important; border: none !important; border-radius: 12px !important; color: transparent !important; margin-top: -120px !important; position: relative; z-index: 5; }}
    div[data-testid="stPopover"] > button:hover {{ background-color: rgba(128, 128, 128, 0.05) !important; border: 2px solid {current_theme['accent']} !important; }}
    div[data-testid="column"] {{ padding: 2px !important; }}

    div[data-testid="stPopoverBody"] {{ 
        border: 1px solid {current_theme['border']} !important; 
        background-color: {current_theme['popover_bg']} !important; 
        color: {current_theme['text_primary']} !important; 
        min-width: 1200px !important; 
        max-width: 95vw !important;
    }}

    /* --- ZMIANA: white-space: pre-wrap dla zachowania enterów --- */
    .highlight-box {{ 
        background-color: {'#1e1e26' if st.session_state.theme == 'Dark' else '#f8faff'}; 
        padding: 10px; 
        border-radius: 5px; 
        border-left: 5px solid #00ff7f; 
        margin-bottom: 10px; 
        color: {current_theme['text_primary']};
        border: 1px solid {current_theme['border']};
        white-space: pre-wrap; /* TO ODPOWIADA ZA NOWE LINIE */
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
            if row.get('date'): row['date'] = str(row['date'])
            processed_data.append(row)
        return processed_data
    except Exception as e:
        return []


def save_all_data(data):
    if not data:
        df = pd.DataFrame(
            columns=['date', 'asset', 'direction', 'time', 'trade_type', 'outcome', 'pnl', 'general_notes', 'mood',
                     'interfered', 'interfered_how', 'htf_desc', 'htf_keypoints', 'htf_links', 'ltf_desc',
                     'ltf_keypoints', 'ltf_links', 'checklist'])
        conn.update(data=df)
        return
    data_to_save = []
    for row in data:
        new_row = row.copy()
        new_row['htf_links'] = "|||".join(row['htf_links'])
        new_row['ltf_links'] = "|||".join(row['ltf_links'])
        new_row['checklist'] = json.dumps(row['checklist'])
        data_to_save.append(new_row)
    df = pd.DataFrame(data_to_save)
    conn.update(data=df)


if 'all_trades' not in st.session_state:
    with st.spinner("Ładowanie bazy danych..."):
        st.session_state.all_trades = load_data_from_gsheets()

all_trades = st.session_state.all_trades


# --- FUNKCJE CALLBACK ---
def go_to_edit_mode(index):
    st.session_state.editing_index = index
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
    menu = st.radio("MAIN MENU", ["📊 Dashboard", "📝 Daily Journal", "📜 Trades History"], key="menu_nav")
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

    if all_trades:
        df = pd.DataFrame(all_trades)
        df['date'] = pd.to_datetime(df['date'])

        c1, c2, c3, c4 = st.columns(4)
        total_pnl = df['pnl'].sum()
        wins = len(df[df['outcome'] == 'Win'])
        total_valid = len(df[df['direction'] != 'No Trade'])
        wr = (wins / total_valid * 100) if total_valid > 0 else 0

        c1.metric("Net P&L", f"{total_pnl:+.1f} $")
        c2.metric("Win Rate", f"{wr:.1f}%")
        c3.metric("Trades", total_valid)
        c4.metric("No Trade Days", len(df[df['direction'] == 'No Trade']))

        st.divider()
        st.subheader("Trading Calendar")
        col_y, col_m = st.columns(2)
        view_year = col_y.selectbox("Year", range(2024, 2030), index=range(2024, 2030).index(datetime.now().year))
        view_month = col_m.selectbox("Month", range(1, 13), index=datetime.now().month - 1)

        cal = calendar.monthcalendar(view_year, view_month)

        cols = st.columns(7)
        days_header = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, d in enumerate(days_header):
            cols[i].markdown(f"<center><b style='color:{current_theme['text_secondary']}'>{d}</b></center>",
                             unsafe_allow_html=True)

        for week in cal:
            ref_day = next((d for d in week if d != 0), None)
            weekly_pnl = 0.0
            week_end_date = None
            if ref_day:
                ref_date = date(view_year, view_month, ref_day)
                day_idx = week.index(ref_day)
                week_start_date = ref_date - timedelta(days=day_idx)
                week_end_date = week_start_date + timedelta(days=6)
                week_trades = [t for t in all_trades if
                               week_start_date <= datetime.strptime(t['date'], '%Y-%m-%d').date() <= week_end_date]
                weekly_pnl = sum(t['pnl'] for t in week_trades)

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

                    card_html = f"""<div class="day-card" style="background-color: {bg_c}; border-color: {bor_c}; justify-content: center; align-items: center;"><div class="weekly-summary-title" style="color: {txt_c};">Weekly PnL</div><div class="weekly-summary-value" style="color: {pnl_c};">{weekly_pnl:+.1f} $</div></div>"""
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
                            sunday_trades = [t for t in all_trades if t['date'] == str(curr_date_sunday)]
                            if sunday_trades:
                                for t in sunday_trades:
                                    with st.container():
                                        h1, h2 = st.columns([3, 1])
                                        h1.markdown(f"### {t['asset']} ({t['direction']})")
                                        pnl_c = "green" if t['pnl'] > 0 else ("red" if t['pnl'] < 0 else "gray")
                                        h2.markdown(f"<h3 style='color:{pnl_c}'>{t['pnl']:+.1f} $</h3>",
                                                    unsafe_allow_html=True)
                                        st.caption(f"🕒 {t['time']} | 🔄 {t['trade_type']} | 🎯 {t['outcome']}")
                                        if t.get('general_notes'): st.info(f"📝 {t['general_notes']}")
                                        st.markdown("---")
                                        c_htf, c_ltf = st.columns(2)
                                        with c_htf:
                                            # POPRAWA: Zmiana nazwy i dodanie highlight-box z obsługą enterów
                                            st.markdown("#### 🏛️ HTF Analysis")
                                            st.markdown(
                                                f"**HTF Notes:** {t.get('htf_desc', '-').replace(chr(10), '  ' + chr(10))}")
                                            st.markdown(
                                                f"<div class='highlight-box'><b>Key Points:</b><br>{t.get('htf_keypoints', '-')}</div>",
                                                unsafe_allow_html=True)
                                            for l in t.get('htf_links', []):
                                                if "http" in l: st.image(l.strip(), use_container_width=True)
                                        with c_ltf:
                                            # POPRAWA: Zmiana nazwy i dodanie highlight-box z obsługą enterów
                                            st.markdown("#### ⚡ LTF Analysis")
                                            st.markdown(
                                                f"**LTF Notes:** {t.get('ltf_desc', '-').replace(chr(10), '  ' + chr(10))}")
                                            st.markdown(
                                                f"<div class='highlight-box'><b>Key Points:</b><br>{t.get('ltf_keypoints', '-')}</div>",
                                                unsafe_allow_html=True)
                                            for l in t.get('ltf_links', []):
                                                if "http" in l: st.image(l.strip(), use_container_width=True)
                                        st.divider()
                            else:
                                st.write("Brak tradów."); st.info(f"**Weekly Total:** {weekly_pnl:+.1f} $")
                else:
                    if day == 0:
                        cols[i].write("")
                    else:
                        curr_date = date(view_year, view_month, day)
                        day_trades = [t for t in all_trades if t['date'] == str(curr_date)]
                        day_pnl = sum([t['pnl'] for t in day_trades])
                        has_no_trade = any(t['direction'] == 'No Trade' for t in day_trades)
                        valid_trades_count = sum(1 for t in day_trades if t['direction'] != 'No Trade')

                        bg_c, bor_c, txt_c, pnl_c = current_theme['bg_card'], current_theme['border'], current_theme[
                            'text_primary'], current_theme['text_secondary']
                        pnl_disp, badge = "", ""
                        is_evaluation = False
                        if day_trades and valid_trades_count > 0 and day_pnl == 0.0: is_evaluation = True

                        if day_trades:
                            if valid_trades_count > 0:
                                b_bg = "#2d2d3a" if st.session_state.theme == "Dark" else "#e0e7ff"
                                b_txt = "#ccc" if st.session_state.theme == "Dark" else "#4338ca"
                                badge = f"<span style='font-size:0.8em;color:{b_txt};background:{b_bg};padding:2px 6px;border-radius:4px;'>{valid_trades_count}x</span>"
                            if is_evaluation:
                                outcomes = [t['outcome'] for t in day_trades if t['direction'] != 'No Trade']
                                has_loss, has_win = 'Loss' in outcomes, 'Win' in outcomes
                                if has_win:
                                    bg_c, bor_c, pnl_c = (
                                        "rgba(0, 255, 127, 0.15)" if st.session_state.theme == "Dark" else "#dcfce7"), (
                                        "#00ff7f" if st.session_state.theme == "Dark" else "#22c55e"), (
                                        "#00ff7f" if st.session_state.theme == "Dark" else "#15803d")
                                elif has_loss:
                                    bg_c, bor_c, pnl_c = (
                                        "rgba(255, 69, 58, 0.15)" if st.session_state.theme == "Dark" else "#fee2e2"), (
                                        "#ff453a" if st.session_state.theme == "Dark" else "#ef4444"), (
                                        "#ff453a" if st.session_state.theme == "Dark" else "#b91c1c")
                                else:
                                    bg_c, bor_c, pnl_c = "rgba(142, 142, 147, 0.15)", "#8e8e93", "#8e8e93"
                                pnl_disp = f"<span style='font-size:0.7em; opacity:0.8; letter-spacing:1px;'>EVALUATION</span><br>{day_pnl:.1f} $"
                            elif has_no_trade and day_pnl == 0:
                                bg_c, bor_c, pnl_c, pnl_disp = (
                                    "rgba(142, 142, 147, 0.15)" if st.session_state.theme == "Dark" else "#f3f4f6"), "#8e8e93", "#8e8e93", "⚪ No Trade"
                            elif day_pnl > 0:
                                bg_c, bor_c, pnl_c, pnl_disp = (
                                    "rgba(0, 255, 127, 0.15)" if st.session_state.theme == "Dark" else "#dcfce7"), (
                                    "#00ff7f" if st.session_state.theme == "Dark" else "#22c55e"), (
                                    "#00ff7f" if st.session_state.theme == "Dark" else "#15803d"), f"🟢 +{day_pnl:.1f} $"
                            elif day_pnl < 0:
                                bg_c, bor_c, pnl_c, pnl_disp = (
                                    "rgba(255, 69, 58, 0.15)" if st.session_state.theme == "Dark" else "#fee2e2"), (
                                    "#ff453a" if st.session_state.theme == "Dark" else "#ef4444"), (
                                    "#ff453a" if st.session_state.theme == "Dark" else "#b91c1c"), f"🔴 {day_pnl:.1f} $"
                            else:
                                bg_c, bor_c, pnl_c, pnl_disp = "rgba(142, 142, 147, 0.15)", "#8e8e93", "#8e8e93", f"⚪ {day_pnl:.1f} $"

                        card_html = f"""<div class="day-card" style="background-color: {bg_c}; border-color: {bor_c};"><div style="display:flex;justify-content:space-between;align-items:flex-start;"><div style="font-weight:bold;font-size:1.1em;color:{txt_c};">{day}</div><div>{badge}</div></div><div style="font-weight:bold;font-size:1em;color:{pnl_c};text-align:center;">{pnl_disp}</div></div>"""
                        cols[i].markdown(card_html, unsafe_allow_html=True)

                        with cols[i].popover(label=" ", use_container_width=True):
                            if day_trades:
                                st.header(f"📅 {curr_date.strftime('%A, %d %B %Y')}")
                                st.button(f"🔎 Go to History ({curr_date})", key=f"gth_{curr_date}",
                                          use_container_width=True, on_click=go_to_history_for_day, args=(curr_date,))
                                st.markdown(
                                    f"**Daily Net PnL:** :{'green' if day_pnl > 0 else 'red'}[{day_pnl:+.1f} $]")
                                st.divider()
                                for t in day_trades:
                                    with st.container():
                                        h1, h2 = st.columns([3, 1])
                                        h1.markdown(f"### {t['asset']} ({t['direction']})")
                                        pnl_c = "green" if t['pnl'] > 0 else ("red" if t['pnl'] < 0 else "gray")
                                        h2.markdown(f"<h3 style='color:{pnl_c}'>{t['pnl']:+.1f} $</h3>",
                                                    unsafe_allow_html=True)
                                        st.caption(f"🕒 {t['time']} | 🔄 {t['trade_type']} | 🎯 {t['outcome']}")
                                        if t.get('general_notes'): st.info(f"📝 {t['general_notes']}")
                                        cp1, cp2 = st.columns(2)
                                        cp1.write(f"**🧠 Mood:** {t.get('mood', '-')}")
                                        if t.get('interfered') == 'Yes':
                                            cp2.error(f"**⚠️ Interfered:** {t.get('interfered_how', '-')}")
                                        else:
                                            cp2.write("**🛡️ Interfered:** No")
                                        st.markdown("---")
                                        c_htf, c_ltf = st.columns(2)
                                        with c_htf:
                                            # POPRAWA: Zmiana nazwy i dodanie highlight-box z obsługą enterów
                                            st.markdown("#### 🏛️ HTF Analysis")
                                            st.markdown(
                                                f"**HTF Notes:** {t.get('htf_desc', '-').replace(chr(10), '  ' + chr(10))}")
                                            st.markdown(
                                                f"<div class='highlight-box'><b>Key Points:</b><br>{t.get('htf_keypoints', '-')}</div>",
                                                unsafe_allow_html=True)
                                            for l in t.get('htf_links', []):
                                                if "http" in l: st.image(l.strip(), use_container_width=True)
                                        with c_ltf:
                                            # POPRAWA: Zmiana nazwy i dodanie highlight-box z obsługą enterów
                                            st.markdown("#### ⚡ LTF Analysis")
                                            st.markdown(
                                                f"**LTF Notes:** {t.get('ltf_desc', '-').replace(chr(10), '  ' + chr(10))}")
                                            st.markdown(
                                                f"<div class='highlight-box'><b>Key Points:</b><br>{t.get('ltf_keypoints', '-')}</div>",
                                                unsafe_allow_html=True)
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
    curr = all_trades[st.session_state.editing_index] if st.session_state.editing_index is not None else None

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Technical Setup")
        asset = st.selectbox("Asset", ["NQ", "MNQ", "ES", "MES", "XAUUSD"],
                             index=0 if not curr else ["NQ", "MNQ", "ES", "MES", "XAUUSD"].index(curr['asset']))
        trade_date = st.date_input("Date",
                                   date.today() if not curr else datetime.strptime(curr['date'], '%Y-%m-%d').date())
        direction = st.selectbox("Direction", ["Long", "Short", "Both", "No Trade"],
                                 index=0 if not curr else ["Long", "Short", "Both", "No Trade"].index(
                                     curr.get('direction', 'Long')))
        exec_time = st.text_input("Time", value="" if not curr else curr['time'])
        st.write("---")
        htf_links = st.text_area("HTF Links", value="" if not curr else "\n".join(curr['htf_links']))
        # ZMIANA: ETYKIETA
        htf_narr = st.text_area("HTF Notes", value="" if not curr else curr['htf_desc'])
        htf_kp = st.text_area("HTF Key Points", value="" if not curr else curr['htf_keypoints'])

    with col2:
        st.subheader("Execution")
        tt_l = ["Internal -> External", "External -> Internal", "Internal -> Internal", "-"]
        trade_type = st.selectbox("Type", tt_l, index=0 if not curr or curr['trade_type'] not in tt_l else tt_l.index(
            curr['trade_type']))
        ltf_links = st.text_area("LTF Links", value="" if not curr else "\n".join(curr['ltf_links']))
        ltf_kp = st.text_area("LTF Key Points", value="" if not curr else curr['ltf_keypoints'])
        # ZMIANA: ETYKIETA
        ltf_desc = st.text_area("LTF Notes", value="" if not curr else curr['ltf_desc'])
        st.write("---")
        gen_notes = st.text_area("General Notes", value="" if not curr else curr.get('general_notes', ""))

        mood_options = ["Stressed", "Neutral", "Euphoric"]
        mood_val = curr['mood'] if curr and curr.get('mood') in mood_options else "Neutral"
        mood = st.select_slider("Mood", options=mood_options, value=mood_val)

        interfere_val = 1 if curr and curr.get('interfered') == "Yes" else 0
        interfere = st.radio("Interfered?", ["No", "Yes"], index=interfere_val)
        inter_how = st.text_input("How?",
                                  value="" if not curr else curr['interfered_how']) if interfere == "Yes" else ""

    st.divider()
    c1, c2 = st.columns(2)
    outcome = c1.selectbox("Outcome", ["Win", "Loss", "Breakeven", "No Trade"],
                           index=0 if not curr else ["Win", "Loss", "Breakeven", "No Trade"].index(curr['outcome']))
    pnl_val = c2.number_input("PnL ($)", value=0.0 if not curr else float(curr['pnl']))

    st.write("**Checklist**")
    ch_cols = st.columns(3)
    old_ch = curr['checklist'] if curr else [False] * 6
    ch1 = ch_cols[0].checkbox("Good trading conditions?", value=old_ch[0])
    ch2 = ch_cols[1].checkbox("Trade aligns with HTF?", value=old_ch[1])
    ch3 = ch_cols[2].checkbox("Delivery from LTF keypoint?", value=old_ch[2])
    ch4 = ch_cols[0].checkbox("Good Draw of Liquidity?", value=old_ch[3])
    ch5 = ch_cols[1].checkbox("Good execution?", value=old_ch[4])
    ch6 = ch_cols[2].checkbox("Good mental during trading?", value=old_ch[5])

    if st.button("💾 SAVE RECORD", use_container_width=True):
        new_data = {
            "date": str(trade_date), "asset": asset, "direction": direction, "time": exec_time,
            "trade_type": trade_type,
            "htf_links": htf_links.split('\n'), "htf_desc": htf_narr, "htf_keypoints": htf_kp,
            "ltf_links": ltf_links.split('\n'), "ltf_desc": ltf_desc, "ltf_keypoints": ltf_kp,
            "general_notes": gen_notes, "mood": mood, "interfered": interfere, "interfered_how": inter_how,
            "checklist": [ch1, ch2, ch3, ch4, ch5, ch6], "outcome": outcome, "pnl": pnl_val
        }
        if st.session_state.editing_index is not None:
            st.session_state.all_trades[st.session_state.editing_index] = new_data
            st.session_state.editing_index = None
        else:
            st.session_state.all_trades.append(new_data)

        save_all_data(st.session_state.all_trades)
        st.success("Zapisano!")
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
            sel_direction = c_f3.multiselect("Direction", options=df['direction'].unique())

            min_date, max_date = df['date'].min().date(), df['date'].max().date()
            default_val = (preset_date, preset_date) if preset_date else (min_date, max_date)
            sel_date = c_f4.date_input("Date Range", value=default_val)
            st.markdown("---")
            sort_opt = st.selectbox("Sort By",
                                    ["Date (Newest)", "Date (Oldest)", "PnL (High -> Low)", "PnL (Low -> High)"])

        if sel_asset: df = df[df['asset'].isin(sel_asset)]
        if sel_outcome: df = df[df['outcome'].isin(sel_outcome)]
        if sel_direction: df = df[df['direction'].isin(sel_direction)]
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
            with st.expander(f"#{idx + 1} | {t['date']} | {t['asset']} | {t.get('direction', 'Long')} | {t['pnl']}R"):
                st.button(f"✏️ Edit #{idx + 1}", key=f"ed_{idx}", on_click=go_to_edit_mode, args=(idx,))
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
                    st.markdown(
                        f"<div class='highlight-box'><b>HTF Key Points:</b><br>{t.get('htf_keypoints', 'N/A')}</div>",
                        unsafe_allow_html=True)
                    st.write(f"**HTF Notes:** {t['htf_desc']}")
                    for l in t['htf_links']:
                        if "http" in l: st.image(l.strip(), use_container_width=True)
                with cb:
                    st.markdown("### ⚡ LTF Analysis")
                    st.markdown(
                        f"<div class='highlight-box'><b>LTF Key Points:</b><br>{t.get('ltf_keypoints', 'N/A')}</div>",
                        unsafe_allow_html=True)
                    st.write(f"**LTF Notes:** {t['ltf_desc']}")
                    for l in t['ltf_links']:
                        if "http" in l: st.image(l.strip(), use_container_width=True)
    else:
        st.info("Brak tradów w historii.")