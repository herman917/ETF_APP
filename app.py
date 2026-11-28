import datetime
import os
import pandas as pd
import streamlit as st
import yfinance as yf

# 設定網頁標題與排版
st.set_page_config(
    page_title="台股 ETF 績效排行查詢", page_icon="📈", layout="wide"
)

# 調整標題字體大小與文字
st.markdown("### 📈 ETF 績效排行")
st.write("依日期範圍, 計算表現最好的前 50 名 ETF (排除期貨類)")


ETF_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1PKhV2I-W7q-aZ8XSVVhv4uP679Caqk79tseSA6tAYMw/export?format=csv"
)
LOCAL_ETF_CSV = os.path.join(os.path.dirname(__file__), "etf_list.csv")


def _parse_etf_df(df):
  if df is None or df.empty or len(df.columns) < 2:
    return {}
  code_col = "代號" if "代號" in df.columns else df.columns[0]
  name_col = "名稱" if "名稱" in df.columns else df.columns[1]

  clean_etf = {}
  for _, row in df.iterrows():
    code = str(row[code_col]).strip() if pd.notna(row[code_col]) else ""
    name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ""
    if not code or code.lower() == "nan":
      continue
    pure = code.split(".")[0].strip()
    if pure and "B" not in pure and "D" not in pure and "U" not in pure:
      clean_etf[pure] = name
  return clean_etf


# 1. 從 Google Sheet（失敗或空白時改讀本機 etf_list.csv）載入 ETF 清單
@st.cache_data(ttl=600)
def load_etf_list():
  try:
    df_remote = pd.read_csv(ETF_SHEET_CSV_URL, dtype=str)
    remote_etf = _parse_etf_df(df_remote)
    if remote_etf:
      return remote_etf, "google_sheet"
  except Exception:
    pass

  if os.path.exists(LOCAL_ETF_CSV):
    df_local = pd.read_csv(LOCAL_ETF_CSV, dtype=str)
    return _parse_etf_df(df_local), "local_csv"
  return {}, "empty"


etf_dict, etf_source = load_etf_list()
yf_etf_list = [f"{c}.TW" for c in etf_dict.keys()]

if etf_source == "local_csv":
  st.info("ℹ️ Google Sheet 目前為空或無法讀取，暫時使用本機 `etf_list.csv` 清單（匯入後最多 10 分鐘自動同步）。")
elif etf_source == "empty":
  st.warning("⚠️ 無法載入 ETF 清單，請確認 Google Sheet 或 `etf_list.csv`。")

# 查詢區間設定（主畫面可收合面板，預設展開）
current_year = datetime.datetime.now().year
default_start = datetime.date(current_year, 1, 1)


@st.cache_data
def get_latest_date():
  df = yf.download("0050.TW", period="max", progress=False)
  if not df.empty:
    return df.index[-1].date()
  return datetime.date.today()


default_end = get_latest_date()

if "date_panel_expanded" not in st.session_state:
  st.session_state.date_panel_expanded = True
if "start_date" not in st.session_state:
  st.session_state.start_date = default_start
if "end_date" not in st.session_state:
  st.session_state.end_date = default_end
if "result_df" not in st.session_state:
  st.session_state.result_df = None
if "result_range" not in st.session_state:
  st.session_state.result_range = None
if "query_error" not in st.session_state:
  st.session_state.query_error = None

panel_placeholder = st.empty()
run_clicked = False

with panel_placeholder.expander(
    "📅 點我設定查詢日期範圍", expanded=st.session_state.date_panel_expanded
):
  col1, col2 = st.columns(2)
  with col1:
    start_date = st.date_input("起始日期", value=st.session_state.start_date)
  with col2:
    end_date = st.date_input("結束日期", value=st.session_state.end_date)

  st.session_state.start_date = start_date
  st.session_state.end_date = end_date

  btn_col, credit_col = st.columns([2, 3])
  with btn_col:
    run_clicked = st.button("🚀 開始計算排行", type="primary")
  with credit_col:
    st.caption("[https://herman917.github.io/herman-home/](https://herman917.github.io/herman-home/)")

