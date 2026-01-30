import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
import os
import json

# --- KONFIGURACJA I ESTETYKA ---
st.set_page_config(page_title="PB Pro Dashboard", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #0e0e12; border-right: 1px solid #2d2d3a; }
    .stMetric { background-color: #16161d; padding: 20px; border-radius: 12px; border: 1px solid #2d2d3a; color: white; }
    .calendar-day { 
        border: 1px solid #2d2d3a; 
        border-radius: 10px; padding: 10px; height: 110px; 
        text-align: left; background-color: #16161d; color: #888;
    }
    .win-day { background-color: rgba(0, 255, 127, 0.1); border: 1px solid #00ff7f; color: #00ff7f !important; }
    .loss-day { background-color: rgba(255, 69, 58, 0.1); border: 1px solid #ff453a; color: #ff453a !important; }
    .be-day { background-color: rgba(142, 142, 147, 0.1); border: 1px solid #8e8e93; color: #8e8e93 !important; }
    .highlight-box { background-color: #1e1e26; padding: 10px; border-radius: 5px; border-left: 5px solid #00ff7f; margin-bottom: 10px; }
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

# --- SIDEBAR MENU ---
with st.sidebar:
    st.title("⚡ PB TRADING")
    menu = st.radio("MAIN MENU", ["📊 Dashboard", "📝 Daily Journal", "📜 Trades History"])
    st.divider()
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

        st.divider()
        st.subheader("Trading Calendar")
        col_y, col_m = st.columns(2)
        view_year = col_y.selectbox("Year", range(2024, 2030), index=range(2024, 2030).index(datetime.now().year))
        view_month = col_m.selectbox("Month", range(1, 13), index=datetime.now().month - 1)

        cal = calendar.monthcalendar(view_year, view_month)
        cols = st.columns(7)
        for i, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            cols[i].markdown(f"<center><b>{d}</b></center>", unsafe_allow_html=True)

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

                    style = ""
                    if day_trades:
                        if day_pnl > 0:
                            style = "win-day"
                        elif day_pnl < 0:
                            style = "loss-day"
                        elif has_no_trade:
                            style = "be-day"

                    cols[i].markdown(f"""
                        <div class="calendar-day {style}">
                            <span style="font-size: 12px;">{day}</span><br>
                            <div style="text-align: center; margin-top: 5px;">
                                <b>{f"{day_pnl:+.1f} $" if day_pnl != 0 else ("No Trade" if has_no_trade else "")}</b>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
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

        st.write("---")
        htf_links = st.text_area("HTF Links", value="" if not curr else "\n".join(curr['htf_links']))
        htf_narr = st.text_area("HTF Narrative", value="" if not curr else curr['htf_desc'])
        htf_kp = st.text_area("HTF Key Points", value="" if not curr else curr['htf_keypoints'])

    with col2:
        st.subheader("Execution")
        trade_type = st.selectbox("Type", ["Internal -> External", "External -> Internal", "Internal -> Internal"],
                                  index=0 if not curr else ["Internal -> External", "External -> Internal",
                                                            "Internal -> Internal"].index(curr['trade_type']))
        ltf_links = st.text_area("LTF Links", value="" if not curr else "\n".join(curr['ltf_links']))
        ltf_kp = st.text_area("LTF Key Points", value="" if not curr else curr['ltf_keypoints'])
        ltf_desc = st.text_area("LTF Model", value="" if not curr else curr['ltf_desc'])

        st.write("---")
        gen_notes = st.text_area("General Notes", value="" if not curr else curr.get('general_notes', ""))
        mood = st.select_slider("Mood", options=["Stressed", "Neutral", "Euphoric"],
                                value="Neutral" if not curr else curr['mood'])
        interfere = st.radio("Interfered?", ["No", "Yes"], index=0 if not curr or curr['interfered'] == "No" else 1)
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
            all_trades[st.session_state.editing_index] = new_data
            st.session_state.editing_index = None
        else:
            all_trades.append(new_data)
        save_all_data(all_trades)
        st.success("Zapisano!")
        st.rerun()

# --- TRADES HISTORY ---
elif menu == "📜 Trades History":
    st.title("Trade History")
    for i, t in enumerate(reversed(all_trades)):
        idx = len(all_trades) - 1 - i
        with st.expander(f"#{idx + 1} | {t['date']} | {t['asset']} | {t.get('direction', 'Long')} | {t['pnl']}R"):
            if st.button(f"✏️ Edit #{idx + 1}", key=f"ed_{idx}"):
                st.session_state.editing_index = idx
                st.rerun()

            if t.get('general_notes'): st.info(f"**General Notes:** {t['general_notes']}")

            ca, cb = st.columns(2)
            with ca:
                st.markdown("### 🏛️ HTF Analysis")
                st.markdown(
                    f"<div class='highlight-box'><b>HTF Key Points:</b><br>{t.get('htf_keypoints', 'N/A')}</div>",
                    unsafe_allow_html=True)
                st.write(f"**Narrative:** {t['htf_desc']}")
                for l in t['htf_links']:
                    if "http" in l: st.image(l.strip())
            with cb:
                st.markdown("### ⚡ LTF Analysis")
                st.markdown(
                    f"<div class='highlight-box'><b>LTF Key Points:</b><br>{t.get('ltf_keypoints', 'N/A')}</div>",
                    unsafe_allow_html=True)
                st.write(f"**Model:** {t['ltf_desc']}")
                for l in t['ltf_links']:
                    if "http" in l: st.image(l.strip())