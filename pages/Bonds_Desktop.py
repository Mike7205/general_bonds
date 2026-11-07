import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests
from io import StringIO
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(layout="wide", page_title="Obligacje Skarbowe", page_icon="🇵🇱")
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #a8d4e8; }
    .stApp { background-color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# ── Polish Government Bonds catalogue ────────────────────────────────────────
BONDS = {
    # Wholesale – mają notowania na Stooq
    "DS0436": {"name": "DS0436", "type": "fixed", "maturity": "2036-04-25", "coupon": 6.00, "listed": True, "stooq": "DS0436.PL"},
    "DS1034": {"name": "DS1034", "type": "fixed", "maturity": "2034-10-25", "coupon": 5.75, "listed": True, "stooq": "DS1034.PL"},
    "PS1031": {"name": "PS1031", "type": "fixed", "maturity": "2031-10-25", "coupon": 4.75, "listed": True, "stooq": "PS1031.PL"},
    "OK0129": {"name": "OK0129", "type": "zero", "maturity": "2029-01-25", "coupon": 0.0, "listed": True, "stooq": "OK0129.PL"},
    "NZ0332": {"name": "NZ0332", "type": "floating", "maturity": "2032-03-25", "coupon": None, "listed": True, "stooq": "NZ0332.PL"},
    "IZ0836": {"name": "IZ0836", "type": "inflation", "maturity": "2036-08-25", "margin": 1.5, "listed": True, "stooq": "IZ0836.PL"},
    # Retail – brak notowań wtórnych
    "OTS0127": {"name": "OTS0127 (3M)", "type": "fixed_retail", "maturity": "2027-01", "coupon": 2.00, "listed": False},
    "ROR1027": {"name": "ROR1027 (1Y)", "type": "floating_retail", "maturity": "2027-10", "coupon": 4.00, "margin_nbp": 0.0, "listed": False},
    "DOR1028": {"name": "DOR1028 (2Y)", "type": "floating_retail", "maturity": "2028-10", "coupon": 4.15, "margin_nbp": 0.15, "listed": False},
    "TOS1029": {"name": "TOS1029 (3Y)", "type": "fixed_retail", "maturity": "2029-10", "coupon": 4.40, "listed": False},
    "COI1030": {"name": "COI1030 (4Y)", "type": "inflation", "maturity": "2030-10", "margin": 1.50, "first_year": 4.75, "listed": False},
    "EDO1036": {"name": "EDO1036 (10Y)", "type": "inflation", "maturity": "2036-10", "margin": 2.00, "first_year": 5.35, "listed": False},
    "ROS1032": {"name": "ROS1032 (6Y family)", "type": "inflation", "maturity": "2032-10", "margin": 2.00, "first_year": 5.00, "listed": False},
    "ROD1038": {"name": "ROD1038 (12Y family)", "type": "inflation", "maturity": "2038-10", "margin": 2.50, "first_year": 5.60, "listed": False},
}

PLANNED_AUCTIONS = [
    {"date": "2026-10-14", "settlement": "2026-10-16", "series": "OK0129 / PS1031 / NZ0332 / DS0436", "supply_mln": "7 000–12 000"},
    {"date": "2026-10-22", "settlement": "2026-10-26", "series": "OK0129 / PS1031 / NZ0332 / DS0436", "supply_mln": "8 000–14 000"},
    {"date": "2026-10-28", "settlement": "2026-10-30", "series": "OK0129 / PS1031 / NZ0332 / DS0436", "supply_mln": "7 000–12 000"},
    {"date": "2026-11-12", "settlement": "2026-11-16", "series": "TBD (MF monthly plan)", "supply_mln": "TBD"},
    {"date": "2026-11-18", "settlement": "2026-11-20", "series": "TBD", "supply_mln": "TBD"},
    {"date": "2026-11-25", "settlement": "2026-11-27", "series": "TBD", "supply_mln": "TBD"},
    {"date": "2026-12-09", "settlement": "2026-12-11", "series": "TBD", "supply_mln": "TBD"},
    {"date": "2026-12-16", "settlement": "2026-12-18", "series": "TBD", "supply_mln": "TBD"},
    {"date": "2027-01-09", "settlement": "2027-01-13", "series": "TBD", "supply_mln": "TBD"},
]

CURRENT_CPI = 4.2
NBP_REF_RATE = 3.75

st.title("Obligacje Skarbowe (Polska)")

with st.sidebar:
    st.header("Wybierz obligację")
    listed = [k for k, v in BONDS.items() if v.get("listed", False)]
    retail = [k for k, v in BONDS.items() if not v.get("listed", False)]
    options = listed + ["---"] + retail
    selected = st.radio("Instrument", options, label_visibility="collapsed")
    st.divider()
    st.subheader("Planowane przetargi (najbliższe ~3 kwartały)")
    planned_df = pd.DataFrame(PLANNED_AUCTIONS)
    st.dataframe(planned_df, use_container_width=True, hide_index=True, height=250)
    st.caption("Źródło: MF – kalendarz i miesięczne plany podaży SPW. Seria i podaż mogą się zmienić.")

if selected == "---" or selected not in BONDS:
    st.info("Wybierz obligację z listy po lewej.")
    st.stop()

bond = BONDS[selected]
st.subheader(f"{bond['name']}  |  typ: {bond['type']}  |  wykup: {bond['maturity']}")

# Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Typ", bond["type"].replace("_", " ").title())
with col2:
    if "coupon" in bond and bond["coupon"] is not None:
        st.metric("Kupon / 1. okres", f"{bond['coupon']:.2f}%")
    else:
        st.metric("Kupon", "zmienny / indeksowany")
with col3:
    if bond["type"] == "inflation":
        margin = bond.get("margin", 0)
        st.metric("Marża nad inflacją", f"+{margin:.2f} pp")
        st.caption(f"Aktualna inflacja (CPI) ≈ {CURRENT_CPI:.1f}%  →  bieżące oprocentowanie ≈ {CURRENT_CPI + margin:.2f}%")

st.subheader("Cena i rentowność")

@st.cache_data(ttl=3600)
def fetch_stooq(ticker: str):
    """Pobiera dane historyczne ze Stooq (format CSV)."""
    if not ticker:
        return None
    url = f"https://stooq.pl/q/d/l/?s={ticker.lower()}&i=d"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        if "Brak danych" in r.text or len(r.text) < 50:
            return None
        df = pd.read_csv(StringIO(r.text))
        if df.empty or "Date" not in df.columns:
            return None
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").dropna(subset=["Close"])
        return df
    except Exception as e:
        st.warning(f"Błąd pobierania ze Stooq ({ticker}): {e}")
        return None

price_df = None
if bond.get("listed") and bond.get("stooq"):
    price_df = fetch_stooq(bond["stooq"])

if price_df is not None and not price_df.empty:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35],
                        subplot_titles=("Cena (Stooq)", "Przybliżona rentowność (YTM proxy)"))
    fig.add_trace(go.Scatter(x=price_df["Date"], y=price_df["Close"], name="Cena", line=dict(color="#1f77b4")), row=1, col=1)

    # Prosty YTM proxy
    if bond.get("coupon") and bond.get("maturity") and bond["type"] == "fixed":
        try:
            mat = pd.to_datetime(bond["maturity"])
            years_left = max(0.5, (mat - pd.Timestamp.today()).days / 365.25)
            ytm_proxy = (bond["coupon"] / (price_df["Close"] / 100)) + ((100 - price_df["Close"]) / (price_df["Close"] * years_left)) * 100
            fig.add_trace(go.Scatter(x=price_df["Date"], y=ytm_proxy, name="YTM proxy %", line=dict(color="#d62728")), row=2, col=1)
        except Exception:
            pass

    fig.update_layout(height=520, hovermode="x unified", showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Źródło danych: Stooq.pl ({bond.get('stooq')})")
else:
    st.info("Brak danych historycznych ze Stooq dla tej serii (typowe dla obligacji detalicznych).")
    fig = go.Figure()
    fig.add_annotation(
        text="Obligacje detaliczne nie mają ciągłego notowania wtórnego<br>na Stooq / Catalyst jak serie hurtowe.",
        xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14)
    )
    fig.update_layout(height=280, title="Brak notowań historycznych")
    st.plotly_chart(fig, use_container_width=True)

