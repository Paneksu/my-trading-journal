import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import json
from streamlit_gsheets import GSheetsConnection

# --- KONFIGURACJA POCZĄTKOWA ---
st.set_page_config(page_title="NQPaneksu Journal", layout="wide", initial_sidebar_state="collapsed")

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

# --- DEFINICJA KOLORÓW DLA MOTYWÓW ---
themes = {
    "Dark": {
        "bg_app": "#0a0b10",
        "bg_sidebar": "#07080d",
        "bg_card": "#111219",
        "bg_metric": "linear-gradient(135deg, #111219 0%, #17122a 100%)",
        "menu_bg": "linear-gradient(135deg, #111219 0%, #141521 100%)",
        "border": "#1d1f30",
        "text_primary": "#e4e5f0",
        "text_secondary": "#52547a",
        "accent": "#7c5bf6",
        "popover_bg": "#111219",
        "card_shadow": "0 4px 24px rgba(0,0,0,0.45)",
        "input_bg": "#0e0f18"
    },
    "Light": {
        "bg_app": "#f4f6fb",
        "bg_sidebar": "#ffffff",
        "bg_card": "#ffffff",
        "bg_metric": "linear-gradient(135deg, #ffffff 0%, #f0ecff 100%)",
        "menu_bg": "linear-gradient(135deg, #ffffff 0%, #f8f5ff 100%)",
        "border": "#dfe2f0",
        "text_primary": "#1a1c2e",
        "text_secondary": "#6b6e8e",
        "accent": "#6c47ff",
        "popover_bg": "#ffffff",
        "card_shadow": "0 4px 16px rgba(0,0,0,0.07)",
        "input_bg": "#ffffff"
    }
}

current_theme = themes[st.session_state.theme]

