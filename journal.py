import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
import os
import json

# --- KONFIGURACJA POCZĄTKOWA ---
st.set_page_config(page_title="NQPaneksu Journal", layout="wide")

# --- ZARZĄDZANIE STANEM (BEZ ZMIANY MOTYWU) ---
if 'menu_nav' not in st.session_state:
    st.session_state.menu_nav = "📊 Dashboard"

if st.session_state.get('navigate_to_history'):
    st.session_state.menu_nav = "📜 Trades History"
    st.session_state.navigate_to_history = False

# --- DEFINICJA KOLORÓW (TYLKO CIEMNY MOTYW) ---
current_theme = {
    "bg_app": "#0e0e12",
    # GRADIENT DLA SIDEBARA
    "bg_sidebar": "linear-gradient(180deg, #09090b 0%, #161625 100%)",
    "bg_card": "#16161d",
    "bg_metric": "linear-gradient(135deg, #16161d 0%, #1c1624 100%)",
    "border": "#2d2d3a",
    "text_primary": "#e0e0e0",
    "text_secondary": "#aaaaaa",
    "accent": "#ff007f",
    "popover_bg": "#16161d",
    "card_shadow": "0 2px 4px rgba(0,0,0,0.2)",
    "input_bg": "#16161d",
    "btn_bg": "#16161d",
    "btn_text": "#e0e0e0",
    "divider": "#2d2d3a"
}

# --- INJECT CSS (DYNAMICZNY) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    /* GLOBALNE TŁO */
    .stApp {{
        background-color: {current_theme['bg_app']};
        color: {current_theme['text_primary']};
    }}

    /* SIDEBAR - Z GRADIENTEM */
    [data-testid="stSidebar"] {{ 
        background: {current_theme['bg_sidebar']}; 
        border-right: 1px solid {current_theme['border']}; 
    }}

    /* METRYKI - Efekt karty z głębią */
    .stMetric {{ 
        background: {current_theme['bg_metric']}; 
        padding: 20px; 
        border-radius: 12px;
        border: 1px solid {current_theme['border']}; 
        color: {current_theme['text_primary']};
        box-shadow: {current_theme['card_shadow']};
    }}

    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{
        color: {current_theme['text_primary']} !important;
    }}

    /* TEXT ELEMENTS */
    h1, h2, h3, h4, p, span, div, label {{
        color: {current_theme['text_primary']};
    }}

    .stMarkdown p {{
        color: {current_theme['text_primary']} !important;
    }}

    /* BUTTONS */
    .stButton button {{
        border: 1px solid {current_theme['border']};
        background: {current_theme['btn_bg']};
        color: {current_theme['btn_text']};
        font-weight: 600;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.1s ease-in-out;
    }}

    .stButton button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
        border-color: {current_theme['accent']};
        color: {current_theme['btn_text']};
    }}

    /* SEPARATORY */
    hr {{
        margin-top: 2em;
        margin-bottom: 2em;
        height: 1px;
        background: {current_theme['divider']};
        border: none;
        opacity: 0.5;
    }}

    /* --- CSS KALENDARZA --- */
    .day-card {{
        height: 120px;
        width: 100%;
        border-radius: 12px;
        padding: 12px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        border: 1px solid {current_theme['border']};
        transition: transform 0.2s, box-shadow 0.2s;
        box-sizing: border-box;
        background-color: {current_theme['bg_card']};
        box-shadow: {current_theme['card_shadow']};
    }}

    div[data-testid="stPopover"] > button {{
        height: 120px !important;
        width: 100% !important;
        background-color: transparent !important;
        border: none !important;
        color: transparent !important;
        margin-top: -120px !important;
        position: relative;
        z-index: 5;
    }}

    div[data-testid="stPopover"] > button:hover {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid {current_theme['accent']} !important;
    }}

    div[data-testid="column"] {{ padding: 2px !important; }}

    div[data-testid="stPopoverBody"] {{
        border: 1px solid {current_theme['border']} !important;
        background-color: {current_theme['popover_bg']} !important;
        color: {current_theme['text_primary']} !important;
        min-width: 500px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        border-radius: 12px !important;
    }}

    /* Highlight Box */
    .highlight-box {{ 
        background-color: #1e1e26; 
        padding: 15px; 
        border-radius: 8px; 
        border-left: 4px solid #00ff7f; 
        margin-bottom: 15px; 
        color: {current_theme['text_primary']};
        border: 1px solid {current_theme['border']};
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        background-color: {current_theme['bg_card']};
        color: {current_theme['text_primary']};
        border-radius: 8px;
        border: 1px solid {current_theme['border']};
    }}

    /* FORM INPUTS */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"],
    input, textarea, select {{
        background-color: {current_theme['input_bg']} !important;
        color: {current_theme['text_primary']} !important;
        border-color: {current_theme['border']} !important;
        border-radius: 8px !important;
    }}

    div[data-baseweb="select"] svg, 
    div[data-baseweb="input"] svg {{
        fill: {current_theme['text_secondary']} !important;
    }}
    </style>