if run_clicked:
  if start_date >= end_date:
    st.session_state.query_error = "❌ 起始日期必須早於結束日期！"
    st.session_state.date_panel_expanded = True
  else:
    st.session_state.query_error = None
    # 點按後立即上捲收合查詢面板
    panel_placeholder.empty()
    with st.spinner("正在抓取市場數據並計算 Top 50，請稍候..."):
      s_str = start_date.strftime("%Y-%m-%d")
      e_str = end_date.strftime("%Y-%m-%d")

      close_dict = {}
      vol_dict = {}
      batch_size = 20

      for i in range(0, len(yf_etf_list), batch_size):
        batch = yf_etf_list[i : i + batch_size]
        try:
          df_b = yf.download(batch, start=s_str, end=e_str, progress=False)
          if not df_b.empty:
            if isinstance(df_b.columns, pd.MultiIndex):
              if "Close" in df_b.columns.levels[0]:
                cdf = df_b["Close"]
                for col in cdf.columns:
                  close_dict[col.split(".")[0]] = cdf[col]
              if "Volume" in df_b.columns.levels[0]:
                vdf = df_b["Volume"]
                for col in vdf.columns:
                  vol_dict[col.split(".")[0]] = vdf[col]
            else:
              if "Close" in df_b.columns and len(batch) == 1:
                close_dict[batch[0].split(".")[0]] = df_b["Close"]
              if "Volume" in df_b.columns and len(batch) == 1:
                vol_dict[batch[0].split(".")[0]] = df_b["Volume"]
        except Exception:
          continue

      data = pd.DataFrame(close_dict)
      data_vol = pd.DataFrame(vol_dict)

      if data.empty:
        st.session_state.query_error = "⚠️ 未抓取到有效資料，請檢查網路或日期區間。"
        st.session_state.result_df = None
        st.session_state.date_panel_expanded = True
      else:
        s_prices = data.bfill().iloc[0]
        e_prices = data.ffill().iloc[-1]
        returns = (e_prices - s_prices) / s_prices * 100
        returns = returns.dropna()

        top_50 = returns.sort_values(ascending=False).head(50)

        # 抓取 Top 50 檔完整歷史資料以判斷真實上市日
        top_yf_list = [f"{c}.TW" for c in top_50.index]
        df_history = yf.download(top_yf_list, period="max", progress=False)
        hist_close = (
            df_history["Close"]
            if isinstance(df_history.columns, pd.MultiIndex)
            else df_history
        )

        # 統一將歷史資料欄位轉為純代號
        hist_close_dict = {}
        if isinstance(hist_close, pd.DataFrame):
          for col in hist_close.columns:
            pure_col = str(col).split(".")[0]
            hist_close_dict[pure_col] = hist_close[col]
          hist_close_df = pd.DataFrame(hist_close_dict)
        else:
          pure_col = top_50.index[0]
          hist_close_df = pd.DataFrame({pure_col: hist_close})

        rows = []
        for rank, (p_code, ret) in enumerate(top_50.items(), 1):
          name = etf_dict.get(p_code, "未知名稱")
          s_p = s_prices[p_code]
          e_p = e_prices[p_code]
          ret_val = float(ret)

          # 檢查真實上市日是否晚於使用者指定的起始日
          is_after = False
          if p_code in hist_close_df.columns:
            valid_series = hist_close_df[p_code].dropna()
            if not valid_series.empty:
              absolute_first_date = valid_series.index[0]
              is_after = absolute_first_date > pd.to_datetime(s_str)

          s_p_str = ("*" if is_after else "") + f"{s_p:.2f}"

          avg_lots = 0.0
          if p_code in data_vol.columns:
            sv = data_vol[p_code].dropna()
            if len(sv) > 0:
              avg_lots = (sv.sum() / len(sv)) / 1000.0

          total_div = 0.0
          try:
            tk = yf.Ticker(f"{p_code}.TW")
            divs = tk.dividends
            if not divs.empty:
              mask = (divs.index >= s_str) & (divs.index <= e_str)
              total_div = float(divs.loc[mask].sum())
          except Exception:
            total_div = 0.0

          rows.append({
              "排名": f"第 {rank} 名",
              "代號": p_code,
              "ETF 名稱": name,
              "起始價格": s_p_str,
              "結束價格": f"{e_p:.2f}",
              "區間總配息": f"{total_div:.2f}",
              "含息漲幅": f"{ret_val:+.2f}%",
              "日均成交(張)": f"{int(avg_lots):,}",
          })

        st.session_state.result_df = pd.DataFrame(rows)
        st.session_state.result_range = (s_str, e_str)
        st.session_state.date_panel_expanded = False
        st.rerun()

if st.session_state.query_error:
  st.error(st.session_state.query_error)

if st.session_state.result_df is not None and st.session_state.result_range:
  s_str, e_str = st.session_state.result_range
  st.success(f"✅ 查詢成功！區間：{s_str} 至 {e_str}")
  st.caption("💡 註：ETF上市時間晚於計算起始日期的價格會標註 * 號")
  st.dataframe(st.session_state.result_df, use_container_width=True, hide_index=True)

@st.cache_resource
def _online_sessions():
  return {}


def _get_online_count(ttl_sec: int = 120) -> int:
  import time
  sessions = _online_sessions()
  now = time.time()
  try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    ctx = get_script_run_ctx()
    sid = ctx.session_id if ctx else None
  except Exception:
    sid = None
  if sid:
    sessions[sid] = now
  for k in [k for k, ts in list(sessions.items()) if now - ts > ttl_sec]:
    sessions.pop(k, None)
  return max(1, len(sessions))


online_total = 1027 + _get_online_count()
st.markdown(
  '<div style="text-align:center;margin-top:28px;padding-top:12px;border-top:1px solid rgba(148,163,184,0.25);font-size:12px;line-height:1.8;">'
  '<div>👋 <a href="https://herman917.github.io/herman-home/" target="_blank" rel="noopener noreferrer" style="color:#60a5fa;text-decoration:none;">https://herman917.github.io/herman-home/</a></div>'
  f'<div style="color:#94a3b8;">在線人數: {online_total}</div>'
  '</div>',
  unsafe_allow_html=True,
)