# --- INJECT CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=DM+Mono:wght@300;400;500&display=swap');

    * {{ font-family: 'DM Sans', -apple-system, sans-serif !important; }}
    h1, h2, h3, h4, h5, h6 {{ font-family: 'Syne', sans-serif !important; font-weight: 700 !important; }}
    [data-testid="stMetricValue"], .weekly-summary-value {{ font-family: 'DM Mono', monospace !important; }}

    /* Chrome Streamlit - ukrycie */
    [data-testid="stHeader"] {{ display: none !important; }}
    [data-testid="stSidebar"] {{ display: none !important; }}
    [data-testid="collapsedControl"] {{ display: none !important; }}

    /* Layout */
    .block-container {{ padding-top: 0.85rem; padding-bottom: 0rem; max-width: 98%; }}
    .stApp {{ background-color: {current_theme['bg_app']}; color: {current_theme['text_primary']}; }}

    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: {current_theme['border']}; border-radius: 10px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: {current_theme['accent']}; }}

    /* Aktywny przycisk nawigacyjny */
    button[kind="primary"] {{
        background: linear-gradient(135deg, {current_theme['accent']} 0%, {current_theme['accent']}bb 100%) !important;
        border: none !important;
        color: #ffffff !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.3px !important;
        box-shadow: 0 4px 20px {current_theme['accent']}45 !important;
        transition: all 0.2s !important;
    }}
    button[kind="primary"]:hover {{
        box-shadow: 0 6px 28px {current_theme['accent']}65 !important;
        transform: translateY(-1px) !important;
    }}

    /* Kontener menu nawigacyjnego */
    div.element-container:has(.nav-marker) + div.element-container > div[data-testid="stHorizontalBlock"] {{
        background: {current_theme['menu_bg']};
        padding: 10px 16px;
        border-radius: 16px;
        border: 1px solid {current_theme['border']};
        border-bottom: 2px solid {current_theme['accent']};
        box-shadow: {current_theme['card_shadow']};
        margin-bottom: 22px;
    }}

    /* Metryki */
    div[data-testid="stMetric"] {{
        background: {current_theme['bg_metric']};
        padding: 12px 14px !important;
        border-radius: 12px !important;
        border: 1px solid {current_theme['border']};
        color: {current_theme['text_primary']};
        box-shadow: {current_theme['card_shadow']};
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
        overflow: hidden;
    }}
    div[data-testid="stMetric"]::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, {current_theme['accent']}, transparent);
        border-radius: 12px 12px 0 0;
    }}
    div[data-testid="stMetric"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.25);
    }}
    [data-testid="stMetricValue"] {{
        font-family: 'DM Mono', monospace !important;
        font-size: 1.35rem !important;
        font-weight: 500 !important;
        padding-bottom: 0px !important;
        color: {current_theme['text_primary']} !important;
        letter-spacing: -1px;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 0.68rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.9px;
        color: {current_theme['text_secondary']} !important;
    }}

    /* Tekst */
    h1, h2, h3, h4, p, span, div, label {{ color: {current_theme['text_primary']}; }}
    .stMarkdown p {{ color: {current_theme['text_primary']} !important; }}

    /* Przyciski */
    div[data-testid="stButton"] button {{
        border: 1px solid {current_theme['border']};
        background-color: {current_theme['bg_card']};
        color: {current_theme['text_primary']};
        font-weight: 500;
        font-size: 0.84rem;
        letter-spacing: 0.1px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-radius: 9px !important;
        transition: all 0.18s;
    }}
    div[data-testid="stButton"] button:hover {{
        border-color: {current_theme['accent']};
        box-shadow: 0 4px 16px rgba(0,0,0,0.18);
        transform: translateY(-1px);
    }}

    /* Okrągłe przyciski ikonek w ostatniej kolumnie */
    div[data-testid="column"]:last-child div[data-testid="stButton"] button {{
        border-radius: 50% !important;
        width: 42px !important;
        height: 42px !important;
        margin-left: auto !important;
        padding: 0 !important;
    }}

    /* Fullscreen na obrazkach */
    [data-testid="stImage"] {{ overflow: visible !important; position: relative !important; }}
    button[title="View fullscreen"] {{
        display: flex !important; visibility: visible !important; opacity: 1 !important;
        background-color: rgba(0,0,0,0.65) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        width: 2.5rem !important; height: 2.5rem !important;
        right: 0.5rem !important; top: 0.5rem !important;
        z-index: 999999 !important; cursor: pointer !important;
        border-radius: 10px !important;
        align-items: center !important; justify-content: center !important;
        transition: all 0.2s !important;
    }}
    button[title="View fullscreen"]:hover {{
        background-color: rgba(0,0,0,0.9) !important;
        border-color: {current_theme['accent']} !important;
        transform: scale(1.05);
    }}
    button[title="View fullscreen"] svg {{ fill: white !important; width: 1.2rem !important; height: 1.2rem !important; }}

    /* Kafelki dni w kalendarzu */
    .day-card {{
        height: 80px; width: 100%;
        border-radius: 10px; padding: 6px 8px;
        display: flex; flex-direction: column; justify-content: space-between;
        border: 1px solid {current_theme['border']};
        transition: border-color 0.15s, box-shadow 0.15s;
        box-sizing: border-box;
        background-color: {current_theme['bg_card']};
        box-shadow: {current_theme['card_shadow']};
    }}
    .weekly-summary-title {{
        font-size: 0.6em; text-transform: uppercase;
        letter-spacing: 1.2px; opacity: 0.55; font-weight: 600;
    }}
    .weekly-summary-value {{
        font-family: 'DM Mono', monospace !important;
        font-size: 0.88em; font-weight: 500;
        line-height: 1.2; text-align: center; letter-spacing: -0.5px;
    }}

    /* === CALENDAR CELLS === */
    /* Kolumna z kafelkiem: position relative, żeby absolutnie pozycjonować popover */
    div[data-testid="column"]:has(.day-card) {{
        position: relative !important;
    }}

    /* Wrapper element-container popovera - absolutnie przyklejony do karty */
    div[data-testid="column"]:has(.day-card) div.element-container:has(div[data-testid="stPopover"]) {{
        position: absolute !important;
        top: 3px !important; left: 3px !important; right: 3px !important;
        height: 80px !important;
        z-index: 20 !important;
        margin: 0 !important;
        pointer-events: auto !important;
    }}

    /* Przycisk popovera - w pełni transparentna nakładka */
    div[data-testid="column"]:has(.day-card) div[data-testid="stPopover"] > button {{
        height: 80px !important; width: 100% !important;
        background: transparent !important;
        border: none !important; outline: none !important;
        box-shadow: none !important;
        padding: 0 !important; margin: 0 !important;
        border-radius: 10px !important;
        transition: background-color 0.15s, border 0.15s !important;
    }}

    /* Ukrycie "expand_more" i całej zawartości buttona */
    div[data-testid="column"]:has(.day-card) div[data-testid="stPopover"] > button * {{
        display: none !important;
        visibility: hidden !important;
    }}

    /* Hover */
    div[data-testid="column"]:has(.day-card) div[data-testid="stPopover"] > button:hover {{
        background-color: rgba(124, 91, 246, 0.08) !important;
        border: 1px solid {current_theme['accent']} !important;
    }}

    div[data-testid="column"] {{ padding: 3px !important; }}

    /* Popover body */
    div[data-testid="stPopoverBody"] {{
        border: 1px solid {current_theme['border']} !important;
        background-color: {current_theme['popover_bg']} !important;
        color: {current_theme['text_primary']} !important;
        min-width: 1200px !important; max-width: 95vw !important;
        border-radius: 16px !important;
        box-shadow: 0 24px 80px rgba(0,0,0,0.5) !important;
    }}

    /* Highlight box */
    .highlight-box {{
        background-color: {'rgba(124,91,246,0.07)' if st.session_state.theme == 'Dark' else '#f8f5ff'};
        padding: 12px 14px;
        border-radius: 9px;
        border-left: 3px solid {current_theme['accent']};
        border-top: 1px solid {current_theme['border']};
        border-right: 1px solid {current_theme['border']};
        border-bottom: 1px solid {current_theme['border']};
        margin-bottom: 10px;
        color: {current_theme['text_primary']};
        white-space: pre-wrap;
        font-size: 0.9rem;
        line-height: 1.55;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        background-color: {current_theme['bg_card']};
        color: {current_theme['text_primary']};
        border-radius: 10px;
        border: 1px solid {current_theme['border']};
        font-weight: 500;
    }}
    [data-testid="stExpander"] {{
        border: 1px solid {current_theme['border']} !important;
        border-radius: 12px !important;
        overflow: hidden;
    }}

    /* Inputy, selecty */
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"], input, textarea, select {{
        background-color: {current_theme['input_bg']} !important;
        color: {current_theme['text_primary']} !important;
        border-color: {current_theme['border']} !important;
        border-radius: 8px !important;
    }}
    div[data-baseweb="select"] svg, div[data-baseweb="input"] svg {{
        fill: {current_theme['text_secondary']} !important;
    }}

    /* Linia podziału */
    hr {{ border-color: {current_theme['border']} !important; opacity: 0.7; }}

    /* Alerty / info boxy */
    div[data-testid="stAlert"] {{ border-radius: 10px !important; }}
    </style>
