import datetime
import pandas as pd
import streamlit as st
import yfinance as yf

# 設定網頁標題與排版
st.set_page_config(
    page_title="台股 ETF 績效排行查詢", page_icon="📈", layout="wide"
)

st.title("📈 台灣全市場股票型與主動式 ETF 績效排行")
st.write("透過自訂的起始與結束日期，自動計算並列出表現最好的前 30 名 ETF。")


# 1. 完整全市場股票型與主動式 ETF 清單
@st.cache_data
def load_etf_list():
  etf_dict = {
      "00685L": "群益台灣加權正2",
      "0050": "元大台灣50",
      "0051": "富邦中型100",
      "0052": "富邦科技",
      "0053": "元大電子",
      "0055": "元大MSCI金融",
      "0056": "元大高股息",
      "0057": "富邦摩台",
      "006203": "元大富櫃50",
      "006204": "永豐臺灣加權",
      "006208": "富邦台50",
      "00639": "富邦深漢剛",
      "00652": "富邦印度",
      "00661": "富邦台港反1",
      "00692": "富邦公司治理",
      "00701": "國泰台灣標普高股息",
      "00713": "元大台灣高息低波",
      "00728": "第一金工業30",
      "00730": "富邦臺灣優質高息",
      "00731": "FH富時高息低波",
      "00733": "富邦臺灣中小",
      "00735": "國泰日經225",
      "00736": "國泰新興市場",
      "00737": "國泰中國A50",
      "00739": "元大日經225",
      "00757": "統一FANG+",
      "00762": "元大全球未來通訊",
      "00830": "國泰費城半導體",
      "00850": "元大臺灣ESG永續",
      "00851": "元大全球未來通訊",
      "00861": "元大全球未來關鍵科技",
      "00875": "國泰台灣5G+",
      "00876": "新光臺灣半導體30",
      "00878": "國泰永續高股息",
      "00881": "國泰台灣5G+優選",
      "00882": "中信中國高股息",
      "00885": "富邦越南",
      "00891": "中信關鍵半導體",
      "00892": "富邦臺灣半導體",
      "00893": "國泰智能車",
      "00894": "中信小資高價30",
      "00895": "富邦未來車",
      "00896": "中信綠能及電動車",
      "00897": "富邦基因免疫生技",
      "00898": "國泰基因免疫革命",
      "00900": "富邦特選高股息30",
      "00901": "永豐智能車供應鏈",
      "00903": "富邦台灣中小",
      "00904": "群益半導體收益",
      "00905": "FT臺灣Smart",
      "00907": "永豐優息存股",
      "00909": "國泰數位支付",
      "00910": "第一金全球AI",
      "00911": "華南永昌S&P半導體",
      "00912": "兆豐台灣產業龍頭",
      "00913": "兆豐特選台灣晶圓製造",
      "00915": "凱基優選高股息30",
      "00916": "國泰全球品牌50",
      "00918": "大華優利高填息30",
      "00919": "群益台灣精選高息",
      "00921": "兆豐龍頭等權重",
      "00922": "國泰台灣領袖50",
      "00923": "群益台灣碳排優息",
      "00924": "復華S&P500成長",
      "00927": "群益半導體收益",
      "00929": "復華台灣科技優息",
      "00930": "永豐ESG低碳高息",
      "00932": "台新臺灣永續高息",
      "00934": "中信成長高股息",
      "00935": "野村臺灣新科技50",
      "00936": "台新臺灣優息成長",
      "00939": "統一台灣高息動能",
      "00940": "元大台灣價值高息",
      "00941": "中信上游半導體",
      "00943": "兆豐臺灣電子成長高息",
      "00944": "野村趨勢動能高息",
      "00946": "群益科技高息成長",
      "00947": "台新臺灣IC設計",
      "00949": "復華日本龍頭",
      "00951": "台新日本半導體",
      "00952": "凱基台灣優選30",
      "00956": "統一台灣核心優選",
      "00400A": "主動國泰動能高息",
      "00401A": "主動摩根台灣鑫收",
      "00402A": "主動安聯美國科技",
      "00403A": "主動統一升級50",
      "00404A": "主動聯博動能50",
      "00405A": "主動富邦台灣龍耀",
      "00406A": "主動中信台灣收益",
      "00407A": "主動凱基台灣",
      "00408A": "主動第一金優股息",
      "00409A": "主動復華全球50",
      "00410A": "主動永豐科技趨勢",
      "00411A": "主動統一前沿科技",
      "00412A": "主動安聯亞半導體",
      "00415A": "主動群益核心50",
      "00980A": "主動野村臺灣優選",
      "00981A": "主動統一台股增長",
      "00982A": "主動群益台灣強棒",
      "00983A": "主動中信ARK創新",
      "00984A": "主動安聯台灣高息",
      "00985A": "主動野村台灣50",
      "00986A": "主動台新龍頭成長",
      "00987A": "主動台新優勢成長",
      "00988A": "主動統一全球創新",
      "00989A": "主動摩根美國科技",
      "00990A": "主動元大AI新經濟",
      "00991A": "主動復華未來50",
      "00992A": "主動群益科技創新",
      "00993A": "主動安聯台灣",
      "00994A": "主動第一金台股優",
      "00995A": "主動中信台灣卓越",
      "00996A": "主動兆豐台灣豐收",
      "00997A": "主動群益美國增長",
      "00998A": "主動復華金融股息",
      "00999A": "主動野村臺灣高息",
  }
  clean_etf = {}
  for code, name in etf_dict.items():
    pure = code.split(".")[0]
    if "B" not in pure and "D" not in pure and "U" not in pure:
      clean_etf[pure] = name
  return clean_etf


etf_dict = load_etf_list()
yf_etf_list = [f"{c}.TW" for c in etf_dict.keys()]

# 側邊欄設定
st.sidebar.header("📅 查詢區間設定")
current_year = datetime.datetime.now().year
default_start = datetime.date(current_year, 1, 1)


@st.cache_data
def get_latest_date():
  df = yf.download("0050.TW", period="max", progress=False)
  if not df.empty:
    return df.index[-1].date()
  return datetime.date.today()


default_end = get_latest_date()

start_date = st.sidebar.date_input("起始日期", default_start)
end_date = st.sidebar.date_input("結束日期", default_end)

if st.sidebar.button("🚀 開始計算排行", type="primary"):
  if start_date >= end_date:
    st.error("❌ 起始日期必須早於結束日期！")
  else:
    with st.spinner("正在抓取最新市場數據並計算 Top 30，請稍候..."):
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
        st.warning("⚠️ 未抓取到有效資料，請檢查網路或日期區間。")
      else:
        s_prices = data.bfill().iloc[0]
        e_prices = data.ffill().iloc[-1]
        returns = (e_prices - s_prices) / s_prices * 100
        returns = returns.dropna()

        top_30 = returns.sort_values(ascending=False).head(30)
        rows = []

        for rank, (p_code, ret) in enumerate(top_30.items(), 1):
          name = etf_dict.get(p_code, "未知名稱")
          s_p = s_prices[p_code]
          e_p = e_prices[p_code]
          ret_val = float(ret)

          first_idx = data[p_code].first_valid_index()
          is_after = (
              first_idx > pd.to_datetime(s_str)
              if first_idx is not None
              else False
          )
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

        df_result = pd.DataFrame(rows)
        st.success(f"✅ 查詢成功！區間：{s_str} 至 {e_str}")
        st.caption("💡 註：ETF在起始日期還未上市的股價會標註 * 號")
        st.dataframe(df_result, use_container_width=True, hide_index=True)