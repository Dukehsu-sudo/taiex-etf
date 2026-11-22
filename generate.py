#!/usr/bin/env python3
"""
每日自動抓取 TAIEX / 0050 / 00631L / 00685L（還原後）資料
產生互動查詢頁 index.html

預估價公式：
  0050     = 大盤點數 × 近 240 個交易日平均比例
  00631L   = 大盤點數 × 近   2 個交易日平均比例
  00685L   = 大盤點數 × 近   2 個交易日平均比例
  比例     = ETF 還原收盤價 / TAIEX
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print("請先安裝: pip install yfinance pandas")
    raise

# ========== 設定 ==========
TICKERS = {
    "^TWII": "TAIEX",
    "0050.TW": "0050",
    "00631L.TW": "00631L",
    "00685L.TW": "00685L",
}

# 各標的使用的平均比例天數
RATIO_DAYS = {
    "0050": 240,
    "00631L": 2,
    "00685L": 2,
}

CHART_YEARS = 12
OUTPUT = Path("index.html")


def fetch_data():
    end = datetime.now()
    start = end - timedelta(days=365 * CHART_YEARS + 30)

    print(f"正在抓取資料 {start.date()} ~ {end.date()} ...")
    data = {}
    for sym, name in TICKERS.items():
        h = yf.Ticker(sym).history(start=start.strftime("%Y-%m-%d"), auto_adjust=True)
        if h.empty:
            raise RuntimeError(f"無法取得 {sym} 資料")
        data[name] = h["Close"]

    df = pd.DataFrame(data).dropna()
    print(f"共 {len(df)} 筆交易日  ({df.index[0].date()} ~ {df.index[-1].date()})")
    return df


def calc_ratios(df: pd.DataFrame) -> dict:
    """依各標的設定天數計算平均比例"""
    ratios = {}
    for col, days in RATIO_DAYS.items():
        n = min(days, len(df))
        sub = df.tail(n)
        ratios[col] = float((sub[col] / sub["TAIEX"]).mean())
        print(f"  {col}: 近 {n} 日平均比例 = {ratios[col]:.10f}")
    return ratios


def build_chart_data(df: pd.DataFrame) -> list:
    records = []
    for idx, row in df.iterrows():
        records.append({
            "d": idx.strftime("%Y-%m-%d"),
            "t": round(float(row["TAIEX"]), 2),
            "a": round(float(row["0050"]), 2),
            "b": round(float(row["00631L"]), 2),
            "c": round(float(row["00685L"]), 2),
        })
    return records


def build_html(df: pd.DataFrame, ratios: dict, chart: list) -> str:
    latest = df.iloc[-1]
    latest_date = latest.name.strftime("%Y-%m-%d")
    prices = {
        "TAIEX": round(float(latest["TAIEX"]), 2),
        "0050": round(float(latest["0050"]), 2),
        "00631L": round(float(latest["00631L"]), 2),
        "00685L": round(float(latest["00685L"]), 2),
    }
    last_update = datetime.now().strftime("%Y/%m/%d %H:%M")

    ratios_json = json.dumps(ratios, ensure_ascii=False)
    prices_json = json.dumps(prices, ensure_ascii=False)
    chart_json = json.dumps(chart, ensure_ascii=False)

    days_0050 = RATIO_DAYS["0050"]
    days_l = RATIO_DAYS["00631L"]

    html = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>台股 0050 / 正2 合理價估算</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f1419;
    --card: #1a2332;
    --text: #e7e9ea;
    --muted: #8b98a5;
    --accent: #1d9bf0;
    --green: #00ba7c;
    --red: #f4212e;
    --border: #2f3336;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans TC", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
    padding: 16px;
    max-width: 720px;
    margin: 0 auto;
  }}
  h1 {{ font-size: 1.3rem; margin-bottom: 4px; }}
  .sub {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 18px; }}
  .card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 14px;
  }}
  .card h2 {{
    font-size: 0.98rem;
    margin-bottom: 12px;
    color: var(--accent);
  }}
  .input-row {{
    display: flex;
    gap: 10px;
    align-items: center;
  }}
  input[type="number"] {{
    flex: 1;
    background: #0f1419;
    border: 1px solid var(--border);
    color: var(--text);
    padding: 11px 14px;
    border-radius: 8px;
    font-size: 1.1rem;
    font-weight: 600;
  }}
  button {{
    background: var(--accent);
    border: none;
    color: #fff;
    padding: 11px 18px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    white-space: nowrap;
  }}
  button:hover {{ opacity: 0.9; }}
  .hint {{
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 8px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
  }}
  th, td {{
    padding: 9px 6px;
    text-align: right;
    border-bottom: 1px solid var(--border);
  }}
  th {{
    color: var(--muted);
    font-weight: 500;
    font-size: 0.78rem;
  }}
  td:first-child, th:first-child {{ text-align: left; }}
  .pos {{ color: var(--green); }}
  .neg {{ color: var(--red); }}
  .neu {{ color: var(--muted); }}
  .name {{ font-weight: 600; }}
  .note {{
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 12px;
    line-height: 1.55;
  }}
  .latest {{
    font-size: 0.8rem;
    color: var(--muted);
    margin-bottom: 10px;
  }}
  #chartWrap {{
    position: relative;
    height: 280px;
  }}
  .tabs {{
    display: flex;
    gap: 6px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }}
  .tab {{
    padding: 5px 11px;
    border-radius: 16px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--muted);
    cursor: pointer;
    font-size: 0.78rem;
  }}
  .tab.active {{
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
  }}
  .range-tabs {{
    display: flex;
    gap: 5px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }}
  .range-tab {{
    padding: 4px 10px;
    border-radius: 14px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--muted);
    cursor: pointer;
    font-size: 0.75rem;
  }}
  .range-tab.active {{
    background: #38444d;
    color: #fff;
    border-color: #38444d;
  }}
  .update-info {{
    font-size: 0.75rem;
    color: var(--muted);
    margin-bottom: 14px;
  }}
</style>
</head>
<body>
  <h1>台股 0050 / 正2 合理價估算</h1>
  <p class="sub">0050 用近 {days_0050} 日｜正2 用近 {days_l} 日平均比例｜資料已還原分割</p>
  <p class="update-info">最後更新：{last_update}（台灣時間）｜由 GitHub Actions 每日自動更新</p>

  <div class="card">
    <h2>輸入目前大盤點數</h2>
    <div class="input-row">
      <input type="number" id="taiexInput" placeholder="例如 36000" step="1" value="{prices["TAIEX"]}">
      <button onclick="calc()">計算</button>
    </div>
    <p class="hint">輸入後按「計算」，或直接改數字後按 Enter</p>
  </div>

  <div class="card">
    <h2>估算結果</h2>
    <p class="latest" id="latestInfo">最新市價基準日：{latest_date}</p>
    <table>
      <thead>
        <tr>
          <th>標的</th>
          <th>預估價</th>
          <th>合理價（理論）</th>
          <th>折溢價</th>
          <th>%</th>
        </tr>
      </thead>
      <tbody id="resultBody"></tbody>
    </table>
    <p class="note">
      <b>預估價</b>：0050 用近 {days_0050} 日平均比例；00631L / 00685L 用近 {days_l} 日平均比例<br>
      <b>合理價（理論）</b> = 最新收盤市價（實務上應參考投信公布的淨值 NAV）<br>
      折溢價 = 合理價（理論） − 預估價　｜　正數 = 市價相對預估偏高<br>
      ※ 正2 因每日再平衡與波動耗損，急漲急跌後預估價與市價仍可能出現偏離。
    </p>
  </div>

  <div class="card">
    <h2>歷史走勢</h2>
    <div class="range-tabs" id="rangeTabs">
      <button class="range-tab" data-range="all">All</button>
      <button class="range-tab" data-range="6m">6M</button>
      <button class="range-tab" data-range="ytd">YTD</button>
      <button class="range-tab active" data-range="1y">1Y</button>
      <button class="range-tab" data-range="2y">2Y</button>
      <button class="range-tab" data-range="3y">3Y</button>
      <button class="range-tab" data-range="5y">5Y</button>
      <button class="range-tab" data-range="10y">10Y</button>
    </div>
    <div class="tabs">
      <button class="tab active" data-mode="norm" onclick="setMode('norm')">正規化 (期初=100)</button>
      <button class="tab" data-mode="price" onclick="setMode('price')">實際價格</button>
    </div>
    <div id="chartWrap"><canvas id="chart"></canvas></div>
  </div>

<script>
const RATIOS = {ratios_json};
const LATEST = {prices_json};
const LATEST_DATE = "{latest_date}";
const CHART = {chart_json};

let chart = null;
let mode = "norm";
let range = "1y";

document.getElementById("latestInfo").textContent =
  "最新市價基準日：" + LATEST_DATE + "（TAIEX " + LATEST.TAIEX.toLocaleString() + "）";

function fmt(n, dig) {{
  dig = dig || 2;
  if (n == null || isNaN(n)) return "—";
  return n.toLocaleString("zh-TW", {{ minimumFractionDigits: dig, maximumFractionDigits: dig }});
}}

function calc() {{
  const taiex = parseFloat(document.getElementById("taiexInput").value);
  if (!taiex || taiex <= 0) {{
    alert("請輸入有效的大盤點數");
    return;
  }}

  const items = [
    {{ name: "0050", ratio: RATIOS["0050"], market: LATEST["0050"] }},
    {{ name: "00631L", ratio: RATIOS["00631L"], market: LATEST["00631L"] }},
    {{ name: "00685L", ratio: RATIOS["00685L"], market: LATEST["00685L"] }}
  ];

  let html = "";
  for (let i = 0; i < items.length; i++) {{
    const it = items[i];
    const est = taiex * it.ratio;
    const fair = it.market;
    const diff = fair - est;
    const pct = (diff / est) * 100;
    const cls = diff > 0.01 ? "pos" : (diff < -0.01 ? "neg" : "neu");
    const sign = diff > 0 ? "+" : "";

    html += "<tr>" +
      "<td class=\\"name\\">" + it.name + "</td>" +
      "<td>" + fmt(est) + "</td>" +
      "<td>" + fmt(fair) + "</td>" +
      "<td class=\\"" + cls + "\\">" + sign + fmt(diff) + "</td>" +
      "<td class=\\"" + cls + "\\">" + sign + fmt(pct, 2) + "%</td>" +
      "</tr>";
  }}
  document.getElementById("resultBody").innerHTML = html;
}}

function getFilteredData() {{
  if (range === "all") return CHART;

  const last = new Date(CHART[CHART.length - 1].d);
  let from = new Date(last);

  if (range === "6m") {{
    from.setMonth(from.getMonth() - 6);
  }} else if (range === "ytd") {{
    from = new Date(last.getFullYear(), 0, 1);
  }} else if (range === "1y") {{
    from.setFullYear(from.getFullYear() - 1);
  }} else if (range === "2y") {{
    from.setFullYear(from.getFullYear() - 2);
  }} else if (range === "3y") {{
    from.setFullYear(from.getFullYear() - 3);
  }} else if (range === "5y") {{
    from.setFullYear(from.getFullYear() - 5);
  }} else if (range === "10y") {{
    from.setFullYear(from.getFullYear() - 10);
  }}

  return CHART.filter(function(r) {{
    return new Date(r.d) >= from;
  }});
}}

function setMode(m) {{
  mode = m;
  document.querySelectorAll(".tab").forEach(function(t) {{
    t.classList.toggle("active", t.dataset.mode === m);
  }});
  renderChart();
}}

function setRange(r) {{
  range = r;
  document.querySelectorAll(".range-tab").forEach(function(t) {{
    t.classList.toggle("active", t.dataset.range === r);
  }});
  renderChart();
}}

document.getElementById("rangeTabs").addEventListener("click", function(e) {{
  if (e.target.classList.contains("range-tab")) {{
    setRange(e.target.dataset.range);
  }}
}});

function renderChart() {{
  const data = getFilteredData();
  if (!data.length) return;

  const labels = data.map(function(r) {{ return r.d; }});
  const t0 = data[0].t, a0 = data[0].a, b0 = data[0].b, c0 = data[0].c;

  let datasets;
  if (mode === "norm") {{
    datasets = [
      {{ label: "TAIEX", data: data.map(function(r) {{ return r.t / t0 * 100; }}), borderColor: "#1d9bf0", tension: 0.15, pointRadius: 0 }},
      {{ label: "0050", data: data.map(function(r) {{ return r.a / a0 * 100; }}), borderColor: "#00ba7c", tension: 0.15, pointRadius: 0 }},
      {{ label: "00631L", data: data.map(function(r) {{ return r.b / b0 * 100; }}), borderColor: "#ff7a00", tension: 0.15, pointRadius: 0 }},
      {{ label: "00685L", data: data.map(function(r) {{ return r.c / c0 * 100; }}), borderColor: "#c084fc", tension: 0.15, pointRadius: 0 }}
    ];
  }} else {{
    datasets = [
      {{ label: "TAIEX (右軸)", data: data.map(function(r) {{ return r.t; }}), borderColor: "#1d9bf0", tension: 0.15, pointRadius: 0, yAxisID: "y1" }},
      {{ label: "0050", data: data.map(function(r) {{ return r.a; }}), borderColor: "#00ba7c", tension: 0.15, pointRadius: 0 }},
      {{ label: "00631L", data: data.map(function(r) {{ return r.b; }}), borderColor: "#ff7a00", tension: 0.15, pointRadius: 0 }},
      {{ label: "00685L", data: data.map(function(r) {{ return r.c; }}), borderColor: "#c084fc", tension: 0.15, pointRadius: 0 }}
    ];
  }}

  const ctx = document.getElementById("chart").getContext("2d");
  if (chart) chart.destroy();
  chart = new Chart(ctx, {{
    type: "line",
    data: {{ labels: labels, datasets: datasets }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: "index", intersect: false }},
      plugins: {{ legend: {{ labels: {{ color: "#e7e9ea", boxWidth: 12 }} }} }},
      scales: {{
        x: {{ ticks: {{ color: "#8b98a5", maxTicksLimit: 7 }}, grid: {{ color: "#2f3336" }} }},
        y: {{ ticks: {{ color: "#8b98a5" }}, grid: {{ color: "#2f3336" }} }},
        ...(mode === "price" ? {{
          y1: {{ position: "right", ticks: {{ color: "#1d9bf0" }}, grid: {{ drawOnChartArea: false }} }}
        }} : {{}})
      }}
    }}
  }});
}}

document.getElementById("taiexInput").addEventListener("keydown", function(e) {{
  if (e.key === "Enter") calc();
}});

calc();
renderChart();
</script>
</body>
</html>
'''
    return html


def main():
    df = fetch_data()
    print("計算比例：")
    ratios = calc_ratios(df)
    chart = build_chart_data(df)
    html = build_html(df, ratios, chart)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"\n已產生 {OUTPUT} （{len(html):,} bytes）")
    print(f"最後資料日期：{df.index[-1].date()}")


if __name__ == "__main__":
    main()
