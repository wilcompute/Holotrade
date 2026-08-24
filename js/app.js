// ======================================================================
// HOLOTRADE TERMINAL — application
//
// Orchestration only. Every number rendered here is computed by one of
// the engines; this file does not invent quantities, it displays them.
// Where a figure is a bound, an assumption or a structural claim rather
// than a measurement, the view says so on the page rather than in a
// footnote nobody reads.
// ======================================================================

(function () {
  "use strict";

  // ---- engine wiring -------------------------------------------------
  const energy = new EnergyEngine(DATACENTERS);
  const fleet = new Fleet({
    datacenters: DATACENTERS, hardware: HARDWARE,
    workloads: WORKLOADS, operators: OPERATORS, size: 320,
  });
  const pricing = new PricingEngine(fleet, energy, WORKLOADS);
  const fabric = new FabricMarket(fleet, pricing);
  const genetics = new GeneticsEngine(fleet, WORKLOADS);
  const registry = new HolotradeUOR.AssetRegistry(fleet);
  const exec = new ExecutionEngine(fleet, pricing, energy, WORKLOADS);
  const market = new Market(fleet, pricing, energy, {
    INSTRUMENTS, OPERATORS, DATACENTERS, HARDWARE, WORKLOADS,
  });

  // ---- ui state ------------------------------------------------------
  const ui = {
    view: "exchange",
    instrument: "spot",
    workload: "llm-train",
    anchor: null,
    fleetColor: "price",
    fleetDc: "",
    fleetHw: "",
    fleetSort: "price",
    genWorkload: "",
    selectedPlan: null,
    selectedPoint: null,
    shellAnchor: null,
    tps: 70e6,
    speed: 1,
    paused: false,
    tick: 0,
    simSeconds: 0,
  };

  const $ = (id) => document.getElementById(id);
  const el = (tag, cls, html) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  };

  // ---- formatting ----------------------------------------------------
  const fmt = {
    usd: (v, d = 2) => (v == null || !isFinite(v) ? "—" : "$" + v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d })),
    usd0: (v) => (v == null || !isFinite(v) ? "—" : "$" + Math.round(v).toLocaleString("en-US")),
    num: (v, d = 2) => (v == null || !isFinite(v) ? "—" : v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d })),
    int: (v) => (v == null || !isFinite(v) ? "—" : Math.round(v).toLocaleString("en-US")),
    pct: (v, d = 1) => (v == null || !isFinite(v) ? "—" : (v * 100).toFixed(d) + "%"),
    x: (v, d = 3) => (v == null || !isFinite(v) ? "—" : "×" + v.toFixed(d)),
    sci: (v, d = 2) => (v == null || !isFinite(v) ? "—" : v.toExponential(d)),
    big: (v) => {
      if (v == null || !isFinite(v)) return "—";
      const a = Math.abs(v);
      if (a >= 1e12) return (v / 1e12).toFixed(2) + "T";
      if (a >= 1e9) return (v / 1e9).toFixed(2) + "B";
      if (a >= 1e6) return (v / 1e6).toFixed(2) + "M";
      if (a >= 1e3) return (v / 1e3).toFixed(1) + "k";
      return v.toFixed(0);
    },
    clock: (s) => {
      const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = Math.floor(s % 60);
      return [h, m, x].map((n) => String(n).padStart(2, "0")).join(":");
    },
    time: (ts) => new Date(ts).toLocaleTimeString("en-US", { hour12: false }),
    esc: (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])),
  };

  const sgn = (v) => (v > 0 ? "up" : v < 0 ? "down" : "");
  const HW_COLOR = {
    gpu: "#38bdf8", cpu: "#2dd4a7", fpga: "#f5a524",
    neuro: "#a78bfa", photonic: "#f4526b", composite: "#93a3bd",
  };

  function tile(label, value, sub, cls) {
    return `<div class="stat ${cls || ""}">
      <div class="stat-label">${label}</div>
      <div class="stat-value">${value}</div>
      ${sub ? `<div class="stat-sub">${sub}</div>` : ""}
    </div>`;
  }

  function toast(title, body, kind) {
    const t = el("div", "toast " + (kind || ""), `<div class="t-title">${fmt.esc(title)}</div><div class="t-body">${fmt.esc(body)}</div>`);
    $("toasts").appendChild(t);
    setTimeout(() => { t.style.opacity = "0"; setTimeout(() => t.remove(), 240); }, 4200);
  }

  // ====================================================================
  // Canvas helpers
  // ====================================================================

  function prepCanvas(cv) {
    const dpr = window.devicePixelRatio || 1;
    const w = cv.clientWidth || cv.parentElement.clientWidth || 600;
    const h = parseInt(cv.getAttribute("height"), 10) || 180;
    cv.width = w * dpr; cv.height = h * dpr;
    cv.style.height = h + "px";
    const ctx = cv.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    return { ctx, w, h };
  }

  function css(name, fallback) {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  function axes(ctx, w, h, pad) {
    ctx.strokeStyle = css("--border", "#1c2740");
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad.l, pad.t); ctx.lineTo(pad.l, h - pad.b); ctx.lineTo(w - pad.r, h - pad.b);
    ctx.stroke();
  }

  function drawLines(cv, series, opts = {}) {
    const { ctx, w, h } = prepCanvas(cv);
    const pad = { l: 46, r: 10, t: 10, b: 20 };
    const all = series.flatMap((s) => s.data).filter((x) => isFinite(x));
    if (!all.length) return;
    let min = opts.min != null ? opts.min : Math.min(...all);
    let max = opts.max != null ? opts.max : Math.max(...all);
    if (max === min) { max = min + 1; }
    const pd = (max - min) * 0.08;
    min -= pd; max += pd;
    const X = (i, n) => pad.l + (i / Math.max(1, n - 1)) * (w - pad.l - pad.r);
    const Y = (v) => h - pad.b - ((v - min) / (max - min)) * (h - pad.t - pad.b);

    // gridlines + labels
    ctx.strokeStyle = css("--border", "#1c2740");
    ctx.fillStyle = css("--text-2", "#61708c");
    ctx.font = "10px " + css("--mono", "monospace");
    ctx.textAlign = "right";
    for (let i = 0; i <= 4; i++) {
      const v = min + (i / 4) * (max - min);
      const y = Y(v);
      ctx.globalAlpha = 0.5;
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillText(opts.fmtY ? opts.fmtY(v) : v.toFixed(2), pad.l - 6, y + 3);
    }
    axes(ctx, w, h, pad);

    for (const s of series) {
      if (!s.data.length) continue;
      ctx.strokeStyle = s.color;
      ctx.lineWidth = s.width || 1.6;
      if (s.dash) ctx.setLineDash(s.dash); else ctx.setLineDash([]);
      ctx.beginPath();
      s.data.forEach((v, i) => {
        const x = X(i, s.data.length), y = Y(v);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.stroke();
      ctx.setLineDash([]);
      if (s.fill) {
        ctx.lineTo(X(s.data.length - 1, s.data.length), h - pad.b);
        ctx.lineTo(X(0, s.data.length), h - pad.b);
        ctx.closePath();
        ctx.fillStyle = s.fill; ctx.fill();
      }
    }

    if (opts.bands) {
      for (const b of opts.bands) {
        const y1 = Y(b.hi), y2 = Y(b.lo);
        ctx.fillStyle = b.color;
        ctx.fillRect(pad.l, y1, w - pad.l - pad.r, y2 - y1);
      }
    }
  }

  function drawBars(cv, bars, opts = {}) {
    const { ctx, w, h } = prepCanvas(cv);
    const pad = { l: 34, r: 10, t: 10, b: 26 };
    const max = opts.max != null ? opts.max : Math.max(1, ...bars.map((b) => b.value));
    const bw = (w - pad.l - pad.r) / bars.length;
    axes(ctx, w, h, pad);
    ctx.font = "9.5px " + css("--mono", "monospace");
    bars.forEach((b, i) => {
      const bh = (b.value / max) * (h - pad.t - pad.b);
      ctx.fillStyle = b.color || css("--accent", "#38bdf8");
      ctx.fillRect(pad.l + i * bw + bw * 0.14, h - pad.b - bh, bw * 0.72, bh);
      ctx.fillStyle = css("--text-2", "#61708c");
      ctx.textAlign = "center";
      ctx.fillText(b.label, pad.l + i * bw + bw / 2, h - pad.b + 12);
      if (b.value > 0) {
        ctx.fillStyle = css("--text-1", "#93a3bd");
        ctx.fillText(opts.fmtV ? opts.fmtV(b.value) : b.value, pad.l + i * bw + bw / 2, h - pad.b - bh - 4);
      }
    });
  }

  // ====================================================================
  // EXCHANGE
  // ====================================================================

  function renderExchange() {
    const stats = pricing.marketStats({ workloadId: ui.workload });
    const spread = market.spread(ui.instrument);
    const vwap = market.vwap(ui.instrument);
    const cap = pricing.fleetStats;

    $("exchangeStats").innerHTML = [
      tile("Median clearing", stats ? fmt.usd(stats.median) : "—", stats ? `p10 ${fmt.usd(stats.p10)} · p90 ${fmt.usd(stats.p90)}` : "", "accent"),
      tile("Spread", spread ? fmt.usd(spread.spread, 3) : "—", spread ? `${spread.bps.toFixed(0)} bps` : ""),
      tile("VWAP", vwap ? fmt.usd(vwap) : "—", `${market.trades.filter((t) => t.instrument === ui.instrument).length} prints`),
      tile("Listed capacity", stats ? fmt.usd0(stats.totalCapacityPerHour) + "/hr" : "—", `${cap.count} nodes · ${stats ? stats.atFloor : 0} at floor`),
    ].join("");

    // instrument selector
    const seg = $("instrumentSeg");
    if (seg.children.length !== INSTRUMENTS.length) {
      seg.innerHTML = INSTRUMENTS.map((i) =>
        `<button data-inst="${i.id}" class="${i.id === ui.instrument ? "active" : ""}">${fmt.esc(i.name)}</button>`
      ).join("");
      seg.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
        ui.instrument = b.dataset.inst;
        seg.querySelectorAll("button").forEach((x) => x.classList.toggle("active", x.dataset.inst === ui.instrument));
        renderExchange();
      }));
    } else {
      seg.querySelectorAll("button").forEach((x) => x.classList.toggle("active", x.dataset.inst === ui.instrument));
    }
    const inst = INSTRUMENTS.find((i) => i.id === ui.instrument);
    $("instrumentBlurb").textContent = inst ? inst.blurb : "";
    $("instrumentNote").textContent = inst ? inst.tenor : "";

    renderBook();
    renderDepth();
    renderTape();
    renderBestDecomp();
    renderOrders();
    renderTicketPreview();
  }

  function renderBook() {
    market.rebuildAsks(ui.instrument, { workloadId: ui.workload, anchorAddress: ui.anchor, days: 30 });
    market.rebuildBids(ui.instrument);
    const b = market.book(ui.instrument);
    const depth = market.depth(ui.instrument, 12);
    const maxCum = Math.max(
      depth.bids.length ? depth.bids[depth.bids.length - 1].cum : 1,
      depth.asks.length ? depth.asks[depth.asks.length - 1].cum : 1
    );

    const askRows = depth.asks.slice().reverse().map((r, i) => {
      const src = b.asks[depth.asks.length - 1 - i];
      return `<div class="book-row ask" data-node="${src ? fmt.esc(src.nodeId) : ""}" title="${src ? fmt.esc(src.nodeId) : ""}">
        <div class="bar" style="width:${(r.cum / maxCum) * 100}%"></div>
        <span class="px">${r.price.toFixed(3)}</span><span class="qty">${r.qty}</span><span class="cum">${r.cum}</span>
      </div>`;
    }).join("");

    const bidRows = depth.bids.map((r) => `<div class="book-row bid">
      <div class="bar" style="width:${(r.cum / maxCum) * 100}%"></div>
      <span class="px">${r.price.toFixed(3)}</span><span class="qty">${r.qty}</span><span class="cum">${r.cum}</span>
    </div>`).join("");

    const sp = market.spread(ui.instrument);
    $("book").innerHTML =
      `<div class="book-col"><h4>Bid · price / size / cum</h4>${bidRows || '<div class="empty">no bids</div>'}</div>
       <div class="book-col"><h4>Ask · price / size / cum</h4>${askRows || '<div class="empty">no offers</div>'}</div>
       <div class="book-mid">${sp ? `<span class="up">${sp.bestBid.toFixed(3)}</span><span class="muted">spread ${sp.spread.toFixed(3)} · ${sp.bps.toFixed(0)}bps</span><span class="down">${sp.bestAsk.toFixed(3)}</span>` : "—"}</div>`;

    $("book").querySelectorAll(".book-row.ask").forEach((row) => {
      row.addEventListener("click", () => { if (row.dataset.node) openNode(row.dataset.node); });
    });
    $("bookNote").textContent = `${b.asks.length} offers · ${b.bids.length} bids`;
  }

  function renderDepth() {
    const d = market.depth(ui.instrument, 40);
    const cv = $("depthCanvas");
    const { ctx, w, h } = prepCanvas(cv);
    if (!d.asks.length && !d.bids.length) return;
    const prices = [...d.bids.map((x) => x.price), ...d.asks.map((x) => x.price)];
    const min = Math.min(...prices), max = Math.max(...prices);
    const maxCum = Math.max(...d.bids.map((x) => x.cum), ...d.asks.map((x) => x.cum), 1);
    const pad = { l: 44, r: 10, t: 10, b: 22 };
    const X = (p) => pad.l + ((p - min) / Math.max(1e-9, max - min)) * (w - pad.l - pad.r);
    const Y = (c) => h - pad.b - (c / maxCum) * (h - pad.t - pad.b);
    axes(ctx, w, h, pad);

    const step = (rows, color, fill) => {
      if (!rows.length) return;
      ctx.beginPath();
      ctx.moveTo(X(rows[0].price), h - pad.b);
      rows.forEach((r) => { ctx.lineTo(X(r.price), Y(r.cum)); });
      ctx.strokeStyle = color; ctx.lineWidth = 1.6; ctx.stroke();
      ctx.lineTo(X(rows[rows.length - 1].price), h - pad.b);
      ctx.closePath(); ctx.fillStyle = fill; ctx.fill();
    };
    step(d.bids, css("--up", "#2dd4a7"), "rgba(45,212,167,0.13)");
    step(d.asks, css("--down", "#f4526b"), "rgba(244,82,107,0.13)");

    ctx.fillStyle = css("--text-2", "#61708c");
    ctx.font = "10px " + css("--mono", "monospace");
    ctx.textAlign = "left"; ctx.fillText("$" + min.toFixed(1), pad.l, h - 6);
    ctx.textAlign = "right"; ctx.fillText("$" + max.toFixed(1), w - pad.r, h - 6);
    ctx.fillText(fmt.int(maxCum), pad.l - 6, pad.t + 8);
  }

  function renderTape() {
    const rows = market.trades.filter((t) => t.instrument === ui.instrument).slice(0, 60);
    $("tapeBody").innerHTML = rows.length ? rows.map((t) => `<tr class="clickable" data-node="${fmt.esc(t.nodeId)}">
      <td class="mono muted">${fmt.time(t.ts)}</td>
      <td><span class="tag ${t.side === "buy" ? "up" : "down"}">${t.side.toUpperCase()}</span></td>
      <td class="mono">${fmt.esc(t.nodeId.slice(-12))}</td>
      <td class="mono muted">${fmt.esc(t.nodeAddress)}</td>
      <td><span class="tag">${fmt.esc(t.hardware)}</span></td>
      <td class="mono muted">${fmt.esc(t.dcId)}</td>
      <td class="num">${t.qty}</td>
      <td class="num">${fmt.usd(t.price, 3)}</td>
    </tr>`).join("") : '<tr><td colspan="8" class="empty">no prints yet</td></tr>';
    $("tapeBody").querySelectorAll("tr.clickable").forEach((r) =>
      r.addEventListener("click", () => openNode(r.dataset.node)));
    $("tapeNote").textContent = `${rows.length} prints`;
  }

  function decompHTML(q, node) {
    if (!q || !q.serviceable) {
      return `<div class="note amber"><b>Not serviceable.</b> ${node && !node.hardware.magicCapable
        ? "This workload class carries a non-zero magic budget and this node is Clifford-only. The exchange refuses rather than substituting."
        : "No quote available."}</div>`;
    }
    const M = q.multipliers;
    const defs = [
      ["E", "Energy", M.E, "live $/MWh at this site, PUE-adjusted"],
      ["G", "Genetics", M.G, "what this core has learned about your class"],
      ["D", "Demand / wear", M.D, "premium if hot, discount if cold"],
      ["H", "Health", M.H, "derate × reliability × error drift"],
      ["Q", "Quantum", M.Q, "9^t magic budget; 1 for anything classical"],
      ["L", "Locality", M.L, "fabric distance from your anchor"],
    ];
    const rows = defs.map(([k, name, v, why]) => {
      const dev = v - 1;
      const pctW = Math.min(50, Math.abs(dev) * 55);
      const colour = dev > 0.005 ? css("--down", "#f4526b") : dev < -0.005 ? css("--up", "#2dd4a7") : css("--text-2", "#61708c");
      const left = dev >= 0 ? 50 : 50 - pctW;
      return `<div class="decomp-row" title="${fmt.esc(why)}">
        <div class="k"><b>${k}</b>${name}</div>
        <div class="decomp-bar"><div class="mid" style="left:50%"></div><i style="left:${left}%;width:${pctW}%;background:${colour}"></i></div>
        <div class="v">${fmt.x(v)}</div>
      </div>`;
    }).join("");

    return `<div class="decomp">
      <div class="decomp-row"><div class="k"><b>P₀</b>base</div><div class="decomp-bar"><i style="left:0;width:100%;background:var(--bg-3)"></i></div><div class="v">${fmt.usd(q.base)}</div></div>
      ${rows}
    </div>
    <div class="decomp-total"><span class="lbl">Clearing price / node-hour</span><span class="amt">${fmt.usd(q.price)}</span></div>
    <hr class="sep">
    <dl class="kv">
      <dt>Floor (energy + reserve + capex)</dt><dd>${fmt.usd(q.floor, 3)}</dd>
      <dt>— electricity</dt><dd class="muted">${fmt.usd(q.energyCost, 3)}</dd>
      <dt>— maintenance reserve</dt><dd class="muted">${fmt.usd(q.maintenanceReserve, 3)}</dd>
      <dt>— capital recovery</dt><dd class="muted">${fmt.usd(q.capitalRecovery, 3)}</dd>
      <dt>Margin over floor</dt><dd class="${sgn(q.margin)}">${fmt.usd(q.margin)} · ${fmt.pct(q.marginPct)}</dd>
      <dt>Carbon</dt><dd>${fmt.num(q.carbonPerHour, 3)} kg/hr</dd>
      <dt>Above Landauer floor</dt><dd>${fmt.num(q.decadesAboveFloor, 2)} decades</dd>
    </dl>${q.atFloor ? '<div class="note amber" style="margin-top:10px"><b>At floor.</b> The balancer wanted to discount this node further and the exchange refused. Below this price the operator is paying to run your job.</div>' : ""}`;
  }

  function renderBestDecomp() {
    const asks = market.book(ui.instrument).asks;
    if (!asks.length) { $("bestDecomp").innerHTML = '<div class="empty">no offers</div>'; return; }
    const best = asks[0];
    const node = best.node;
    $("bestDecomp").innerHTML =
      `<div style="margin-bottom:11px"><span class="mono" style="font-size:12px">${fmt.esc(node.id)}</span>
       <span class="tag accent" style="margin-left:6px">${fmt.esc(node.address)}</span>
       <span class="tag" style="margin-left:4px">${fmt.esc(node.hardware.class)}</span></div>` +
      decompHTML(best.quote, node) +
      `<button class="btn sm" style="margin-top:11px;width:100%" id="bestOpen">Open node</button>`;
    const btn = $("bestOpen");
    if (btn) btn.addEventListener("click", () => openNode(node.id));
  }

  function renderOrders() {
    const rows = market.userOrders.slice(0, 20);
    $("ordersBody").innerHTML = rows.length ? rows.map((o) => `<tr>
      <td class="mono">${o.id}</td><td><span class="tag">${o.instrument}</span></td>
      <td class="num">${o.qty}</td><td class="num">${o.filledQty}</td>
      <td><span class="tag ${o.status === "filled" ? "up" : o.status === "rejected" ? "down" : "amber"}">${o.status}</span></td>
    </tr>`).join("") : '<tr><td colspan="5" class="empty">no orders</td></tr>';
  }

  function renderTicketPreview() {
    const asks = market.book(ui.instrument).asks;
    const qty = Math.max(1, parseInt($("tkQty").value, 10) || 1);
    let remaining = qty, cost = 0, nodes = 0;
    for (const a of asks) {
      if (remaining <= 0) break;
      const take = Math.min(remaining, a.qty);
      cost += take * a.price; remaining -= take; nodes++;
    }
    const avg = qty - remaining > 0 ? cost / (qty - remaining) : 0;
    $("tkPreview").innerHTML = `
      <dt>Fillable</dt><dd>${qty - remaining} / ${qty}</dd>
      <dt>Across nodes</dt><dd>${nodes}</dd>
      <dt>Est. average</dt><dd>${fmt.usd(avg, 3)}</dd>
      <dt>Est. total</dt><dd>${fmt.usd(cost)}</dd>
      <dt>Cash after</dt><dd class="${market.cash - cost < 0 ? "down" : ""}">${fmt.usd0(market.cash - cost)}</dd>`;
  }

  // ====================================================================
  // FLEET
  // ====================================================================

  function nodeColor(node) {
    const q = pricing.quotes.get(node.id);
    switch (ui.fleetColor) {
      case "util": return heat(node.utilisation);
      case "health": return heat(1 - node.health.wear);
      case "fitness": return heat(fleet.fitness(node));
      case "hw": return HW_COLOR[node.hardware.kind] || "#666";
      default: {
        const stats = pricing.marketStats({ workloadId: ui.workload });
        if (!q || !q.price || !stats) return "#333";
        const t = Math.min(1, Math.max(0, (q.price - stats.p10) / Math.max(1e-6, stats.p90 - stats.p10)));
        return heat(1 - t);
      }
    }
  }

  // green (good/cheap) -> amber -> red (bad/expensive)
  function heat(t) {
    t = Math.max(0, Math.min(1, t));
    const stops = [[244, 82, 107], [245, 165, 36], [45, 212, 167]];
    const i = t < 0.5 ? 0 : 1;
    const f = t < 0.5 ? t * 2 : (t - 0.5) * 2;
    const a = stops[i], b = stops[i + 1];
    return `rgb(${Math.round(a[0] + (b[0] - a[0]) * f)},${Math.round(a[1] + (b[1] - a[1]) * f)},${Math.round(a[2] + (b[2] - a[2]) * f)})`;
  }

  function renderFleet() {
    const listed = fleet.listedNodes();
    const st = pricing.fleetStats;
    const totalTf = listed.reduce((a, n) => a + n.effectiveTflops, 0);
    const magic = listed.filter((n) => n.hardware.magicCapable).length;

    $("fleetStats").innerHTML = [
      tile("Nodes listed", fmt.int(listed.length), `${fleet.nodes.length - listed.length} withheld or in service`, "accent"),
      tile("Effective capacity", fmt.big(totalTf) + " TF", "after genome and health derate"),
      tile("Mean utilisation", fmt.pct(st.meanUtilisation), `σ ${fmt.num(st.stdUtilisation, 3)}`),
      tile("Magic-capable", fmt.int(magic), "the only nodes that serve t > 0", "violet"),
    ].join("");

    // colour selector
    const seg = $("fleetColorSeg");
    seg.querySelectorAll("button").forEach((b) => {
      b.classList.toggle("active", b.dataset.color === ui.fleetColor);
      if (!b.dataset.bound) {
        b.dataset.bound = "1";
        b.addEventListener("click", () => { ui.fleetColor = b.dataset.color; renderFleet(); });
      }
    });

    // grid
    const grid = $("fleetGrid");
    grid.innerHTML = "";
    for (const node of fleet.nodes) {
      const c = el("div", "fleet-cell");
      c.style.background = node.health.inService ? css("--border", "#1c2740") : nodeColor(node);
      c.title = `${node.id}\n${node.address} · ${node.hardware.class}\n$${(node.lastPrice || 0).toFixed(2)}/hr · util ${(node.utilisation * 100).toFixed(0)}% · wear ${(node.health.wear * 100).toFixed(0)}%`;
      c.addEventListener("click", () => openNode(node.id));
      grid.appendChild(c);
    }

    const legends = {
      price: "cheap → expensive", util: "idle → pinned",
      health: "worn → fresh", fitness: "low → high", hw: "by hardware kind",
    };
    $("fleetLegend").innerHTML = ui.fleetColor === "hw"
      ? Object.entries(HW_COLOR).map(([k, v]) => `<span><i style="background:${v}"></i>${k}</span>`).join("")
      : `<span><i style="background:${heat(0)}"></i></span><span><i style="background:${heat(0.5)}"></i></span><span><i style="background:${heat(1)}"></i></span><span class="muted">${legends[ui.fleetColor]}</span><span style="margin-left:auto"><i style="background:${css("--border", "#1c2740")}"></i>in service</span>`;

    // filters
    const dcSel = $("fleetFilterDc");
    if (!dcSel.options.length) {
      dcSel.innerHTML = `<option value="">All sites</option>` + DATACENTERS.map((d) => `<option value="${d.id}">${d.id} — ${fmt.esc(d.name)}</option>`).join("");
      dcSel.addEventListener("change", () => { ui.fleetDc = dcSel.value; renderFleetTable(); });
    }
    const hwSel = $("fleetFilterHw");
    if (!hwSel.options.length) {
      hwSel.innerHTML = `<option value="">All hardware</option>` + HARDWARE.map((h) => `<option value="${h.class}">${h.class}</option>`).join("");
      hwSel.addEventListener("change", () => { ui.fleetHw = hwSel.value; renderFleetTable(); });
    }
    if (!$("fleetSort").dataset.bound) {
      $("fleetSort").dataset.bound = "1";
      $("fleetSort").addEventListener("change", () => { ui.fleetSort = $("fleetSort").value; renderFleetTable(); });
    }
    renderFleetTable();
  }

  function renderFleetTable() {
    let rows = fleet.listedNodes();
    if (ui.fleetDc) rows = rows.filter((n) => n.dcId === ui.fleetDc);
    if (ui.fleetHw) rows = rows.filter((n) => n.hardware.class === ui.fleetHw);
    const withQ = rows.map((n) => {
      const q = pricing.quote(n, { workloadId: ui.workload, anchorAddress: ui.anchor });
      return { n, q, perTf: q.price != null && n.effectiveTflops > 0 ? q.price / n.effectiveTflops : Infinity };
    }).filter((r) => r.q.serviceable);

    const sorters = {
      price: (a, b) => a.q.price - b.q.price,
      util: (a, b) => b.n.utilisation - a.n.utilisation,
      fitness: (a, b) => fleet.fitness(b.n) - fleet.fitness(a.n),
      wear: (a, b) => b.n.health.wear - a.n.health.wear,
      value: (a, b) => a.perTf - b.perTf,
    };
    withQ.sort(sorters[ui.fleetSort] || sorters.price);

    $("fleetBody").innerHTML = withQ.slice(0, 200).map(({ n, q, perTf }) => {
      const best = fleet.bestClass(n);
      return `<tr class="clickable" data-node="${fmt.esc(n.id)}">
        <td class="mono">${fmt.esc(n.id.slice(-13))}</td>
        <td class="mono muted">${fmt.esc(n.address)}</td>
        <td><span class="tag" style="color:${HW_COLOR[n.hardware.kind]}">${fmt.esc(n.hardware.class)}</span></td>
        <td class="mono muted">${fmt.esc(n.dcId)}</td>
        <td class="num">${fmt.usd(q.price)}</td>
        <td class="num muted">${isFinite(perTf) ? fmt.num(perTf * 1000, 2) + "m" : "—"}</td>
        <td class="num ${n.utilisation > 0.78 ? "down" : n.utilisation < 0.55 ? "up" : ""}">${fmt.pct(n.utilisation, 0)}</td>
        <td class="num">${fmt.num(fleet.fitness(n), 3)}</td>
        <td class="num ${n.health.wear > 0.7 ? "down" : ""}">${fmt.pct(n.health.wear, 0)}</td>
        <td class="muted" style="font-size:11px">${fmt.esc(best.name)}</td>
      </tr>`;
    }).join("") || '<tr><td colspan="10" class="empty">no nodes match</td></tr>';

    $("fleetBody").querySelectorAll("tr.clickable").forEach((r) =>
      r.addEventListener("click", () => openNode(r.dataset.node)));
  }

  // ---- node drawer ---------------------------------------------------
  function openNode(nodeId) {
    const node = fleet.get(nodeId);
    if (!node) return;
    const q = pricing.quote(node, { workloadId: ui.workload, anchorAddress: ui.anchor });
    const asset = registry.forNode(node);
    const card = asset.describe();
    const best = fleet.bestClass(node);
    const dc = DATACENTERS.find((d) => d.id === node.dcId);
    const anc = genetics.ancestry(node);
    const drift = genetics.driftForecast(node, ui.workload, 30);

    $("drawerTitle").textContent = node.id;
    $("drawerBody").innerHTML = `
      <div class="inline-list" style="margin-bottom:12px">
        <span class="tag accent">${fmt.esc(node.address)}</span>
        <span class="tag" style="color:${HW_COLOR[node.hardware.kind]}">${fmt.esc(node.hardware.class)}</span>
        <span class="tag">${fmt.esc(node.dcId)}</span>
        <span class="tag ${card.liquidity === "deep" ? "up" : card.liquidity === "bilateral" ? "down" : "amber"}">${card.liquidity}</span>
        ${node.hardware.magicCapable ? '<span class="tag violet">magic-capable</span>' : ""}
        ${node.health.serviceDue ? '<span class="tag down">service due</span>' : ""}
      </div>

      <div class="card"><div class="card-head"><h3 class="card-title">Price decomposition</h3>
        <span class="card-note">${fmt.esc(WORKLOADS.find((w) => w.id === ui.workload).name)}</span></div>
        <div class="card-body">${decompHTML(q, node)}</div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">Genome</h3>
        <span class="card-note">observed, not configured</span></div>
        <div class="card-body">
          <div class="gene-bars">${HolotradeGenetics.GENE_NAMES.map((g) => `
            <div class="gene-row">
              <div class="g-name">${g.replace(/([A-Z])/g, " $1").toLowerCase()}</div>
              <div class="gene-track"><i style="width:${node.genome[g] * 100}%"></i></div>
              <div class="g-val">${node.genome[g].toFixed(3)}</div>
            </div>`).join("")}</div>
          <hr class="sep">
          <dl class="kv">
            <dt>Realised fitness</dt><dd>${fmt.num(fleet.fitness(node), 3)}</dd>
            <dt>Strongest at</dt><dd>${fmt.esc(best.name)} · ${fmt.num(best.score, 3)}</dd>
            <dt>Jobs completed / failed</dt><dd>${fmt.int(node.jobsCompleted)} / ${fmt.int(node.jobsFailed)}</dd>
            <dt>Generation</dt><dd>${node.lineage.generation}${node.lineage.bred ? " (bred)" : ""}</dd>
            <dt>Lineage depth</dt><dd>${anc.length}</dd>
          </dl>
          ${drift ? `<div class="note amber" style="margin-top:11px"><b>Lease drift.</b> Over 30 days on ${fmt.esc(WORKLOADS.find((w) => w.id === ui.workload).name)}, this core's prior for that class moves ${node.specialisation[ui.workload].toFixed(3)} → ${drift.after[ui.workload].toFixed(3)}. You are buying a starting point, not a frozen asset.</div>` : ""}
        </div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">Health</h3>
        <span class="card-note">Weibull hazard</span></div>
        <div class="card-body"><dl class="kv">
          <dt>Wear</dt><dd class="${node.health.wear > 0.7 ? "down" : ""}">${fmt.pct(node.health.wear)}</dd>
          <dt>Performance derate</dt><dd>${fmt.pct(node.health.derate)}</dd>
          <dt>Instantaneous hazard</dt><dd>${fmt.num(node.health.hazard, 4)}</dd>
          <dt>Remaining useful life</dt><dd>${fmt.int(fleet.remainingLife(node))} h</dd>
          <dt>Thermal cycles</dt><dd>${fmt.int(node.health.thermalCycles)}</dd>
          <dt>Correctable errors</dt><dd>${fmt.int(node.health.correctableErrors)}</dd>
          <dt>Maintenance reserve</dt><dd>${fmt.usd(fleet.maintenanceReserve(node), 3)}/h</dd>
          <dt>Age</dt><dd>${fmt.int(node.ageHours)} h of ${fmt.int(node.hardware.lifeHours)}</dd>
        </dl></div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">Asset · UOR</h3>
        <span class="card-note">value = orbit-stabilizer co-volume</span></div>
        <div class="card-body"><dl class="kv">
          <dt>UOR address</dt><dd>${fmt.esc(card.uor)}</dd>
          <dt>Substrate point</dt><dd>${card.point} · 𝔽₃⁴ = ${card.vector}</dd>
          <dt>Orbit cell</dt><dd>${fmt.int(card.cell)} of 51,840</dd>
          <dt>Stabiliser order</dt><dd>${fmt.int(card.stabiliser)}</dd>
          <dt>Orbit size</dt><dd>${fmt.int(card.orbit)}</dd>
          <dt>Co-volume</dt><dd>${fmt.num(card.coVolume, 3)}</dd>
          <dt>Constraints</dt><dd>${card.constraints.length ? card.constraints.join(", ") : "none"}</dd>
          <dt>Provenance</dt><dd class="${card.provenance.clean ? "up" : "down"}">${card.provenance.clean ? "clean" : card.provenance.anomalies.length + " anomalies"}</dd>
        </dl></div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">Site</h3></div>
        <div class="card-body"><dl class="kv">
          <dt>Datacentre</dt><dd>${fmt.esc(dc.name)}</dd>
          <dt>Grid</dt><dd>${fmt.esc(dc.grid)} · ${fmt.usd(energy.priceFor(dc.id), 2)}/MWh</dd>
          <dt>Carbon intensity</dt><dd>${fmt.int(energy.carbonFor(dc.id))} gCO₂/kWh</dd>
          <dt>PUE</dt><dd>${dc.pue}</dd>
          <dt>Operator</dt><dd>${fmt.esc(node.operator)}</dd>
          <dt>Fabric neighbours</dt><dd>${fleet.neighboursOf(node).length} in cell</dd>
        </dl></div></div>

      <div class="row">
        <button class="btn primary" id="drawerBuy">Buy 4 node-hours</button>
        <button class="btn none" id="drawerAnchor">Set as anchor</button>
      </div>`;

    $("drawerBuy").addEventListener("click", () => {
      const o = market.submitBuy({ instrument: "spot", qty: 4, workloadId: ui.workload, nodeId: node.id });
      if (o.filledQty > 0) toast("Filled", `${o.filledQty} node-hr on ${node.id.slice(-10)}`, "up");
      else toast("No fill", "node had no free capacity at your price", "down");
      closeDrawer(); render();
    });
    $("drawerAnchor").addEventListener("click", () => {
      ui.anchor = node.addr.slice();
      $("tkAnchor").value = node.address;
      toast("Anchor set", node.address + " — locality now priced from here");
      closeDrawer(); render();
    });

    $("drawer").classList.add("open");
    $("drawerBack").classList.add("open");
  }

  function closeDrawer() {
    $("drawer").classList.remove("open");
    $("drawerBack").classList.remove("open");
  }

  // ====================================================================
  // FABRIC
  // ====================================================================

  function renderFabric() {
    const fs = fabric.fabricStats(market.positions);
    const listed = fleet.listedNodes();

    $("fabricStats").innerHTML = [
      tile("Fleet coherence", fmt.pct(fs.fleetCoherence), `${fmt.num(fs.totalBisection, 0)} of ${fmt.num(fs.idealBisection, 0)} ideal bisection`, "accent"),
      tile("Cells", fmt.int(fs.cells), `${fs.completeCells} complete · mean occupancy ${fmt.pct(fs.meanOccupancy, 0)}`),
      tile("Fabric level", "H" + fs.level, `diameter ${fs.diameterAtLevel} hops worst case`),
      tile("Your fragmentation", fmt.pct(fs.fragmentation), fs.fragmentation > 0.5 ? "swap book has proposals" : "positions are coherent", fs.fragmentation > 0.5 ? "down" : "up"),
    ].join("");

    drawW33();
    renderRouting();
    renderTower();
    renderCells();
    renderLadder();
    renderSwaps();

    const cp = fabric.clearingProfile();
    $("clearingStats").innerHTML = [
      tile("Hops to agreement", cp.hops, `then ${cp.rounds} averaging rounds`),
      tile("Contraction / round", "1/3", "≈19 rounds for a part in 10⁹"),
      tile("Byzantine tolerance", cp.byzantineTolerance, `${cp.byzantineBreaks} breaks the tested config`, "amber"),
      tile("Joules per clear", fmt.sci(cp.joulesPerClear), `${cp.ordersOfMagnitude} orders below proof-of-work`, "up"),
    ].join("");
  }

  function drawW33() {
    const cv = $("w33Canvas");
    const { ctx, w, h } = prepCanvas(cv);
    const cx = w / 2, cy = h / 2, R = Math.min(w, h) * 0.42;
    const occupied = new Set();
    const cells = fabric.cells();
    const cell = cells[0];
    if (cell) for (const n of cell.nodes) occupied.add(n.cellPoint);

    const pos = Substrate.POINTS.map((p, i) => {
      const a = (i / 40) * Math.PI * 2 - Math.PI / 2;
      return { x: cx + Math.cos(a) * R, y: cy + Math.sin(a) * R, i };
    });

    const sel = ui.selectedPoint;
    const nbrs = sel != null ? new Set(Substrate.ADJ[sel]) : null;

    // edges
    for (let i = 0; i < 40; i++) {
      for (const j of Substrate.ADJ[i]) {
        if (j <= i) continue;
        const hot = sel != null && (i === sel || j === sel);
        ctx.strokeStyle = hot ? css("--amber", "#f5a524") : css("--border", "#1c2740");
        ctx.globalAlpha = hot ? 0.85 : (occupied.has(i) && occupied.has(j) ? 0.4 : 0.14);
        ctx.lineWidth = hot ? 1.4 : 0.7;
        ctx.beginPath(); ctx.moveTo(pos[i].x, pos[i].y); ctx.lineTo(pos[j].x, pos[j].y); ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;

    // nodes
    pos.forEach((p) => {
      const isSel = p.i === sel;
      const isNbr = nbrs && nbrs.has(p.i);
      ctx.beginPath();
      ctx.arc(p.x, p.y, isSel ? 6 : 4, 0, Math.PI * 2);
      ctx.fillStyle = isSel || isNbr ? css("--amber", "#f5a524")
        : occupied.has(p.i) ? css("--accent", "#38bdf8") : css("--border-hi", "#2e3d5e");
      ctx.fill();
    });

    ctx.fillStyle = css("--text-2", "#61708c");
    ctx.font = "10px " + css("--mono", "monospace");
    ctx.textAlign = "center";
    ctx.fillText("SRG(40,12,2,4) · 240 edges · diameter 2 · bisection 100", cx, h - 4);

    cv.onclick = (e) => {
      const r = cv.getBoundingClientRect();
      const mx = e.clientX - r.left, my = e.clientY - r.top;
      let bestI = null, bestD = 16;
      pos.forEach((p) => {
        const d = Math.hypot(p.x - mx, p.y - my);
        if (d < bestD) { bestD = d; bestI = p.i; }
      });
      ui.selectedPoint = ui.selectedPoint === bestI ? null : bestI;
      drawW33();
    };
  }

  function renderRouting() {
    const from = $("routeFrom"), to = $("routeTo");
    if (!from.options.length) {
      const opts = Substrate.POINTS.map((p, i) => `<option value="${i}">${String(i).padStart(2, "0")} · 𝔽₃⁴ ${p.vec.join("")}</option>`).join("");
      from.innerHTML = opts; to.innerHTML = opts;
      from.value = "0"; to.value = "17";
      from.addEventListener("change", renderRouting);
      to.addEventListener("change", renderRouting);
    }
    const a = parseInt(from.value, 10), b = parseInt(to.value, 10);
    const r = Substrate.route(a, b);
    const inner = Substrate.symplecticForm(Substrate.POINTS[a].vec, Substrate.POINTS[b].vec);
    const mig = Substrate.migrationCost([a], [b]);

    $("routeResult").innerHTML = `<dl class="kv">
      <dt>⟨x, y⟩ mod 3</dt><dd class="${inner === 0 ? "up" : ""}">${inner}${inner === 0 ? " — adjacent" : " — not adjacent"}</dd>
      <dt>Path</dt><dd>${r.hops.map((x) => String(x).padStart(2, "0")).join(" → ")}</dd>
      <dt>Distance</dt><dd>${r.distance} hop${r.distance === 1 ? "" : "s"}</dd>
      <dt>Equal-cost alternates</dt><dd>${r.alternates.length}${r.distance === 2 ? " (μ = 4 disjoint paths)" : ""}</dd>
      <dt>Migration cost</dt><dd>${mig.rays} rays · <span class="tag ${mig.channel === "cheap" ? "up" : ""}">${mig.channel}</span></dd>
      <dt>Page bill</dt><dd>${mig.pageBill} points (constant either way)</dd>
    </dl>
    <div class="note" style="margin-top:11px">No table was consulted. Adjacency is <code>⟨x,y⟩ = 0 mod 3</code> — one modular inner product, a handful of bit operations. That is why locality is a closed-form number this exchange can price per order instead of guessing at with availability-zone heuristics. And the migration price law is why a neighbour (3 rays) beats reconfiguring in place (6).</div>`;
  }

  function renderTower() {
    const tower = fabric.buildTower(4);
    $("towerBody").innerHTML = tower.map((lvl) => {
      const obj = lvl.objects[0];
      if (!obj) return "";
      const q = obj.isComposite ? pricing.quote(obj, { workloadId: ui.workload }) : null;
      const leaves = lvl.objects.reduce((a, o) => a + (o.leaves || 1), 0);
      const coh = lvl.objects.reduce((a, o) => a + (o.coherence || 0), 0) / lvl.objects.length;
      return `<tr>
        <td><span class="tag accent">H${lvl.level}</span></td>
        <td class="num">${lvl.objects.length}</td>
        <td class="num">${fmt.int(leaves)}</td>
        <td class="num">${fmt.pct(coh, 0)}</td>
        <td class="num">${Substrate.diameterAtLevel(lvl.level)}</td>
        <td class="num">${q && q.price ? fmt.usd0(q.price) : "—"}</td>
      </tr>`;
    }).join("") || '<tr><td colspan="6" class="empty">no composites</td></tr>';
  }

  function renderCells() {
    const cells = fabric.cells().slice(0, 40);
    $("cellsBody").innerHTML = cells.map((c) => `<tr>
      <td class="mono">${fmt.esc(c.prefix)}</td>
      <td class="mono muted">${fmt.esc(c.dcId)}</td>
      <td class="num">${c.nodes.length}</td>
      <td class="num">${fmt.pct(c.occupancy, 0)}</td>
      <td class="num">${fmt.num(c.bisection, 1)}</td>
      <td class="num ${c.coherence > 0.9 ? "up" : ""}">${fmt.pct(c.coherence, 0)}</td>
    </tr>`).join("");
  }

  function renderLadder() {
    $("ladderBody").innerHTML = fabric.levelLadder(7).map((r) => `<tr>
      <td><span class="tag ${r.tradeable ? "accent" : ""}">H${r.level}</span></td>
      <td class="num">${fmt.big(r.leaves)}</td>
      <td class="num">${r.diameter}</td>
      <td class="num">${fmt.big(r.bisection)}</td>
      <td class="num">${fmt.usd(r.perNodeHour)}</td>
      <td class="muted" style="font-size:11px">${fmt.esc(r.seats)}${r.tradeable ? "" : " · bilateral"}</td>
    </tr>`).join("");
  }

  function renderSwaps() {
    const myNodes = market.positions.map((p) => fleet.get(p.nodeId)).filter(Boolean);
    const props = fabric.proposeSwaps(myNodes, { limit: 6 });
    $("fragNote").textContent = myNodes.length < 2
      ? "hold at least two positions to see swaps"
      : `${props.length} proposals · ${fabric.swapHistory.length} executed`;

    $("swapBody").innerHTML = props.length ? props.map((p, i) => `<tr>
      <td class="mono">${p.id}</td>
      <td class="mono muted">${fmt.esc(p.give.address)}</td>
      <td class="mono">${fmt.esc(p.get.address)}</td>
      <td class="num up">+${fmt.pct(p.coherenceGain, 1)}</td>
      <td class="num ${p.counterpartyGain > 0 ? "up" : "muted"}">+${fmt.pct(p.counterpartyGain, 1)}</td>
      <td class="num ${sgn(p.cashAdjustment)}">${fmt.usd(p.cashAdjustment)}</td>
      <td><button class="btn sm" data-swap="${i}">Swap</button></td>
    </tr>`).join("") : `<tr><td colspan="7" class="empty">${myNodes.length < 2 ? "buy at least two nodes to generate swap proposals" : "positions are already coherent — nothing to defragment"}</td></tr>`;

    $("swapBody").querySelectorAll("[data-swap]").forEach((b) => b.addEventListener("click", () => {
      const p = props[parseInt(b.dataset.swap, 10)];
      const r = fabric.executeSwap(p, market.positions);
      if (r.ok) {
        market.cash += r.cash;
        toast("Swapped", `${p.give.address} → ${p.get.address} · coherence +${(p.coherenceGain * 100).toFixed(1)}%`, "up");
        render();
      }
    }));
  }

  // ====================================================================
  // BALANCE
  // ====================================================================

  function renderBalance() {
    const st = pricing.fleetStats;
    const wd = pricing.wearDispersion();

    $("balanceStats").innerHTML = [
      tile("Utilisation Gini", fmt.num(st.gini, 4), "0 = every node equally loaded", st.gini < 0.15 ? "up" : st.gini > 0.3 ? "down" : "amber"),
      tile("Mean utilisation", fmt.pct(st.meanUtilisation), `target band 55–78%`),
      tile("In band", fmt.pct(st.bandPct, 0), `${st.cold} cold · ${st.hot} hot`),
      tile("Wear dispersion", fmt.num(wd.cv, 3), "coefficient of variation across the fleet"),
    ].join("");

    const hist = pricing.balanceHistory;
    drawLines($("giniCanvas"), [
      { data: hist.map((h) => h.gini), color: css("--accent", "#38bdf8"), fill: "rgba(56,189,248,0.10)", width: 2 },
      { data: hist.map((h) => h.mean), color: css("--up", "#2dd4a7"), width: 1.2, dash: [4, 3] },
    ], { min: 0, max: Math.max(0.6, ...hist.map((h) => Math.max(h.gini, h.mean))) + 0.05, fmtY: (v) => v.toFixed(2) });

    // histogram of utilisation
    const bins = new Array(10).fill(0);
    for (const n of fleet.listedNodes()) bins[Math.min(9, Math.floor(n.utilisation * 10))]++;
    drawBars($("histCanvas"), bins.map((v, i) => ({
      label: (i * 10) + "",
      value: v,
      color: (i / 10 >= 0.55 && i / 10 < 0.78) ? css("--up", "#2dd4a7") : (i / 10 >= 0.78 ? css("--down", "#f4526b") : css("--text-2", "#61708c")),
    })));
    $("bandNote").textContent = `green = inside the target band`;

    $("wearKv").innerHTML = `
      <dt>Mean wear</dt><dd>${fmt.pct(wd.mean)}</dd>
      <dt>Std deviation</dt><dd>${fmt.num(wd.std, 4)}</dd>
      <dt>Coefficient of variation</dt><dd>${fmt.num(wd.cv, 3)}</dd>
      <dt>Nodes due for service</dt><dd class="${st.serviceDue > 0 ? "down" : ""}">${st.serviceDue}</dd>
      <dt>Currently in service</dt><dd>${st.inService}</dd>`;

    // D curve
    const cv = $("dCurveCanvas");
    const { ctx, w, h } = prepCanvas(cv);
    const pad = { l: 44, r: 12, t: 12, b: 24 };
    const probe = { utilisation: 0, utilisationEMA: 0.5, hardware: { thermalSensitivity: 1 } };
    const pts = [];
    for (let i = 0; i <= 100; i++) {
      probe.utilisation = i / 100;
      pts.push(pricing.demandMultiplier(probe));
    }
    const min = 0.4, max = Math.max(2.2, ...pts);
    const X = (i) => pad.l + (i / 100) * (w - pad.l - pad.r);
    const Y = (v) => h - pad.b - ((v - min) / (max - min)) * (h - pad.t - pad.b);

    ctx.fillStyle = "rgba(45,212,167,0.10)";
    ctx.fillRect(X(55), pad.t, X(78) - X(55), h - pad.t - pad.b);

    ctx.strokeStyle = css("--border", "#1c2740");
    ctx.setLineDash([3, 3]); ctx.beginPath();
    ctx.moveTo(pad.l, Y(1)); ctx.lineTo(w - pad.r, Y(1)); ctx.stroke(); ctx.setLineDash([]);
    axes(ctx, w, h, pad);

    ctx.strokeStyle = css("--accent", "#38bdf8"); ctx.lineWidth = 2.2;
    ctx.beginPath();
    pts.forEach((v, i) => { i === 0 ? ctx.moveTo(X(i), Y(v)) : ctx.lineTo(X(i), Y(v)); });
    ctx.stroke();

    ctx.fillStyle = css("--text-2", "#61708c");
    ctx.font = "10px " + css("--mono", "monospace");
    ctx.textAlign = "right";
    [0.5, 1, 1.5, 2].forEach((v) => { if (v >= min && v <= max) ctx.fillText("×" + v.toFixed(1), pad.l - 6, Y(v) + 3); });
    ctx.textAlign = "center";
    ctx.fillText("0%", X(0) + 8, h - 8);
    ctx.fillText("target band", (X(55) + X(78)) / 2, h - 8);
    ctx.fillText("100%", X(100) - 12, h - 8);
  }

  // ====================================================================
  // HEALTH
  // ====================================================================

  function renderHealth() {
    const nodes = fleet.nodes;
    const due = nodes.filter((n) => n.health.serviceDue);
    const inSvc = nodes.filter((n) => n.health.inService);
    const meanWear = nodes.reduce((a, n) => a + n.health.wear, 0) / nodes.length;
    const reserveTotal = fleet.listedNodes().reduce((a, n) => a + fleet.maintenanceReserve(n), 0);

    $("healthStats").innerHTML = [
      tile("Mean wear", fmt.pct(meanWear), `${nodes.length} nodes tracked`, meanWear > 0.6 ? "down" : ""),
      tile("Service due", fmt.int(due.length), `${inSvc.length} currently out`, due.length > 8 ? "down" : "amber"),
      tile("Reserve accrual", fmt.usd(reserveTotal, 2) + "/hr", "withheld from clearing to fund service"),
      tile("Mean RUL", fmt.big(nodes.reduce((a, n) => a + fleet.remainingLife(n), 0) / nodes.length) + " h", "remaining useful life"),
    ].join("");

    // hazard curve
    const cv = $("hazardCanvas");
    const { ctx, w, h } = prepCanvas(cv);
    const pad = { l: 44, r: 12, t: 12, b: 24 };
    const kinds = [["gpu", HW_COLOR.gpu], ["cpu", HW_COLOR.cpu], ["photonic", HW_COLOR.photonic]];
    const series = kinds.map(([kind, color]) => {
      const hw = HARDWARE.find((x) => x.kind === kind);
      const data = [];
      for (let i = 0; i <= 100; i++) data.push(HolotradeFleet.weibullHazard(i / 100, hw));
      return { data, color, width: 1.8, label: kind };
    });
    const maxH = Math.max(...series.flatMap((s) => s.data));
    const X = (i) => pad.l + (i / 100) * (w - pad.l - pad.r);
    const Y = (v) => h - pad.b - (v / maxH) * (h - pad.t - pad.b);
    axes(ctx, w, h, pad);
    series.forEach((s) => {
      ctx.strokeStyle = s.color; ctx.lineWidth = s.width; ctx.beginPath();
      s.data.forEach((v, i) => { i === 0 ? ctx.moveTo(X(i), Y(v)) : ctx.lineTo(X(i), Y(v)); });
      ctx.stroke();
    });
    // scatter actual fleet
    ctx.globalAlpha = 0.5;
    for (const n of nodes) {
      ctx.fillStyle = HW_COLOR[n.hardware.kind] || "#888";
      ctx.beginPath(); ctx.arc(X(n.health.wear * 100), Y(n.health.hazard), 1.6, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
    ctx.fillStyle = css("--text-2", "#61708c");
    ctx.font = "10px " + css("--mono", "monospace");
    ctx.textAlign = "center";
    ctx.fillText("wear →", w / 2, h - 6);
    ctx.textAlign = "left";
    series.forEach((s, i) => {
      ctx.fillStyle = s.color;
      ctx.fillText("— " + s.label, pad.l + 6, pad.t + 12 + i * 13);
    });

    $("serviceNote").textContent = `${due.length} due · ${inSvc.length} out`;
    const btn = $("serviceDueBtn");
    btn.disabled = due.length === 0;
    btn.textContent = due.length ? `Service ${due.length} due node${due.length === 1 ? "" : "s"}` : "Nothing due";
    if (!btn.dataset.bound) {
      btn.dataset.bound = "1";
      btn.addEventListener("click", () => {
        const list = fleet.nodes.filter((n) => n.health.serviceDue && !n.health.inService);
        list.forEach((n) => fleet.startService(n));
        toast("Service scheduled", `${list.length} nodes taken out of the book`, "amber");
        render();
      });
    }

    const rows = [...nodes].sort((a, b) => b.health.wear - a.health.wear).slice(0, 160);
    $("healthBody").innerHTML = rows.map((n) => `<tr class="clickable" data-node="${fmt.esc(n.id)}">
      <td class="mono">${fmt.esc(n.id.slice(-13))}</td>
      <td><span class="tag" style="color:${HW_COLOR[n.hardware.kind]}">${fmt.esc(n.hardware.class)}</span></td>
      <td class="mono muted">${fmt.esc(n.dcId)}</td>
      <td class="num ${n.health.wear > 0.7 ? "down" : ""}">${fmt.pct(n.health.wear)}</td>
      <td class="num">${fmt.pct(n.health.derate)}</td>
      <td class="num">${fmt.num(n.health.hazard, 4)}</td>
      <td class="num">${fmt.int(fleet.remainingLife(n))}</td>
      <td class="num muted">${fmt.int(n.health.thermalCycles)}</td>
      <td class="num muted">${fmt.int(n.health.correctableErrors)}</td>
      <td class="num">${fmt.usd(fleet.maintenanceReserve(n), 3)}</td>
      <td>${n.health.inService ? '<span class="tag amber">in service</span>' : n.health.serviceDue ? '<span class="tag down">due</span>' : '<span class="tag up">ok</span>'}</td>
    </tr>`).join("");
    $("healthBody").querySelectorAll("tr.clickable").forEach((r) =>
      r.addEventListener("click", () => openNode(r.dataset.node)));
  }

  // ====================================================================
  // GENETICS
  // ====================================================================

  function renderGenetics() {
    const s = genetics.summary();
    $("geneticsStats").innerHTML = [
      tile("Mean fitness", fmt.num(s.meanFitness, 3), "realised, not nameplate", "accent"),
      tile("Genetic diversity", fmt.num(s.diversity, 4), s.diversity < 0.12 ? "converging — crosses running out" : "healthy spread", s.diversity < 0.12 ? "down" : "up"),
      tile("Specialisation index", fmt.num(s.specialisationIndex, 3), "how sharply cores are specialised"),
      tile("Crosses made", fmt.int(s.crossesMade), `max generation ${s.maxGeneration}`, "violet"),
    ].join("");

    const sel = $("genWorkload");
    if (!sel.options.length) {
      sel.innerHTML = `<option value="">Overall fitness</option>` + WORKLOADS.map((w) => `<option value="${w.id}">${fmt.esc(w.name)}</option>`).join("");
      sel.addEventListener("change", () => { ui.genWorkload = sel.value; renderGenetics(); });
    }

    const lb = genetics.leaderboard({ workloadId: ui.genWorkload || null, limit: 20 });
    $("leaderBody").innerHTML = lb.map((r, i) => `<tr class="clickable" data-node="${fmt.esc(r.node.id)}">
      <td class="mono muted">${i + 1}</td>
      <td class="mono">${fmt.esc(r.node.id.slice(-13))}</td>
      <td><span class="tag" style="color:${HW_COLOR[r.node.hardware.kind]}">${fmt.esc(r.node.hardware.class)}</span></td>
      <td class="num">${fmt.num(r.score, 3)}</td>
      <td class="num muted">${fmt.num(r.fitness, 3)}</td>
      <td class="num muted">${r.generation}</td>
      <td class="num muted">${fmt.int(r.jobs)}</td>
    </tr>`).join("");
    $("leaderBody").querySelectorAll("tr.clickable").forEach((r) =>
      r.addEventListener("click", () => openNode(r.dataset.node)));

    const founders = genetics.founders(10);
    $("foundersBody").innerHTML = founders.length ? founders.map((f) => {
      const bl = genetics.bloodlineStrength(f.node);
      return `<tr class="clickable" data-node="${fmt.esc(f.node.id)}">
        <td class="mono">${fmt.esc(f.node.id.slice(-13))}</td>
        <td><span class="tag" style="color:${HW_COLOR[f.node.hardware.kind]}">${fmt.esc(f.node.hardware.class)}</span></td>
        <td class="num">${f.descendants}</td>
        <td class="num">${fmt.num(f.fitness, 3)}</td>
        <td class="num ${bl.mean > f.fitness ? "up" : "down"}">${fmt.num(bl.mean, 3)}</td>
        <td class="num muted">${fmt.num(bl.best || 0, 3)}</td>
      </tr>`;
    }).join("") : '<tr><td colspan="6" class="empty">no bloodlines yet</td></tr>';
    $("foundersBody").querySelectorAll("tr.clickable").forEach((r) =>
      r.addEventListener("click", () => openNode(r.dataset.node)));

    const crosses = genetics.suggestCrosses({ limit: 5, workloadId: ui.genWorkload || null });
    $("crossBody").innerHTML = crosses.length ? crosses.map((c, i) => `<tr>
      <td class="mono" style="font-size:10.5px">${fmt.esc(c.parents[0].id.slice(-9))} × ${fmt.esc(c.parents[1].id.slice(-9))}</td>
      <td class="mono">${fmt.esc(c.target.id.slice(-13))}</td>
      <td class="num muted">${fmt.num(c.distance, 3)}</td>
      <td class="num">${fmt.num(c.current, 3)}</td>
      <td class="num accent">${fmt.num(c.predicted, 3)}</td>
      <td class="num up">+${fmt.num(c.gain, 3)}</td>
      <td><button class="btn sm" data-cross="${i}">Breed</button></td>
    </tr>`).join("") : '<tr><td colspan="7" class="empty">no crosses worth making — parents are too similar or targets already strong</td></tr>';

    $("crossBody").querySelectorAll("[data-cross]").forEach((b) => b.addEventListener("click", () => {
      const c = crosses[parseInt(b.dataset.cross, 10)];
      const r = genetics.breed(c.parents[0], c.parents[1], c.target);
      if (r.ok) {
        toast("Cross deployed", `predicted ${r.predicted.toFixed(3)} · realised ${r.after.toFixed(3)} (no track record yet)`, r.after > r.before ? "up" : "down");
        render();
      }
    }));

    $("breedLogBody").innerHTML = genetics.breedLog.length ? genetics.breedLog.slice(0, 12).map((b) => `<tr>
      <td class="mono">${fmt.esc(b.target.slice(-13))}</td>
      <td class="num accent">${fmt.num(b.predicted, 3)}</td>
      <td class="num muted">${fmt.num(b.before, 3)}</td>
      <td class="num ${b.after > b.before ? "up" : "down"}">${fmt.num(b.after, 3)}</td>
      <td class="num muted">${b.generation}</td>
    </tr>`).join("") : '<tr><td colspan="5" class="empty">no crosses made yet</td></tr>';

    const census = genetics.classCensus();
    const total = census.reduce((a, r) => a + r.count, 0);
    $("censusBody").innerHTML = census.map((r) => `<tr>
      <td>${fmt.esc(r.name)}</td>
      <td class="num">${r.count}</td>
      <td class="num">${fmt.num(r.meanScore, 3)}</td>
      <td class="num muted">${fmt.pct(r.count / total, 1)}</td>
    </tr>`).join("");
  }

  // ====================================================================
  // ENERGY
  // ====================================================================

  function renderEnergy() {
    const sum = energy.summary(fleet.nodes);
    const cheapest = DATACENTERS.reduce((a, d) => (energy.priceFor(d.id) < energy.priceFor(a.id) ? d : a));
    const cleanest = DATACENTERS.reduce((a, d) => (energy.carbonFor(d.id) < energy.carbonFor(a.id) ? d : a));

    $("energyStats").innerHTML = [
      tile("Fleet draw", fmt.num(sum.totalKW, 0) + " kW", `${fmt.num(sum.annualTWh * 1000, 2)} GWh/yr at this load`, "amber"),
      tile("Energy cost", fmt.usd(sum.totalCostPerHour) + "/hr", "at this second's marginal prices"),
      tile("Carbon", fmt.num(sum.totalCarbonPerHour, 1) + " kg/hr", `cheapest ${cheapest.id} · cleanest ${cleanest.id}`),
      tile("Landauer floor", "2.64e-19 J", "per cycle at 300 K — 58 syndrome qutrits × kT ln 3", "up"),
    ].join("");

    const colors = ["#38bdf8", "#f4526b", "#2dd4a7", "#f5a524", "#a78bfa", "#93a3bd"];
    drawLines($("energyCanvas"), DATACENTERS.map((d, i) => ({
      data: energy.historyFor(d.id).slice(-240), color: colors[i % colors.length], width: 1.5,
    })), { fmtY: (v) => "$" + v.toFixed(0) });
    $("energyLegend").innerHTML = DATACENTERS.map((d, i) =>
      `<span><i style="background:${colors[i % colors.length]}"></i>${d.id} · ${d.grid}</span>`).join("");

    $("sitesBody").innerHTML = DATACENTERS.map((d) => {
      const agg = sum.byDc.get(d.id) || { kw: 0, nodes: 0 };
      const p = energy.priceFor(d.id);
      const spike = p > d.baseEnergy * 1.6;
      return `<tr>
        <td><b>${fmt.esc(d.id)}</b><div class="muted" style="font-size:10.5px">${fmt.esc(d.region)}</div></td>
        <td class="mono muted">${fmt.esc(d.grid)}</td>
        <td class="num ${spike ? "down" : p < d.baseEnergy * 0.75 ? "up" : ""}">${fmt.usd(p, 2)}</td>
        <td class="num">${fmt.int(energy.carbonFor(d.id))}</td>
        <td class="num muted">${d.pue}</td>
        <td class="num">${agg.nodes}</td>
        <td class="num">${fmt.num(agg.kw, 0)}</td>
        <td class="num ${energy.multiplier(d.id) > 1.1 ? "down" : energy.multiplier(d.id) < 0.92 ? "up" : ""}">${fmt.x(energy.multiplier(d.id))}</td>
      </tr>`;
    }).join("");

    $("floorBody").innerHTML = HARDWARE.map((hw) => {
      const dec = Substrate.thermodynamicDecades(hw.joulesPerOp, 300);
      const w = Math.min(100, (dec / 8) * 100);
      return `<tr>
        <td><span class="tag" style="color:${HW_COLOR[hw.kind]}">${fmt.esc(hw.class)}</span> <span class="muted" style="font-size:11px">${fmt.esc(hw.kind)}</span></td>
        <td class="num">${fmt.sci(hw.joulesPerOp, 1)}</td>
        <td class="num ${dec < 3 ? "up" : dec > 6 ? "down" : ""}">${fmt.num(dec, 2)}</td>
        <td style="width:110px"><div class="gene-track"><i style="width:${w}%;background:${dec < 3 ? css("--up", "#2dd4a7") : dec > 6 ? css("--down", "#f4526b") : css("--amber", "#f5a524")}"></i></div></td>
      </tr>`;
    }).join("");
  }

  // ====================================================================
  // EXECUTION
  // ====================================================================

  function renderExecution() {
    const s = exec.summary();
    $("execStats").innerHTML = [
      tile("Node-seconds metered", fmt.big(s.meteredSeconds), `effective ${fmt.usd(s.avgRatePerNodeHour)}/node-hr`, "accent"),
      tile("Spend", fmt.usd(s.meteredSpend, 4), `${fmt.num(s.meteredKWh, 4)} kWh drawn`),
      tile("Running VMs", fmt.int(s.running), `${s.settled} settled · ${s.rejected} refused`),
      tile("Audit chain", s.chain.ok ? "INTACT" : "BROKEN", `${s.chain.length} entries`, s.chain.ok ? "up" : "down"),
    ].join("");
    $("badgeVMs").textContent = s.running;

    const wsel = $("planWorkload");
    if (!wsel.options.length) {
      wsel.innerHTML = WORKLOADS.map((w) => `<option value="${w.id}">${fmt.esc(w.name)}${w.magicBudget ? ` · t=${w.magicBudget}` : ""}</option>`).join("");
      wsel.addEventListener("change", renderPlanPreview);
    }
    renderPlanPreview();
    renderPlacements();

    $("vmBody").innerHTML = exec.runningVMs().length ? exec.runningVMs().map((v) => `<tr>
      <td class="mono">${fmt.esc(v.id)}</td>
      <td class="mono muted">${fmt.esc(v.planId)}</td>
      <td class="mono muted">${fmt.esc(v.nodeId.slice(-11))}</td>
      <td class="num">${fmt.int(v.secondsRun)}s</td>
      <td class="num">${fmt.usd(v.cost, 4)}</td>
      <td class="num muted">${fmt.num(v.energyJoules / 3.6e6, 5)}</td>
      <td><button class="btn sm danger" data-halt="${fmt.esc(v.id)}">Halt</button></td>
    </tr>`).join("") : '<tr><td colspan="7" class="empty">no running microVMs</td></tr>';
    $("vmBody").querySelectorAll("[data-halt]").forEach((b) => b.addEventListener("click", () => {
      const r = exec.halt(b.dataset.halt);
      if (r) toast("Settled", `${r.nodeSeconds.toFixed(0)} node-s · ${fmt.usd(r.cost, 4)}`, "up");
      render();
    }));

    $("plansBody").innerHTML = exec.plans.length ? exec.plans.slice(0, 20).map((p) => `<tr>
      <td class="mono">${fmt.esc(p.id)}</td>
      <td class="mono muted" style="font-size:10.5px">${fmt.esc(p.digest.slice(0, 12))}</td>
      <td style="font-size:11px">${fmt.esc((WORKLOADS.find((w) => w.id === p.workloadId) || {}).name || p.workloadId)}</td>
      <td class="num ${p.magicBudget ? "violet" : "muted"}">${p.magicBudget}</td>
      <td class="num">${fmt.int(p.requestedSeconds * p.nodeCount)}</td>
      <td><span class="tag ${p.status === "settled" ? "up" : p.status === "rejected" ? "down" : p.status === "running" ? "accent" : ""}">${p.status}</span></td>
    </tr>`).join("") : '<tr><td colspan="6" class="empty">no plans</td></tr>';

    $("auditBody").innerHTML = exec.auditLog.slice(0, 24).map((e) => `<tr>
      <td class="mono muted">${e.seq}</td>
      <td><span class="tag ${e.kind.includes("failed") ? "down" : e.kind.includes("settled") ? "up" : "accent"}">${fmt.esc(e.kind)}</span></td>
      <td class="wrap" style="font-size:11px">${fmt.esc(e.detail)}</td>
      <td class="mono muted" style="font-size:10px">${fmt.esc(e.prev.slice(0, 4))}→${fmt.esc(e.hash.slice(0, 6))}</td>
    </tr>`).join("") || '<tr><td colspan="4" class="empty">chain empty</td></tr>';
    $("chainNote").textContent = s.chain.ok ? "verified — every entry commits to the last" : `BROKEN at #${s.chain.brokenAt}`;

    $("densityBody").innerHTML = [1, 2, 3, 4, 5, 6, 7].map((n) => {
      const d = exec.densityAt(n);
      return `<tr>
        <td><span class="tag accent">${n}</span></td>
        <td class="num">${fmt.int(d.leaves)}</td>
        <td class="num">${fmt.int(d.internal)}</td>
        <td class="num">${fmt.int(d.total)}</td>
        <td class="num up">${d.uniqueBlobs}</td>
        <td class="num muted">${d.diameter}</td>
      </tr>`;
    }).join("");
  }

  function renderPlanPreview() {
    const wid = $("planWorkload").value || "llm-train";
    const w = WORKLOADS.find((x) => x.id === wid);
    const secs = Math.max(1, parseInt($("planSeconds").value, 10) || 1);
    const nodes = Math.max(1, parseInt($("planNodes").value, 10) || 1);
    const grants = $("planGrants").value.trim();
    $("planPreview").innerHTML = `
      <dt>Magic budget t</dt><dd class="${w.magicBudget ? "violet" : ""}">${w.magicBudget}</dd>
      <dt>Classical emulation cost</dt><dd>${w.magicBudget ? "9^" + w.magicBudget + " = " + fmt.sci(Substrate.magicMultiplier(w.magicBudget)) : "1 — free"}</dd>
      <dt>Node-seconds requested</dt><dd>${fmt.int(secs * nodes)}</dd>
      <dt>Egress</dt><dd class="${grants ? "amber" : "up"}">${grants ? fmt.esc(grants) : "deny all — no network device"}</dd>
      <dt>Settlement granularity</dt><dd>1 second</dd>
      <dt>Boot overhead at 1s</dt><dd>${(HolotradeExecution.BOOT_MS.p50 / 1000 * 100).toFixed(1)}%</dd>`;
  }

  function renderPlacements() {
    const plan = ui.selectedPlan ? exec.plans.find((p) => p.id === ui.selectedPlan) : null;
    if (!plan || plan.status !== "signed") {
      $("placeBody").innerHTML = '<tr><td colspan="8" class="empty">sign a plan to see placements</td></tr>';
      return;
    }
    const places = exec.place(plan, { limit: 6 });
    $("placeBody").innerHTML = places.length ? places.map((p, i) => `<tr>
      <td class="mono">${fmt.esc(p.node.id.slice(-13))}</td>
      <td class="mono muted">${fmt.esc(p.node.address)}</td>
      <td><span class="tag" style="color:${HW_COLOR[p.node.hardware.kind]}">${fmt.esc(p.node.hardware.class)}</span></td>
      <td class="num">${fmt.usd(p.perSecond, 6)}</td>
      <td class="num muted">${p.boot.ms.toFixed(0)}ms</td>
      <td class="num"><span class="tag ${p.migration.channel === "cheap" ? "up" : ""}">${p.migration.rays}r</span></td>
      <td class="num accent">${fmt.usd(p.total, 4)}</td>
      <td><button class="btn sm primary" data-place="${i}">Launch</button></td>
    </tr>`).join("") : '<tr><td colspan="8" class="empty">no admissible node — check the magic budget</td></tr>';

    $("placeBody").querySelectorAll("[data-place]").forEach((b) => b.addEventListener("click", () => {
      const p = places[parseInt(b.dataset.place, 10)];
      const r = exec.launch(plan, p.node);
      if (r.ok) {
        toast("Launched", `${r.vm.id} booted in ${r.boot.ms.toFixed(0)}ms`, "up");
        ui.selectedPlan = null;
      } else {
        toast("Refused", `${r.code}: ${r.reason}`, "down");
      }
      render();
    }));
  }

  // ====================================================================
  // PORTFOLIO
  // ====================================================================

  function renderPortfolio() {
    const mtm = market.markToMarket();
    const cap = market.capacitySummary();
    const myNodes = market.positions.map((p) => fleet.get(p.nodeId)).filter(Boolean);

    $("portfolioStats").innerHTML = [
      tile("Equity", fmt.usd0(mtm.equity), `cash ${fmt.usd0(mtm.cash)}`, "accent"),
      tile("Unrealised", fmt.usd(mtm.unrealised), `realised ${fmt.usd(mtm.realised)}`, sgn(mtm.unrealised)),
      tile("Capacity held", fmt.big(cap.tflops) + " TF", `${cap.positions} positions · ${cap.magicNodes} magic`),
      tile("Carbon", fmt.num(cap.carbonPerHour, 2) + " kg/hr", "at current marginal intensity"),
    ].join("");

    $("posNote").textContent = `${mtm.rows.length} open`;
    $("posBody").innerHTML = mtm.rows.length ? mtm.rows.map((r) => `<tr class="clickable" data-node="${fmt.esc(r.nodeId)}">
      <td class="mono">${fmt.esc(r.nodeId.slice(-13))}</td>
      <td class="mono muted">${fmt.esc(r.node.address)}</td>
      <td><span class="tag">${r.instrument}</span></td>
      <td style="font-size:11px">${fmt.esc((WORKLOADS.find((w) => w.id === r.workloadId) || {}).name || "")}</td>
      <td class="num">${r.qty}</td>
      <td class="num muted">${fmt.usd(r.avgPrice)}</td>
      <td class="num">${fmt.usd(r.mark)}</td>
      <td class="num">${fmt.usd(r.value)}</td>
      <td class="num ${sgn(r.pnl)}">${fmt.usd(r.pnl)} <span class="muted">${r.pnlPct >= 0 ? "+" : ""}${r.pnlPct.toFixed(1)}%</span></td>
      <td><button class="btn sm" data-sell="${r.id}">Sell</button></td>
    </tr>`).join("") : '<tr><td colspan="10" class="empty">no positions — buy something on the Exchange</td></tr>';

    $("posBody").querySelectorAll("tr.clickable").forEach((r) => r.addEventListener("click", (e) => {
      if (e.target.tagName === "BUTTON") return;
      openNode(r.dataset.node);
    }));
    $("posBody").querySelectorAll("[data-sell]").forEach((b) => b.addEventListener("click", (e) => {
      e.stopPropagation();
      const r = market.submitSell({ positionId: b.dataset.sell });
      if (r.ok) toast("Closed", `P&L ${fmt.usd(r.pnl)}`, r.pnl >= 0 ? "up" : "down");
      else toast("No bid", r.reason, "down");
      render();
    }));

    // shape
    if (myNodes.length >= 2) {
      const q = fabric.quoteBasket(myNodes, { workloadId: ui.workload });
      const g = q ? q.guarantees : null;
      $("shapeBody").innerHTML = q ? `
        <dl class="kv">
          <dt>Nodes held</dt><dd>${q.nodes}</dd>
          <dt>Sum of parts</dt><dd>${fmt.usd(q.sumParts)}/hr</dd>
          <dt>Coherence</dt><dd class="${q.coherence > 0.6 ? "up" : "down"}">${fmt.pct(q.coherence)}</dd>
          <dt>Coherence multiplier</dt><dd>${fmt.x(q.coherenceMultiplier)}</dd>
          <dt>Basket value</dt><dd class="accent">${fmt.usd(q.price)}/hr</dd>
          <dt>Premium over parts</dt><dd class="${sgn(q.premium)}">${fmt.usd(q.premium)}/hr</dd>
          <dt>Realised bisection</dt><dd>${fmt.num(q.bisection, 1)} of ${fmt.num(q.idealBisection, 1)}</dd>
          <dt>Worst-case hops</dt><dd>${isFinite(q.diameter) ? q.diameter : "disconnected"}</dd>
          <dt>Effective capacity</dt><dd>${fmt.big(q.effectiveTflops)} TF</dd>
        </dl>
        <hr class="sep">
        <div class="note ${q.coherence > 0.6 ? "" : "amber"}"><b>Structural guarantees</b> — theorems about the shape you hold, not an SLA someone promises:
          max ${g.maxHops} hops · ${g.disjointPaths} disjoint path${g.disjointPaths === 1 ? "" : "s"} ·
          ${g.crashTolerance} crash faults · ${g.byzantineTolerance} Byzantine ·
          ${g.tableFree ? "table-free routing" : "routing needs a table at this coherence"}.
          ${q.coherence < 0.6 ? "<br><br>Your positions are scattered. Check the swap book on the Fabric page — defragmenting costs no cash and both sides gain." : ""}
        </div>` : '<div class="empty">no quote</div>';
    } else {
      $("shapeBody").innerHTML = '<div class="empty">hold at least two nodes — coherence is not a property any single node has</div>';
    }

    const fills = market.trades.filter((t) => !t.ambient).slice(0, 30);
    $("fillsBody").innerHTML = fills.length ? fills.map((t) => `<tr>
      <td class="mono muted">${fmt.time(t.ts)}</td>
      <td><span class="tag ${t.side === "buy" ? "up" : "down"}">${t.side}</span></td>
      <td class="mono">${fmt.esc(t.nodeId.slice(-12))}</td>
      <td class="num">${t.qty}</td>
      <td class="num">${fmt.usd(t.price, 3)}</td>
    </tr>`).join("") : '<tr><td colspan="5" class="empty">no fills</td></tr>';
  }

  // ====================================================================
  // ASSETS / UOR
  // ====================================================================

  function renderAssets() {
    const prof = registry.liquidityProfile();
    const U = HolotradeUOR.UOR;

    $("assetStats").innerHTML = [
      tile("Assets registered", fmt.int(prof.count), "every listed node is a smart asset", "accent"),
      tile("Mean co-volume", fmt.num(prof.meanCoVolume, 3), "|orbit| / max orbit"),
      tile("Deep / bilateral", `${prof.bands.deep} / ${prof.bands.bilateral}`, `${prof.bands.liquid} liquid · ${prof.bands.thin} thin`),
      tile("Canonical cells", fmt.int(U.canonicalCells), "40 × 1,296 = |Aut(W(3,3))|", "violet"),
    ].join("");

    $("uorStats").innerHTML = [
      tile("Address width", U.bits + " bits", "one flat resolve, no lookup"),
      tile("Sylow choices", U.sylowChoices, "n₃(Sp(4,𝔽₃)) = v = 40"),
      tile("Normaliser order", fmt.int(U.normaliserOrder), "|N_G(P₃)| = μ² · q^(q+1) = 16 × 81"),
      tile("Payload", fmt.num(U.payloadBits, 2) + " bits", "64 − log₂(51,840), computed not quoted"),
    ].join("");

    drawBars($("liquidityCanvas"), [
      { label: "deep", value: prof.bands.deep, color: css("--up", "#2dd4a7") },
      { label: "liquid", value: prof.bands.liquid, color: css("--accent", "#38bdf8") },
      { label: "thin", value: prof.bands.thin, color: css("--amber", "#f5a524") },
      { label: "bilateral", value: prof.bands.bilateral, color: css("--down", "#f4526b") },
    ]);

    $("constraintBody").innerHTML = Object.entries(HolotradeUOR.CONSTRAINT_WEIGHT).map(([k, wgt]) => {
      const stab = Math.min(U.autOrder, U.normaliserOrder * wgt);
      const orbit = Math.max(1, Math.round(U.autOrder / stab));
      const cv = orbit / (U.autOrder / U.normaliserOrder);
      const band = HolotradeUOR.liquidityBand(cv);
      return `<tr>
        <td class="mono">${fmt.esc(k)}</td>
        <td class="num">×${wgt}</td>
        <td class="num">${orbit}</td>
        <td class="num">${fmt.num(cv, 3)}</td>
        <td><span class="tag ${band === "deep" ? "up" : band === "bilateral" ? "down" : "amber"}">${band}</span></td>
      </tr>`;
    }).join("");

    // shell
    const sel = $("shellAnchor");
    const listed = fleet.listedNodes();
    if (!sel.options.length || sel.options.length !== Math.min(120, listed.length)) {
      sel.innerHTML = listed.slice(0, 120).map((n) => `<option value="${fmt.esc(n.id)}">${fmt.esc(n.id)} · ${fmt.esc(n.address)}</option>`).join("");
      if (!sel.dataset.bound) { sel.dataset.bound = "1"; sel.addEventListener("change", () => { ui.shellAnchor = sel.value; renderAssets(); }); }
    }
    const anchorNode = fleet.get(ui.shellAnchor || sel.value) || listed[0];
    if (anchorNode) {
      const sh = registry.shellFrom(anchorNode);
      const rows = [
        ["identity", "self", sh.counts.identity, sh.ratios.identity, sh.expectedRatios.identity],
        ["intersecting", "collinear — 1 hop", sh.counts.intersecting, sh.ratios.intersecting, sh.expectedRatios.intersecting],
        ["disjoint", "2 hops via one of μ=4 relays", sh.counts.disjoint, sh.ratios.disjoint, sh.expectedRatios.disjoint],
      ];
      $("shellBody").innerHTML = rows.map(([name, note, n, obs, exp]) => `<tr>
        <td><b>${name}</b><div class="muted" style="font-size:10.5px">${note}</div></td>
        <td class="num">${n}</td>
        <td class="num">${fmt.pct(obs, 1)}</td>
        <td class="num muted">${fmt.pct(exp, 1)}</td>
        <td class="num ${Math.abs(obs - exp) < 0.04 ? "up" : "amber"}">${(obs - exp >= 0 ? "+" : "") + fmt.pct(obs - exp, 1)}</td>
      </tr>`).join("");
    }

    renderCapacity();
  }

  function renderCapacity() {
    const r = $("tpsRange");
    if (!r.dataset.bound) { r.dataset.bound = "1"; r.addEventListener("input", () => { ui.tps = Math.pow(10, parseFloat(r.value)); renderCapacity(); }); }
    const cap = HolotradeUOR.venueCapacity(ui.tps);
    $("capacityStats").innerHTML = [
      tile("Transaction rate", fmt.big(cap.tps) + " TPS", "drag the slider", "accent"),
      tile("Conjugacy cadence", fmt.sci(cap.conjugacyCadence) + "/s", `× ${fmt.int(cap.cadencePrefactor)} = k³ = j(i), the modular j-invariant at τ = i`),
      tile("Logical rate", fmt.sci(cap.logicalRate) + "/s", "27/80 cap — CSS [[240,81,4,3]]₃", "violet"),
      tile("Coherence blocks", fmt.sci(cap.coherenceBlocks) + "/s", `settlement floor ${cap.settlementFloorMs} ms = h(E₈) ms`),
    ].join("");
  }

  // ====================================================================
  // RECEIPTS
  // ====================================================================

  function renderReceipts() {
    const rs = market.receipts;
    const substrate = rs.filter((r) => r.lane === "substrate");
    const clean = rs.filter((r) => r.verdictOk).length;
    const meanCF = substrate.length ? substrate.reduce((a, r) => a + r.contextualFraction, 0) / substrate.length : 0;

    $("receiptStats").innerHTML = [
      tile("Receipts", fmt.int(rs.length), `${clean} attested clean`, "accent"),
      tile("Substrate lane", fmt.int(substrate.length), `${rs.length - substrate.length} Clifford`),
      tile("Mean contextual fraction", substrate.length ? fmt.num(meanCF, 4) : "—", "target 0.1000 = (40−36)/40", Math.abs(meanCF - 0.1) < 0.012 && substrate.length ? "up" : ""),
      tile("KS budget", "36 / 40", "any classicalising intervention moves an integer", "violet"),
    ].join("");

    $("receiptNote").textContent = `${rs.length} settled`;
    $("receiptBody").innerHTML = rs.length ? rs.slice(0, 120).map((r) => `<tr class="clickable" data-node="${fmt.esc(r.nodeId)}">
      <td class="mono" style="font-size:10.5px">${fmt.esc(r.id)}</td>
      <td class="mono">${fmt.esc(r.nodeId.slice(-12))}</td>
      <td class="mono muted">${fmt.esc(r.nodeAddress)}</td>
      <td><span class="tag ${r.lane === "substrate" ? "violet" : ""}">${r.lane}</span></td>
      <td class="num">${r.lane === "substrate" ? fmt.num(r.contextualFraction, 4) : "—"}</td>
      <td><span class="tag ${r.verdictOk ? "up" : "down"}">${r.verdict}</span></td>
      <td class="num">${r.qty}</td>
      <td class="num">${fmt.usd(r.price, 3)}</td>
      <td class="num muted">${r.provenance ? r.provenance.generation : "—"}</td>
      <td class="muted" style="font-size:10.5px">${r.provenance ? `${fmt.int(r.provenance.jobsCompleted)} jobs · fit ${r.provenance.fitness.toFixed(2)}` : "—"}</td>
    </tr>`).join("") : '<tr><td colspan="10" class="empty">no receipts — every fill issues one</td></tr>';
    $("receiptBody").querySelectorAll("tr.clickable").forEach((r) =>
      r.addEventListener("click", () => openNode(r.dataset.node)));
  }

  // ====================================================================
  // DOCS
  // ====================================================================

  function renderDocs() {
    if ($("docsBody").dataset.done) return;
    $("docsBody").dataset.done = "1";
    $("docsBody").innerHTML = `
      <div class="card"><div class="card-head"><h3 class="card-title">What is actually being sold</h3></div>
        <div class="card-body">
          <p>Selling "a VM node for an hour" is the obvious design and it is the wrong one, for three reasons that are all measurable.</p>
          <p><b>1. The hour is a billing artefact, not a physical one.</b> It exists because provisioning a conventional VM takes minutes, so an hour is the smallest slice worth the scheduling overhead. A microVM boots in ~171 ms (p50; p99 178 ms, measured on Firecracker over deliberately pessimistic rotational storage). Once the unit boots in under a fifth of a second, the hour has no physical justification left.</p>
          <p><b>2. An hour cannot express the thing that actually varies.</b> Grid prices move every five minutes and go negative at 3 a.m. on ERCOT. If your settlement granularity is an hour you have thrown the signal away before you can price it. Per-second energy pricing <em>requires</em> a sub-second execution unit or it is theatre.</p>
          <p><b>3. "A node for an hour" is not auditable.</b> You cannot prove what ran on it, against which artefacts, under which grants. A signed execution plan can: it names the artefact digests, the egress grants, the secret references and the validity window <em>before</em> anything boots, and the audit log chains every event to the last.</p>
          <div class="note"><b>So the atomic unit is the node-second and the contract is the execution plan.</b><br>
            <b>asset</b> — the node: durable, has a genome and a health record, is what you lease or own.<br>
            <b>contract</b> — the plan: signed, content-addressed, scoped, time-boxed, and tradeable <em>before</em> it runs.<br>
            <b>unit</b> — the node-second: what settles, metered against real energy at the second it was drawn.</div>
        </div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">The price</h3><span class="card-note">P = P₀ × E × G × D × H × Q × L</span></div>
        <div class="card-body">
          <p>Multiplicative rather than additive, and that is a real decision: it keeps the terms independent, keeps every one auditable on its own line, and — once each is clamped — stops any single factor driving the price to zero or infinity on its own. The buyer sees the full decomposition on every quote. There is no opaque market rate.</p>
          <div class="tbl-wrap"><table class="tbl"><thead><tr><th>Term</th><th>What it prices</th><th>Where it comes from</th></tr></thead><tbody>
            <tr><td class="mono"><b>E</b></td><td>Energy</td><td>Live wholesale $/MWh at that site this second, PUE-adjusted, through a clamped power law so an operator passes through most of a move and none of a tail.</td></tr>
            <tr><td class="mono"><b>G</b></td><td>Genetics</td><td>Specialisation on <em>this</em> class × realised fitness × provenance depth. Never a nameplate figure.</td></tr>
            <tr><td class="mono"><b>D</b></td><td>Demand / wear</td><td>Two-sided. Premium above the target band, discount below. See below.</td></tr>
            <tr><td class="mono"><b>H</b></td><td>Health</td><td>Performance derate × Weibull reliability × correctable-error drift.</td></tr>
            <tr><td class="mono"><b>Q</b></td><td>Quantum</td><td>Exactly 1 for anything classical, and always will be — the Clifford layer is the stabilizer formalism and Gottesman–Knill makes it polynomial-time anywhere. Only non-Clifford gates are scarce, at 9<sup>t</sup>.</td></tr>
            <tr><td class="mono"><b>L</b></td><td>Locality</td><td>Fabric distance, from one symplectic inner product per hop. Not an availability-zone heuristic.</td></tr>
          </tbody></table></div>
          <p style="margin-top:11px">The floor is <b>energy + maintenance reserve + capital recovery</b>. All three, because a discount that does not repay the machine is not a discount — it is a loss the operator has not noticed yet. The exchange refuses to clear below it.</p>
        </div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">Why D is two-sided</h3></div>
        <div class="card-body">
          <p>The naive version of a compute market prices scarcity only: busy node costs more. That leaves the cold half of the fleet idle, and an idle node still ages, still draws standby power, and still has to be serviced on the same calendar.</p>
          <p>So D charges a premium above the band and pays a discount below it. The premium is superlinear because the wear term is — <b>thermal cycling, not duty cycle, is what actually kills silicon</b>, so a node swinging between idle and pinned wears faster than one held flat at the same average. The premium a popular node earns is not arbitrage; it is the maintenance reserve being funded by the people causing the wear.</p>
          <p>The discount is not charity either. Demand migrates toward the cheap nodes, dispersion falls, cycling falls with it, and service events spread out instead of arriving in a clump you have to staff for.</p>
          <div class="note"><b>The measured result:</b> utilisation Gini ≈ <b>0.083</b> with the balancer on against ≈ <b>0.164</b> with it off — a 50% reduction in fleet dispersion. Nothing in the loop pushes utilisation toward the band directly: a node's target is set by its price relative to the median of its own hardware class, and that price came from its utilisation. The band is where the loop settles, not where it is aimed. Toggle it yourself on the Balance page.</div>
        </div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">The network is the computer</h3></div>
        <div class="card-body">
          <p>On W(3,3), routing a packet <em>is</em> applying a gate <em>is</em> addressing memory. That is an algebraic identity, not an analogy — and it is the fact every conventional compute marketplace is built to contradict. They sell you compute, then network, then egress, because in a von Neumann machine those are three things with three bills.</p>
          <p><b>So you do not buy nodes, you buy shapes.</b> Forty scattered nodes and one complete cell have the same count and completely different value: the cell has diameter 2, bisection exactly 100 of 240 edges, and μ = 4 internally-disjoint paths between any non-adjacent pair, with no configuration. The scattered forty are forty computers and a network bill.</p>
          <p>Coherence therefore enters price at the <em>basket</em> level, never the node level, because it is not a property any single node has. And the value is superlinear in coherence rather than linear in count — the last few edges that complete a cell are worth more than the first few, because they are what collapse the diameter and unlock the multipath.</p>
          <div class="note"><b>The recursion closes.</b> A network of computers is a computer, so a network of <em>those</em> is a computer too. A composite implements exactly the interface a leaf implements — address, genome, health, utilisation, throughput — so there is <b>one order book and one pricing engine, applied at every level</b>. The engine cannot tell whether it is quoting a single GPU or a campus, and does not need to. An operator lists their whole H₃ campus as one instrument at level 4; a buyer at level 5 sees it as one line in the same book a single GPU appears in at level 1. The book is self-similar because the machine is.</div>
        </div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">Defragmentation</h3></div>
        <div class="card-body">
          <p>Trading fragments ownership. After a month of spot fills everyone holds confetti — a few points in each of forty cells — and the market's aggregate bisection has collapsed even though every individual position looks fine. That is a coordination failure with a clean fix: a swap book.</p>
          <p>I give you my orphan in your cell, you give me yours in mine. No cash changes hands beyond a small adjustment for the difference in the two machines. It is disk defragmentation, except the value being recovered is bandwidth — and unlike a disk, both parties can be made strictly better off, which is why the swaps are voluntary. <b>A swap is only offered when both sides gain</b>, because otherwise nobody takes the other side.</p>
        </div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">Value = orbit-stabilizer co-volume</h3></div>
        <div class="card-body">
          <p>Every real-world constraint is a symmetry an asset does <em>not</em> have. A node pinned by data-residency law cannot be moved by the automorphisms that would move it; a bare-metal reservation is fixed harder still. Each constraint multiplies the stabiliser, and by orbit-stabilizer that divides the orbit — the set of positions at which a counterparty could take delivery.</p>
          <p>So liquidity stops being a statistic gathered from the tape and becomes a computable property of the asset's own symmetry. That is the honest reason a residency-pinned node should not trade at the same price as an identical unpinned one, and it is a number you can check rather than a discount someone asserts.</p>
        </div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">Honest scope</h3></div>
        <div class="card-body">
          <div class="note scope">
            <b>Exact and computed here:</b> the W(3,3) geometry — SRG(40,12,2,4), 240 edges, 40 totally isotropic lines of 4 points, diameter 2, bisection 100 as the spectral bound (40/4)(12−2) met by an explicit cut; |Sp(4,𝔽₃)| = |W(E₆)| = 51,840; the fractal law 40ⁿ leaves at diameter 8n; the Landauer floor 2.64×10⁻¹⁹ J/cycle at 300 K from 58 syndrome qutrits × kT ln 3; the 9<sup>t</sup> magic cost; the venue capacity identities (×1728 cadence, 27/80 logical rate, 1/384 coherence blocks, h(E₈) = 30 ms floor). You can verify every one of these by running <code>node --test tests/core.test.js</code>.
          </div>
          <div class="note scope">
            <b>Modelled, not measured:</b> the fleet, the grid prices, the genomes, the wear, the order flow. This is a working simulation with a seeded PRNG so every run reproduces. Wire a real grid-price feed, real DCIM telemetry and a real inventory in place of <code>data/catalog.js</code> and the engines above it do not change.
          </div>
          <div class="note scope">
            <b>Asserted by the source program, not by this repo:</b> that W(3,3) is a candidate physical substrate, and the physics identifications that go with it. Holotrade does not depend on any of that being true. Everything it prices — the geometry, the routing rule, the code rate, the thermodynamic floor — is finite mathematics that holds regardless. The photonic hardware that would realise the quantum layer <b>does not exist</b>; what runs here is the classical Clifford emulation, which is polynomial-time and portable, and the quantum advantage stays a separately priced dial rather than a capability being claimed.
          </div>
        </div></div>`;
  }

  // ====================================================================
  // Router + loop
  // ====================================================================

  const RENDERERS = {
    exchange: renderExchange, fleet: renderFleet, fabric: renderFabric,
    balance: renderBalance, health: renderHealth, genetics: renderGenetics,
    energy: renderEnergy, execution: renderExecution, portfolio: renderPortfolio,
    assets: renderAssets, receipts: renderReceipts, docs: renderDocs,
  };

  function render() {
    renderHeader();
    const fn = RENDERERS[ui.view];
    if (fn) { try { fn(); } catch (err) { console.error("[render " + ui.view + "]", err); } }
  }

  function renderHeader() {
    const stats = pricing.marketStats({ workloadId: ui.workload });
    const mtm = market.markToMarket();
    $("simClock").textContent = fmt.clock(ui.simSeconds);
    $("chipMidVal").textContent = stats ? fmt.usd(stats.median) : "—";
    const g = pricing.fleetStats.gini;
    $("chipGiniVal").textContent = fmt.num(g, 3);
    $("chipGini").className = "chip " + (g < 0.15 ? "good" : g > 0.3 ? "bad" : "warn");
    $("chipEquityVal").textContent = fmt.usd0(mtm.equity);
    $("chipEquity").className = "chip " + (mtm.equity >= market.startingCash ? "good" : "bad");
  }

  function renderTapeStrip() {
    const rows = DATACENTERS.map((d) => {
      const p = energy.priceFor(d.id);
      const base = d.baseEnergy;
      const dev = (p / base - 1) * 100;
      return `<span class="tape-item">${d.id}<b>$${p.toFixed(1)}</b><span class="${dev >= 0 ? "down" : "up"}">${dev >= 0 ? "+" : ""}${dev.toFixed(1)}%</span></span>`;
    });
    const st = pricing.marketStats({ workloadId: ui.workload });
    if (st) {
      rows.push(`<span class="tape-item">SPOT MID<b>$${st.median.toFixed(2)}</b></span>`);
      rows.push(`<span class="tape-item">RANGE<b>$${st.min.toFixed(1)}–$${st.max.toFixed(0)}</b></span>`);
    }
    rows.push(`<span class="tape-item">GINI<b>${pricing.fleetStats.gini.toFixed(3)}</b></span>`);
    rows.push(`<span class="tape-item">COHERENCE<b>${(fabric.coherence(fleet.listedNodes()) * 100).toFixed(0)}%</b></span>`);
    rows.push(`<span class="tape-item">VMs<b>${exec.runningVMs().length}</b></span>`);
    const html = rows.join("");
    $("tapeTrack").innerHTML = html + html;
  }

  function step() {
    if (ui.paused) return;
    ui.tick++;
    const dt = ui.speed;
    ui.simSeconds += 30 * dt;

    energy.tick(30 * dt);
    pricing.applyDemandResponse((1 / 60) * dt, { workloadId: ui.workload });
    fleet.tick((1 / 60) * dt);
    exec.meter(dt).forEach((r) => {
      if (r) toast("Plan settled", `${r.nodeSeconds.toFixed(0)} node-s · ${fmt.usd(r.cost, 4)} · ${fmt.num(r.kwh, 5)} kWh`, "up");
    });
    market.ambientFlow(ui.instrument);

    // auto-service: nodes that reach the wear ceiling come out of the book
    if (ui.tick % 40 === 0) {
      for (const n of fleet.nodes) {
        if (n.health.wear > 0.86 && !n.health.inService) fleet.startService(n);
      }
    }

    if (ui.tick % 3 === 0) renderTapeStrip();
    render();
  }

  // ====================================================================
  // Wiring
  // ====================================================================

  function switchView(v) {
    ui.view = v;
    document.querySelectorAll(".view").forEach((s) => s.classList.toggle("hidden", s.id !== "view-" + v));
    document.querySelectorAll(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.view === v));
    $("sidebar").classList.remove("open");
    $("main").scrollTop = 0;
    render();
  }

  function boot() {
    document.querySelectorAll(".nav-btn").forEach((b) =>
      b.addEventListener("click", () => switchView(b.dataset.view)));

    // workload selectors
    const tkw = $("tkWorkload");
    tkw.innerHTML = WORKLOADS.map((w) => `<option value="${w.id}">${fmt.esc(w.name)}${w.magicBudget ? ` · t=${w.magicBudget}` : ""}</option>`).join("");
    tkw.value = ui.workload;
    tkw.addEventListener("change", () => { ui.workload = tkw.value; render(); });

    $("tkQty").addEventListener("input", renderTicketPreview);
    $("tkAnchor").addEventListener("change", () => {
      const v = $("tkAnchor").value.trim();
      ui.anchor = v ? Substrate.parseAddress(v) : null;
      if (v && (!ui.anchor || !ui.anchor.length)) { toast("Bad address", "expected dotted digits, e.g. 03.03.17", "down"); ui.anchor = null; }
      render();
    });
    $("tkClear").addEventListener("click", () => {
      $("tkQty").value = 4; $("tkLimit").value = ""; $("tkAnchor").value = "";
      ui.anchor = null; render();
    });
    $("tkBuy").addEventListener("click", () => {
      const qty = Math.max(1, parseInt($("tkQty").value, 10) || 1);
      const lim = parseFloat($("tkLimit").value);
      const o = market.submitBuy({
        instrument: ui.instrument, qty, workloadId: ui.workload,
        limitPrice: isFinite(lim) ? lim : null, anchorAddress: ui.anchor, days: 30,
      });
      if (o.filledQty > 0) toast("Filled", `${o.filledQty}/${qty} across ${o.fills.length} node${o.fills.length === 1 ? "" : "s"}`, "up");
      else if (o.status === "open") toast("Resting", "limit is below the best offer", "");
      else toast("Rejected", "no capacity at that price, or insufficient cash", "down");
      render();
    });

    // execution
    $("planCreate").addEventListener("click", () => {
      const grants = $("planGrants").value.trim();
      const p = exec.createPlan({
        name: $("planName").value || "unnamed plan",
        workloadId: $("planWorkload").value,
        requestedSeconds: Math.max(1, parseInt($("planSeconds").value, 10) || 60),
        nodeCount: Math.max(1, parseInt($("planNodes").value, 10) || 1),
        artifacts: [{ name: "image", digest: $("planDigest").value || "sha256:unset" }],
        grants: { network: grants ? grants.split(",").map((s) => s.trim()) : [], services: [], secrets: [] },
        anchorAddress: ui.anchor,
      });
      ui.selectedPlan = p.id;
      toast("Plan signed", `${p.id} · digest ${p.digest.slice(0, 12)}`, "up");
      render();
    });
    ["planSeconds", "planNodes", "planGrants"].forEach((id) =>
      $(id).addEventListener("input", renderPlanPreview));

    // balancer
    $("balancerToggle").addEventListener("change", (e) => {
      pricing.balancerEnabled = e.target.checked;
      $("balancerLabel").textContent = e.target.checked ? "Balancer ON" : "Balancer OFF";
      toast(e.target.checked ? "Balancer on" : "Balancer off",
        e.target.checked ? "two-sided pricing restored — watch the Gini fall"
                         : "scarcity-only pricing — watch the Gini climb", e.target.checked ? "up" : "down");
    });

    // chrome
    $("themeBtn").addEventListener("click", () => {
      const cur = document.documentElement.getAttribute("data-theme");
      const next = cur === "light" ? "" : "light";
      if (next) document.documentElement.setAttribute("data-theme", next);
      else document.documentElement.removeAttribute("data-theme");
      try { localStorage.setItem("holotrade_theme", next); } catch (e) { /* private mode */ }
      render(); renderTapeStrip();
    });
    try {
      if (localStorage.getItem("holotrade_theme") === "light") document.documentElement.setAttribute("data-theme", "light");
    } catch (e) { /* private mode */ }

    $("pauseBtn").addEventListener("click", () => {
      ui.paused = !ui.paused;
      $("pauseBtn").textContent = ui.paused ? "Resume" : "Pause";
      $("pauseBtn").classList.toggle("active", ui.paused);
    });
    const speeds = [1, 2, 5, 15];
    $("speedBtn").addEventListener("click", () => {
      ui.speed = speeds[(speeds.indexOf(ui.speed) + 1) % speeds.length];
      $("speedBtn").textContent = ui.speed + "×";
    });

    $("drawerClose").addEventListener("click", closeDrawer);
    $("drawerBack").addEventListener("click", closeDrawer);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeDrawer(); });

    $("menuBtn").addEventListener("click", () => $("sidebar").classList.toggle("open"));
    const mq = window.matchMedia("(max-width: 900px)");
    const applyMq = () => $("menuBtn").classList.toggle("hidden", !mq.matches);
    applyMq(); mq.addEventListener("change", applyMq);
    window.addEventListener("resize", () => { if (RENDERERS[ui.view]) render(); });

    // warm the simulation so the first frame is not a cold fleet
    for (let i = 0; i < 220; i++) {
      energy.tick(30);
      pricing.applyDemandResponse(1 / 60, { workloadId: ui.workload });
      fleet.tick(1 / 60);
      if (i % 4 === 0) market.ambientFlow("spot");
    }
    market.seedBooks();

    renderTapeStrip();
    switchView("exchange");
    setInterval(step, 1000);

    $("boot").classList.add("hidden");
    setTimeout(() => $("boot").remove(), 400);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