# Sekcja inflacyjna
if bond["type"] == "inflation":
    st.subheader("Obligacja indeksowana inflacją")
    margin = bond.get("margin", 0)
    first = bond.get("first_year", None)
    c1, c2, c3 = st.columns(3)
    c1.metric("Aktualna inflacja CPI (przybliżenie)", f"{CURRENT_CPI:.1f}%")
    c2.metric("Marża", f"+{margin:.2f} pp")
    c3.metric("Bieżące oprocentowanie (szacunek)", f"{CURRENT_CPI + margin:.2f}%")
    if first:
        st.caption(f"Pierwszy okres odsetkowy: {first:.2f}%. Kolejne okresy: inflacja + {margin:.2f} pp.")
    st.markdown("""
    **Jak to działa:**  
    Po pierwszym okresie oprocentowanie = wskaźnik inflacji (CPI) + stała marża.  
    Dzięki temu realna stopa procentowa jest chroniona przed wzrostem inflacji.
    """)

# Tabela parametrów
st.subheader("Podstawowe parametry")
info = {
    "Seria": bond["name"],
    "Typ oprocentowania": bond["type"],
    "Termin wykupu": bond["maturity"],
    "Notowana na giełdzie (Catalyst)": "Tak" if bond.get("listed") else "Nie (detaliczna / oszczędnościowa)",
}
if "coupon" in bond and bond["coupon"] is not None:
    info["Kupon / 1. okres (%)"] = bond["coupon"]
if bond["type"] == "inflation":
    info["Marża nad inflacją (pp)"] = bond.get("margin")
if bond.get("stooq"):
    info["Ticker Stooq"] = bond["stooq"]

st.table(pd.Series(info).to_frame("Wartość"))

st.caption("© 2026 – dane ze Stooq.pl dla serii hurtowych. Obligacje detaliczne nie mają ciągłych notowań wtórnych. Inflacja i stawki NBP należy aktualizować.")
