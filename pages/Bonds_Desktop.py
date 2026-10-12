import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
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
# Listed on Catalyst / GPW (wholesale + some retail-related) + current retail offer + planned auctions

BONDS = {
    # Wholesale fixed / zero / floating (examples of currently active series)
    "DS0436": {"name": "DS0436", "type": "fixed", "maturity": "2036-04-25", "coupon": 6.00, "listed": True, "yticker": None},
    "DS1034": {"name": "DS1034", "type": "fixed", "maturity": "2034-10-25", "coupon": 5.75, "listed": True, "yticker": None},
    "PS1031": {"name": "PS1031", "type": "fixed", "maturity": "2031-10-25", "coupon": 4.75, "listed": True, "yticker": None},
    "OK0129": {"name": "OK0129", "type": "zero", "maturity": "2029-01-25", "coupon": 0.0, "listed": True, "yticker": None},
    "NZ0332": {"name": "NZ0332", "type": "floating", "maturity": "2032-03-25", "coupon": None, "listed": True, "yticker": None},
    "IZ0836": {"name": "IZ0836", "type": "inflation", "maturity": "2036-08-25", "margin": 1.5, "listed": True, "yticker": None},
    # Retail savings bonds (current October 2026 offer)
    "OTS0127": {"name": "OTS0127 (3M)", "type": "fixed_retail", "maturity": "2027-01", "coupon": 2.00, "listed": False, "yticker": None},
    "ROR1027": {"name": "ROR1027 (1Y)", "type": "floating_retail", "maturity": "2027-10", "coupon": 4.00, "margin_nbp": 0.0, "listed": False},
    "DOR1028": {"name": "DOR1028 (2Y)", "type": "floating_retail", "maturity": "2028-10", "coupon": 4.15, "margin_nbp": 0.15, "listed": False},
    "TOS1029": {"name": "TOS1029 (3Y)", "type": "fixed_retail", "maturity": "2029-10", "coupon": 4.40, "listed": False},
    "COI1030": {"name": "COI1030 (4Y)", "type": "inflation", "maturity": "2030-10", "margin": 1.50, "first_year": 4.75, "listed": False},
    "EDO1036": {"name": "EDO1036 (10Y)", "type": "inflation", "maturity": "2036-10", "margin": 2.00, "first_year": 5.35, "listed": False},
    "ROS1032": {"name": "ROS1032 (6Y family)", "type": "inflation", "maturity": "2032-10", "margin": 2.00, "first_year": 5.00, "listed": False},
    "ROD1038": {"name": "ROD1038 (12Y family)", "type": "inflation", "maturity": "2038-10", "margin": 2.50, "first_year": 5.60, "listed": False},
}

# Planned auctions next ~3 quarters (simplified from MF calendar Oct 2026 – Q1 2027)
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

# Approximate current Polish CPI (user can update; or fetch later)
CURRENT_CPI = 4.2  # % y/y, placeholder – replace with live source if desired
NBP_REF_RATE = 3.75  # % current NBP reference rate

st.title("Global Economy Indicators – Obligacje Skarbowe (Polska)")

# Sidebar
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

# Metrics row
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
        real_rate = margin  # approximation for ongoing periods
        st.metric("Marża nad inflacją", f"+{margin:.2f} pp")
        st.caption(f"Aktualna inflacja (CPI) ≈ {CURRENT_CPI:.1f}%  →  bieżące oprocentowanie ≈ {CURRENT_CPI + margin:.2f}%")

# Chart section
st.subheader("Cena i rentowność")

# Try to fetch price history if ticker available; otherwise show informative placeholder + yield curve style
@st.cache_data(ttl=3600)
def try_fetch(ticker: str | None):
    if not ticker:
        return None
    try:
        df = yf.download(ticker, period="5y", interval="1d", progress=False)
        if df.empty:
            return None
        df = df.reset_index()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return None

price_df = try_fetch(bond.get("yticker"))

if price_df is not None and not price_df.empty:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35],
                        subplot_titles=("Cena", "Przybliżona rentowność (YTM proxy)"))
    fig.add_trace(go.Scatter(x=price_df["Date"], y=price_df["Close"], name="Cena", line=dict(color="#1f77b4")), row=1, col=1)
    # Simple YTM proxy for illustration (not precise)
    if bond.get("coupon") and bond.get("maturity"):
        # rough remaining years
        try:
            mat = pd.to_datetime(bond["maturity"])
            years_left = max(0.5, (mat - pd.Timestamp.today()).days / 365.25)
            ytm_proxy = (bond["coupon"] / (price_df["Close"] / 100)) + ((100 - price_df["Close"]) / (price_df["Close"] * years_left)) * 100
            fig.add_trace(go.Scatter(x=price_df["Date"], y=ytm_proxy, name="YTM proxy %", line=dict(color="#d62728")), row=2, col=1)
        except Exception:
            pass
    fig.update_layout(height=520, hovermode="x unified", showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Brak historii cen z Yahoo Finance dla tej serii (typowe dla wielu polskich obligacji hurtowych). Poniżej dane referencyjne i przybliżenie rentowności.")
    # Static reference view
    fig = go.Figure()
    fig.add_annotation(text="Dane cenowe dostępne na Catalyst / BondSpot / Notoria<br>lub po podłączeniu dedykowanego źródła",
                       xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14))
    fig.update_layout(height=280, title="Cena obligacji (wymaga źródła danych)")
    st.plotly_chart(fig, use_container_width=True)

# Inflation section for inflation-linked
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

# Additional info table
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
st.table(pd.Series(info).to_frame("Wartość"))

st.caption("© 2026 – adaptacja Tech Analytical Desktop pod obligacje skarbowe. Dane orientacyjne; aktualne ceny i rentowności sprawdź na Catalyst / MF / obligatoryjne źródła. Inflacja i stawki NBP należy aktualizować.")
