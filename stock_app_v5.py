"""
======================================================
  NIFTY 50 STOCK ANALYZER — STREAMLIT WEB APP
  Run with: streamlit run stock_app.py
======================================================
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import time
import ta
import plotly.graph_objects as go
import plotly.express as px

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Nifty50 Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.main { background-color: #0a0f1e; }

h1, h2, h3 { font-family: 'Space Mono', monospace; }

.stApp { background-color: #0a0f1e; color: #e2e8f0; }

.metric-card {
    background: linear-gradient(135deg, #1a2035 0%, #141928 100%);
    border: 1px solid #2d3a5a;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin: 6px 0;
}
.metric-card .label {
    font-size: 12px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-family: 'Space Mono', monospace;
}
.metric-card .value {
    font-size: 26px;
    font-weight: 700;
    color: #f1f5f9;
    margin: 6px 0;
}
.metric-card .delta {
    font-size: 13px;
    color: #94a3b8;
}

.decision-strong-buy {
    background: linear-gradient(135deg, #052e16, #14532d);
    border: 2px solid #22c55e;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    font-family: 'Space Mono', monospace;
    font-size: 22px;
    color: #4ade80;
    font-weight: 700;
    letter-spacing: 2px;
}
.decision-buy {
    background: linear-gradient(135deg, #052e16, #166534);
    border: 2px solid #86efac;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    font-family: 'Space Mono', monospace;
    font-size: 22px;
    color: #86efac;
    font-weight: 700;
    letter-spacing: 2px;
}
.decision-hold {
    background: linear-gradient(135deg, #1c1400, #292107);
    border: 2px solid #facc15;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    font-family: 'Space Mono', monospace;
    font-size: 22px;
    color: #facc15;
    font-weight: 700;
    letter-spacing: 2px;
}
.decision-avoid {
    background: linear-gradient(135deg, #1c0505, #290707);
    border: 2px solid #f87171;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    font-family: 'Space Mono', monospace;
    font-size: 22px;
    color: #f87171;
    font-weight: 700;
    letter-spacing: 2px;
}

.section-header {
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 2px;
    border-bottom: 1px solid #1e3a5f;
    padding-bottom: 8px;
    margin: 20px 0 14px 0;
}

.note-good  { color: #4ade80; font-size: 14px; margin: 4px 0; }
.note-warn  { color: #facc15; font-size: 14px; margin: 4px 0; }
.note-bad   { color: #f87171; font-size: 14px; margin: 4px 0; }
.note-na    { color: #64748b; font-size: 14px; margin: 4px 0; }

.stDataFrame { background: #1a2035; }

div[data-testid="stSidebarContent"] {
    background-color: #0d1326;
    border-right: 1px solid #1e2d4a;
}

.stButton > button {
    background: linear-gradient(135deg, #1d4ed8, #1e40af);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 32px;
    font-family: 'Space Mono', monospace;
    font-size: 14px;
    letter-spacing: 1px;
    width: 100%;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 3-INDEX BENCHMARK FRAMEWORK
# Large Cap → Nifty 50 peers
# Mid Cap   → Nifty Midcap 150 peers
# Small Cap → Nifty Smallcap 250 peers
# Each stock is silently compared to its own peer group
# ─────────────────────────────────────────────

# Real-world thresholds based on current Indian market (2025-26)
# SEBI top 100 = Large Cap, 101-250 = Mid Cap, rest = Small Cap
# In today's market these roughly translate to:
LARGE_CAP_THRESHOLD = 500_000_000_000   # ₹50,000 Cr
MID_CAP_THRESHOLD   = 150_000_000_000   # ₹15,000 Cr

# ── Large Cap benchmark — Nifty 50 stocks ──
LARGE_CAP_TICKERS = {
    "Banking & Finance":      ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS","AXISBANK.NS"],
    "IT & Technology":        ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS"],
    "Energy & Oil":           ["RELIANCE.NS","ONGC.NS","BPCL.NS","NTPC.NS"],
    "FMCG & Consumer":        ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS"],
    "Auto":                   ["MARUTI.NS","TATAMOTORS.NS","M&M.NS","BAJAJ-AUTO.NS"],
    "Pharma":                 ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS"],
    "Industrials & Infra":    ["LT.NS","POWERGRID.NS","ADANIPORTS.NS"],
    "Metals & Materials":     ["TATASTEEL.NS","HINDALCO.NS","JSWSTEEL.NS"],
    "Telecom":                ["BHARTIARTL.NS"],
    "Consumer Discretionary": ["TITAN.NS","ASIANPAINT.NS"],
    "Cement":                 ["ULTRACEMCO.NS","GRASIM.NS"],
}

# ── Mid Cap benchmark — Nifty Midcap 150 stocks ──
# These are solid, well-known midcaps that trade actively on Yahoo Finance
MIDCAP_TICKERS = {
    "Banking & Finance":      ["FEDERALBNK.NS","IDFCFIRSTB.NS","BANDHANBNK.NS","MUTHOOTFIN.NS"],
    "IT & Technology":        ["MPHASIS.NS","PERSISTENT.NS","COFORGE.NS","KPITTECH.NS"],
    "Pharma":                 ["TORNTPHARM.NS","ALKEM.NS","AUROPHARMA.NS","LALPATHLAB.NS"],
    "Auto & Ancillaries":     ["BALKRISIND.NS","ESCORTS.NS","ASHOKLEY.NS","TVSMOTOR.NS"],
    "Consumer":               ["VOLTAS.NS","TRENT.NS","RELAXO.NS"],
    "Industrials":            ["CUMMINSIND.NS","THERMAX.NS","BHEL.NS","SIEMENS.NS"],
    "Chemicals":              ["PIIND.NS","ATUL.NS","DEEPAKNTR.NS"],
    "Real Estate":            ["GODREJPROP.NS","OBEROIRLTY.NS","PHOENIXLTD.NS"],
}

# ── Small Cap benchmark — Nifty Smallcap 250 stocks ──
# Carefully chosen stocks known to have Yahoo Finance data
SMALLCAP_TICKERS = {
    "Banking & Finance":      ["RBLBANK.NS","UJJIVANSFB.NS","EQUITASBNK.NS"],
    "IT & Technology":        ["TANLA.NS","INTELLECT.NS","MASTEK.NS"],
    "Pharma":                 ["GRANULES.NS","GLENMARK.NS","JBCHEPHARM.NS"],
    "Consumer":               ["VSTIND.NS","NYKAA.NS"],
    "Industrials":            ["GRINDWELL.NS","RATNAMANI.NS","WELCORP.NS"],
    "Chemicals":              ["FINEORG.NS","NAVINFLUOR.NS","GALAXYSURF.NS"],
}

ALL_LARGE_TICKERS  = [t for v in LARGE_CAP_TICKERS.values()  for t in v]
ALL_MID_TICKERS    = [t for v in MIDCAP_TICKERS.values()      for t in v]
ALL_SMALL_TICKERS  = [t for v in SMALLCAP_TICKERS.values()    for t in v]

def classify_stock(market_cap):
    """Classify stock into Large / Mid / Small cap."""
    if market_cap is None:
        return "Large Cap", "🔵"
    if market_cap >= LARGE_CAP_THRESHOLD:
        return "Large Cap", "🔵"
    elif market_cap >= MID_CAP_THRESHOLD:
        return "Mid Cap", "🟡"
    else:
        return "Small Cap", "🟢"

# ─────────────────────────────────────────────
# CAP-SPECIFIC SCORING WEIGHTS
# Growth matters more for small/mid
# Stability matters more for large
# ─────────────────────────────────────────────
CAP_WEIGHTS = {
    "Large Cap": {
        "rule": 0.35, "ml": 0.25, "cashflow": 0.20, "governance": 0.12, "moat": 0.08
    },
    "Mid Cap": {
        "rule": 0.30, "ml": 0.25, "cashflow": 0.18, "governance": 0.12, "moat": 0.15
    },
    "Small Cap": {
        "rule": 0.28, "ml": 0.22, "cashflow": 0.15, "governance": 0.20, "moat": 0.15
    },
}

# ─────────────────────────────────────────────
# DATA FUNCTIONS
# ─────────────────────────────────────────────
def _build_single_benchmark(ticker_dict, label):
    """Build sector-balanced benchmark for one cap category."""
    metrics = ["pe_ratio","pb_ratio","roe","roa","debt_to_equity",
               "revenue_growth","earnings_growth","profit_margin",
               "gross_margin","operating_margin","current_ratio",
               "institutional_holding"]
    sector_records = {s: [] for s in ticker_dict}

    for sector_name, tickers in ticker_dict.items():
        for t in tickers:
            try:
                info = yf.Ticker(t).info
                sector_records[sector_name].append({
                    "pe_ratio":              info.get("trailingPE"),
                    "pb_ratio":              info.get("priceToBook"),
                    "roe":                   info.get("returnOnEquity"),
                    "roa":                   info.get("returnOnAssets"),
                    "debt_to_equity":        info.get("debtToEquity"),
                    "revenue_growth":        info.get("revenueGrowth"),
                    "earnings_growth":       info.get("earningsGrowth"),
                    "profit_margin":         info.get("profitMargins"),
                    "gross_margin":          info.get("grossMargins"),
                    "operating_margin":      info.get("operatingMargins"),
                    "current_ratio":         info.get("currentRatio"),
                    "institutional_holding": info.get("heldPercentInstitutions"),
                })
                time.sleep(0.2)
            except:
                pass

    sector_medians = []
    for sector_name, records in sector_records.items():
        if not records: continue
        df = pd.DataFrame(records)
        sector_med = {}
        for col in metrics:
            if col in df.columns:
                val = df[col].dropna().median()
                if not np.isnan(val):
                    sector_med[col] = val
        if sector_med:
            sector_medians.append(sector_med)

    if not sector_medians:
        return {}
    df_med = pd.DataFrame(sector_medians)
    return {col: df_med[col].dropna().median() for col in metrics if col in df_med.columns}

@st.cache_data(ttl=3600)
def build_all_benchmarks():
    """Build all 3 benchmarks. Cached for 1 hour."""
    large  = _build_single_benchmark(LARGE_CAP_TICKERS,  "Large Cap")
    mid    = _build_single_benchmark(MIDCAP_TICKERS,     "Mid Cap")
    small  = _build_single_benchmark(SMALLCAP_TICKERS,   "Small Cap")
    return {"Large Cap": large, "Mid Cap": mid, "Small Cap": small}


@st.cache_data(ttl=900)
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info

        fund = {
            "name":               info.get("longName", ticker),
            "sector":             info.get("sector", "N/A"),
            "pe_ratio":           info.get("trailingPE"),
            "pb_ratio":           info.get("priceToBook"),
            "roe":                info.get("returnOnEquity"),
            "roa":                info.get("returnOnAssets"),
            "debt_to_equity":     info.get("debtToEquity"),
            "revenue_growth":     info.get("revenueGrowth"),
            "earnings_growth":    info.get("earningsGrowth"),
            "profit_margin":      info.get("profitMargins"),
            "gross_margin":       info.get("grossMargins"),
            "operating_margin":   info.get("operatingMargins"),
            "current_ratio":      info.get("currentRatio"),
            "ev_ebitda":          info.get("enterpriseToEbitda"),
            "market_cap":         info.get("marketCap"),
            "promoter_holding":   info.get("heldPercentInsiders"),
            "institutional_holding": info.get("heldPercentInstitutions"),
        }

        # Cash flow
        cf = {}
        try:
            cfs = stock.cashflow
            inc = stock.financials
            if cfs is not None and not cfs.empty:
                for lbl in ["Operating Cash Flow","Total Cash From Operating Activities","Cash Flow From Continuing Operating Activities"]:
                    if lbl in cfs.index:
                        cf["cfo"] = float(cfs.loc[lbl].iloc[0]); break
                for lbl in ["Capital Expenditure","Purchase Of PPE","Purchases Of Property Plant And Equipment"]:
                    if lbl in cfs.index:
                        cf["capex"] = abs(float(cfs.loc[lbl].iloc[0])); break
                cfo = cf.get("cfo", 0); capex = cf.get("capex", 0)
                if cfo and capex:
                    cf["fcf"] = cfo - capex
            if inc is not None and not inc.empty:
                for lbl in ["Net Income","Net Income Common Stockholders"]:
                    if lbl in inc.index:
                        cf["net_income"] = float(inc.loc[lbl].iloc[0]); break
                for lbl in ["Total Revenue","Operating Revenue"]:
                    if lbl in inc.index:
                        cf["revenue"] = float(inc.loc[lbl].iloc[0]); break
            if cf.get("cfo") and cf.get("net_income") and cf["net_income"] != 0:
                cf["cfo_to_pat"] = round(cf["cfo"] / cf["net_income"], 2)
            if cf.get("capex") and cf.get("revenue") and cf["revenue"] != 0:
                cf["capex_to_revenue"] = round(cf["capex"] / cf["revenue"], 4)
        except:
            pass

        # Technicals + Risk Metrics
        tech = {}
        try:
            hist  = stock.history(period="1y")

            # Fetch Nifty separately — don't let it crash everything
            try:
                nifty = yf.Ticker("^NSEI").history(period="1y")["Close"]
            except:
                nifty = None

            if not hist.empty and len(hist) >= 50:
                close   = hist["Close"]
                returns = close.pct_change().dropna()

                # Standard indicators
                rsi         = ta.momentum.RSIIndicator(close, window=14).rsi()
                macd_obj    = ta.trend.MACD(close)
                macd_line   = macd_obj.macd()
                signal_line = macd_obj.macd_signal()
                ma50        = close.rolling(50).mean().iloc[-1]
                ma200       = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
                ltp         = close.iloc[-1]
                vol_10      = hist["Volume"].iloc[-10:].mean()
                vol_30      = hist["Volume"].iloc[-30:].mean()

                # ── Risk Metrics ──
                volatility = round(returns.std() * np.sqrt(252) * 100, 2)

                rolling_max  = close.cummax()
                drawdown     = (close - rolling_max) / rolling_max
                max_drawdown = round(drawdown.min() * 100, 2)

                # Beta — only if Nifty data available
                beta = None
                try:
                    if nifty is not None:
                        common_idx = returns.index.intersection(nifty.pct_change().dropna().index)
                        if len(common_idx) > 30:
                            stock_ret = returns.loc[common_idx]
                            nifty_ret = nifty.pct_change().dropna().loc[common_idx]
                            cov  = np.cov(stock_ret, nifty_ret)[0][1]
                            var  = np.var(nifty_ret)
                            beta = round(cov / var, 2) if var != 0 else None
                except:
                    pass

                # Sharpe Ratio
                risk_free  = 0.065 / 252
                excess_ret = returns.mean() - risk_free
                sharpe     = round((excess_ret / returns.std()) * np.sqrt(252), 2) if returns.std() != 0 else None

                # Value at Risk (95%)
                var_95 = round(np.percentile(returns, 5) * 100, 2)

                # ATR
                try:
                    high    = hist["High"]; low = hist["Low"]
                    atr     = round(ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range().iloc[-1], 2)
                    atr_pct = round((atr / ltp) * 100, 2)
                except:
                    atr = None; atr_pct = None

                # 1-year return
                ret_1y = round(((ltp - close.iloc[0]) / close.iloc[0]) * 100, 2)

                # Risk label
                if volatility < 20:   risk_label = ("🟢 Low Risk",    "low")
                elif volatility < 35: risk_label = ("🟡 Medium Risk", "medium")
                else:                 risk_label = ("🔴 High Risk",   "high")

                tech = {
                    "ltp":          round(ltp, 2),
                    "rsi":          round(float(rsi.iloc[-1]), 2),
                    "ma50":         round(ma50, 2),
                    "ma200":        round(ma200, 2) if ma200 else None,
                    "above_ma50":   ltp > ma50,
                    "above_ma200":  (ltp > ma200) if ma200 else None,
                    "macd_bullish": float(macd_line.iloc[-1]) > float(signal_line.iloc[-1]),
                    "high_52w":     round(close.max(), 2),
                    "low_52w":      round(close.min(), 2),
                    "pct_from_high":round(((ltp - close.max()) / close.max()) * 100, 1),
                    "vol_trend_up": vol_10 > vol_30,
                    "history":      hist,
                    "volatility":   volatility,
                    "max_drawdown": max_drawdown,
                    "beta":         beta,
                    "sharpe":       sharpe,
                    "var_95":       var_95,
                    "atr":          atr,
                    "atr_pct":      atr_pct,
                    "ret_1y":       ret_1y,
                    "risk_label":   risk_label,
                }
        except:
            pass

        return fund, cf, tech
    except Exception as e:
        st.warning(f"⚠️ Error fetching {ticker}: {str(e)}")
        return None, {}, {}

# ─────────────────────────────────────────────
# SECTOR NORMS — realistic Indian market levels
# ─────────────────────────────────────────────
SECTOR_NORMS = {
    "Technology":         {"pe_max": 45, "pe_mid": 32, "roe_min": 0.15, "margin_min": 0.12, "growth_min": 0.07, "skip_de": False, "skip_cr": False, "pb_focus": False},
    "Financial Services": {"pe_max": 25, "pe_mid": 16, "roe_min": 0.10, "margin_min": 0.12, "growth_min": 0.07, "skip_de": True,  "skip_cr": True,  "pb_focus": True },
    "Banking":            {"pe_max": 25, "pe_mid": 16, "roe_min": 0.10, "margin_min": 0.12, "growth_min": 0.07, "skip_de": True,  "skip_cr": True,  "pb_focus": True },
    "Consumer Defensive": {"pe_max": 65, "pe_mid": 48, "roe_min": 0.18, "margin_min": 0.10, "growth_min": 0.06, "skip_de": False, "skip_cr": False, "pb_focus": False},
    "Consumer Cyclical":  {"pe_max": 45, "pe_mid": 30, "roe_min": 0.12, "margin_min": 0.07, "growth_min": 0.08, "skip_de": False, "skip_cr": False, "pb_focus": False},
    "Healthcare":         {"pe_max": 40, "pe_mid": 28, "roe_min": 0.12, "margin_min": 0.12, "growth_min": 0.08, "skip_de": False, "skip_cr": False, "pb_focus": False},
    "Energy":             {"pe_max": 18, "pe_mid": 12, "roe_min": 0.08, "margin_min": 0.05, "growth_min": 0.04, "skip_de": False, "skip_cr": False, "pb_focus": False},
    "Basic Materials":    {"pe_max": 18, "pe_mid": 12, "roe_min": 0.08, "margin_min": 0.07, "growth_min": 0.04, "skip_de": False, "skip_cr": False, "pb_focus": False},
    "Industrials":        {"pe_max": 35, "pe_mid": 24, "roe_min": 0.10, "margin_min": 0.07, "growth_min": 0.07, "skip_de": False, "skip_cr": False, "pb_focus": False},
    "Communication":      {"pe_max": 35, "pe_mid": 24, "roe_min": 0.10, "margin_min": 0.08, "growth_min": 0.07, "skip_de": False, "skip_cr": False, "pb_focus": False},
    "Real Estate":        {"pe_max": 40, "pe_mid": 28, "roe_min": 0.08, "margin_min": 0.12, "growth_min": 0.06, "skip_de": False, "skip_cr": False, "pb_focus": True },
    "Utilities":          {"pe_max": 25, "pe_mid": 18, "roe_min": 0.08, "margin_min": 0.08, "growth_min": 0.04, "skip_de": False, "skip_cr": False, "pb_focus": False},
}
DEFAULT_NORMS = {"pe_max": 35, "pe_mid": 25, "roe_min": 0.10, "margin_min": 0.08, "growth_min": 0.07, "skip_de": False, "skip_cr": False, "pb_focus": False}

def get_sector_norms(sector: str) -> dict:
    if not sector or sector == "N/A":
        return DEFAULT_NORMS
    for key in SECTOR_NORMS:
        if key.lower() in sector.lower():
            return SECTOR_NORMS[key]
    return DEFAULT_NORMS

def score_stock(fund, tech, cf, benchmarks):
    scores = {}
    sector = fund.get("sector", "N/A")
    norms  = get_sector_norms(sector)
    scores["sector"] = sector
    scores["norms"]  = norms

    # ── Classify by market cap → pick right benchmark ──
    mc       = fund.get("market_cap")
    cap_type, cap_icon = classify_stock(mc)
    benchmark = benchmarks.get(cap_type, benchmarks.get("Large Cap", {}))
    scores["cap_type"] = cap_type
    scores["cap_icon"] = cap_icon

    # ── Cap-specific scoring adjustments ──
    # Small/mid caps get more credit for growth, less penalised for thin margins
    growth_bonus    = 1.5 if cap_type == "Small Cap" else (1.2 if cap_type == "Mid Cap" else 1.0)
    margin_leniency = 0.7 if cap_type == "Small Cap" else (0.85 if cap_type == "Mid Cap" else 1.0)

    pe  = fund.get("pe_ratio")
    roe = fund.get("roe")
    de  = fund.get("debt_to_equity");  b_de = benchmark.get("debt_to_equity")
    rg  = fund.get("revenue_growth")
    eg  = fund.get("earnings_growth")
    pm  = fund.get("profit_margin")
    cr  = fund.get("current_ratio")
    pb  = fund.get("pb_ratio");        b_pb = benchmark.get("pb_ratio")
    rsi = tech.get("rsi")
    above50  = tech.get("above_ma50")
    above200 = tech.get("above_ma200")
    macd_b   = tech.get("macd_bullish")

    # ── Rule Score ──
    r = 0; r_max = 13
    pe_notes = []

    # PE — use wider ceiling for small/mid (they grow faster, deserve premium)
    pe_max_adj = norms["pe_max"] * (1.3 if cap_type == "Small Cap" else (1.15 if cap_type == "Mid Cap" else 1.0))
    pe_mid_adj = norms["pe_mid"] * (1.3 if cap_type == "Small Cap" else (1.15 if cap_type == "Mid Cap" else 1.0))

    if pe:
        if pe <= pe_mid_adj:
            r += 2
            pe_notes.append(f"✅ PE {pe:.1f} ≤ {cap_type} midpoint {pe_mid_adj:.0f} — attractively priced")
        elif pe <= pe_max_adj:
            r += 1
            pe_notes.append(f"✅ PE {pe:.1f} within {cap_type} norm (≤{pe_max_adj:.0f})")
        else:
            pe_notes.append(f"❌ PE {pe:.1f} above {cap_type} ceiling {pe_max_adj:.0f} — expensive")
    scores["pe_notes"] = pe_notes

    # ROE
    if roe:
        if roe >= norms["roe_min"] * 1.25:
            r += 2
        elif roe >= norms["roe_min"]:
            r += 1

    # Debt/Equity
    if not norms["skip_de"]:
        if de and b_de and de < b_de: r += 1

    # Growth — small/mid get bonus: lower threshold needed to score
    growth_threshold = norms["growth_min"] / growth_bonus
    if rg and rg > growth_threshold: r += 1
    if eg and eg > growth_threshold: r += 1

    # Profit margin — leniency for small/mid
    margin_threshold = norms["margin_min"] * margin_leniency
    if pm and pm > margin_threshold: r += 1

    # Current ratio
    if not norms["skip_cr"]:
        if cr and cr > 1.2: r += 1

    # P/B focus for banks
    if norms["pb_focus"] and pb:
        if pb < 2.5: r += 1

    # Technicals
    if rsi:
        r += 2 if 35<=rsi<=70 else (1 if rsi<35 else 0)
    if above50:  r += 1
    if above200: r += 2
    if macd_b:   r += 1

    scores["rule"] = (min(r, r_max), r_max)

    # ── Governance Score ──
    # Small caps: promoter holding is MORE important (insider conviction)
    g = 0; g_max = 4
    promoter = fund.get("promoter_holding")
    inst     = fund.get("institutional_holding"); b_inst = benchmark.get("institutional_holding")
    roa      = fund.get("roa");                   b_roa  = benchmark.get("roa")

    promoter_min = 0.50 if cap_type == "Small Cap" else (0.40 if cap_type == "Mid Cap" else 0.35)
    if promoter and promoter >= promoter_min: g += 1
    elif promoter and promoter >= 0.25: g += 0  # too low for any cap
    if inst and b_inst and inst >= b_inst: g += 1
    elif inst and inst >= 0.15: g += 1
    if pb and b_pb and 1.0 <= pb <= b_pb * 2.5: g += 1
    if roa and b_roa and roa > b_roa: g += 1
    elif roa and roa > 0.04: g += 1
    scores["governance"] = (g, g_max)

    # ── Cash Flow Score ──
    c = 0; c_max = 5
    cfo       = cf.get("cfo")
    fcf       = cf.get("fcf")
    cfo_pat   = cf.get("cfo_to_pat")
    capex_rev = cf.get("capex_to_revenue")

    if cfo is not None:
        c += 1 if cfo > 0 else 0
    else:
        c += 1

    if cfo_pat is not None:
        c += 2 if cfo_pat >= 0.7 else (1 if cfo_pat >= 0.4 else 0)
    else:
        c += 1

    if fcf is not None:
        c += 1 if fcf > 0 else 0
    else:
        c += 1

    capex_threshold = 0.20 if sector and any(s in sector for s in ["Energy","Utilities","Industrials","Materials"]) else 0.12
    if capex_rev is not None:
        c += 1 if capex_rev <= capex_threshold else 0
    else:
        c += 1

    scores["cashflow"] = (min(c, c_max), c_max)

    # ── Moat Score ──
    m = 0; m_max = 5
    gm = fund.get("gross_margin");     b_gm = benchmark.get("gross_margin")
    om = fund.get("operating_margin"); b_om = benchmark.get("operating_margin")

    if roe and norms["roe_min"]:
        m += 2 if roe >= norms["roe_min"]*1.4 else (1 if roe >= norms["roe_min"] else 0)
    if gm and b_gm and gm >= b_gm: m += 1
    elif gm and gm > 0.12: m += 1
    if om and b_om and om >= b_om: m += 1
    elif om and om > 0.08: m += 1
    # Market cap threshold per category
    mc_moat = 5e11 if cap_type == "Large Cap" else (5e10 if cap_type == "Mid Cap" else 5e9)
    if mc and mc >= mc_moat: m += 1
    scores["moat"] = (min(m, m_max), m_max)

    # ── ML Confidence ──
    def norm(val, ref, hib=True):
        if not val or not ref or ref == 0: return 0.5
        ratio = val / ref
        return min(ratio, 2) / 2 if hib else min(ref / val, 2) / 2

    pe_ref = pe_mid_adj
    features = [
        norm(roe, norms["roe_min"], True),
        norm(pe, pe_ref, False),
        0.5 if norms["skip_de"] else norm(de, b_de, False),
        norm(pm, margin_threshold, True),
        norm(rg, growth_threshold, True),
        norm(eg, growth_threshold, True),
        0.80 if (rsi and 35<=rsi<=70) else (0.50 if rsi and rsi<35 else 0.20),
        1.0 if above50  else 0.0,
        1.0 if above200 else 0.0,
        1.0 if macd_b   else 0.0,
        1.0 if tech.get("vol_trend_up") else 0.5,
        min((fund.get("promoter_holding") or 0.35) / 0.5, 1.0),
        min((fund.get("institutional_holding") or 0.20) / 0.3, 1.0),
        min((cf.get("cfo_to_pat") or 0.7) / 1.0, 1.0),
        1.0 if (fcf and fcf > 0) else 0.5,
    ]
    weights = [0.10, 0.08, 0.06, 0.07, 0.07, 0.06, 0.08, 0.07, 0.08, 0.05, 0.03, 0.07, 0.05, 0.08, 0.06]
    total   = sum(weights)
    weights = [w / total for w in weights]
    ml_conf = round(sum(f * w for f, w in zip(features, weights)) * 100, 1)
    scores["ml"] = ml_conf

    # ── Blended — cap-specific weights ──
    r_s, r_m = scores["rule"]
    g_s, g_m = scores["governance"]
    c_s, c_m = scores["cashflow"]
    m_s, m_m = scores["moat"]
    cw = CAP_WEIGHTS[cap_type]
    blended = (
        (r_s/r_m)*100 * cw["rule"]       +
        ml_conf       * cw["ml"]         +
        (c_s/c_m)*100 * cw["cashflow"]   +
        (g_s/g_m)*100 * cw["governance"] +
        (m_s/m_m)*100 * cw["moat"]
    )
    scores["blended"] = round(blended, 1)

    if blended >= 62:   verdict = ("✅ STRONG BUY",    "strong-buy")
    elif blended >= 50: verdict = ("📈 BUY / CONSIDER","buy")
    elif blended >= 38: verdict = ("⚠️ HOLD / WATCH",  "hold")
    else:               verdict = ("❌ AVOID",          "avoid")
    scores["verdict"] = verdict

    return scores

# ─────────────────────────────────────────────
# RATIONALE GENERATOR
# ─────────────────────────────────────────────
def generate_rationale(fund, tech, cf, scores, benchmark):
    """Build plain-English rationale bullets for the decision."""
    norms   = scores["norms"]
    sector  = scores["sector"]
    verdict = scores["verdict"][0]
    blended = scores["blended"]
    ml      = scores["ml"]

    pe  = fund.get("pe_ratio");        roe = fund.get("roe")
    de  = fund.get("debt_to_equity");  pm  = fund.get("profit_margin")
    rg  = fund.get("revenue_growth");  eg  = fund.get("earnings_growth")
    cr  = fund.get("current_ratio");   pb  = fund.get("pb_ratio")
    rsi = tech.get("rsi")
    above50  = tech.get("above_ma50")
    above200 = tech.get("above_ma200")
    macd_b   = tech.get("macd_bullish")
    cfo_pat  = cf.get("cfo_to_pat");   fcf = cf.get("fcf")
    promoter = fund.get("promoter_holding")
    inst     = fund.get("institutional_holding")

    positives = []
    negatives = []
    neutrals  = []

    # ── Valuation ──
    if pe:
        if pe <= norms["pe_mid"]:
            positives.append(f"**Valuation is attractive** — P/E of {pe:.1f}x is below the sector midpoint of {norms['pe_mid']}x for {sector}, suggesting the stock may be underpriced relative to peers.")
        elif pe <= norms["pe_max"]:
            neutrals.append(f"**Valuation is fair** — P/E of {pe:.1f}x is within the acceptable sector range ({norms['pe_mid']}–{norms['pe_max']}x) for {sector}. Not cheap, not expensive.")
        else:
            negatives.append(f"**Valuation is stretched** — P/E of {pe:.1f}x exceeds the sector ceiling of {norms['pe_max']}x for {sector}. The stock is priced for perfection; any earnings miss could hurt.")

    # ── Profitability ──
    if roe:
        if roe >= norms["roe_min"] * 1.3:
            positives.append(f"**Strong profitability** — ROE of {roe*100:.1f}% is well above the {sector} minimum of {norms['roe_min']*100:.0f}%, indicating management is generating excellent returns on shareholder equity.")
        elif roe >= norms["roe_min"]:
            neutrals.append(f"**Adequate profitability** — ROE of {roe*100:.1f}% meets the sector minimum of {norms['roe_min']*100:.0f}%, but leaves room for improvement.")
        else:
            negatives.append(f"**Weak profitability** — ROE of {roe*100:.1f}% falls below the sector minimum of {norms['roe_min']*100:.0f}%, suggesting the business is not generating sufficient returns on equity.")

    if pm:
        if pm >= norms["margin_min"] * 1.5:
            positives.append(f"**Healthy margins** — Profit margin of {pm*100:.1f}% is well above the sector floor of {norms['margin_min']*100:.0f}%, indicating strong pricing power or cost control.")
        elif pm >= norms["margin_min"]:
            neutrals.append(f"**Margins are acceptable** — Profit margin of {pm*100:.1f}% is above the sector minimum of {norms['margin_min']*100:.0f}%.")
        else:
            negatives.append(f"**Thin margins** — Profit margin of {pm*100:.1f}% is below the sector minimum of {norms['margin_min']*100:.0f}%. Could indicate pricing pressure or high costs.")

    # ── Growth ──
    if rg and eg:
        if rg > norms["growth_min"] and eg > norms["growth_min"]:
            positives.append(f"**Growth is solid** — Revenue growing at {rg*100:.1f}% and earnings at {eg*100:.1f}%, both above the {norms['growth_min']*100:.0f}% sector threshold. The business is expanding.")
        elif rg > norms["growth_min"]:
            neutrals.append(f"**Revenue growing but earnings lagging** — Revenue up {rg*100:.1f}% but earnings growth of {eg*100:.1f}% is below target. Watch margin trends.")
        elif eg > norms["growth_min"]:
            neutrals.append(f"**Earnings growing but revenue soft** — Earnings up {eg*100:.1f}% but revenue growth of {rg*100:.1f}% is weak. Could be cost-cutting rather than real growth.")
        else:
            negatives.append(f"**Growth is weak** — Both revenue ({rg*100:.1f}%) and earnings ({eg*100:.1f}%) are below the {norms['growth_min']*100:.0f}% sector threshold. Limited near-term upside catalyst.")

    # ── Debt ──
    if not norms["skip_de"] and de:
        b_de = benchmark.get("debt_to_equity")
        if b_de and de < b_de * 0.7:
            positives.append(f"**Low debt** — Debt/Equity of {de:.2f} is well below the Nifty 50 median, giving the company financial flexibility and reducing downside risk.")
        elif b_de and de > b_de * 1.3:
            negatives.append(f"**High debt** — Debt/Equity of {de:.2f} is above the Nifty 50 median of {b_de:.2f}. Elevated leverage could be a risk if earnings disappoint or rates rise.")
    elif norms["skip_de"]:
        neutrals.append(f"**Debt/Equity not applicable** — {sector} companies borrow to operate by nature; D/E ratio is excluded from scoring for this sector.")

    # ── Cash Flow ──
    if cfo_pat:
        if cfo_pat >= 0.8:
            positives.append(f"**Earnings are cash-backed** — CFO/PAT ratio of {cfo_pat:.2f} means profits are well supported by actual cash generation. This reduces the risk of accounting-inflated earnings.")
        elif cfo_pat >= 0.5:
            neutrals.append(f"**Moderate cash conversion** — CFO/PAT of {cfo_pat:.2f} is acceptable but not excellent. Some reported profits may not yet be in cash form.")
        else:
            negatives.append(f"**Poor cash conversion** — CFO/PAT of {cfo_pat:.2f} is a red flag. Reported profits are not being matched by real cash generation — could indicate aggressive accounting.")
    if fcf:
        if fcf > 0:
            positives.append(f"**Free cash flow positive** — The company generates surplus cash after all capital expenditure, meaning it can fund growth, pay dividends, or reduce debt without external financing.")
        else:
            neutrals.append(f"**Negative free cash flow** — The company is spending more on capex than it generates in operating cash. This is acceptable during growth phases but watch the trend.")

    # ── Technicals ──
    if rsi:
        if 40 <= rsi <= 65:
            positives.append(f"**Healthy technical momentum** — RSI of {rsi} sits in the ideal 40–65 zone, indicating steady buying interest without being overbought.")
        elif rsi > 65:
            negatives.append(f"**Technically overbought** — RSI of {rsi} is above 65, suggesting the stock has run up quickly. Short-term pullback risk is elevated; wait for a better entry.")
        else:
            neutrals.append(f"**Technically oversold** — RSI of {rsi} is below 40. Could be a bounce opportunity, but also signals recent selling pressure. High risk.")

    if above200 is True and above50 is True:
        positives.append("**Strong trend structure** — Price is above both the 50-day and 200-day moving averages, confirming a bullish trend on both short and long timeframes.")
    elif above200 is True and above50 is False:
        neutrals.append("**Mixed trend** — Price is above the 200-day MA (long-term bullish) but below the 50-day MA (short-term weakness). Could be a temporary dip within an uptrend.")
    elif above200 is False:
        negatives.append("**Below long-term trend line** — Price is under the 200-day MA, indicating a long-term downtrend. Buying against the trend requires strong fundamental conviction.")

    if macd_b is True:
        positives.append("**MACD is bullish** — The MACD line has crossed above the signal line, a classic momentum buy signal indicating increasing upward price pressure.")
    elif macd_b is False:
        negatives.append("**MACD is bearish** — The MACD line is below the signal line, suggesting weakening momentum and potential further downside in the near term.")

    # ── Governance ──
    if promoter and promoter >= 0.45:
        positives.append(f"**Strong promoter commitment** — Promoters hold {promoter*100:.1f}% of shares, showing high confidence from founders/management in the company's future.")
    elif promoter and promoter < 0.25:
        negatives.append(f"**Low promoter holding** — Only {promoter*100:.1f}% held by promoters. Low insider ownership can sometimes signal reduced confidence or governance concerns.")

    if inst and inst >= 0.25:
        positives.append(f"**Strong institutional backing** — {inst*100:.1f}% held by FIIs/DIIs/mutual funds, indicating confidence from professional investors who conduct deep due diligence.")

    # ── ML Explanation ──
    if ml >= 68:
        ml_explanation = f"The ML model (confidence: **{ml}%**) independently confirms a strong buy signal. It weighs 15 factors across valuation, momentum, governance, and cash flow — all pointing positively."
    elif ml >= 55:
        ml_explanation = f"The ML model (confidence: **{ml}%**) signals a moderate buy. Most weighted factors are positive, but a few drag the score — likely valuation or momentum."
    elif ml >= 42:
        ml_explanation = f"The ML model (confidence: **{ml}%**) is neutral. The stock has a mixed profile — some strong factors offset by weaknesses. Not a clear buy or sell."
    else:
        ml_explanation = f"The ML model (confidence: **{ml}%**) flags caution. Multiple key factors — likely valuation, momentum, or cash flow — are scoring poorly simultaneously."

    # ── Overall Summary ──
    if blended >= 68:
        summary = f"**{fund.get('name','This stock')} scores {blended}% overall.** The fundamentals are solid, technicals support entry, and cash flows are healthy. The risk/reward looks favourable at current levels."
    elif blended >= 55:
        summary = f"**{fund.get('name','This stock')} scores {blended}% overall.** More positives than negatives — a reasonable buy for investors comfortable with moderate risk. Watch the weaker areas before sizing up."
    elif blended >= 42:
        summary = f"**{fund.get('name','This stock')} scores {blended}% overall.** The stock has real merits but also real concerns. Better to watch and wait for a cleaner setup before committing capital."
    else:
        summary = f"**{fund.get('name','This stock')} scores {blended}% overall.** Multiple red flags across valuation, momentum, or fundamentals make this unattractive at current levels. Avoid until the picture improves."

    return {
        "summary":      summary,
        "positives":    positives,
        "negatives":    negatives,
        "neutrals":     neutrals,
        "ml_explanation": ml_explanation,
    }

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

if "confirmed_tickers" not in st.session_state:
    st.session_state.confirmed_tickers = []
if "quick_load" not in st.session_state:
    st.session_state.quick_load = ""

with st.sidebar:
    st.markdown("## 📈 Stock Analyzer")
    st.markdown("*Nifty 50 Benchmark Engine*")
    st.markdown("---")

    st.markdown("### Enter Stock Tickers")
    st.markdown("Just type the symbol — `.NS` is added automatically")

    # Quick pick buttons load into session state
    st.markdown("**Quick picks:**")
    quick = {
        "🏦 Banking": "HDFCBANK\nICICIBANK\nSBIN",
        "💻 IT":      "TCS\nINFY\nWIPRO",
        "⚡ Energy":  "RELIANCE\nONGC\nNTPC",
        "🚗 Auto":    "MARUTI\nTATAMOTORS\nM&M",
    }
    cols = st.columns(2)
    for i, (label, preset) in enumerate(quick.items()):
        if cols[i%2].button(label, key=f"qp_{label}"):
            st.session_state.quick_load = preset

    # Text area — seeded by quick pick if clicked, otherwise blank/previous
    default_text = st.session_state.quick_load if st.session_state.quick_load else "RELIANCE\nTATAMOTORS\nZOMATO"
    raw_input = st.text_area(
        "One ticker per line:",
        value=default_text,
        height=150,
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Analyze button locks in whatever is currently in the text area
    if st.button("🔍 Analyze Stocks", type="primary"):
        raw_tickers = [t.strip().upper() for t in raw_input.strip().split("\n") if t.strip()]
        # Auto-append .NS if not already there
        fixed_tickers = []
        for t in raw_tickers:
            if not t.endswith(".NS") and not t.endswith(".BO"):
                t = t + ".NS"
            fixed_tickers.append(t)
        st.session_state.confirmed_tickers = fixed_tickers
        st.session_state.quick_load = ""

    # Always show what will actually be analyzed
    if st.session_state.confirmed_tickers:
        st.markdown("**Analyzing:**")
        for t in st.session_state.confirmed_tickers:
            st.markdown(f"&nbsp;&nbsp;`{t}`")

    analyze_btn = bool(st.session_state.confirmed_tickers)
    st.markdown("---")
    st.markdown("⚠️ *For educational purposes only. Not financial advice.*")

# ─────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────
st.markdown("# 📊 Nifty 50 Stock Analyzer")
st.markdown("*Fundamentals · Technicals · Governance · Cash Flow · Moat*")
st.markdown("---")

if not analyze_btn:
    st.markdown("""
    <div style='text-align:center; padding: 60px 0; color: #475569;'>
        <div style='font-size: 64px; margin-bottom: 20px;'>📈</div>
        <div style='font-family: Space Mono, monospace; font-size: 18px; color: #94a3b8;'>
            Enter ticker symbols in the sidebar and click Analyze
        </div>
        <div style='margin-top: 12px; font-size: 14px; color: #475569;'>
            Format: SYMBOL.NS &nbsp;|&nbsp; Example: RELIANCE.NS, TCS.NS, ZOMATO.NS
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    tickers = st.session_state.confirmed_tickers

    if not tickers:
        st.error("Please enter at least one ticker symbol.")
    else:
        # Build all 3 benchmarks silently
        with st.spinner("📊 Building peer benchmarks for Large / Mid / Small cap... (~90 seconds first time)"):
            benchmarks = build_all_benchmarks()

        total_stocks = len(ALL_LARGE_TICKERS) + len(ALL_MID_TICKERS) + len(ALL_SMALL_TICKERS)
        st.success(f"✅ Benchmarks ready — {total_stocks} peer stocks across 🔵 Large / 🟡 Mid / 🟢 Small cap indices")

        # ── Fetch all stock data first ──
        all_data    = {}

        for ticker in tickers:
            with st.spinner(f"Fetching {ticker}..."):
                fund, cf, tech = get_stock_data(ticker)
            if fund:
                scores = score_stock(fund, cf, tech, benchmarks)
                all_data[ticker] = (fund, cf, tech, scores)
            else:
                st.warning(f"⚠️ Could not fetch data for {ticker} — skipping.")

        if not all_data:
            st.error("No valid data found. Please check your ticker symbols.")
        else:
            # ── Build full export dataframe ──
            summary_rows = []
            for t, (f, c, tc, sc) in all_data.items():
                r_s, r_m = sc["rule"]; g_s, g_m = sc["governance"]
                c_s, c_m = sc["cashflow"]; m_s, m_m = sc["moat"]
                summary_rows.append({
                    "Ticker":           t,
                    "Company":          f.get("name", t),
                    "Sector":           f.get("sector","N/A"),
                    "LTP (₹)":          tc.get("ltp","N/A"),
                    "52W High":         tc.get("high_52w","N/A"),
                    "52W Low":          tc.get("low_52w","N/A"),
                    "Blended Score %":  sc["blended"],
                    "ML Score %":       sc["ml"],
                    "Rules":            f"{r_s}/{r_m}",
                    "Governance":       f"{g_s}/{g_m}",
                    "Cash Flow":        f"{c_s}/{c_m}",
                    "Moat":             f"{m_s}/{m_m}",
                    "P/E":              f.get("pe_ratio","N/A"),
                    "P/B":              f.get("pb_ratio","N/A"),
                    "ROE %":            round(f.get("roe",0)*100,1) if f.get("roe") else "N/A",
                    "ROA %":            round(f.get("roa",0)*100,1) if f.get("roa") else "N/A",
                    "Debt/Equity":      f.get("debt_to_equity","N/A"),
                    "Profit Margin %":  round(f.get("profit_margin",0)*100,1) if f.get("profit_margin") else "N/A",
                    "Revenue Growth %": round(f.get("revenue_growth",0)*100,1) if f.get("revenue_growth") else "N/A",
                    "Earnings Growth %":round(f.get("earnings_growth",0)*100,1) if f.get("earnings_growth") else "N/A",
                    "RSI":              tc.get("rsi","N/A"),
                    "Above 50MA":       "Yes" if tc.get("above_ma50") else "No",
                    "Above 200MA":      "Yes" if tc.get("above_ma200") else "No",
                    "MACD Bullish":     "Yes" if tc.get("macd_bullish") else "No",
                    "CFO/PAT":          c.get("cfo_to_pat","N/A"),
                    "FCF (B)":          round(c.get("fcf",0)/1e9,2) if c.get("fcf") else "N/A",
                    "Promoter %":       round(f.get("promoter_holding",0)*100,1) if f.get("promoter_holding") else "N/A",
                    "Institutional %":  round(f.get("institutional_holding",0)*100,1) if f.get("institutional_holding") else "N/A",
                    "Decision":         sc["verdict"][0],
                    "Cap Type":         f"{sc.get('cap_icon','🔵')} {sc.get('cap_type','Large Cap')}",
                })
            df_summary = pd.DataFrame(summary_rows)

            # ── Comparison summary ──
            if len(all_data) > 1:
                st.markdown("<div class='section-header'>COMPARISON OVERVIEW</div>", unsafe_allow_html=True)

                display_cols = ["Ticker","Company","Cap Type","Sector","LTP (₹)","Blended Score %","ML Score %","Rules","Governance","Cash Flow","Moat","Decision"]
                st.dataframe(df_summary[display_cols], use_container_width=True, hide_index=True)

                # ── Excel Export ──
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    # Sheet 1: Summary
                    df_summary.to_excel(writer, sheet_name="Summary", index=False)
                    # Sheet 2: Fundamentals only
                    fund_cols = ["Ticker","Company","Sector","P/E","P/B","ROE %","ROA %","Debt/Equity","Profit Margin %","Revenue Growth %","Earnings Growth %","Decision"]
                    df_summary[fund_cols].to_excel(writer, sheet_name="Fundamentals", index=False)
                    # Sheet 3: Technicals only
                    tech_cols = ["Ticker","Company","LTP (₹)","52W High","52W Low","RSI","Above 50MA","Above 200MA","MACD Bullish","Decision"]
                    df_summary[tech_cols].to_excel(writer, sheet_name="Technicals", index=False)
                    # Sheet 4: Cash Flow & Governance
                    cf_cols = ["Ticker","Company","CFO/PAT","FCF (B)","Promoter %","Institutional %","Governance","Cash Flow","Decision"]
                    df_summary[cf_cols].to_excel(writer, sheet_name="CashFlow & Governance", index=False)

                buffer.seek(0)
                st.download_button(
                    label="📥 Download Full Report as Excel",
                    data=buffer,
                    file_name="stock_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

                fig_cmp = px.bar(
                    df_summary, x="Ticker", y="Blended Score %",
                    color="Blended Score %", text="Blended Score %",
                    color_continuous_scale=["#f87171","#facc15","#4ade80"],
                    range_color=[0, 100],
                )
                fig_cmp.update_traces(texttemplate="%{text}%", textposition="outside")
                fig_cmp.update_layout(
                    paper_bgcolor="#0a0f1e", plot_bgcolor="#0d1326",
                    font=dict(color="#94a3b8"),
                    xaxis=dict(gridcolor="#1e2d4a"),
                    yaxis=dict(gridcolor="#1e2d4a", range=[0,110]),
                    showlegend=False, height=300,
                    margin=dict(l=0,r=0,t=20,b=0)
                )
                st.plotly_chart(fig_cmp, use_container_width=True)
                st.markdown("---")

            # ── One tab per stock ──
            tab_labels = [f"{t.replace('.NS','')}  {all_data[t][3]['verdict'][0].split()[0]}" for t in all_data]
            stock_tabs = st.tabs(tab_labels)

            def fmt(v, pct=False):
                if v is None: return "N/A"
                if pct: return f"{v*100:.1f}%"
                return f"{v:.2f}"

            def cmp(sv, bv, hib=True):
                if sv is None or bv is None: return "⚪"
                return "✅" if (sv > bv) == hib else "❌"

            for tab, ticker in zip(stock_tabs, all_data.keys()):
                fund, cf, tech, scores = all_data[ticker]
                verdict_text, verdict_class = scores["verdict"]
                norms  = scores["norms"]
                sector = scores["sector"]
                r_s, r_m = scores["rule"]
                g_s, g_m = scores["governance"]
                c_s, c_m = scores["cashflow"]
                m_s, m_m = scores["moat"]

                with tab:
                    # ── Header metrics ──
                    cap_type = scores.get("cap_type","Large Cap")
                    cap_icon = scores.get("cap_icon","🔵")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown(f"""<div class='metric-card'>
                            <div class='label'>Company</div>
                            <div class='value' style='font-size:15px'>{fund.get('name','N/A')}</div>
                            <div class='delta'>{cap_icon} {cap_type} · {sector}</div>
                        </div>""", unsafe_allow_html=True)
                    with col2:
                        ltp = tech.get("ltp","N/A")
                        pct = tech.get("pct_from_high","N/A")
                        st.markdown(f"""<div class='metric-card'>
                            <div class='label'>LTP</div>
                            <div class='value'>₹{ltp}</div>
                            <div class='delta'>{pct}% from 52W High</div>
                        </div>""", unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"""<div class='metric-card'>
                            <div class='label'>Blended Score</div>
                            <div class='value'>{scores['blended']}%</div>
                            <div class='delta'>ML: {scores['ml']}%</div>
                        </div>""", unsafe_allow_html=True)
                    with col4:
                        mc = fund.get("market_cap")
                        mc_str = f"₹{mc/1e12:.1f}T" if mc and mc>=1e12 else (f"₹{mc/1e9:.0f}B" if mc else "N/A")
                        st.markdown(f"""<div class='metric-card'>
                            <div class='label'>Market Cap</div>
                            <div class='value' style='font-size:20px'>{mc_str}</div>
                            <div class='delta'>52W: ₹{tech.get('low_52w','N/A')} – ₹{tech.get('high_52w','N/A')}</div>
                        </div>""", unsafe_allow_html=True)

                    # ── Decision Banner ──
                    st.markdown(f"<div class='decision-{verdict_class}'>{verdict_text}</div>", unsafe_allow_html=True)

                    # ── Rationale ──
                    rationale = generate_rationale(fund, tech, cf, scores, benchmarks.get(scores.get("cap_type","Large Cap"), {}))
                    st.markdown("<div class='section-header'>WHY THIS DECISION</div>", unsafe_allow_html=True)
                    st.markdown(rationale["summary"])

                    rat_col1, rat_col2 = st.columns(2)
                    with rat_col1:
                        if rationale["positives"]:
                            st.markdown("**✅ What's working in its favour:**")
                            for p in rationale["positives"]:
                                st.markdown(f"- {p}")
                        if rationale["neutrals"]:
                            st.markdown("**⚠️ Mixed signals to watch:**")
                            for n in rationale["neutrals"]:
                                st.markdown(f"- {n}")
                    with rat_col2:
                        if rationale["negatives"]:
                            st.markdown("**❌ Key concerns:**")
                            for n in rationale["negatives"]:
                                st.markdown(f"- {n}")
                        st.markdown("---")
                        st.markdown("**🤖 ML Model Explanation:**")
                        st.markdown(rationale["ml_explanation"])

                    # ── Score Bars ──
                    st.markdown("<div class='section-header'>SCORE BREAKDOWN</div>", unsafe_allow_html=True)
                    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                    with sc1:
                        st.metric("📊 Fundamentals + Tech", f"{r_s}/{r_m}")
                        st.progress(r_s/r_m)
                    with sc2:
                        st.metric("🏛️ Governance", f"{g_s}/{g_m}")
                        st.progress(g_s/g_m)
                    with sc3:
                        st.metric("💵 Cash Flow", f"{c_s}/{c_m}")
                        st.progress(c_s/c_m)
                    with sc4:
                        st.metric("🏰 Moat", f"{m_s}/{m_m}")
                        st.progress(m_s/m_m)
                    with sc5:
                        risk_label = tech.get("risk_label", ("⚪ N/A", "na"))
                        st.metric("⚠️ Risk Level", risk_label[0])
                        vol = tech.get("volatility")
                        st.progress(min(vol/100, 1.0) if vol else 0.0)

                    # ── Detail tabs ──
                    dtab1, dtab2, dtab3, dtab4, dtab5 = st.tabs(["📈 Price Chart","📋 Fundamentals","💵 Cash Flow","🏛️ Governance","⚠️ Risk"])

                    with dtab1:
                        if "history" in tech:
                            hist = tech["history"]
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name="Price", line=dict(color="#38bdf8", width=2)))
                            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"].rolling(50).mean(), mode="lines", name="50 MA", line=dict(color="#f59e0b", width=1, dash="dash")))
                            if len(hist) >= 200:
                                fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"].rolling(200).mean(), mode="lines", name="200 MA", line=dict(color="#a78bfa", width=1, dash="dot")))
                            fig.update_layout(paper_bgcolor="#0a0f1e", plot_bgcolor="#0d1326", font=dict(color="#94a3b8"), xaxis=dict(gridcolor="#1e2d4a"), yaxis=dict(gridcolor="#1e2d4a", title="Price (₹)"), legend=dict(bgcolor="#1a2035"), height=380, margin=dict(l=0,r=0,t=20,b=0))
                            st.plotly_chart(fig, use_container_width=True)

                            rsi_s = ta.momentum.RSIIndicator(hist["Close"], window=14).rsi()
                            fig2 = go.Figure()
                            fig2.add_trace(go.Scatter(x=hist.index, y=rsi_s, mode="lines", name="RSI", line=dict(color="#4ade80", width=2)))
                            fig2.add_hline(y=70, line_dash="dash", line_color="#f87171", annotation_text="Overbought")
                            fig2.add_hline(y=30, line_dash="dash", line_color="#4ade80", annotation_text="Oversold")
                            fig2.update_layout(paper_bgcolor="#0a0f1e", plot_bgcolor="#0d1326", font=dict(color="#94a3b8"), xaxis=dict(gridcolor="#1e2d4a"), yaxis=dict(gridcolor="#1e2d4a", title="RSI", range=[0,100]), height=200, margin=dict(l=0,r=0,t=10,b=0))
                            st.plotly_chart(fig2, use_container_width=True)

                    with dtab2:
                        bm = benchmarks.get(scores.get("cap_type","Large Cap"), {})
                        pe_val = fund.get("pe_ratio")
                        pe_sig = "⚪"
                        if pe_val:
                            pe_sig = "✅" if pe_val <= norms["pe_mid"] else ("⚠️" if pe_val <= norms["pe_max"] else "❌")
                        roe = fund.get("roe"); pm = fund.get("profit_margin")
                        rg  = fund.get("revenue_growth"); eg = fund.get("earnings_growth"); cr = fund.get("current_ratio")
                        st.info(f"🏭 Sector: **{sector}** · {cap_icon} **{cap_type}**  |  P/E norm: {norms['pe_mid']}–{norms['pe_max']}x  |  Min ROE: {norms['roe_min']*100:.0f}%  |  {'🏦 D/E skipped' if norms['skip_de'] else ''}")
                        rows = [
                            ["P/E Ratio",        fmt(fund.get("pe_ratio")),           f"{norms['pe_mid']}–{norms['pe_max']}x (sector)", pe_sig],
                            ["P/B Ratio",        fmt(fund.get("pb_ratio")),           fmt(bm.get("pb_ratio")),    cmp(fund.get("pb_ratio"), bm.get("pb_ratio"), False)],
                            ["ROE",              fmt(fund.get("roe"), True),           f"≥{norms['roe_min']*100:.0f}% (sector min)",      "✅" if roe and roe>=norms["roe_min"] else "❌"],
                            ["ROA",              fmt(fund.get("roa"), True),           fmt(bm.get("roa"), True),   cmp(fund.get("roa"), bm.get("roa"), True)],
                            ["Debt / Equity",    fmt(fund.get("debt_to_equity")),     "Skipped" if norms["skip_de"] else fmt(bm.get("debt_to_equity")), "⚪" if norms["skip_de"] else cmp(fund.get("debt_to_equity"), bm.get("debt_to_equity"), False)],
                            ["Gross Margin",     fmt(fund.get("gross_margin"), True),  fmt(bm.get("gross_margin"), True), cmp(fund.get("gross_margin"), bm.get("gross_margin"), True)],
                            ["Oper. Margin",     fmt(fund.get("operating_margin"),True),fmt(bm.get("operating_margin"),True), cmp(fund.get("operating_margin"), bm.get("operating_margin"), True)],
                            ["Profit Margin",    fmt(fund.get("profit_margin"), True), f"≥{norms['margin_min']*100:.0f}% (sector min)",   "✅" if pm and pm>=norms["margin_min"] else "❌"],
                            ["Revenue Growth",   fmt(fund.get("revenue_growth"), True),f"≥{norms['growth_min']*100:.0f}% (sector min)",   "✅" if rg and rg>norms["growth_min"] else "❌"],
                            ["Earnings Growth",  fmt(fund.get("earnings_growth"),True),f"≥{norms['growth_min']*100:.0f}% (sector min)",   "✅" if eg and eg>norms["growth_min"] else "❌"],
                            ["Current Ratio",    fmt(fund.get("current_ratio")),      "Skipped" if norms["skip_cr"] else "1.2+",          "⚪" if norms["skip_cr"] else ("✅" if cr and cr>1.2 else "❌")],
                            ["EV/EBITDA",        fmt(fund.get("ev_ebitda")),          fmt(bm.get("ev_ebitda")),   ""],
                            ["RSI (14)",         str(tech.get("rsi","N/A")),           "35–70 ideal",                     "✅" if tech.get("rsi") and 35<=tech.get("rsi")<=70 else "⚠️"],
                            ["Above 50-day MA",  "Yes" if tech.get("above_ma50")  else "No", "Yes preferred", "✅" if tech.get("above_ma50")  else "❌"],
                            ["Above 200-day MA", "Yes" if tech.get("above_ma200") else "No", "Yes preferred", "✅" if tech.get("above_ma200") else "❌"],
                            ["MACD Bullish",     "Yes" if tech.get("macd_bullish") else "No","Yes preferred", "✅" if tech.get("macd_bullish") else "❌"],
                        ]
                        st.dataframe(pd.DataFrame(rows, columns=["Metric","Stock","Target","Signal"]), use_container_width=True, hide_index=True)

                    with dtab3:
                        cfo = cf.get("cfo"); fcf = cf.get("fcf"); pat = cf.get("net_income")
                        c1,c2,c3 = st.columns(3)
                        with c1: st.metric("Operating CF", f"₹{cfo/1e9:.1f}B" if cfo else "N/A")
                        with c2: st.metric("Free Cash Flow", f"₹{fcf/1e9:.1f}B" if fcf else "N/A")
                        with c3: st.metric("Net Income", f"₹{pat/1e9:.1f}B" if pat else "N/A")
                        cf_rows = [
                            ["CFO / PAT",       cf.get("cfo_to_pat","N/A"), "≥0.8 excellent", "✅" if cf.get("cfo_to_pat") and cf.get("cfo_to_pat")>=0.8 else ("⚠️" if cf.get("cfo_to_pat") and cf.get("cfo_to_pat")>=0.5 else "❌")],
                            ["Capex / Revenue", f"{cf.get('capex_to_revenue',0)*100:.1f}%" if cf.get("capex_to_revenue") else "N/A", "≤8% asset-light", "✅" if cf.get("capex_to_revenue") and cf.get("capex_to_revenue")<=0.08 else "⚠️"],
                            ["FCF Positive",    "Yes" if fcf and fcf>0 else "No", "Yes preferred", "✅" if fcf and fcf>0 else "❌"],
                        ]
                        st.dataframe(pd.DataFrame(cf_rows, columns=["Metric","Value","Target","Signal"]), use_container_width=True, hide_index=True)

                    with dtab4:
                        promoter = fund.get("promoter_holding"); inst = fund.get("institutional_holding")
                        g1,g2 = st.columns(2)
                        with g1: st.metric("Promoter Holding", f"{promoter*100:.1f}%" if promoter else "N/A")
                        with g2: st.metric("Institutional Holding", f"{inst*100:.1f}%" if inst else "N/A")
                        if promoter and inst:
                            fig3 = go.Figure(go.Pie(
                                labels=["Promoters","Institutions","Public"],
                                values=[promoter*100, inst*100, max(0,(1-promoter-inst)*100)],
                                hole=0.5, marker_colors=["#38bdf8","#4ade80","#64748b"]
                            ))
                            fig3.update_layout(paper_bgcolor="#0a0f1e", font=dict(color="#94a3b8"), height=280, margin=dict(l=0,r=0,t=20,b=0))
                            st.plotly_chart(fig3, use_container_width=True)

                    with dtab5:
                        st.markdown("<div class='section-header'>RISK METRICS</div>", unsafe_allow_html=True)

                        vol      = tech.get("volatility")
                        mdd      = tech.get("max_drawdown")
                        beta     = tech.get("beta")
                        sharpe   = tech.get("sharpe")
                        var95    = tech.get("var_95")
                        atr_pct  = tech.get("atr_pct")
                        ret_1y   = tech.get("ret_1y")
                        rl       = tech.get("risk_label", ("⚪ N/A","na"))

                        # ── Risk overview cards ──
                        rm1, rm2, rm3, rm4 = st.columns(4)
                        with rm1:
                            st.markdown(f"""<div class='metric-card'>
                                <div class='label'>Risk Level</div>
                                <div class='value' style='font-size:18px'>{rl[0]}</div>
                                <div class='delta'>Based on annualised volatility</div>
                            </div>""", unsafe_allow_html=True)
                        with rm2:
                            st.markdown(f"""<div class='metric-card'>
                                <div class='label'>1-Year Return</div>
                                <div class='value' style='color:{"#4ade80" if ret_1y and ret_1y>0 else "#f87171"}'>{ret_1y}%</div>
                                <div class='delta'>Price change last 12 months</div>
                            </div>""", unsafe_allow_html=True)
                        with rm3:
                            st.markdown(f"""<div class='metric-card'>
                                <div class='label'>Sharpe Ratio</div>
                                <div class='value'>{sharpe if sharpe else 'N/A'}</div>
                                <div class='delta'>>1 good · >2 excellent</div>
                            </div>""", unsafe_allow_html=True)
                        with rm4:
                            st.markdown(f"""<div class='metric-card'>
                                <div class='label'>Beta vs Nifty</div>
                                <div class='value'>{beta if beta else 'N/A'}</div>
                                <div class='delta'>>1 more volatile than market</div>
                            </div>""", unsafe_allow_html=True)

                        st.markdown("")

                        # ── Risk metrics table ──
                        risk_rows = [
                            ["Annualised Volatility",  f"{vol}%" if vol else "N/A",
                             "<20% Low · 20–35% Medium · >35% High",
                             "🟢" if vol and vol<20 else ("🟡" if vol and vol<35 else "🔴")],
                            ["Max Drawdown (1Y)",      f"{mdd}%" if mdd else "N/A",
                             ">-20% acceptable · <-40% high risk",
                             "🟢" if mdd and mdd>-20 else ("🟡" if mdd and mdd>-40 else "🔴")],
                            ["Beta vs Nifty 50",       str(beta) if beta else "N/A",
                             "<0.8 defensive · 0.8–1.2 market · >1.2 aggressive",
                             "🟢" if beta and beta<0.8 else ("🟡" if beta and beta<=1.2 else "🔴")],
                            ["Sharpe Ratio",           str(sharpe) if sharpe else "N/A",
                             ">1 good · >2 excellent · <0 losing",
                             "🟢" if sharpe and sharpe>1 else ("🟡" if sharpe and sharpe>0 else "🔴")],
                            ["Value at Risk (95%,1D)", f"{var95}%" if var95 else "N/A",
                             "Max expected daily loss 95% of days",
                             "🟢" if var95 and var95>-2 else ("🟡" if var95 and var95>-4 else "🔴")],
                            ["ATR % (Daily Swing)",    f"{atr_pct}%" if atr_pct else "N/A",
                             "Average daily price range as % of price",
                             "🟢" if atr_pct and atr_pct<2 else ("🟡" if atr_pct and atr_pct<4 else "🔴")],
                        ]
                        st.dataframe(pd.DataFrame(risk_rows, columns=["Metric","Value","Interpretation","Signal"]),
                                     use_container_width=True, hide_index=True)

                        # ── Drawdown chart ──
                        if "history" in tech:
                            hist_r = tech["history"]["Close"]
                            rolling_max = hist_r.cummax()
                            dd_series   = ((hist_r - rolling_max) / rolling_max) * 100
                            fig_dd = go.Figure()
                            fig_dd.add_trace(go.Scatter(
                                x=dd_series.index, y=dd_series,
                                mode="lines", fill="tozeroy",
                                name="Drawdown %",
                                line=dict(color="#f87171", width=1.5),
                                fillcolor="rgba(248,113,113,0.15)"
                            ))
                            fig_dd.update_layout(
                                paper_bgcolor="#0a0f1e", plot_bgcolor="#0d1326",
                                font=dict(color="#94a3b8"),
                                xaxis=dict(gridcolor="#1e2d4a"),
                                yaxis=dict(gridcolor="#1e2d4a", title="Drawdown %"),
                                title=dict(text="Drawdown from Peak (1 Year)", font=dict(color="#94a3b8")),
                                height=280, margin=dict(l=0,r=0,t=40,b=0)
                            )
                            st.plotly_chart(fig_dd, use_container_width=True)

                        st.caption("⚠️ Risk metrics are based on 1-year historical data. Past volatility does not guarantee future risk levels.")
