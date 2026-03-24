"""
======================================================
  GLOBAL STOCK ANALYZER — STREAMLIT WEB APP
  India (NSE) + US Markets
  Run with: streamlit run stock_app.py
======================================================
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import time
import io
import ta
import plotly.graph_objects as go
import plotly.express as px

warnings.filterwarnings("ignore")

st.set_page_config(page_title="Global Stock Analyzer", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Space Mono', monospace; }
.stApp { background-color: #0a0f1e; color: #e2e8f0; }
.metric-card { background: linear-gradient(135deg,#1a2035 0%,#141928 100%); border: 1px solid #2d3a5a; border-radius: 12px; padding: 18px; text-align: center; margin: 6px 0; }
.metric-card .label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 1px; font-family: 'Space Mono', monospace; }
.metric-card .value { font-size: 24px; font-weight: 700; color: #f1f5f9; margin: 6px 0; }
.metric-card .delta { font-size: 12px; color: #94a3b8; }
.decision-strong-buy { background: linear-gradient(135deg,#052e16,#14532d); border: 2px solid #22c55e; border-radius: 16px; padding: 22px; text-align: center; font-family: 'Space Mono',monospace; font-size: 20px; color: #4ade80; font-weight: 700; letter-spacing: 2px; }
.decision-buy { background: linear-gradient(135deg,#052e16,#166534); border: 2px solid #86efac; border-radius: 16px; padding: 22px; text-align: center; font-family: 'Space Mono',monospace; font-size: 20px; color: #86efac; font-weight: 700; letter-spacing: 2px; }
.decision-hold { background: linear-gradient(135deg,#1c1400,#292107); border: 2px solid #facc15; border-radius: 16px; padding: 22px; text-align: center; font-family: 'Space Mono',monospace; font-size: 20px; color: #facc15; font-weight: 700; letter-spacing: 2px; }
.decision-avoid { background: linear-gradient(135deg,#1c0505,#290707); border: 2px solid #f87171; border-radius: 16px; padding: 22px; text-align: center; font-family: 'Space Mono',monospace; font-size: 20px; color: #f87171; font-weight: 700; letter-spacing: 2px; }
.section-header { font-family: 'Space Mono',monospace; font-size: 12px; color: #38bdf8; text-transform: uppercase; letter-spacing: 2px; border-bottom: 1px solid #1e3a5f; padding-bottom: 8px; margin: 18px 0 12px 0; }
div[data-testid="stSidebarContent"] { background-color: #0d1326; border-right: 1px solid #1e2d4a; }
.stButton > button { background: linear-gradient(135deg,#1d4ed8,#1e40af); color: white; border: none; border-radius: 10px; padding: 12px 32px; font-family: 'Space Mono',monospace; font-size: 13px; letter-spacing: 1px; width: 100%; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════
# BENCHMARK TICKERS
# ═══════════════════════════════════════════
IN_LARGE = {
    "Banking":    ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS","AXISBANK.NS"],
    "IT":         ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS"],
    "Energy":     ["RELIANCE.NS","ONGC.NS","BPCL.NS","NTPC.NS"],
    "FMCG":       ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS"],
    "Auto":       ["MARUTI.NS","TATAMOTORS.NS","M&M.NS","BAJAJ-AUTO.NS"],
    "Pharma":     ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS"],
    "Infra":      ["LT.NS","POWERGRID.NS","ADANIPORTS.NS"],
    "Metals":     ["TATASTEEL.NS","HINDALCO.NS","JSWSTEEL.NS"],
    "Telecom":    ["BHARTIARTL.NS"],
    "Consumer":   ["TITAN.NS","ASIANPAINT.NS"],
    "Cement":     ["ULTRACEMCO.NS","GRASIM.NS"],
}
IN_MID = {
    "Banking":    ["FEDERALBNK.NS","IDFCFIRSTB.NS","BANDHANBNK.NS","MUTHOOTFIN.NS"],
    "IT":         ["MPHASIS.NS","PERSISTENT.NS","COFORGE.NS","KPITTECH.NS"],
    "Pharma":     ["TORNTPHARM.NS","ALKEM.NS","AUROPHARMA.NS","LALPATHLAB.NS"],
    "Auto":       ["BALKRISIND.NS","ESCORTS.NS","ASHOKLEY.NS","TVSMOTOR.NS"],
    "Consumer":   ["VOLTAS.NS","TRENT.NS"],
    "Industrials":["CUMMINSIND.NS","THERMAX.NS","BHEL.NS","SIEMENS.NS"],
    "Chemicals":  ["PIIND.NS","ATUL.NS","DEEPAKNTR.NS"],
    "RealEstate": ["GODREJPROP.NS","OBEROIRLTY.NS","PHOENIXLTD.NS"],
}
IN_SMALL = {
    "Banking":    ["RBLBANK.NS","UJJIVANSFB.NS","EQUITASBNK.NS"],
    "IT":         ["TANLA.NS","INTELLECT.NS","MASTEK.NS"],
    "Pharma":     ["GRANULES.NS","GLENMARK.NS","JBCHEPHARM.NS"],
    "Consumer":   ["VSTIND.NS","NYKAA.NS"],
    "Industrials":["GRINDWELL.NS","RATNAMANI.NS","WELCORP.NS"],
    "Chemicals":  ["FINEORG.NS","NAVINFLUOR.NS","GALAXYSURF.NS"],
}
US_SP500 = {
    "Tech":       ["AAPL","MSFT","NVDA","GOOGL","META"],
    "Finance":    ["JPM","BAC","GS","MS","WFC"],
    "Healthcare": ["JNJ","UNH","PFE","MRK","ABBV"],
    "Consumer":   ["AMZN","WMT","PG","KO","PEP"],
    "Energy":     ["XOM","CVX","COP","SLB"],
    "Industrials":["CAT","HON","GE","MMM"],
    "Materials":  ["LIN","APD","SHW","NEM"],
}
US_NASDAQ = {
    "Tech":       ["AAPL","MSFT","NVDA","GOOGL","META","AMZN","TSLA"],
    "Biotech":    ["AMGN","GILD","BIIB","REGN"],
    "SemiCond":   ["AVGO","QCOM","AMD","INTC","MU"],
    "Software":   ["CRM","ADBE","PYPL","INTU","SNOW"],
}
US_RUSSELL = {
    "Finance":    ["SFNC","HTLF","FFIN","TOWN"],
    "Healthcare": ["ACAD","THRM","PRAX","INVA"],
    "Consumer":   ["JACK","KRUS","PLAY"],
    "Tech":       ["QTWO","ALKT","IRTC"],
    "Industrials":["SKYW","ARCB","MATX","MRTN"],
}

IN_LARGE_THRESH = 500_000_000_000
IN_MID_THRESH   = 150_000_000_000
US_LARGE_THRESH =  10_000_000_000
US_MID_THRESH   =   2_000_000_000

def detect_market(ticker):
    t = ticker.upper()
    if t.endswith(".NS") or t.endswith(".BO"): return "IN"
    return "US"

def classify_stock(market_cap, market):
    if market == "IN":
        if market_cap is None or market_cap >= IN_LARGE_THRESH: return "Large Cap","🔵","Nifty 50"
        elif market_cap >= IN_MID_THRESH: return "Mid Cap","🟡","Nifty Midcap 150"
        else: return "Small Cap","🟢","Nifty Smallcap 250"
    else:
        if market_cap is None or market_cap >= US_LARGE_THRESH: return "Large Cap","🔵","S&P 500"
        elif market_cap >= US_MID_THRESH: return "Mid Cap","🟡","NASDAQ 100"
        else: return "Small Cap","🟢","Russell 2000"

SECTOR_NORMS = {
    "Technology":         {"pe_max":45,"pe_mid":32,"roe_min":0.15,"margin_min":0.12,"growth_min":0.07,"skip_de":False,"skip_cr":False,"pb_focus":False},
    "Financial Services": {"pe_max":25,"pe_mid":16,"roe_min":0.10,"margin_min":0.12,"growth_min":0.07,"skip_de":True, "skip_cr":True, "pb_focus":True },
    "Banking":            {"pe_max":25,"pe_mid":16,"roe_min":0.10,"margin_min":0.12,"growth_min":0.07,"skip_de":True, "skip_cr":True, "pb_focus":True },
    "Consumer Defensive": {"pe_max":65,"pe_mid":48,"roe_min":0.18,"margin_min":0.10,"growth_min":0.06,"skip_de":False,"skip_cr":False,"pb_focus":False},
    "Consumer Cyclical":  {"pe_max":45,"pe_mid":30,"roe_min":0.12,"margin_min":0.07,"growth_min":0.08,"skip_de":False,"skip_cr":False,"pb_focus":False},
    "Healthcare":         {"pe_max":40,"pe_mid":28,"roe_min":0.12,"margin_min":0.12,"growth_min":0.08,"skip_de":False,"skip_cr":False,"pb_focus":False},
    "Energy":             {"pe_max":18,"pe_mid":12,"roe_min":0.08,"margin_min":0.05,"growth_min":0.04,"skip_de":False,"skip_cr":False,"pb_focus":False},
    "Basic Materials":    {"pe_max":18,"pe_mid":12,"roe_min":0.08,"margin_min":0.07,"growth_min":0.04,"skip_de":False,"skip_cr":False,"pb_focus":False},
    "Industrials":        {"pe_max":35,"pe_mid":24,"roe_min":0.10,"margin_min":0.07,"growth_min":0.07,"skip_de":False,"skip_cr":False,"pb_focus":False},
    "Communication":      {"pe_max":35,"pe_mid":24,"roe_min":0.10,"margin_min":0.08,"growth_min":0.07,"skip_de":False,"skip_cr":False,"pb_focus":False},
    "Real Estate":        {"pe_max":40,"pe_mid":28,"roe_min":0.08,"margin_min":0.12,"growth_min":0.06,"skip_de":False,"skip_cr":False,"pb_focus":True },
    "Utilities":          {"pe_max":25,"pe_mid":18,"roe_min":0.08,"margin_min":0.08,"growth_min":0.04,"skip_de":False,"skip_cr":False,"pb_focus":False},
}
DEFAULT_NORMS = {"pe_max":35,"pe_mid":25,"roe_min":0.10,"margin_min":0.08,"growth_min":0.07,"skip_de":False,"skip_cr":False,"pb_focus":False}

def get_sector_norms(sector):
    if not sector or sector=="N/A": return DEFAULT_NORMS
    for key in SECTOR_NORMS:
        if key.lower() in sector.lower(): return SECTOR_NORMS[key]
    return DEFAULT_NORMS

CAP_WEIGHTS = {
    "Large Cap": {"rule":0.35,"ml":0.25,"cashflow":0.20,"governance":0.12,"moat":0.08},
    "Mid Cap":   {"rule":0.30,"ml":0.25,"cashflow":0.18,"governance":0.12,"moat":0.15},
    "Small Cap": {"rule":0.28,"ml":0.22,"cashflow":0.15,"governance":0.20,"moat":0.15},
}

METRICS = ["pe_ratio","pb_ratio","roe","roa","debt_to_equity","revenue_growth",
           "earnings_growth","profit_margin","gross_margin","operating_margin",
           "current_ratio","institutional_holding"]

def _build_bm(ticker_dict):
    sec_recs = {s:[] for s in ticker_dict}
    for sname, tickers in ticker_dict.items():
        for t in tickers:
            try:
                info = yf.Ticker(t).info
                sec_recs[sname].append({
                    "pe_ratio":info.get("trailingPE"),"pb_ratio":info.get("priceToBook"),
                    "roe":info.get("returnOnEquity"),"roa":info.get("returnOnAssets"),
                    "debt_to_equity":info.get("debtToEquity"),"revenue_growth":info.get("revenueGrowth"),
                    "earnings_growth":info.get("earningsGrowth"),"profit_margin":info.get("profitMargins"),
                    "gross_margin":info.get("grossMargins"),"operating_margin":info.get("operatingMargins"),
                    "current_ratio":info.get("currentRatio"),"institutional_holding":info.get("heldPercentInstitutions"),
                })
                time.sleep(0.15)
            except: pass
    sec_meds = []
    for recs in sec_recs.values():
        if not recs: continue
        df=pd.DataFrame(recs); med={}
        for col in METRICS:
            if col in df.columns:
                v=df[col].dropna().median()
                if not np.isnan(v): med[col]=v
        if med: sec_meds.append(med)
    if not sec_meds: return {}
    df_m=pd.DataFrame(sec_meds)
    return {col:df_m[col].dropna().median() for col in METRICS if col in df_m.columns}

@st.cache_data(ttl=3600)
def build_all_benchmarks():
    return {
        "IN_Large": _build_bm(IN_LARGE), "IN_Mid":  _build_bm(IN_MID),   "IN_Small":  _build_bm(IN_SMALL),
        "US_SP500": _build_bm(US_SP500), "US_NASDAQ":_build_bm(US_NASDAQ),"US_Russell":_build_bm(US_RUSSELL),
    }

def get_bm_key(market, cap_type):
    if market=="IN": return {"Large Cap":"IN_Large","Mid Cap":"IN_Mid","Small Cap":"IN_Small"}[cap_type]
    return {"Large Cap":"US_SP500","Mid Cap":"US_NASDAQ","Small Cap":"US_Russell"}[cap_type]

@st.cache_data(ttl=900)
def get_stock_data(ticker):
    try:
        stock=yf.Ticker(ticker); info=stock.info
        fund={
            "name":info.get("longName",ticker),"sector":info.get("sector","N/A"),
            "currency":info.get("financialCurrency","INR"),"market_cap":info.get("marketCap"),
            "pe_ratio":info.get("trailingPE"),"pb_ratio":info.get("priceToBook"),
            "roe":info.get("returnOnEquity"),"roa":info.get("returnOnAssets"),
            "debt_to_equity":info.get("debtToEquity"),"revenue_growth":info.get("revenueGrowth"),
            "earnings_growth":info.get("earningsGrowth"),"profit_margin":info.get("profitMargins"),
            "gross_margin":info.get("grossMargins"),"operating_margin":info.get("operatingMargins"),
            "current_ratio":info.get("currentRatio"),"ev_ebitda":info.get("enterpriseToEbitda"),
            "promoter_holding":info.get("heldPercentInsiders"),"institutional_holding":info.get("heldPercentInstitutions"),
        }
        cf={}
        try:
            cfs=stock.cashflow; inc=stock.financials
            if cfs is not None and not cfs.empty:
                for lbl in ["Operating Cash Flow","Total Cash From Operating Activities","Cash Flow From Continuing Operating Activities"]:
                    if lbl in cfs.index: cf["cfo"]=float(cfs.loc[lbl].iloc[0]); break
                for lbl in ["Capital Expenditure","Purchase Of PPE","Purchases Of Property Plant And Equipment"]:
                    if lbl in cfs.index: cf["capex"]=abs(float(cfs.loc[lbl].iloc[0])); break
                if cf.get("cfo") and cf.get("capex"): cf["fcf"]=cf["cfo"]-cf["capex"]
            if inc is not None and not inc.empty:
                for lbl in ["Net Income","Net Income Common Stockholders"]:
                    if lbl in inc.index: cf["net_income"]=float(inc.loc[lbl].iloc[0]); break
                for lbl in ["Total Revenue","Operating Revenue"]:
                    if lbl in inc.index: cf["revenue"]=float(inc.loc[lbl].iloc[0]); break
            if cf.get("cfo") and cf.get("net_income") and cf["net_income"]!=0:
                cf["cfo_to_pat"]=round(cf["cfo"]/cf["net_income"],2)
            if cf.get("capex") and cf.get("revenue") and cf["revenue"]!=0:
                cf["capex_to_revenue"]=round(cf["capex"]/cf["revenue"],4)
        except: pass

        tech={}
        try:
            hist=stock.history(period="1y")
            try:
                mkt_idx="^NSEI" if (ticker.endswith(".NS") or ticker.endswith(".BO")) else "^GSPC"
                idx_close=yf.Ticker(mkt_idx).history(period="1y")["Close"]
            except: idx_close=None

            if not hist.empty and len(hist)>=50:
                close=hist["Close"]; returns=close.pct_change().dropna()
                rsi=ta.momentum.RSIIndicator(close,window=14).rsi()
                macd_obj=ta.trend.MACD(close); macd_line=macd_obj.macd(); sig_line=macd_obj.macd_signal()
                ma50=close.rolling(50).mean().iloc[-1]
                ma200=close.rolling(200).mean().iloc[-1] if len(close)>=200 else None
                ltp=close.iloc[-1]
                volatility=round(returns.std()*np.sqrt(252)*100,2)
                max_drawdown=round(((close-close.cummax())/close.cummax()).min()*100,2)
                sharpe=round(((returns.mean()-0.065/252)/returns.std())*np.sqrt(252),2) if returns.std()!=0 else None
                var_95=round(np.percentile(returns,5)*100,2)
                ret_1y=round(((ltp-close.iloc[0])/close.iloc[0])*100,2)
                beta=None
                try:
                    if idx_close is not None:
                        ir=idx_close.pct_change().dropna(); common=returns.index.intersection(ir.index)
                        if len(common)>30:
                            sr=returns.loc[common]; nr=ir.loc[common]
                            cov=np.cov(sr,nr)[0][1]; var=np.var(nr)
                            beta=round(cov/var,2) if var!=0 else None
                except: pass
                try: atr_pct=round((ta.volatility.AverageTrueRange(hist["High"],hist["Low"],close,window=14).average_true_range().iloc[-1]/ltp)*100,2)
                except: atr_pct=None
                if volatility<20: rl=("🟢 Low Risk","low")
                elif volatility<35: rl=("🟡 Medium Risk","medium")
                else: rl=("🔴 High Risk","high")
                tech={
                    "ltp":round(ltp,2),"rsi":round(float(rsi.iloc[-1]),2),
                    "ma50":round(ma50,2),"ma200":round(ma200,2) if ma200 else None,
                    "above_ma50":ltp>ma50,"above_ma200":(ltp>ma200) if ma200 else None,
                    "macd_bullish":float(macd_line.iloc[-1])>float(sig_line.iloc[-1]),
                    "high_52w":round(close.max(),2),"low_52w":round(close.min(),2),
                    "pct_from_high":round(((ltp-close.max())/close.max())*100,1),
                    "vol_trend_up":hist["Volume"].iloc[-10:].mean()>hist["Volume"].iloc[-30:].mean(),
                    "history":hist,"volatility":volatility,"max_drawdown":max_drawdown,
                    "beta":beta,"sharpe":sharpe,"var_95":var_95,"atr_pct":atr_pct,
                    "ret_1y":ret_1y,"risk_label":rl,
                }
        except: pass
        return fund, cf, tech
    except Exception as e:
        st.warning(f"⚠️ Could not fetch {ticker}: {e}")
        return None, {}, {}

def score_stock(fund, tech, cf, benchmarks, market):
    sc={}; sector=fund.get("sector","N/A"); norms=get_sector_norms(sector)
    mc=fund.get("market_cap"); cap_type,cap_icon,idx_name=classify_stock(mc,market)
    bm_key=get_bm_key(market,cap_type); bm=benchmarks.get(bm_key,{})
    sc.update({"sector":sector,"norms":norms,"cap_type":cap_type,"cap_icon":cap_icon,"index_name":idx_name,"bm_key":bm_key})

    pe=fund.get("pe_ratio"); roe=fund.get("roe"); de=fund.get("debt_to_equity"); b_de=bm.get("debt_to_equity")
    rg=fund.get("revenue_growth"); eg=fund.get("earnings_growth"); pm=fund.get("profit_margin")
    pb=fund.get("pb_ratio"); b_pb=bm.get("pb_ratio"); cr=fund.get("current_ratio")
    rsi=tech.get("rsi"); above50=tech.get("above_ma50"); above200=tech.get("above_ma200"); macd_b=tech.get("macd_bullish")
    pa=1.3 if cap_type=="Small Cap" else (1.15 if cap_type=="Mid Cap" else 1.0)
    gb=1.5 if cap_type=="Small Cap" else (1.2 if cap_type=="Mid Cap" else 1.0)
    ml=0.7 if cap_type=="Small Cap" else (0.85 if cap_type=="Mid Cap" else 1.0)
    pe_max_a=norms["pe_max"]*pa; pe_mid_a=norms["pe_mid"]*pa
    gt=norms["growth_min"]/gb; mt=norms["margin_min"]*ml

    r=0; r_max=13; pe_notes=[]
    if pe:
        if pe<=pe_mid_a: r+=2; pe_notes.append(f"✅ PE {pe:.1f} ≤ {cap_type} midpoint {pe_mid_a:.0f}")
        elif pe<=pe_max_a: r+=1; pe_notes.append(f"✅ PE {pe:.1f} within {cap_type} norm ≤{pe_max_a:.0f}")
        else: pe_notes.append(f"❌ PE {pe:.1f} above ceiling {pe_max_a:.0f}")
    sc["pe_notes"]=pe_notes
    if roe: r+=2 if roe>=norms["roe_min"]*1.25 else (1 if roe>=norms["roe_min"] else 0)
    if not norms["skip_de"] and de and b_de and de<b_de: r+=1
    if rg and rg>gt: r+=1
    if eg and eg>gt: r+=1
    if pm and pm>mt: r+=1
    if not norms["skip_cr"] and cr and cr>1.2: r+=1
    if norms["pb_focus"] and pb and pb<2.5: r+=1
    if rsi: r+=2 if 35<=rsi<=70 else (1 if rsi<35 else 0)
    if above50: r+=1
    if above200: r+=2
    if macd_b: r+=1
    sc["rule"]=(min(r,r_max),r_max)

    g=0; g_max=4
    promoter=fund.get("promoter_holding"); inst=fund.get("institutional_holding")
    roa=fund.get("roa"); b_roa=bm.get("roa"); b_inst=bm.get("institutional_holding")
    pmin=0.50 if cap_type=="Small Cap" else (0.40 if cap_type=="Mid Cap" else 0.35)
    if promoter and promoter>=pmin: g+=1
    if inst and b_inst and inst>=b_inst: g+=1
    elif inst and inst>=0.15: g+=1
    if pb and b_pb and 1.0<=pb<=b_pb*2.5: g+=1
    if roa and b_roa and roa>b_roa: g+=1
    elif roa and roa>0.04: g+=1
    sc["governance"]=(g,g_max)

    c=0; c_max=5
    cfo=cf.get("cfo"); fcf=cf.get("fcf"); cfo_pat=cf.get("cfo_to_pat"); capex_rev=cf.get("capex_to_revenue")
    c+=1 if cfo is None else (1 if cfo>0 else 0)
    if cfo_pat is not None: c+=2 if cfo_pat>=0.7 else (1 if cfo_pat>=0.4 else 0)
    else: c+=1
    c+=1 if fcf is None else (1 if fcf>0 else 0)
    cap_t=0.20 if sector and any(s in sector for s in ["Energy","Utilities","Industrials","Materials"]) else 0.12
    c+=1 if capex_rev is None else (1 if capex_rev<=cap_t else 0)
    sc["cashflow"]=(min(c,c_max),c_max)

    m=0; m_max=5
    gm=fund.get("gross_margin"); b_gm=bm.get("gross_margin"); om=fund.get("operating_margin"); b_om=bm.get("operating_margin")
    if roe: m+=2 if roe>=norms["roe_min"]*1.4 else (1 if roe>=norms["roe_min"] else 0)
    if gm and b_gm and gm>=b_gm: m+=1
    elif gm and gm>0.12: m+=1
    if om and b_om and om>=b_om: m+=1
    elif om and om>0.08: m+=1
    mc_m=5e11 if cap_type=="Large Cap" else (5e10 if cap_type=="Mid Cap" else 5e9)
    if mc and mc>=mc_m: m+=1
    sc["moat"]=(min(m,m_max),m_max)

    def norm(val,ref,hib=True):
        if not val or not ref or ref==0: return 0.5
        rv=val/ref; return min(rv,2)/2 if hib else min(ref/val,2)/2

    feats=[norm(roe,norms["roe_min"],True),norm(pe,pe_mid_a,False),
           0.5 if norms["skip_de"] else norm(de,b_de,False),norm(pm,mt,True),
           norm(rg,gt,True),norm(eg,gt,True),
           0.80 if (rsi and 35<=rsi<=70) else (0.50 if rsi and rsi<35 else 0.20),
           1.0 if above50 else 0.0,1.0 if above200 else 0.0,1.0 if macd_b else 0.0,
           1.0 if tech.get("vol_trend_up") else 0.5,min((promoter or 0.35)/0.5,1.0),
           min((inst or 0.20)/0.3,1.0),min((cfo_pat or 0.7)/1.0,1.0),1.0 if (fcf and fcf>0) else 0.5]
    wts=[0.10,0.08,0.06,0.07,0.07,0.06,0.08,0.07,0.08,0.05,0.03,0.07,0.05,0.08,0.06]
    wts=[w/sum(wts) for w in wts]
    ml_conf=round(sum(f*w for f,w in zip(feats,wts))*100,1)
    sc["ml"]=ml_conf

    r_s,r_m=sc["rule"]; g_s,g_m=sc["governance"]; c_s,c_m=sc["cashflow"]; m_s,m_m=sc["moat"]
    cw=CAP_WEIGHTS[cap_type]
    blended=((r_s/r_m)*100*cw["rule"]+ml_conf*cw["ml"]+(c_s/c_m)*100*cw["cashflow"]+(g_s/g_m)*100*cw["governance"]+(m_s/m_m)*100*cw["moat"])
    sc["blended"]=round(blended,1)
    if blended>=62: verdict=("✅ STRONG BUY","strong-buy")
    elif blended>=50: verdict=("📈 BUY / CONSIDER","buy")
    elif blended>=38: verdict=("⚠️ HOLD / WATCH","hold")
    else: verdict=("❌ AVOID","avoid")
    sc["verdict"]=verdict
    return sc

def generate_rationale(fund, tech, cf, scores, bm):
    norms=scores["norms"]; blended=scores["blended"]; ml=scores["ml"]; cap_type=scores["cap_type"]; sector=scores["sector"]
    pe=fund.get("pe_ratio"); roe=fund.get("roe"); de=fund.get("debt_to_equity")
    rg=fund.get("revenue_growth"); eg=fund.get("earnings_growth"); pm=fund.get("profit_margin")
    rsi=tech.get("rsi"); above50=tech.get("above_ma50"); above200=tech.get("above_ma200"); macd_b=tech.get("macd_bullish")
    cfo_pat=cf.get("cfo_to_pat"); fcf=cf.get("fcf"); promoter=fund.get("promoter_holding"); inst=fund.get("institutional_holding")
    pa=1.3 if cap_type=="Small Cap" else (1.15 if cap_type=="Mid Cap" else 1.0)
    pe_mid_a=norms["pe_mid"]*pa; pe_max_a=norms["pe_max"]*pa
    pos=[]; neg=[]; neu=[]

    if pe:
        if pe<=pe_mid_a: pos.append(f"**Valuation attractive** — PE {pe:.1f}x below the {cap_type} midpoint {pe_mid_a:.0f}x.")
        elif pe<=pe_max_a: neu.append(f"**Valuation fair** — PE {pe:.1f}x within the {cap_type} range.")
        else: neg.append(f"**Valuation stretched** — PE {pe:.1f}x exceeds the {cap_type} ceiling {pe_max_a:.0f}x.")
    if roe:
        if roe>=norms["roe_min"]*1.3: pos.append(f"**Strong profitability** — ROE {roe*100:.1f}% well above {sector} minimum.")
        elif roe>=norms["roe_min"]: neu.append(f"**Adequate profitability** — ROE {roe*100:.1f}% meets the sector minimum.")
        else: neg.append(f"**Weak profitability** — ROE {roe*100:.1f}% below {sector} minimum.")
    if rg and eg:
        gt=norms["growth_min"]
        if rg>gt and eg>gt: pos.append(f"**Growth solid** — Revenue +{rg*100:.1f}% and earnings +{eg*100:.1f}%, both above {gt*100:.0f}% target.")
        elif rg>gt: neu.append(f"**Revenue growing but earnings lagging** — Revenue +{rg*100:.1f}%, earnings +{eg*100:.1f}%.")
        else: neg.append(f"**Growth weak** — Revenue +{rg*100:.1f}% and earnings +{eg*100:.1f}% below target.")
    if cfo_pat is not None:
        if cfo_pat>=0.8: pos.append(f"**Earnings are cash-backed** — CFO/PAT {cfo_pat:.2f} confirms profits are real.")
        elif cfo_pat>=0.5: neu.append(f"**Moderate cash conversion** — CFO/PAT {cfo_pat:.2f}.")
        else: neg.append(f"**Poor cash conversion** — CFO/PAT {cfo_pat:.2f} is a red flag.")
    if fcf is not None:
        if fcf>0: pos.append("**Free cash flow positive** — Self-funding after capex.")
        else: neu.append("**Negative FCF** — Heavy investment phase; watch the trend.")
    if rsi:
        if 35<=rsi<=70: pos.append(f"**Healthy momentum** — RSI {rsi} in ideal zone.")
        elif rsi>70: neg.append(f"**Overbought** — RSI {rsi} signals the stock may be overextended.")
        else: neu.append(f"**Oversold** — RSI {rsi} could bounce but risky.")
    if above200 and above50: pos.append("**Strong trend** — Above both 50-day and 200-day MAs.")
    elif above200 and not above50: neu.append("**Mixed trend** — Above 200MA but below 50MA.")
    elif not above200: neg.append("**Below 200MA** — Long-term downtrend; requires strong conviction.")
    if macd_b: pos.append("**MACD bullish** — Increasing upward momentum.")
    else: neg.append("**MACD bearish** — Weakening momentum.")
    if promoter and promoter>=0.45: pos.append(f"**Strong insider holding** — {promoter*100:.1f}% confidence.")
    elif promoter and promoter<0.25: neg.append(f"**Low insider holding** — Only {promoter*100:.1f}%.")
    if inst and inst>=0.25: pos.append(f"**Strong institutional backing** — {inst*100:.1f}%.")

    if ml>=62: ml_exp=f"ML model ({ml}%) strongly confirms — most of 15 weighted factors are positive."
    elif ml>=50: ml_exp=f"ML model ({ml}%) moderately supports — more positives than negatives."
    elif ml>=38: ml_exp=f"ML model ({ml}%) neutral — mixed signals across valuation, momentum, and fundamentals."
    else: ml_exp=f"ML model ({ml}%) flags caution — multiple key factors scoring poorly."

    if blended>=62: summary=f"**{fund.get('name','This stock')} scores {blended}%.** Fundamentals, technicals, and cash flows align. Risk/reward looks favourable."
    elif blended>=50: summary=f"**{fund.get('name','This stock')} scores {blended}%.** More positives than negatives — reasonable buy for moderate risk tolerance."
    elif blended>=38: summary=f"**{fund.get('name','This stock')} scores {blended}%.** Real merits but real concerns too. Wait for a cleaner setup."
    else: summary=f"**{fund.get('name','This stock')} scores {blended}%.** Multiple red flags. Avoid until picture improves."
    return {"summary":summary,"positives":pos,"negatives":neg,"neutrals":neu,"ml_explanation":ml_exp}

def fmt(v, pct=False):
    if v is None: return "N/A"
    if pct: return f"{v*100:.1f}%"
    return f"{v:.2f}"

def cmp(sv, bv, hib=True):
    if sv is None or bv is None: return "⚪"
    return "✅" if (sv>bv)==hib else "❌"

# ═══════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════
if "confirmed_tickers" not in st.session_state: st.session_state.confirmed_tickers=[]
if "confirmed_market"  not in st.session_state: st.session_state.confirmed_market="Auto-detect"
if "quick_load"        not in st.session_state: st.session_state.quick_load=""

with st.sidebar:
    st.markdown("## 📈 Global Stock Analyzer")
    st.markdown("*🇮🇳 India NSE · 🇺🇸 US Markets*")
    st.markdown("---")
    market_override=st.radio("Market",["Auto-detect","🇮🇳 India (NSE)","🇺🇸 US Markets"],index=0)
    st.markdown("---")
    st.markdown("### Enter Tickers")
    if market_override=="🇮🇳 India (NSE)": st.markdown("Type symbol — `.NS` added automatically"); dft="RELIANCE\nTATAMOTORS\nZOMATO"
    elif market_override=="🇺🇸 US Markets": st.markdown("Type symbol — e.g. `AAPL`, `NVDA`"); dft="AAPL\nNVDA\nJPM"
    else: st.markdown("Indian: type symbol | US: type as-is (e.g. AAPL)"); dft="RELIANCE\nAAPL\nTATAMOTORS"
    if st.session_state.quick_load: dft=st.session_state.quick_load
    raw_input=st.text_area("Tickers:",value=dft,height=140,label_visibility="collapsed")

    st.markdown("**Quick picks:**")
    quick_all={"🏦 IN Banks":"HDFCBANK\nICICIBANK\nSBIN","💻 IN IT":"TCS\nINFY\nWIPRO",
               "🚗 IN Auto":"MARUTI\nTATAMOTORS\nM&M","🍎 US Tech":"AAPL\nMSFT\nNVDA",
               "💊 US Health":"JNJ\nPFE\nMRK","🏦 US Banks":"JPM\nBAC\nGS"}
    cols=st.columns(2)
    for i,(label,preset) in enumerate(quick_all.items()):
        if cols[i%2].button(label,key=f"qp_{label}"):
            st.session_state.quick_load=preset; st.rerun()

    st.markdown("---")
    if st.button("🔍 Analyze Stocks",type="primary"):
        raw_list=[t.strip().upper() for t in raw_input.strip().split("\n") if t.strip()]
        fixed=[]
        for t in raw_list:
            mo=market_override
            if mo=="Auto-detect":
                if detect_market(t)=="IN" and not t.endswith(".NS") and not t.endswith(".BO"): t+=".NS"
            elif mo=="🇮🇳 India (NSE)":
                if not t.endswith(".NS") and not t.endswith(".BO"): t+=".NS"
            fixed.append(t)
        st.session_state.confirmed_tickers=fixed; st.session_state.confirmed_market=market_override; st.session_state.quick_load=""

    if st.session_state.confirmed_tickers:
        st.markdown("**Analyzing:**")
        for t in st.session_state.confirmed_tickers:
            flag="🇮🇳" if (t.endswith(".NS") or t.endswith(".BO")) else "🇺🇸"
            st.markdown(f"&nbsp;&nbsp;{flag} `{t}`")

    analyze_btn=bool(st.session_state.confirmed_tickers)
    st.markdown("---")
    st.markdown("⚠️ *Educational only. Not financial advice.*")

# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════
st.markdown("# 📊 Global Stock Analyzer")
st.markdown("*🇮🇳 India · 🇺🇸 US · Fundamental · Technical · Risk · ML Scoring*")
st.markdown("---")

if not analyze_btn:
    st.markdown("""<div style='text-align:center;padding:60px 0;'>
        <div style='font-size:64px;margin-bottom:20px;'>📈</div>
        <div style='font-family:Space Mono,monospace;font-size:18px;color:#94a3b8;'>Enter tickers in the sidebar and click Analyze</div>
        <div style='margin-top:12px;font-size:14px;color:#475569;'>🇮🇳 Indian: RELIANCE, TCS &nbsp;|&nbsp; 🇺🇸 US: AAPL, NVDA, JPM</div>
    </div>""", unsafe_allow_html=True)
else:
    tickers=st.session_state.confirmed_tickers
    with st.spinner("📊 Building 6 benchmarks (IN Large/Mid/Small + US S&P500/NASDAQ/Russell)... ~2 min first time"):
        benchmarks=build_all_benchmarks()
    st.success("✅ Benchmarks ready — 🇮🇳 Nifty 50 · Midcap 150 · Smallcap 250 &nbsp;|&nbsp; 🇺🇸 S&P 500 · NASDAQ 100 · Russell 2000")

    all_data={}
    for ticker in tickers:
        with st.spinner(f"Fetching {ticker}..."):
            fund,cf,tech=get_stock_data(ticker)
        if fund:
            market="IN" if (ticker.endswith(".NS") or ticker.endswith(".BO")) else "US"
            scores=score_stock(fund,tech,cf,benchmarks,market)
            all_data[ticker]=(fund,cf,tech,scores,market)

    if not all_data:
        st.error("No valid data. Check your ticker symbols.")
    else:
        summary_rows=[]
        for t,(f,c,tc,sc,mkt) in all_data.items():
            r_s,r_m=sc["rule"]; g_s,g_m=sc["governance"]; c_s,c_m=sc["cashflow"]; m_s,m_m=sc["moat"]
            curr="₹" if mkt=="IN" else "$"
            summary_rows.append({
                "Ticker":t,"Market":"🇮🇳 India" if mkt=="IN" else "🇺🇸 US","Company":f.get("name",t),
                "Cap Type":f"{sc['cap_icon']} {sc['cap_type']}","Benchmark":sc["index_name"],
                "Sector":f.get("sector","N/A"),"LTP":f"{curr}{tc.get('ltp','N/A')}",
                "Score %":sc["blended"],"ML %":sc["ml"],"Rules":f"{r_s}/{r_m}",
                "Gov":f"{g_s}/{g_m}","Cash Flow":f"{c_s}/{c_m}","Moat":f"{m_s}/{m_m}",
                "Risk":tc.get("risk_label",("N/A","na"))[0],"1Y Return %":tc.get("ret_1y","N/A"),
                "Volatility %":tc.get("volatility","N/A"),"Max DD %":tc.get("max_drawdown","N/A"),
                "Sharpe":tc.get("sharpe","N/A"),"Beta":tc.get("beta","N/A"),
                "P/E":f.get("pe_ratio","N/A"),"ROE %":round(f.get("roe",0)*100,1) if f.get("roe") else "N/A",
                "Rev Growth %":round(f.get("revenue_growth",0)*100,1) if f.get("revenue_growth") else "N/A",
                "CFO/PAT":c.get("cfo_to_pat","N/A"),"Insider %":round(f.get("promoter_holding",0)*100,1) if f.get("promoter_holding") else "N/A",
                "Decision":sc["verdict"][0],
            })
        df_summary=pd.DataFrame(summary_rows)

        if len(all_data)>1:
            st.markdown("<div class='section-header'>COMPARISON OVERVIEW</div>",unsafe_allow_html=True)
            disp=["Ticker","Market","Company","Cap Type","Benchmark","LTP","Score %","ML %","Risk","Decision"]
            st.dataframe(df_summary[disp],use_container_width=True,hide_index=True)
            fig_c=px.bar(df_summary,x="Ticker",y="Score %",color="Score %",text="Score %",
                         color_continuous_scale=["#f87171","#facc15","#4ade80"],range_color=[0,100])
            fig_c.update_traces(texttemplate="%{text}%",textposition="outside")
            fig_c.update_layout(paper_bgcolor="#0a0f1e",plot_bgcolor="#0d1326",font=dict(color="#94a3b8"),
                                xaxis=dict(gridcolor="#1e2d4a"),yaxis=dict(gridcolor="#1e2d4a",range=[0,115]),
                                showlegend=False,height=300,margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig_c,use_container_width=True)
            buf=io.BytesIO()
            with pd.ExcelWriter(buf,engine="openpyxl") as w:
                df_summary.to_excel(w,sheet_name="Summary",index=False)
                df_summary[["Ticker","Market","Company","Cap Type","Benchmark","Sector","P/E","ROE %","Rev Growth %","Decision"]].to_excel(w,sheet_name="Fundamentals",index=False)
                df_summary[["Ticker","Market","Company","Risk","1Y Return %","Volatility %","Max DD %","Sharpe","Beta","Decision"]].to_excel(w,sheet_name="Risk",index=False)
            buf.seek(0)
            st.download_button("📥 Download Excel Report",data=buf,file_name="stock_analysis.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            st.markdown("---")

        tab_labels=[f"{t.replace('.NS','').replace('.BO','')} {all_data[t][3]['verdict'][0].split()[0]}" for t in all_data]
        stock_tabs=st.tabs(tab_labels)

        for tab,ticker in zip(stock_tabs,all_data.keys()):
            fund,cf,tech,scores,market=all_data[ticker]
            vtext,vclass=scores["verdict"]; norms=scores["norms"]; sector=scores["sector"]
            cap_type=scores["cap_type"]; cap_icon=scores["cap_icon"]; idx_name=scores["index_name"]
            bm=benchmarks.get(scores["bm_key"],{})
            r_s,r_m=scores["rule"]; g_s,g_m=scores["governance"]; c_s,c_m=scores["cashflow"]; m_s,m_m=scores["moat"]
            curr="₹" if market=="IN" else "$"; flag="🇮🇳" if market=="IN" else "🇺🇸"
            rl=tech.get("risk_label",("N/A","na"))

            with tab:
                h1,h2,h3,h4=st.columns(4)
                with h1:
                    st.markdown(f"""<div class='metric-card'><div class='label'>Company</div>
                        <div class='value' style='font-size:13px'>{fund.get('name','N/A')}</div>
                        <div class='delta'>{flag} {cap_icon} {cap_type} · {sector}</div></div>""",unsafe_allow_html=True)
                with h2:
                    ltp=tech.get('ltp','N/A'); pct=tech.get('pct_from_high','N/A')
                    st.markdown(f"""<div class='metric-card'><div class='label'>LTP</div>
                        <div class='value'>{curr}{ltp}</div><div class='delta'>{pct}% from 52W High</div></div>""",unsafe_allow_html=True)
                with h3:
                    st.markdown(f"""<div class='metric-card'><div class='label'>Score · Risk</div>
                        <div class='value'>{scores['blended']}%</div>
                        <div class='delta'>{rl[0]} · ML {scores['ml']}%</div></div>""",unsafe_allow_html=True)
                with h4:
                    mc=fund.get("market_cap")
                    if mc: mc_s=f"{curr}{mc/1e12:.1f}T" if mc>=1e12 else (f"{curr}{mc/1e9:.0f}B" if mc>=1e9 else f"{curr}{mc/1e6:.0f}M")
                    else: mc_s="N/A"
                    st.markdown(f"""<div class='metric-card'><div class='label'>Mkt Cap · Index</div>
                        <div class='value' style='font-size:18px'>{mc_s}</div>
                        <div class='delta'>{idx_name}</div></div>""",unsafe_allow_html=True)

                st.markdown(f"<div class='decision-{vclass}'>{vtext}</div>",unsafe_allow_html=True)

                rat=generate_rationale(fund,tech,cf,scores,bm)
                st.markdown("<div class='section-header'>WHY THIS DECISION</div>",unsafe_allow_html=True)
                st.markdown(rat["summary"])
                rc1,rc2=st.columns(2)
                with rc1:
                    if rat["positives"]:
                        st.markdown("**✅ Working in its favour:**")
                        for p in rat["positives"]: st.markdown(f"- {p}")
                    if rat["neutrals"]:
                        st.markdown("**⚠️ Mixed signals:**")
                        for n in rat["neutrals"]: st.markdown(f"- {n}")
                with rc2:
                    if rat["negatives"]:
                        st.markdown("**❌ Key concerns:**")
                        for n in rat["negatives"]: st.markdown(f"- {n}")
                    st.markdown("---")
                    st.markdown("**🤖 ML:**")
                    st.markdown(rat["ml_explanation"])

                st.markdown("<div class='section-header'>SCORE BREAKDOWN</div>",unsafe_allow_html=True)
                sb1,sb2,sb3,sb4,sb5=st.columns(5)
                vol=tech.get("volatility")
                with sb1: st.metric("📊 Rules",f"{r_s}/{r_m}"); st.progress(r_s/r_m)
                with sb2: st.metric("🏛️ Gov",f"{g_s}/{g_m}"); st.progress(g_s/g_m)
                with sb3: st.metric("💵 CF",f"{c_s}/{c_m}"); st.progress(c_s/c_m)
                with sb4: st.metric("🏰 Moat",f"{m_s}/{m_m}"); st.progress(m_s/m_m)
                with sb5: st.metric("⚠️ Risk",rl[0]); st.progress(min(vol/100,1.0) if vol else 0.0)

                dt1,dt2,dt3,dt4,dt5=st.tabs(["📈 Chart","📋 Fundamentals","💵 Cash Flow","🏛️ Governance","⚠️ Risk"])

                with dt1:
                    if "history" in tech:
                        hist=tech["history"]
                        fig=go.Figure()
                        fig.add_trace(go.Scatter(x=hist.index,y=hist["Close"],mode="lines",name="Price",line=dict(color="#38bdf8",width=2)))
                        fig.add_trace(go.Scatter(x=hist.index,y=hist["Close"].rolling(50).mean(),mode="lines",name="50 MA",line=dict(color="#f59e0b",width=1,dash="dash")))
                        if len(hist)>=200: fig.add_trace(go.Scatter(x=hist.index,y=hist["Close"].rolling(200).mean(),mode="lines",name="200 MA",line=dict(color="#a78bfa",width=1,dash="dot")))
                        fig.update_layout(paper_bgcolor="#0a0f1e",plot_bgcolor="#0d1326",font=dict(color="#94a3b8"),
                                          xaxis=dict(gridcolor="#1e2d4a"),yaxis=dict(gridcolor="#1e2d4a",title=f"Price ({curr})"),
                                          legend=dict(bgcolor="#1a2035"),height=380,margin=dict(l=0,r=0,t=20,b=0))
                        st.plotly_chart(fig,use_container_width=True)
                        rsi_s=ta.momentum.RSIIndicator(hist["Close"],window=14).rsi()
                        fig2=go.Figure()
                        fig2.add_trace(go.Scatter(x=hist.index,y=rsi_s,mode="lines",name="RSI",line=dict(color="#4ade80",width=2)))
                        fig2.add_hline(y=70,line_dash="dash",line_color="#f87171",annotation_text="Overbought")
                        fig2.add_hline(y=30,line_dash="dash",line_color="#4ade80",annotation_text="Oversold")
                        fig2.update_layout(paper_bgcolor="#0a0f1e",plot_bgcolor="#0d1326",font=dict(color="#94a3b8"),
                                           xaxis=dict(gridcolor="#1e2d4a"),yaxis=dict(gridcolor="#1e2d4a",title="RSI",range=[0,100]),height=200,margin=dict(l=0,r=0,t=10,b=0))
                        st.plotly_chart(fig2,use_container_width=True)

                with dt2:
                    pe_val=fund.get("pe_ratio"); pa=1.3 if cap_type=="Small Cap" else (1.15 if cap_type=="Mid Cap" else 1.0)
                    pe_sig="⚪"
                    if pe_val: pe_sig="✅" if pe_val<=norms["pe_mid"]*pa else ("⚠️" if pe_val<=norms["pe_max"]*pa else "❌")
                    roe_v=fund.get("roe"); pm_v=fund.get("profit_margin"); rg_v=fund.get("revenue_growth")
                    eg_v=fund.get("earnings_growth"); cr_v=fund.get("current_ratio")
                    gt=norms["growth_min"]; mt=norms["margin_min"]
                    st.info(f"{flag} **{sector}** · {cap_icon} **{cap_type}** · Benchmark: **{idx_name}**  |  PE: {norms['pe_mid']}–{norms['pe_max']}x  |  Min ROE: {norms['roe_min']*100:.0f}%")
                    rows=[
                        ["P/E Ratio",      fmt(fund.get("pe_ratio")),           f"{norms['pe_mid']}–{norms['pe_max']}x",pe_sig],
                        ["P/B Ratio",      fmt(fund.get("pb_ratio")),           fmt(bm.get("pb_ratio")),               cmp(fund.get("pb_ratio"),bm.get("pb_ratio"),False)],
                        ["ROE",            fmt(fund.get("roe"),True),            f"≥{norms['roe_min']*100:.0f}%",       "✅" if roe_v and roe_v>=norms["roe_min"] else "❌"],
                        ["ROA",            fmt(fund.get("roa"),True),            fmt(bm.get("roa"),True),               cmp(fund.get("roa"),bm.get("roa"),True)],
                        ["Debt/Equity",    fmt(fund.get("debt_to_equity")),     "Skipped" if norms["skip_de"] else fmt(bm.get("debt_to_equity")),"⚪" if norms["skip_de"] else cmp(fund.get("debt_to_equity"),bm.get("debt_to_equity"),False)],
                        ["Gross Margin",   fmt(fund.get("gross_margin"),True),   fmt(bm.get("gross_margin"),True),      cmp(fund.get("gross_margin"),bm.get("gross_margin"),True)],
                        ["Oper. Margin",   fmt(fund.get("operating_margin"),True),fmt(bm.get("operating_margin"),True),cmp(fund.get("operating_margin"),bm.get("operating_margin"),True)],
                        ["Profit Margin",  fmt(fund.get("profit_margin"),True),  f"≥{mt*100:.0f}%",                    "✅" if pm_v and pm_v>=mt else "❌"],
                        ["Rev Growth",     fmt(fund.get("revenue_growth"),True), f"≥{gt*100:.0f}%",                    "✅" if rg_v and rg_v>gt else "❌"],
                        ["EPS Growth",     fmt(fund.get("earnings_growth"),True),f"≥{gt*100:.0f}%",                    "✅" if eg_v and eg_v>gt else "❌"],
                        ["Current Ratio",  fmt(fund.get("current_ratio")),      "Skipped" if norms["skip_cr"] else "1.2+","⚪" if norms["skip_cr"] else ("✅" if cr_v and cr_v>1.2 else "❌")],
                        ["EV/EBITDA",      fmt(fund.get("ev_ebitda")),           fmt(bm.get("ev_ebitda")),              ""],
                        ["RSI (14)",       str(tech.get("rsi","N/A")),           "35–70 ideal",                        "✅" if tech.get("rsi") and 35<=tech.get("rsi")<=70 else "⚠️"],
                        ["Above 50 MA",    "Yes" if tech.get("above_ma50") else "No","Yes preferred",                  "✅" if tech.get("above_ma50") else "❌"],
                        ["Above 200 MA",   "Yes" if tech.get("above_ma200") else "No","Yes preferred",                 "✅" if tech.get("above_ma200") else "❌"],
                        ["MACD Bullish",   "Yes" if tech.get("macd_bullish") else "No","Yes preferred",                "✅" if tech.get("macd_bullish") else "❌"],
                    ]
                    st.dataframe(pd.DataFrame(rows,columns=["Metric","Stock","Target","Signal"]),use_container_width=True,hide_index=True)

                with dt3:
                    cfo_v=cf.get("cfo"); fcf_v=cf.get("fcf"); pat=cf.get("net_income")
                    c1,c2,c3=st.columns(3)
                    with c1: st.metric("Operating CF",f"{curr}{cfo_v/1e9:.1f}B" if cfo_v else "N/A")
                    with c2: st.metric("Free Cash Flow",f"{curr}{fcf_v/1e9:.1f}B" if fcf_v else "N/A")
                    with c3: st.metric("Net Income",f"{curr}{pat/1e9:.1f}B" if pat else "N/A")
                    cf_rows=[
                        ["CFO/PAT",       cf.get("cfo_to_pat","N/A"),"≥0.8 excellent","✅" if cf.get("cfo_to_pat") and cf.get("cfo_to_pat")>=0.8 else ("⚠️" if cf.get("cfo_to_pat") and cf.get("cfo_to_pat")>=0.5 else "❌")],
                        ["Capex/Revenue", f"{cf.get('capex_to_revenue',0)*100:.1f}%" if cf.get("capex_to_revenue") else "N/A","≤12% preferred","✅" if cf.get("capex_to_revenue") and cf.get("capex_to_revenue")<=0.12 else "⚠️"],
                        ["FCF Positive",  "Yes" if fcf_v and fcf_v>0 else "No","Yes preferred","✅" if fcf_v and fcf_v>0 else "❌"],
                    ]
                    st.dataframe(pd.DataFrame(cf_rows,columns=["Metric","Value","Target","Signal"]),use_container_width=True,hide_index=True)

                with dt4:
                    promoter=fund.get("promoter_holding"); inst=fund.get("institutional_holding")
                    g1,g2=st.columns(2)
                    insider_label="Promoter" if market=="IN" else "Insider"
                    with g1: st.metric(f"{insider_label} Holding",f"{promoter*100:.1f}%" if promoter else "N/A")
                    with g2: st.metric("Institutional Holding",f"{inst*100:.1f}%" if inst else "N/A")
                    if promoter and inst:
                        fig3=go.Figure(go.Pie(labels=[insider_label,"Institutions","Public"],
                                              values=[promoter*100,inst*100,max(0,(1-promoter-inst)*100)],
                                              hole=0.5,marker_colors=["#38bdf8","#4ade80","#64748b"]))
                        fig3.update_layout(paper_bgcolor="#0a0f1e",font=dict(color="#94a3b8"),height=280,margin=dict(l=0,r=0,t=20,b=0))
                        st.plotly_chart(fig3,use_container_width=True)

                with dt5:
                    st.markdown("<div class='section-header'>RISK METRICS</div>",unsafe_allow_html=True)
                    vol=tech.get("volatility"); mdd=tech.get("max_drawdown"); beta=tech.get("beta")
                    sharpe=tech.get("sharpe"); var95=tech.get("var_95"); atr_pct=tech.get("atr_pct"); ret_1y=tech.get("ret_1y")
                    rm1,rm2,rm3,rm4=st.columns(4)
                    with rm1:
                        st.markdown(f"""<div class='metric-card'><div class='label'>Risk Level</div>
                            <div class='value' style='font-size:16px'>{rl[0]}</div>
                            <div class='delta'>Annualised volatility</div></div>""",unsafe_allow_html=True)
                    with rm2:
                        color="#4ade80" if ret_1y and ret_1y>0 else "#f87171"
                        st.markdown(f"""<div class='metric-card'><div class='label'>1-Year Return</div>
                            <div class='value' style='color:{color}'>{ret_1y}%</div>
                            <div class='delta'>Price change last 12M</div></div>""",unsafe_allow_html=True)
                    with rm3:
                        st.markdown(f"""<div class='metric-card'><div class='label'>Sharpe Ratio</div>
                            <div class='value'>{sharpe if sharpe else 'N/A'}</div>
                            <div class='delta'>>1 good · >2 excellent</div></div>""",unsafe_allow_html=True)
                    with rm4:
                        idx_lbl="Nifty 50" if market=="IN" else "S&P 500"
                        st.markdown(f"""<div class='metric-card'><div class='label'>Beta vs {idx_lbl}</div>
                            <div class='value'>{beta if beta else 'N/A'}</div>
                            <div class='delta'>>1 more volatile</div></div>""",unsafe_allow_html=True)
                    st.markdown("")
                    risk_rows=[
                        ["Annualised Volatility",f"{vol}%" if vol else "N/A","<20% Low · 20–35% Med · >35% High","🟢" if vol and vol<20 else ("🟡" if vol and vol<35 else "🔴")],
                        ["Max Drawdown (1Y)",     f"{mdd}%" if mdd else "N/A",">-20% ok · <-40% high risk","🟢" if mdd and mdd>-20 else ("🟡" if mdd and mdd>-40 else "🔴")],
                        ["Beta vs Index",         str(beta) if beta else "N/A","<0.8 defensive · 0.8-1.2 market · >1.2 aggressive","🟢" if beta and beta<0.8 else ("🟡" if beta and beta<=1.2 else "🔴")],
                        ["Sharpe Ratio",          str(sharpe) if sharpe else "N/A",">1 good · >2 excellent","🟢" if sharpe and sharpe>1 else ("🟡" if sharpe and sharpe>0 else "🔴")],
                        ["VaR (95%, 1D)",         f"{var95}%" if var95 else "N/A","Max expected daily loss","🟢" if var95 and var95>-2 else ("🟡" if var95 and var95>-4 else "🔴")],
                        ["ATR % (Daily Swing)",   f"{atr_pct}%" if atr_pct else "N/A","Avg daily price range","🟢" if atr_pct and atr_pct<2 else ("🟡" if atr_pct and atr_pct<4 else "🔴")],
                    ]
                    st.dataframe(pd.DataFrame(risk_rows,columns=["Metric","Value","Interpretation","Signal"]),use_container_width=True,hide_index=True)
                    if "history" in tech:
                        hc=tech["history"]["Close"]; dd_s=((hc-hc.cummax())/hc.cummax())*100
                        fig_dd=go.Figure()
                        fig_dd.add_trace(go.Scatter(x=dd_s.index,y=dd_s,mode="lines",fill="tozeroy",
                                                    line=dict(color="#f87171",width=1.5),fillcolor="rgba(248,113,113,0.15)"))
                        fig_dd.update_layout(paper_bgcolor="#0a0f1e",plot_bgcolor="#0d1326",font=dict(color="#94a3b8"),
                                             xaxis=dict(gridcolor="#1e2d4a"),yaxis=dict(gridcolor="#1e2d4a",title="Drawdown %"),
                                             title=dict(text="Drawdown from Peak (1Y)",font=dict(color="#94a3b8")),
                                             height=260,margin=dict(l=0,r=0,t=40,b=0))
                        st.plotly_chart(fig_dd,use_container_width=True)
                    st.caption("⚠️ Risk metrics based on 1-year historical data. Past volatility ≠ future risk.")
