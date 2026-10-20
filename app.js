(() => {
  const data = window.DASHBOARD_DATA || { metrics: [], reports: [], peers: [] };
  const rows = data.metrics || [];
  const reports = data.reports || [];
  const annual = rows.filter(row => row.category === "annual").sort((a, b) => a.year - b.year);
  const latest = [...rows].sort((a, b) => a.year - b.year || a.period_order - b.period_order).at(-1) || annual.at(-1);
  const trillion = value => value == null ? "—" : (value / 1e12).toLocaleString("ko-KR", { maximumFractionDigits: 1 });
  const eok = value => value == null ? "—" : Math.round(value / 1e8).toLocaleString("ko-KR");
  const pct = value => value == null ? "—" : `${Number(value).toLocaleString("ko-KR", { maximumFractionDigits: 2 })}%`;
  const reportName = row => ({ FY: "사업보고서", H1: "반기보고서", Q1: "1분기보고서", Q3: "3분기보고서" }[row.period] || row.period);

  document.querySelector("#updatedAt").textContent = data.generated_at
    ? `최근 생성 ${new Date(data.generated_at).toLocaleString("ko-KR", { dateStyle: "long", timeStyle: "short" })}`
    : "생성 기록 없음";
  document.querySelector("#latestPeriod").textContent = latest
    ? `${latest.year} · ${latest.fs_div === "CFS" ? "연결" : "별도"}`
    : "첫 수집 전";

  const cards = latest ? [
    ["매출액", trillion(latest.revenue), "조원", reportName(latest), "#15171b"],
    ["영업이익", trillion(latest.operating_income), "조원", `영업이익률 ${pct(latest.operating_margin_pct)}`, "#f12836"],
    ["당기순이익", trillion(latest.net_income), "조원", `ROE ${pct(latest.roe_pct)}`, "#ff7a1a"],
    ["부채비율", latest.debt_to_equity_pct == null ? "—" : Number(latest.debt_to_equity_pct).toLocaleString("ko-KR"), "%", "부채 ÷ 자본", "#4e6be8"],
  ] : [
    ["매출액", "—", "", "Actions 실행 후 표시", "#15171b"],
    ["영업이익", "—", "", "Actions 실행 후 표시", "#f12836"],
    ["당기순이익", "—", "", "Actions 실행 후 표시", "#ff7a1a"],
    ["부채비율", "—", "", "Actions 실행 후 표시", "#4e6be8"],
  ];
  document.querySelector("#summaryCards").innerHTML = cards.map(([label, value, unit, note, color]) =>
    `<article class="metric-card" style="--accent:${color}"><div class="metric-label">${label}</div><div class="metric-value">${value}<span class="metric-unit">${unit}</span></div><div class="metric-note">${note}</div></article>`
  ).join("");

  function lineChart(target, series, colors, formatter) {
    const element = document.querySelector(target);
    if (!annual.length) {
      element.innerHTML = `<div class="empty"><strong>연간 데이터 대기 중</strong><span>첫 수집 후 추이가 표시됩니다.</span></div>`;
      return;
    }
    const width = 640, height = 270, pad = { l: 40, r: 16, t: 16, b: 31 };
    const values = series.flatMap(key => annual.map(row => row[key]).filter(value => value != null));
    const min = Math.min(0, ...values), max = Math.max(1, ...values), span = max - min || 1;
    const x = index => pad.l + (annual.length === 1 ? (width - pad.l - pad.r) / 2 : index * (width - pad.l - pad.r) / (annual.length - 1));
    const y = value => pad.t + (max - value) * (height - pad.t - pad.b) / span;
    const grid = [0, .25, .5, .75, 1].map(step => {
      const yy = pad.t + step * (height - pad.t - pad.b), value = max - step * span;
      return `<line class="axis" x1="${pad.l}" y1="${yy}" x2="${width - pad.r}" y2="${yy}"/><text class="axis-label" x="${pad.l - 7}" y="${yy + 3}" text-anchor="end">${formatter(value)}</text>`;
    }).join("");
    const labels = annual.map((row, index) => `<text class="axis-label" x="${x(index)}" y="${height - 7}" text-anchor="middle">${row.year}</text>`).join("");
    const lines = series.map((key, seriesIndex) => {
      const points = annual.map((row, index) => row[key] == null ? null : [x(index), y(row[key])]).filter(Boolean);
      return `<polyline class="chart-line" stroke="${colors[seriesIndex]}" points="${points.map(point => point.join(",")).join(" ")}"/>${points.map(point => `<circle class="chart-dot" fill="${colors[seriesIndex]}" cx="${point[0]}" cy="${point[1]}" r="3.5"/>`).join("")}`;
    }).join("");
    element.innerHTML = `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">${grid}${labels}${lines}</svg>`;
  }
  lineChart("#incomeChart", ["revenue", "operating_income", "net_income"], ["#15171b", "#f12836", "#ff7a1a"], value => `${(value / 1e12).toFixed(0)}`);
  lineChart("#ratioChart", ["operating_margin_pct", "debt_to_equity_pct"], ["#008b72", "#4e6be8"], value => `${value.toFixed(0)}%`);

  const categories = [
    ["annual", "Annual", "사업보고서"],
    ["half-year", "Half-year", "반기보고서"],
    ["quarterly", "Quarterly", "1·3분기보고서"],
  ];
  const isSaved = report => report.status === "saved" || Number(report.account_count || report.accounts || 0) > 0;
  const saved = reports.filter(isSaved);
  const totalExpected = reports.length || ((new Date().getFullYear() - Number(data.start_year || 2010) + 1) * 4);
  document.querySelector("#coverageSummary").textContent = `${saved.length} / ${totalExpected}개 보고서 수집`;
  document.querySelector("#coverageGrid").innerHTML = categories.map(([category, label, description]) => {
    const all = reports.filter(report => report.category === category);
    const count = all.filter(isSaved).length;
    const rate = all.length ? Math.round(count / all.length * 100) : 0;
    return `<article class="coverage-card"><strong>${label}</strong><div class="coverage-bar"><i style="width:${rate}%"></i></div><p>${description} · ${count}/${all.length || 0}개</p></article>`;
  }).join("") + `<article class="coverage-card"><strong>Coverage</strong><div class="coverage-bar"><i style="width:${totalExpected ? Math.round(saved.length / totalExpected * 100) : 0}%"></i></div><p>2010년 이후 연결 우선 수집</p></article>`;

  const tableMetrics = [
    ["revenue", "매출액"], ["operating_income", "영업이익"], ["net_income", "당기순이익"],
    ["assets", "자산총계"], ["liabilities", "부채총계"], ["equity", "자본총계"],
    ["current_assets", "유동자산"], ["current_liabilities", "유동부채"],
    ["cash_and_equivalents", "현금및현금성자산"], ["borrowings", "차입금"],
    ["operating_cash_flow", "영업현금흐름"], ["capex", "유형자산 취득"],
    ["free_cash_flow", "잉여현금흐름"], ["net_debt", "순차입금"],
    ["operating_margin_pct", "영업이익률"], ["net_margin_pct", "순이익률"],
    ["debt_to_equity_pct", "부채비율"], ["current_ratio_pct", "유동비율"],
    ["equity_ratio_pct", "자기자본비율"], ["roa_pct", "ROA"], ["roe_pct", "ROE"],
  ];
  const formatMetric = (key, value) => {
    if (value == null || value === "") return "—";
    return key.endsWith("_pct") ? pct(value) : eok(value);
  };
  const tables = document.querySelector("#tablesByCategory"), empty = document.querySelector("#emptyState");
  const tableHtml = (category, title, subtitle) => {
    const selected = rows.filter(row => row.category === category).sort((a, b) => b.year - a.year || b.period_order - a.period_order);
    const headings = ["연도", "보고서", ...tableMetrics.map(([, label]) => label)];
    const body = selected.map(row => `<tr><td>${row.year}</td><td><span class="tag">${reportName(row)} · ${row.fs_div || "—"}</span></td>${tableMetrics.map(([key]) => `<td>${formatMetric(key, row[key])}</td>`).join("")}</tr>`).join("");
    return `<section class="period-table"><div class="period-table-heading"><div><h3>${title}</h3><p>${subtitle}</p></div><span>${selected.length}개 기간</span></div><div class="table-shell"><table><thead><tr>${headings.map(label => `<th>${label}</th>`).join("")}</tr></thead><tbody>${body || `<tr><td class="no-data" colspan="${headings.length}">공시 데이터를 기다리고 있습니다.</td></tr>`}</tbody></table></div></section>`;
  };
  tables.innerHTML = [
    tableHtml("annual", "Annual · 연간", "사업보고서 기준"),
    tableHtml("half-year", "Half-year · 반기", "반기보고서 기준"),
    tableHtml("quarterly", "Quarterly · 분기", "1분기·3분기 보고서 기준"),
  ].join("");
  empty.hidden = rows.length > 0;

  document.querySelector("#peerTable").innerHTML = (data.peers || []).map(peer =>
    `<tr><td>${peer["기업명"] || peer.name || "—"}</td><td>${String(peer["종목코드"] || peer.stock_code || "").padStart(6, "0")}</td><td>${peer["기업구분"] || "국내 반도체 기업"}</td><td>${peer["비교 목적"] || peer.relationship || "산업 참고"}</td></tr>`
  ).join("") || `<tr><td class="no-data" colspan="4">비교기업 정보가 없습니다.</td></tr>`;
})();