""", unsafe_allow_html=True)

# --- CALENDAR FIX via JS (img onerror = guaranteed DOM access) ---
st.markdown("""
<img src="x" onerror="
(function(){
  var accent='{ACC}';
  function fix(){
    document.querySelectorAll('[data-testid=stPopover]').forEach(function(p){
      var col=p.closest('[data-testid=column]');
      if(!col||!col.querySelector('.day-card'))return;
      col.style.setProperty('position','relative','important');
      // find wrapper element (parent of stPopover)
      var ec=p.parentElement;
      while(ec&&ec!==col){
        if(ec.children.length===1&&ec.firstElementChild===p){
          Object.assign(ec.style,{position:'absolute',top:'3px',left:'3px',right:'3px',height:'80px',zIndex:'20',margin:'0',padding:'0'});
        }
        ec=ec.parentElement;
      }
      var btn=p.querySelector('button');
      if(btn){
        Object.assign(btn.style,{height:'80px',width:'100%',background:'transparent',border:'none',outline:'none',padding:'0',margin:'0',boxShadow:'none',borderRadius:'10px',cursor:'pointer',display:'block'});
        Array.from(btn.children).forEach(function(c){c.style.display='none';});
        btn.onmouseenter=function(){this.style.background='rgba(124,91,246,0.1)';this.style.border='1px solid #7c5bf6';};
        btn.onmouseleave=function(){this.style.background='transparent';this.style.border='none';};
      }
    });
  }
  new MutationObserver(function(){fix();}).observe(document.body,{childList:true,subtree:true});
  [0,200,600,1500,3000].forEach(function(t){setTimeout(fix,t);});
})();
" style="display:none">
""".replace('{ACC}', '#7c5bf6'), unsafe_allow_html=True)

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

            try:
                rr_str = str(row.get('rr', 0)).replace(',', '.')
                row['rr'] = float(rr_str) if rr_str else 0.0
            except:
                row['rr'] = 0.0

            row['account_type'] = row.get('account_type') if row.get('account_type') else 'Funded'

            bt_val = row.get('is_backtest', False)
            if isinstance(bt_val, str):
                row['is_backtest'] = bt_val.strip().lower() in ['true', '1', '1.0', 't', 'y', 'yes']
            else:
                row['is_backtest'] = bool(bt_val)

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

        for col in columns:
            if col not in new_row:
                new_row[col] = "" if col not in ['is_backtest', 'confluences', 'checklist', 'htf_links',
                                                 'ltf_links'] else False if col == 'is_backtest' else []

        new_row['is_backtest'] = bool(new_row.get('is_backtest', False))
        data_to_save.append(new_row)

    df = pd.DataFrame(data_to_save)
    df = df[columns]
    conn.update(data=df)


if 'all_trades' not in st.session_state:
    with st.spinner("Ładowanie bazy danych..."):
        st.session_state.all_trades = load_data_from_gsheets()

all_trades = st.session_state.all_trades


# --- FUNKCJE CALLBACK ---
def change_menu(opt):
    st.session_state.menu_nav = opt
    if opt != "📜 Trades History" and 'history_filter_date' in st.session_state:
        del st.session_state.history_filter_date


def go_to_edit_mode(index):
    st.session_state.editing_index = index
    if st.session_state.all_trades[index].get('is_backtest', False):
        st.session_state.menu_nav = "⏪ Backtesting"
        st.session_state.bt_nav_section = "Trade Entry"
    else:
        st.session_state.menu_nav = "📝 Daily Journal"


def delete_trade(index):
    if 0 <= index < len(st.session_state.all_trades):
        st.session_state.all_trades.pop(index)
        save_all_data(st.session_state.all_trades)


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


# Ujednolicony rendering zawartości transakcji (odporny na zepsute linki, całkowicie bez filtra http)
def render_trade_content(t):
    if str(t.get('notes', '')).strip(): st.info(f"**📝 Notes:**\n{t['notes']}")
    cm1, cm2 = st.columns(2)
    if str(t.get('model_mistakes', '')).strip(): cm1.error(f"**🚫 Model Mistakes:**\n{t['model_mistakes']}")
    if str(t.get('mental_mistakes', '')).strip(): cm2.warning(f"**🧠 Mental Mistakes:**\n{t['mental_mistakes']}")

    if t.get('confluences'): st.markdown(f"**🧩 Confluences:** {', '.join(t.get('confluences', []))}")

    st.markdown("---")
    c_htf, c_ltf = st.columns(2)
    with c_htf:
        valid_htf = [str(l).strip() for l in t.get('htf_links', []) if str(l).strip()]
        if valid_htf:
            st.markdown("#### 🏛️ HTF Links")
            for link in valid_htf:
                img_url = link if link.startswith("http") else "https://" + link
                try:
                    st.image(img_url, use_container_width=True)
                except Exception:
                    st.error("Nie udało się załadować podglądu (błędny link).")
                    st.markdown(f"🔗 [Otwórz link ręcznie]({img_url})")
    with c_ltf:
        valid_ltf = [str(l).strip() for l in t.get('ltf_links', []) if str(l).strip()]
        if valid_ltf:
            st.markdown("#### ⚡ LTF Links")
            for link in valid_ltf:
                img_url = link if link.startswith("http") else "https://" + link
                try:
                    st.image(img_url, use_container_width=True)
                except Exception:
                    st.error("Nie udało się załadować podglądu (błędny link).")
                    st.markdown(f"🔗 [Otwórz link ręcznie]({img_url})")

    # Kompatybilność wsteczna (stare notatki)
    if t.get('general_notes') or t.get('htf_desc') or t.get('ltf_desc') or t.get('mood'):
        st.markdown("---")
        if t.get('general_notes'): st.info(f"**📝 General Notes:**\n{t['general_notes']}")
        ch1, ch2 = st.columns(2)
        ch1.write(f"**🧠 Mood:** {t.get('mood', '-')}")
        if t.get('interfered') == 'Yes':
            ch2.markdown(f"**⚠️ Interfered:** :red[{t.get('interfered_how', '-')}]")
        else:
            ch2.write("**🛡️ Interfered:** No")
        st.write("---")
        ca, cb = st.columns(2)
        with ca:
            if t.get('htf_keypoints') or t.get('htf_desc'):
                st.markdown("#### 🏛️ HTF Analysis")
                if t.get('htf_keypoints'): st.markdown(
                    f"<div class='highlight-box'><b>HTF Key Points:</b><br>{t.get('htf_keypoints', 'N/A')}</div>",
                    unsafe_allow_html=True)
                if t.get('htf_desc'): st.write(f"**HTF Notes:** {t['htf_desc']}")
        with cb:
            if t.get('ltf_keypoints') or t.get('ltf_desc'):
                st.markdown("#### ⚡ LTF Analysis")
                if t.get('ltf_keypoints'): st.markdown(
                    f"<div class='highlight-box'><b>LTF Key Points:</b><br>{t.get('ltf_keypoints', 'N/A')}</div>",
                    unsafe_allow_html=True)
                if t.get('ltf_desc'): st.write(f"**LTF Notes:** {t['ltf_desc']}")


# Ujednolicony rendering detali w popupie
def render_trade_details(t):
    with st.container():
        h1, h2 = st.columns([3, 1])
        h1.markdown(f"### {t['asset']} ({t['direction']})")
        pnl_c = "green" if t['pnl'] > 0 else ("red" if t['pnl'] < 0 else "gray")
        h2.markdown(f"<h3 style='color:{pnl_c}'>{t['pnl']:+.1f} $</h3>", unsafe_allow_html=True)
        acc_label = t.get('account_type', 'Funded') if not t.get('is_backtest') else "Backtesting"
        st.caption(f"🕒 {t['time']} | 🔄 {t['trade_type']} | 🎯 {t['outcome']} | 💼 {acc_label} | RR: {t.get('rr', 0.0)}")

        render_trade_content(t)


# --- UI: TOP NAVBAR & WŁASNE MENU ---
head_col1, head_col2 = st.columns([20, 1])
with head_col1:
    st.markdown(
        f"""<div style='display:flex;align-items:center;gap:10px;margin-top:-8px;margin-bottom:2px;'>
            <div style='width:34px;height:34px;background:linear-gradient(135deg,{current_theme['accent']},{current_theme['accent']}88);border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0;'>📘</div>
            <h2 style='margin:0;font-size:1.35rem;font-weight:800;letter-spacing:-0.5px;color:{current_theme['text_primary']};line-height:1;'>NQPaneksu <span style='color:{current_theme['accent']};'>Journal</span></h2>
        </div>""",
        unsafe_allow_html=True)
with head_col2:
    btn_icon = "☀️" if st.session_state.theme == "Dark" else "🌙"
    if st.button(btn_icon, key="theme_toggle"):
        st.session_state.theme = "Light" if st.session_state.theme == "Dark" else "Dark"
        st.rerun()

# Znacznik HTML do zaczepienia reguły CSS kolorującej tło menu nawigacyjnego
st.markdown('<div class="nav-marker"></div>', unsafe_allow_html=True)
menu_options = ["📊 Dashboard", "📝 Daily Journal", "📜 Trades History", "⏪ Backtesting", "🗓️ Yearly Calendar",
                "📓 Trade Notes"]
nav_cols = st.columns(len(menu_options))
for i, option in enumerate(menu_options):
    is_active = st.session_state.menu_nav == option
    # Używamy on_click zamiast manualnego st.rerun(), żeby zapobiec bugom z utratą stanu sesji!
    nav_cols[i].button(option, key=f"nav_{i}", use_container_width=True, type="primary" if is_active else "secondary",
                       on_click=change_menu, args=(option,))

menu = st.session_state.menu_nav

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    c_t, c_f, c_y, c_m = st.columns([1.5, 2.5, 1, 1])
    c_t.markdown(f"<h3 style='margin-top:-12px;font-size:1.05rem;font-weight:700;letter-spacing:-0.2px;'>📊 Dashboard</h3>", unsafe_allow_html=True)
    account_filter = c_f.radio("Filter", ["All", "Funded", "Evaluation"], horizontal=True, label_visibility="collapsed")
    view_year = c_y.selectbox("Year", range(2000, 2031), index=range(2000, 2031).index(datetime.now().year),
                              label_visibility="collapsed")
    view_month = c_m.selectbox("Month", range(1, 13), index=datetime.now().month - 1, label_visibility="collapsed")

    if all_trades:
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

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        cal = calendar.monthcalendar(view_year, view_month)

        cols = st.columns(7)
        days_header = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, d in enumerate(days_header):
            cols[i].markdown(
                f"<center><b style='color:{current_theme['text_secondary']}; font-size: 0.85em;'>{d}</b></center>",
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
                if i == 6:
                    bg_c, bor_c, txt_c, pnl_c = current_theme['bg_card'], current_theme['border'], current_theme[
                        'text_primary'], current_theme['text_secondary']
                    if weekly_pnl > 0:
                        bg_c, bor_c, pnl_c = (
                            "rgba(31, 214, 165, 0.12)" if st.session_state.theme == "Dark" else "#dcfce7"), (
                            "#1fd6a5" if st.session_state.theme == "Dark" else "#059669"), (
                            "#1fd6a5" if st.session_state.theme == "Dark" else "#065f46")
                    elif weekly_pnl < 0:
                        bg_c, bor_c, pnl_c = (
                            "rgba(244, 63, 94, 0.12)" if st.session_state.theme == "Dark" else "#fee2e2"), (
                            "#f43f5e" if st.session_state.theme == "Dark" else "#e11d48"), (
                            "#f43f5e" if st.session_state.theme == "Dark" else "#9f1239")

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
                                for t in sunday_trades: render_trade_details(t)
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
                                b_bg = "#1d1e30" if st.session_state.theme == "Dark" else "#ede9fe"
                                b_txt = "#a78bfa" if st.session_state.theme == "Dark" else "#5b21b6"
                                badge = f"<span style='font-size:0.75em;color:{b_txt};background:{b_bg};padding:1px 4px;border-radius:4px;'>{valid_trades_count}x</span>"

                            if has_no_trade and day_pnl == 0:
                                bg_c, bor_c, pnl_c, pnl_disp = (
                                    "rgba(142, 142, 147, 0.15)" if st.session_state.theme == "Dark" else "#f3f4f6"), "#8e8e93", "#8e8e93", "⚪ No Trade"
                            elif day_pnl > 0:
                                bg_c, bor_c, pnl_c, pnl_disp = (
                                    "rgba(31, 214, 165, 0.12)" if st.session_state.theme == "Dark" else "#dcfce7"), (
                                    "#1fd6a5" if st.session_state.theme == "Dark" else "#059669"), (
                                    "#1fd6a5" if st.session_state.theme == "Dark" else "#065f46"), f"🟢 +{day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"
                            elif day_pnl < 0:
                                bg_c, bor_c, pnl_c, pnl_disp = (
                                    "rgba(244, 63, 94, 0.12)" if st.session_state.theme == "Dark" else "#fee2e2"), (
                                    "#f43f5e" if st.session_state.theme == "Dark" else "#e11d48"), (
                                    "#f43f5e" if st.session_state.theme == "Dark" else "#9f1239"), f"🔴 {day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"
                            else:
                                bg_c, bor_c, pnl_c, pnl_disp = "rgba(142, 142, 147, 0.15)", "#8e8e93", "#8e8e93", f"⚪ {day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"

                        card_html = f"""<div class="day-card" style="background-color: {bg_c}; border-color: {bor_c};"><div style="display:flex;justify-content:space-between;align-items:flex-start;"><div style="font-weight:bold;font-size:0.95em;color:{txt_c};">{day}</div><div>{badge}</div></div><div style="font-weight:bold;font-size:0.85em;color:{pnl_c};text-align:center;line-height:1.1;margin-top:-5px;">{pnl_disp}</div></div>"""
                        cols[i].markdown(card_html, unsafe_allow_html=True)

                        with cols[i].popover(label=" ", use_container_width=True):
                            if day_trades:
                                st.header(f"📅 {curr_date.strftime('%A, %d %B %Y')}")
                                st.button(f"🔎 Go to History ({curr_date})", key=f"gth_{curr_date}",
                                          use_container_width=True, on_click=go_to_history_for_day, args=(curr_date,))
                                st.markdown(
                                    f"**Daily Net PnL:** :{'green' if day_pnl > 0 else 'red'}[{day_pnl:+.1f} $] | **RR:** {day_rr:.2f}")
                                st.divider()
                                for t in day_trades: render_trade_details(t)
                            else:
                                st.write("Brak wpisów.")
    else:
        st.info("Brak danych.")

# --- DAILY JOURNAL ---
elif menu == "📝 Daily Journal":
    st.markdown(f"<h3 style='margin-top:-12px;font-size:1.05rem;font-weight:700;letter-spacing:-0.2px;'>📝 Daily Trade Entry</h3>", unsafe_allow_html=True)

    if 'editing_index' not in st.session_state: st.session_state.editing_index = None
    curr = all_trades[st.session_state.editing_index] if st.session_state.editing_index is not None and not all_trades[
        st.session_state.editing_index].get('is_backtest') else None

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
            "checklist": [False] * 6,
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
        st.session_state.dj_temp_conf = []
        st.success("Zapisano!")
        st.session_state.navigate_to_history = True
        st.rerun()

# --- BACKTESTING ---
elif menu == "⏪ Backtesting":
    bt_section_idx = 1 if st.session_state.get('bt_nav_section') == "Trade Entry" else 0

    bt_trades = [t for t in all_trades if t.get('is_backtest', True)]
    df_bt = pd.DataFrame(bt_trades)
    if not df_bt.empty:
        df_bt['date'] = pd.to_datetime(df_bt['date'])

    c_t, c_r, c_y, c_m = st.columns([1.5, 2.5, 1, 1])
    c_t.markdown(f"<h3 style='margin-top:-12px;font-size:1.05rem;font-weight:700;letter-spacing:-0.2px;'>⏪ Backtesting</h3>", unsafe_allow_html=True)
    bt_menu = c_r.radio("Sekcja:", ["Dashboard", "Trade Entry"], horizontal=True, index=bt_section_idx,
                        label_visibility="collapsed", key="bt_main_nav")
    st.session_state.bt_nav_section = bt_menu

    if bt_menu == "Dashboard":
        view_year = c_y.selectbox("Year", range(2000, 2031), index=range(2000, 2031).index(datetime.now().year),
                                  label_visibility="collapsed", key="bt_cal_y")
        view_month = c_m.selectbox("Month", range(1, 13), index=datetime.now().month - 1, label_visibility="collapsed",
                                   key="bt_cal_m")

    if bt_menu == "Dashboard":
        if not df_bt.empty:
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
            c7.metric("Days", unique_days)

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            cal = calendar.monthcalendar(view_year, view_month)

            cols = st.columns(7)
            days_header = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for i, d in enumerate(days_header):
                cols[i].markdown(
                    f"<center><b style='color:{current_theme['text_secondary']}; font-size: 0.85em;'>{d}</b></center>",
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
                                "rgba(31, 214, 165, 0.12)" if st.session_state.theme == "Dark" else "#dcfce7"), (
                                "#1fd6a5" if st.session_state.theme == "Dark" else "#059669"), (
                                "#1fd6a5" if st.session_state.theme == "Dark" else "#065f46")
                        elif weekly_pnl < 0:
                            bg_c, bor_c, pnl_c = (
                                "rgba(244, 63, 94, 0.12)" if st.session_state.theme == "Dark" else "#fee2e2"), (
                                "#f43f5e" if st.session_state.theme == "Dark" else "#e11d48"), (
                                "#f43f5e" if st.session_state.theme == "Dark" else "#9f1239")

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
                                    for t in sunday_trades: render_trade_details(t)
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
                                    badge = f"<span style='font-size:0.75em;color:{b_txt};background:{b_bg};padding:1px 4px;border-radius:4px;'>{valid_trades_count}x</span>"

                                if has_no_trade and day_pnl == 0:
                                    bg_c, bor_c, pnl_c, pnl_disp = (
                                        "rgba(142, 142, 147, 0.15)" if st.session_state.theme == "Dark" else "#f3f4f6"), "#8e8e93", "#8e8e93", "⚪ No Trade"
                                elif day_pnl > 0:
                                    bg_c, bor_c, pnl_c, pnl_disp = (
                                        "rgba(31, 214, 165, 0.12)" if st.session_state.theme == "Dark" else "#dcfce7"), (
                                        "#1fd6a5" if st.session_state.theme == "Dark" else "#059669"), (
                                        "#1fd6a5" if st.session_state.theme == "Dark" else "#065f46"), f"🟢 +{day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"
                                elif day_pnl < 0:
                                    bg_c, bor_c, pnl_c, pnl_disp = (
                                        "rgba(244, 63, 94, 0.12)" if st.session_state.theme == "Dark" else "#fee2e2"), (
                                        "#f43f5e" if st.session_state.theme == "Dark" else "#e11d48"), (
                                        "#f43f5e" if st.session_state.theme == "Dark" else "#9f1239"), f"🔴 {day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"
                                else:
                                    bg_c, bor_c, pnl_c, pnl_disp = "rgba(142, 142, 147, 0.15)", "#8e8e93", "#8e8e93", f"⚪ {day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"

                            card_html = f"""<div class="day-card" style="background-color: {bg_c}; border-color: {bor_c};"><div style="display:flex;justify-content:space-between;align-items:flex-start;"><div style="font-weight:bold;font-size:0.95em;color:{txt_c};">{day}</div><div>{badge}</div></div><div style="font-weight:bold;font-size:0.85em;color:{pnl_c};text-align:center;line-height:1.1;margin-top:-5px;">{pnl_disp}</div></div>"""
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
                                    for t in day_trades: render_trade_details(t)
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
                "checklist": [False] * 6,
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
    st.markdown(f"<h3 style='margin-top:-12px;font-size:1.05rem;font-weight:700;letter-spacing:-0.2px;'>📜 Trade History</h3>", unsafe_allow_html=True)

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

            pnl_sign = "🟢" if float(t['pnl']) > 0 else ("🔴" if float(t['pnl']) < 0 else "⚪")
            with st.expander(
                    f"{pnl_sign}  #{idx + 1} · {t['date']} · {t['asset']} · {t.get('direction', 'Long')} · {t['pnl']:+.1f} ${acc_label}"):
                b1, b2, _ = st.columns([1, 1, 4])
                b1.button(f"✏️ Edit #{idx + 1}", key=f"ed_{idx}", on_click=go_to_edit_mode, args=(idx,),
                          use_container_width=True)
                b2.button(f"🗑️ Delete", key=f"del_{idx}", on_click=delete_trade, args=(idx,), use_container_width=True)

                render_trade_content(t)
    else:
        st.info("Brak tradów w historii.")

# --- YEARLY CALENDAR ---
elif menu == "🗓️ Yearly Calendar":
    c_t, c_y, c_type = st.columns([1.5, 1, 2.5])
    c_t.markdown(f"<h3 style='margin-top:-12px;font-size:1.05rem;font-weight:700;letter-spacing:-0.2px;'>🗓️ Yearly Calendar</h3>", unsafe_allow_html=True)
    view_year = c_y.selectbox("Select Year", range(2000, 2031), index=range(2000, 2031).index(datetime.now().year),
                              label_visibility="collapsed", key="yc_view_year")
    yc_type = c_type.radio("Type:", ["Live Trading", "Backtesting"], horizontal=True, label_visibility="collapsed",
                           key="yc_type")

    if all_trades:
        is_bt = True if yc_type == "Backtesting" else False
        filtered_trades = [t for t in all_trades if t.get('is_backtest', False) == is_bt]

        for view_month in range(1, 13):
            st.markdown(
                f"<h4 style='text-align: center; color: {current_theme['accent']}; margin-top: 20px;'>{calendar.month_name[view_month]} {view_year}</h4>",
                unsafe_allow_html=True)
            cal = calendar.monthcalendar(view_year, view_month)

            cols = st.columns(7)
            days_header = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for i, d in enumerate(days_header):
                cols[i].markdown(
                    f"<center><b style='color:{current_theme['text_secondary']}; font-size: 0.85em;'>{d}</b></center>",
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
                    if i == 6:
                        bg_c, bor_c, txt_c, pnl_c = current_theme['bg_card'], current_theme['border'], current_theme[
                            'text_primary'], current_theme['text_secondary']
                        if weekly_pnl > 0:
                            bg_c, bor_c, pnl_c = (
                                "rgba(31, 214, 165, 0.12)" if st.session_state.theme == "Dark" else "#dcfce7"), (
                                "#1fd6a5" if st.session_state.theme == "Dark" else "#059669"), (
                                "#1fd6a5" if st.session_state.theme == "Dark" else "#065f46")
                        elif weekly_pnl < 0:
                            bg_c, bor_c, pnl_c = (
                                "rgba(244, 63, 94, 0.12)" if st.session_state.theme == "Dark" else "#fee2e2"), (
                                "#f43f5e" if st.session_state.theme == "Dark" else "#e11d48"), (
                                "#f43f5e" if st.session_state.theme == "Dark" else "#9f1239")

                        card_html = f"""<div class="day-card" style="background-color: {bg_c}; border-color: {bor_c}; justify-content: center; align-items: center;"><div class="weekly-summary-title" style="color: {txt_c};">Weekly PnL</div><div class="weekly-summary-value" style="color: {pnl_c}; text-align: center;">{weekly_pnl:+.1f} $<br><span style="font-size: 0.85em; color: {txt_c}; font-weight: normal;">RR: {weekly_rr:.2f}</span></div></div>"""
                        cols[i].markdown(card_html, unsafe_allow_html=True)

                        curr_date_sunday = date(view_year, view_month, day) if day != 0 else (
                            week_end_date if ref_day else None)
                        with cols[i].popover(label=" ", use_container_width=True):
                            if curr_date_sunday:
                                st.header(f"📅 {curr_date_sunday.strftime('%A, %d %B %Y')}")
                                st.button(f"🔎 Go to History ({curr_date_sunday})",
                                          key=f"gth_sun_yc_{i}_{day}_{view_month}_{view_year}",
                                          use_container_width=True, on_click=go_to_history_for_day,
                                          args=(curr_date_sunday,))
                                st.divider()
                                sunday_trades = [t for t in filtered_trades if t['date'] == str(curr_date_sunday)]
                                if sunday_trades:
                                    for t in sunday_trades: render_trade_details(t)
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

                            bg_c, bor_c, txt_c, pnl_c = current_theme['bg_card'], current_theme['border'], \
                            current_theme['text_primary'], current_theme['text_secondary']
                            pnl_disp, badge = "", ""

                            if day_trades:
                                if valid_trades_count > 0:
                                    b_bg = "#2d2d3a" if st.session_state.theme == "Dark" else "#e0e7ff"
                                    b_txt = "#ccc" if st.session_state.theme == "Dark" else "#4338ca"
                                    badge = f"<span style='font-size:0.75em;color:{b_txt};background:{b_bg};padding:1px 4px;border-radius:4px;'>{valid_trades_count}x</span>"

                                if has_no_trade and day_pnl == 0:
                                    bg_c, bor_c, pnl_c, pnl_disp = (
                                        "rgba(142, 142, 147, 0.15)" if st.session_state.theme == "Dark" else "#f3f4f6"), "#8e8e93", "#8e8e93", "⚪ No Trade"
                                elif day_pnl > 0:
                                    bg_c, bor_c, pnl_c, pnl_disp = (
                                        "rgba(31, 214, 165, 0.12)" if st.session_state.theme == "Dark" else "#dcfce7"), (
                                        "#1fd6a5" if st.session_state.theme == "Dark" else "#059669"), (
                                        "#1fd6a5" if st.session_state.theme == "Dark" else "#065f46"), f"🟢 +{day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"
                                elif day_pnl < 0:
                                    bg_c, bor_c, pnl_c, pnl_disp = (
                                        "rgba(244, 63, 94, 0.12)" if st.session_state.theme == "Dark" else "#fee2e2"), (
                                        "#f43f5e" if st.session_state.theme == "Dark" else "#e11d48"), (
                                        "#f43f5e" if st.session_state.theme == "Dark" else "#9f1239"), f"🔴 {day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"
                                else:
                                    bg_c, bor_c, pnl_c, pnl_disp = "rgba(142, 142, 147, 0.15)", "#8e8e93", "#8e8e93", f"⚪ {day_pnl:.1f} $<br><span style='font-size:0.85em;color:{txt_c};font-weight:normal;'>RR: {day_rr:.2f}</span>"

                            card_html = f"""<div class="day-card" style="background-color: {bg_c}; border-color: {bor_c};"><div style="display:flex;justify-content:space-between;align-items:flex-start;"><div style="font-weight:bold;font-size:0.95em;color:{txt_c};">{day}</div><div>{badge}</div></div><div style="font-weight:bold;font-size:0.85em;color:{pnl_c};text-align:center;line-height:1.1;margin-top:-5px;">{pnl_disp}</div></div>"""
                            cols[i].markdown(card_html, unsafe_allow_html=True)

                            with cols[i].popover(label=" ", use_container_width=True):
                                if day_trades:
                                    st.header(f"📅 {curr_date.strftime('%A, %d %B %Y')}")
                                    st.button(f"🔎 Go to History ({curr_date})",
                                              key=f"gth_yc_{curr_date}_{view_month}_{view_year}",
                                              use_container_width=True, on_click=go_to_history_for_day,
                                              args=(curr_date,))
                                    st.markdown(
                                        f"**Daily Net PnL:** :{'green' if day_pnl > 0 else 'red'}[{day_pnl:+.1f} $] | **RR:** {day_rr:.2f}")
                                    st.divider()
                                    for t in day_trades: render_trade_details(t)
                                else:
                                    st.write("Brak wpisów.")
            st.markdown("<hr style='margin: 30px 0; border-color: " + current_theme['border'] + ";'>",
                        unsafe_allow_html=True)
    else:
        st.info("Brak danych.")

# --- TRADE NOTES ---
elif menu == "📓 Trade Notes":
    st.markdown(f"<h3 style='margin-top:-12px;font-size:1.05rem;font-weight:700;letter-spacing:-0.2px;'>📓 Trade Notes</h3>", unsafe_allow_html=True)

    notes_type = st.radio("Wybierz typ wpisów:", ["Live Trading", "Backtesting"], horizontal=True)

    if all_trades:
        is_bt_filter = True if notes_type == "Backtesting" else False
        filtered_trades = [t for t in all_trades if t.get('is_backtest', False) == is_bt_filter]

        trades_with_notes = [
            t for t in filtered_trades
            if str(t.get('notes', '')).strip()
               or str(t.get('model_mistakes', '')).strip()
               or str(t.get('mental_mistakes', '')).strip()
               or t.get('confluences')
               or str(t.get('general_notes', '')).strip()
               or str(t.get('htf_desc', '')).strip()
               or str(t.get('ltf_desc', '')).strip()
               or any(str(link).strip() for link in t.get('htf_links', []))
               or any(str(link).strip() for link in t.get('ltf_links', []))
        ]

        trades_with_notes = sorted(trades_with_notes, key=lambda x: x.get('date', ''), reverse=True)

        st.divider()
        if trades_with_notes:
            st.write(f"Wyświetlam **{len(trades_with_notes)}** wpisów z notatkami.")
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

            for t in trades_with_notes:
                with st.container():
                    pnl_val_n = float(t.get('pnl', 0))
                    pnl_c = "#22d3a5" if pnl_val_n > 0 else ("#f43f5e" if pnl_val_n < 0 else "#6b6e8e")
                    pnl_sign_n = "🟢" if pnl_val_n > 0 else ("🔴" if pnl_val_n < 0 else "⚪")
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:12px;padding:10px 14px;background:{current_theme['bg_card']};border:1px solid {current_theme['border']};border-left:3px solid {current_theme['accent']};border-radius:10px;margin-bottom:8px;'>"
                        f"<span style='font-size:1.1rem;'>{pnl_sign_n}</span>"
                        f"<div><div style='font-weight:700;font-size:0.95rem;color:{current_theme['text_primary']};'>📅 {t.get('date')} &nbsp;·&nbsp; {t.get('asset')} ({t.get('direction', '-')})</div>"
                        f"<div style='font-size:0.8rem;color:{current_theme['text_secondary']};margin-top:2px;'>PnL: <span style='color:{pnl_c};font-weight:600;'>{pnl_val_n:+.1f} $</span> &nbsp;·&nbsp; RR: {t.get('rr', 0.0)}</div></div>"
                        f"</div>",
                        unsafe_allow_html=True)

                    render_trade_content(t)

                    st.markdown("<hr style='border-color: " + current_theme['border'] + "; opacity:0.5;'>", unsafe_allow_html=True)
        else:
            st.info(f"Brak notatek dla kategorii: {notes_type}.")
    else:
        st.info("Brak danych w dzienniku.")