""", unsafe_allow_html=True)

DB_FILE = 'trading_data.json'


def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            try:
                return json.load(f)
            except:
                return []
    return []


def save_all_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)


all_trades = load_data()


# --- FUNKCJA CALLBACK DLA EDYCJI ---
def go_to_edit_mode(index):
    st.session_state.editing_index = index
    st.session_state.menu_nav = "📝 Daily Journal"


# --- SIDEBAR MENU ---
with st.sidebar:
    st.title("📘 NQPaneksu Journal")

    menu = st.radio("MAIN MENU", ["📊 Dashboard", "📝 Daily Journal", "📜 Trades History"], key="menu_nav")
    st.markdown("---")
    if st.button("🗑️ Delete Last Entry"):
        if all_trades:
            all_trades.pop()
            save_all_data(all_trades)
            st.rerun()

# --- DASHBOARD ---
if menu == "📊 Dashboard":
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

        st.markdown("---")
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
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write("")
                else:
                    curr_date = date(view_year, view_month, day)
                    day_trades = [t for t in all_trades if t['date'] == str(curr_date)]
                    day_pnl = sum([t['pnl'] for t in day_trades])
                    has_no_trade = any(t['direction'] == 'No Trade' for t in day_trades)
                    valid_trades_count = sum(1 for t in day_trades if t['direction'] != 'No Trade')

                    bg_color = current_theme['bg_card']
                    border_color = current_theme['border']
                    text_day_color = current_theme['text_primary']
                    text_pnl_color = current_theme['text_secondary']

                    pnl_display = ""
                    trades_count_badge = ""

                    if day_trades:
                        if valid_trades_count > 0:
                            badge_bg = "#2d2d3a"
                            badge_txt = "#ccc"
                            trades_count_badge = f"<span style='font-size: 0.8em; color: {badge_txt}; background: {badge_bg}; padding: 2px 8px; border-radius: 10px; font-weight: bold;'>{valid_trades_count}x</span>"

                        if has_no_trade and day_pnl == 0:
                            bg_color = "rgba(142, 142, 147, 0.15)"
                            border_color = "#8e8e93"
                            text_pnl_color = "#8e8e93"
                            pnl_display = "⚪ No Trade"
                        elif day_pnl > 0:
                            bg_color = "rgba(0, 255, 127, 0.15)"
                            border_color = "#00ff7f"
                            text_pnl_color = "#00ff7f"
                            pnl_display = f"🟢 +{day_pnl:.1f} $"
                        elif day_pnl < 0:
                            bg_color = "rgba(255, 69, 58, 0.15)"
                            border_color = "#ff453a"
                            text_pnl_color = "#ff453a"
                            pnl_display = f"🔴 {day_pnl:.1f} $"
                        else:
                            bg_color = "rgba(142, 142, 147, 0.15)"
                            border_color = "#8e8e93"
                            text_pnl_color = "#8e8e93"
                            pnl_display = f"⚪ {day_pnl:.1f} $"

                    card_html = f"""
                    <div class="day-card" style="background-color: {bg_color}; border-color: {border_color};">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div style="font-weight: bold; font-size: 1.1em; color: {text_day_color};">{day}</div>
                            <div>{trades_count_badge}</div>
                        </div>
                        <div style="font-weight: bold; font-size: 1em; color: {text_pnl_color}; text-align: center;">{pnl_display}</div>
                    </div>
                    """
                    cols[i].markdown(card_html, unsafe_allow_html=True)

                    with cols[i].popover(label=" ", use_container_width=True):
                        if day_trades:
                            st.header(f"📅 {curr_date.strftime('%A, %d %B %Y')}")
                            st.markdown(f"**Daily Net PnL:** :{'green' if day_pnl > 0 else 'red'}[{day_pnl:+.1f} $]")
                            st.markdown("---")
                            for t in day_trades:
                                with st.container():
                                    h1, h2 = st.columns([3, 1])
                                    h1.markdown(f"### {t['asset']} ({t['direction']})")
                                    pnl_c = "green" if t['pnl'] > 0 else ("red" if t['pnl'] < 0 else "gray")
                                    h2.markdown(f"<h3 style='color:{pnl_c}'>{t['pnl']:+.1f} $</h3>",
                                                unsafe_allow_html=True)
                                    d1, d2, d3 = st.columns(3)
                                    d1.caption(f"🕒 {t['time']}")
                                    d2.caption(f"🔄 {t['trade_type']}")
                                    d3.caption(f"🎯 {t['outcome']}")

                                    if t.get('general_notes'): st.info(f"📝 **Note:** {t['general_notes']}")

                                    cp1, cp2 = st.columns(2)
                                    cp1.write(f"**🧠 Mood:** {t.get('mood', '-')}")
                                    if t.get('interfered') == 'Yes':
                                        cp2.error(f"**⚠️ Interfered:** {t.get('interfered_how', '-')}")
                                    else:
                                        cp2.write("**🛡️ Interfered:** No")

                                    st.markdown("---")
                                    c_htf, c_ltf = st.columns(2)
                                    with c_htf:
                                        st.markdown("#### 🏛️ HTF Analysis")
                                        st.success(f"**Narrative:** {t.get('htf_desc', '-')}")
                                        st.markdown(f"**Key Points:** {t.get('htf_keypoints', '-')}")
                                        for l in t.get('htf_links', []):
                                            if "http" in l: st.image(l.strip(), use_container_width=True)
                                    with c_ltf:
                                        st.markdown("#### ⚡ LTF Analysis")
                                        st.warning(f"**Model:** {t.get('ltf_desc', '-')}")
                                        st.markdown(f"**Key Points:** {t.get('ltf_keypoints', '-')}")
                                        for l in t.get('ltf_links', []):
                                            if "http" in l: st.image(l.strip(), use_container_width=True)
                                    st.markdown("---")
                                    st.caption("✅ Checklist Check:")
                                    cl_cols = st.columns(6)
                                    checklist_items = ["Cond.", "HTF", "LTF", "Liq.", "Exec.", "Mental"]
                                    for idx, val in enumerate(t.get('checklist', [])):
                                        cl_cols[idx].checkbox(checklist_items[idx], value=val, disabled=True,
                                                              key=f"d_{curr_date}_{t['time']}_{idx}_{i}")
                                    st.markdown("---")
                        else:
                            st.write("Brak wpisów w dzienniku dla tego dnia.")
    else:
        st.info("Brak danych.")

# --- DAILY JOURNAL ---
elif menu == "📝 Daily Journal":
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
        direction = st.selectbox("Direction", ["Long", "Short", "No Trade"],
                                 index=0 if not curr else ["Long", "Short", "No Trade"].index(
                                     curr.get('direction', 'Long')))
        exec_time = st.text_input("Time", value="" if not curr else curr['time'])

        st.markdown("---")
        htf_links = st.text_area("HTF Links", value="" if not curr else "\n".join(curr['htf_links']))
        htf_narr = st.text_area("HTF Narrative", value="" if not curr else curr['htf_desc'])
        htf_kp = st.text_area("HTF Key Points", value="" if not curr else curr['htf_keypoints'])

    with col2:
        st.subheader("Execution")
        trade_types_list = ["Internal -> External", "External -> Internal", "Internal -> Internal", "-"]
        default_index = 0
        if curr and curr['trade_type'] in trade_types_list:
            default_index = trade_types_list.index(curr['trade_type'])
        trade_type = st.selectbox("Type", trade_types_list, index=default_index)

        ltf_links = st.text_area("LTF Links", value="" if not curr else "\n".join(curr['ltf_links']))
        ltf_kp = st.text_area("LTF Key Points", value="" if not curr else curr['ltf_keypoints'])
        ltf_desc = st.text_area("LTF Model", value="" if not curr else curr['ltf_desc'])

        st.markdown("---")
        gen_notes = st.text_area("General Notes", value="" if not curr else curr.get('general_notes', ""))
        mood = st.select_slider("Mood", options=["Stressed", "Neutral", "Euphoric"],
                                value="Neutral" if not curr else curr['mood'])
        interfere = st.radio("Interfered?", ["No", "Yes"], index=0 if not curr or curr['interfered'] == "No" else 1)
        inter_how = st.text_input("How?",
                                  value="" if not curr else curr['interfered_how']) if interfere == "Yes" else ""

    st.markdown("---")
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
            all_trades[st.session_state.editing_index] = new_data
            st.session_state.editing_index = None
        else:
            all_trades.append(new_data)
        save_all_data(all_trades)
        st.success("Zapisano!")
        st.session_state.navigate_to_history = True
        st.rerun()

# --- TRADES HISTORY ---
elif menu == "📜 Trades History":
    st.title("Trade History")

    if all_trades:
        df = pd.DataFrame(all_trades)
        df['date'] = pd.to_datetime(df['date'])
        df['original_index'] = df.index

        with st.expander("🔍 Filter & Sort Options", expanded=False):
            c_f1, c_f2, c_f3, c_f4 = st.columns(4)
            sel_asset = c_f1.multiselect("Asset", options=df['asset'].unique())
            sel_outcome = c_f2.multiselect("Outcome", options=df['outcome'].unique())
            sel_direction = c_f3.multiselect("Direction", options=df['direction'].unique())
            min_date = df['date'].min().date()
            max_date = df['date'].max().date()
            sel_date = c_f4.date_input("Date Range", value=(min_date, max_date))
            st.markdown("---")
            sort_opt = st.selectbox("Sort By",
                                    ["Date (Newest)", "Date (Oldest)", "PnL (High -> Low)", "PnL (Low -> High)"])

        if sel_asset: df = df[df['asset'].isin(sel_asset)]
        if sel_outcome: df = df[df['outcome'].isin(sel_outcome)]
        if sel_direction: df = df[df['direction'].isin(sel_direction)]
        if isinstance(sel_date, tuple):
            if len(sel_date) == 2:
                start_d, end_d = sel_date
                df = df[(df['date'].dt.date >= start_d) & (df['date'].dt.date <= end_d)]
            elif len(sel_date) == 1:
                df = df[df['date'].dt.date == sel_date[0]]

        if sort_opt == "Date (Newest)":
            df = df.sort_values(by='date', ascending=False)
        elif sort_opt == "Date (Oldest)":
            df = df.sort_values(by='date', ascending=True)
        elif sort_opt == "PnL (High -> Low)":
            df = df.sort_values(by='pnl', ascending=False)
        elif sort_opt == "PnL (Low -> High)":
            df = df.sort_values(by='pnl', ascending=True)

        st.markdown("---")
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
                st.markdown("---")

                ca, cb = st.columns(2)
                with ca:
                    st.markdown("### 🏛️ HTF Analysis")
                    st.markdown(
                        f"<div class='highlight-box'><b>HTF Key Points:</b><br>{t.get('htf_keypoints', 'N/A')}</div>",
                        unsafe_allow_html=True)
                    st.write(f"**Narrative:** {t['htf_desc']}")
                    for l in t['htf_links']:
                        if "http" in l: st.image(l.strip(), use_container_width=True)
                with cb:
                    st.markdown("### ⚡ LTF Analysis")
                    st.markdown(
                        f"<div class='highlight-box'><b>LTF Key Points:</b><br>{t.get('ltf_keypoints', 'N/A')}</div>",
                        unsafe_allow_html=True)
                    st.write(f"**Model:** {t['ltf_desc']}")
                    for l in t['ltf_links']:
                        if "http" in l: st.image(l.strip(), use_container_width=True)
    else:
        st.info("Brak tradów w historii.")