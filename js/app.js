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
    depthZoom: "liquid",
    depthHover: null,
    frontierHover: null,
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
    const rect = cv.getBoundingClientRect();
    const parentWidth = cv.parentElement ? cv.parentElement.getBoundingClientRect().width : 0;
    const w = Math.max(1, Math.round(rect.width || cv.clientWidth || parentWidth || 600));
    // canvas.height reflects back into the HTML attribute. Cache the authored
    // logical height before assigning a DPR-scaled backing-store height, or a
    // 2x screen would double the chart on every redraw.
    if (!cv.dataset.chartHeight) {
      cv.dataset.chartHeight = String(Math.max(96, parseInt(cv.getAttribute("height"), 10) || 180));
    }
    const h = Math.max(96, parseInt(cv.dataset.chartHeight, 10) || 180);
    // Capping DPR avoids allocating multi-megapixel backing stores on a 4x
    // display while retaining crisp type and one-device-pixel rules.
    const dpr = Math.max(1, Math.min(3, window.devicePixelRatio || 1));
    const pixelW = Math.max(1, Math.round(w * dpr));
    const pixelH = Math.max(1, Math.round(h * dpr));
    if (cv.width !== pixelW) cv.width = pixelW;
    if (cv.height !== pixelH) cv.height = pixelH;
    cv.style.height = h + "px";
    cv._holotradeSize = { w, h, dpr };
    const ctx = cv.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    return { ctx, w, h };
  }

  function canvasPoint(cv, e) {
    const rect = cv.getBoundingClientRect();
    const logical = cv._holotradeSize || { w: rect.width, h: rect.height };
    return {
      x: (e.clientX - rect.left) * (logical.w / Math.max(1, rect.width)),
      y: (e.clientY - rect.top) * (logical.h / Math.max(1, rect.height)),
    };
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

  function plotClip(ctx, w, h, pad) {
    ctx.beginPath();
    ctx.rect(pad.l, pad.t, Math.max(1, w - pad.l - pad.r), Math.max(1, h - pad.t - pad.b));
    ctx.clip();
  }

  function chartEmpty(ctx, w, h, message = "No data in this window") {
    ctx.fillStyle = css("--text-2", "#61708c");
    ctx.font = "11px " + css("--mono", "monospace");
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(message, w / 2, h / 2);
    ctx.textBaseline = "alphabetic";
  }

  function chartDomain(values, opts = {}) {
    const data = values.map(Number).filter(Number.isFinite);
    const hasMin = Number.isFinite(Number(opts.min));
    const hasMax = Number.isFinite(Number(opts.max));
    let lo = hasMin ? Number(opts.min) : (data.length ? Math.min(...data) : 0);
    let hi = hasMax ? Number(opts.max) : (data.length ? Math.max(...data) : 1);
    if (opts.includeZero) { lo = Math.min(0, lo); hi = Math.max(0, hi); }
    if (!(hi > lo)) {
      const centre = Number.isFinite(lo) ? lo : 0;
      const span = Math.max(Math.abs(centre) * 0.12, Number(opts.minSpan) || 1);
      if (!hasMin) lo = centre - span / 2;
      if (!hasMax) hi = centre + span / 2;
      if (!(hi > lo)) { lo = centre - span / 2; hi = centre + span / 2; }
    }
    const padding = Math.max(0, Number.isFinite(opts.padding) ? opts.padding : 0.08);
    const span = hi - lo;
    if (!hasMin) lo -= span * padding;
    if (!hasMax) hi += span * padding;
    return [lo, hi];
  }

  function chartPad(w, base = {}) {
    return {
      l: w < 390 ? (base.narrowL || 39) : (base.l || 46),
      r: w < 390 ? (base.narrowR || 8) : (base.r || 10),
      t: base.t || 10,
      b: base.b || 22,
    };
  }

  function drawLines(cv, series, opts = {}) {
    const { ctx, w, h } = prepCanvas(cv);
    const pad = chartPad(w, { l: 46, narrowL: 40, r: 10, t: 10, b: opts.xCaption ? 30 : 22 });
    const all = series.flatMap((s) => Array.isArray(s.data) ? s.data : []).map(Number).filter(Number.isFinite);
    if (!all.length) { chartEmpty(ctx, w, h); return; }
    const [min, max] = chartDomain(all, opts);
    const X = (i, n) => pad.l + (n <= 1 ? 0.5 : i / (n - 1)) * (w - pad.l - pad.r);
    const Y = (v) => h - pad.b - ((v - min) / (max - min)) * (h - pad.t - pad.b);

    // Threshold bands sit behind both the grid and the data.
    if (opts.bands) {
      ctx.save();
      plotClip(ctx, w, h, pad);
      for (const b of opts.bands) {
        const y1 = Y(Math.max(b.lo, b.hi)), y2 = Y(Math.min(b.lo, b.hi));
        ctx.fillStyle = b.color;
        ctx.fillRect(pad.l, y1, w - pad.l - pad.r, y2 - y1);
      }
      ctx.restore();
    }

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

    ctx.save();
    plotClip(ctx, w, h, pad);
    for (const s of series) {
      const data = Array.isArray(s.data) ? s.data : [];
      const segments = [];
      let segment = [];
      data.forEach((raw, i) => {
        const v = Number(raw);
        if (Number.isFinite(v)) segment.push({ i, v });
        else if (segment.length) { segments.push(segment); segment = []; }
      });
      if (segment.length) segments.push(segment);
      for (const part of segments) {
        const trace = () => {
          ctx.beginPath();
          part.forEach((p, i) => {
            const x = X(p.i, data.length), y = Y(p.v);
            i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
          });
        };
        if (s.fill && part.length > 1) {
          trace();
          ctx.lineTo(X(part[part.length - 1].i, data.length), h - pad.b);
          ctx.lineTo(X(part[0].i, data.length), h - pad.b);
          ctx.closePath();
          ctx.fillStyle = s.fill;
          ctx.fill();
        }
        ctx.strokeStyle = s.color;
        ctx.fillStyle = s.color;
        ctx.lineWidth = s.width || 1.6;
        ctx.setLineDash(s.dash || []);
        if (part.length === 1) {
          ctx.beginPath(); ctx.arc(X(part[0].i, data.length), Y(part[0].v), 2.4, 0, Math.PI * 2); ctx.fill();
        } else {
          trace(); ctx.stroke();
        }
      }
      ctx.setLineDash([]);
    }
    ctx.restore();
    if (opts.xCaption) {
      ctx.fillStyle = css("--text-2", "#61708c");
      ctx.font = "10px " + css("--mono", "monospace");
      ctx.textAlign = "center";
      ctx.fillText(opts.xCaption, (pad.l + w - pad.r) / 2, h - 6);
    }
  }

  function drawBars(cv, bars, opts = {}) {
    const { ctx, w, h } = prepCanvas(cv);
    const clean = (bars || []).map((b) => ({ ...b, value: Number(b.value) })).filter((b) => Number.isFinite(b.value));
    if (!clean.length) { chartEmpty(ctx, w, h); return; }
    const pad = chartPad(w, { l: 42, narrowL: 36, r: 10, t: 14, b: 27 });
    const [min, max] = chartDomain(clean.map((b) => b.value), {
      min: Number.isFinite(Number(opts.min)) ? Number(opts.min) : Math.min(0, ...clean.map((b) => b.value)),
      max: opts.max,
      minSpan: 1,
      padding: 0.06,
    });
    const Y = (v) => h - pad.b - ((v - min) / (max - min)) * (h - pad.t - pad.b);
    const zeroY = Y(Math.max(min, Math.min(max, 0)));
    const bw = (w - pad.l - pad.r) / clean.length;

    ctx.font = "9px " + css("--mono", "monospace");
    ctx.fillStyle = css("--text-2", "#61708c");
    ctx.strokeStyle = css("--border", "#1c2740");
    ctx.textAlign = "right";
    for (let i = 0; i <= 3; i++) {
      const v = min + (i / 3) * (max - min), y = Y(v);
      ctx.globalAlpha = 0.45;
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillText(opts.fmtV ? opts.fmtV(v) : fmt.big(v), pad.l - 5, y + 3);
    }
    axes(ctx, w, h, pad);

    ctx.save();
    plotClip(ctx, w, h, pad);
    clean.forEach((b, i) => {
      const y = Y(b.value);
      const top = Math.min(y, zeroY), bh = Math.abs(zeroY - y);
      ctx.fillStyle = b.color || css("--accent", "#38bdf8");
      ctx.fillRect(pad.l + i * bw + bw * 0.14, top, Math.max(1, bw * 0.72), Math.max(b.value === 0 ? 1 : 0, bh));
    });
    ctx.restore();

    ctx.font = "9.5px " + css("--mono", "monospace");
    clean.forEach((b, i) => {
      const y = Y(b.value);
      ctx.fillStyle = css("--text-2", "#61708c");
      ctx.textAlign = "center";
      const labelEvery = opts.labelEvery || Math.max(1, Math.ceil(34 / Math.max(1, bw)));
      if (i % labelEvery === 0) ctx.fillText(String(b.label), pad.l + i * bw + bw / 2, h - pad.b + 13);
      if (b.value !== 0 && bw >= 24) {
        ctx.fillStyle = css("--text-1", "#93a3bd");
        ctx.fillText(opts.fmtV ? opts.fmtV(b.value) : fmt.big(b.value), pad.l + i * bw + bw / 2,
          b.value >= 0 ? Math.max(pad.t + 9, y - 4) : Math.min(h - pad.b - 4, y + 11));
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
    $("instrumentBlurb").textContent = inst ? inst.blurb.replace(/\blive\b/gi, "current simulated") : "";
    $("instrumentNote").textContent = inst ? inst.tenor : "";

    // depth zoom
    const zseg = $("depthZoomSeg");
    zseg.querySelectorAll("button").forEach((b) => {
      b.classList.toggle("active", b.dataset.zoom === ui.depthZoom);
      if (!b.dataset.bound) {
        b.dataset.bound = "1";
        b.addEventListener("click", () => {
          ui.depthZoom = b.dataset.zoom;
          zseg.querySelectorAll("button").forEach((x) =>
            x.classList.toggle("active", x.dataset.zoom === ui.depthZoom));
          renderDepth();
        });
      }
    });

    renderBook();
    renderDepth();
    renderFrontier();
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

  // --------------------------------------------------------------------
  // Depth
  //
  // The naive version of this chart plots the whole book on one linear
  // axis, and on a heterogeneous fleet that is useless: the ask side
  // spans forty-to-one in price because a CPU node and an accelerator
  // are both resting on it, so the bid side collapses into a sliver at
  // the left edge and the shape carries no information.
  //
  // Three fixes, all of which are about telling the truth rather than
  // decorating:
  //
  //   1. ZOOM TO WHERE THE LIQUIDITY IS. The default window covers the
  //      price range holding the first slice of resting ask size.
  //      Everything past it is a long tail of specialist hardware no
  //      marginal buyer is choosing between.
  //   2. DRAW IT AS A STEP FUNCTION. A book is discrete. A smooth curve
  //      implies liquidity at prices where none rests.
  //   3. SHOW THE ORDER ABOUT TO BE SENT. The shaded band is where the
  //      ticket quantity would fill right now; the readout gives the
  //      average, the worst price touched, and slippage in basis points
  //      against the best offer.
  // --------------------------------------------------------------------

  function depthWindow(d, mode) {
    const asks = d.asks.filter((r) => Number.isFinite(r.price) && Number.isFinite(r.cum));
    const bids = d.bids.filter((r) => Number.isFinite(r.price) && Number.isFinite(r.cum));
    const allAsk = asks.length ? Math.max(...asks.map((r) => r.cum)) : 0;
    const bestAsk = asks.length ? asks[0].price : (bids.length ? bids[0].price : 0);
    const bestBid = bids.length ? bids[0].price : bestAsk;
    const expanded = (lo, hi) => {
      const scale = Math.max(Math.abs(lo), Math.abs(hi), 1);
      const [a, b] = chartDomain([lo, hi], { minSpan: scale * 0.02, padding: 0.02 });
      return { lo: a, hi: b };
    };
    if (mode === "full" || !allAsk) {
      const prices = [...bids.map((x) => x.price), ...asks.map((x) => x.price)];
      if (!prices.length) return { lo: 0, hi: 1 };
      return expanded(Math.min(...prices), Math.max(...prices));
    }
    const frac = mode === "half" ? 0.5 : 0.28;
    const target = allAsk * frac;
    let hi = bestAsk;
    for (const a of asks) { hi = a.price; if (a.cum >= target) break; }
    // never let the window collapse so far that the spread is invisible
    const mid = (bestBid + bestAsk) / 2;
    hi = Math.max(hi, mid * 1.12);
    const lo = Math.min(bestBid, mid * 0.9);
    return expanded(lo, hi);
  }

  const depthPad = (w) => chartPad(w, { l: 48, narrowL: 40, r: 12, narrowR: 8, t: 18, b: 26 });

  function renderDepth() {
    const d = market.depth(ui.instrument, 120);
    const cv = $("depthCanvas");
    const { ctx, w, h } = prepCanvas(cv);
    if (!d.asks.length && !d.bids.length) {
      chartEmpty(ctx, w, h, "No resting bids or offers");
      $("depthReadout").innerHTML = '<div class="dr hint">The book is empty for this instrument.</div>';
      return;
    }

    const pad = depthPad(w);
    cv._holotradeDepthPad = pad;
    const win = depthWindow(d, ui.depthZoom);
    const inWin = (r) => Number.isFinite(r.price) && Number.isFinite(r.cum) && r.price >= win.lo && r.price <= win.hi;
    const bids = d.bids.filter(inWin);
    const asks = d.asks.filter(inWin);
    const maxCum = Math.max(1, ...bids.map((r) => r.cum), ...asks.map((r) => r.cum));

    const X = (p) => pad.l + ((p - win.lo) / Math.max(1e-9, win.hi - win.lo)) * (w - pad.l - pad.r);
    const Y = (c) => h - pad.b - (c / maxCum) * (h - pad.t - pad.b);
    const clampX = (x) => Math.max(pad.l, Math.min(w - pad.r, x));

    // horizontal gridlines, labelled in cumulative size
    ctx.font = "10px " + css("--mono", "monospace");
    ctx.strokeStyle = css("--border", "#1c2740");
    ctx.fillStyle = css("--text-2", "#61708c");
    ctx.textAlign = "right";
    for (let i = 1; i <= 4; i++) {
      const c = (i / 4) * maxCum, y = Y(c);
      ctx.globalAlpha = 0.45;
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillText(fmt.int(c), pad.l - 6, y + 3);
    }

    // --- the order about to be sent, shaded on the ask side ----------
    const preview = market.previewBuy(ui.instrument, Math.max(1, parseInt($("tkQty").value, 10) || 1)) || {};
    const fill = {
      filled: Number(preview.filled) || 0,
      qty: Number(preview.requested) || Math.max(1, parseInt($("tkQty").value, 10) || 1),
      cost: Number(preview.cost) || 0,
      worst: Number(preview.worst),
      touched: Number(preview.levelsTouched) || 0,
      avg: Number(preview.average),
      best: Number(preview.best),
      slipBps: Number(preview.slippageBps),
      complete: Boolean(preview.complete),
    };
    if (fill.filled > 0 && Number.isFinite(fill.best) && Number.isFinite(fill.worst) && fill.worst >= win.lo) {
      const x0 = clampX(X(fill.best)), x1 = clampX(X(Math.min(fill.worst, win.hi)));
      ctx.fillStyle = "rgba(56,189,248,0.13)";
      ctx.fillRect(x0, pad.t, Math.max(1.5, x1 - x0), h - pad.t - pad.b);
      ctx.strokeStyle = css("--accent", "#38bdf8");
      ctx.setLineDash([3, 3]); ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(clampX(X(fill.avg)), pad.t);
      ctx.lineTo(clampX(X(fill.avg)), h - pad.b);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // --- step curves --------------------------------------------------
    const staircase = (rows, colour, fillColour, ascending) => {
      if (!rows.length) return;
      const pts = ascending ? rows : rows.slice().reverse();
      const trace = () => {
        ctx.beginPath();
        ctx.moveTo(clampX(X(pts[0].price)), h - pad.b);
        let prevY = h - pad.b;
        for (const r of pts) {
          const x = clampX(X(r.price)), y = Y(r.cum);
          ctx.lineTo(x, prevY);   // horizontal run at the previous level
          ctx.lineTo(x, y);       // vertical riser at this price
          prevY = y;
        }
      };
      const endX = clampX(X(pts[pts.length - 1].price));
      ctx.save();
      plotClip(ctx, w, h, pad);
      trace();
      ctx.lineTo(endX, h - pad.b);
      ctx.closePath(); ctx.fillStyle = fillColour; ctx.fill();
      trace();
      ctx.strokeStyle = colour; ctx.lineWidth = 1.7; ctx.stroke();
      ctx.restore();
    };
    // bids accumulate downward in price, so walk them right-to-left
    staircase(bids, css("--up", "#2dd4a7"), "rgba(45,212,167,0.14)", false);
    staircase(asks, css("--down", "#f4526b"), "rgba(244,82,107,0.14)", true);

    // --- mid marker ---------------------------------------------------
    const sp = market.spread(ui.instrument);
    if (sp) {
      const mid = (sp.bestBid + sp.bestAsk) / 2;
      if (mid >= win.lo && mid <= win.hi) {
        ctx.strokeStyle = css("--text-2", "#61708c");
        ctx.setLineDash([2, 3]); ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(X(mid), pad.t); ctx.lineTo(X(mid), h - pad.b); ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = css("--text-2", "#61708c");
        ctx.textAlign = "center";
        ctx.fillText("mid " + fmt.usd(mid, 2), X(mid), pad.t - 5);
      }
    }

    axes(ctx, w, h, pad);

    ctx.fillStyle = css("--text-2", "#61708c");
    ctx.textAlign = "center";
    const xSteps = w < 430 ? 2 : 4;
    for (let i = 0; i <= xSteps; i++) {
      const p = win.lo + (i / xSteps) * (win.hi - win.lo);
      ctx.fillText("$" + p.toFixed(p < 20 ? 1 : 0), X(p), h - pad.b + 14);
    }

    // --- crosshair -------------------------------------------------------
    if (ui.depthHover != null && ui.depthHover >= win.lo && ui.depthHover <= win.hi) {
      ctx.strokeStyle = css("--accent", "#38bdf8");
      ctx.lineWidth = 0.8; ctx.globalAlpha = 0.6;
      ctx.beginPath();
      ctx.moveTo(X(ui.depthHover), pad.t);
      ctx.lineTo(X(ui.depthHover), h - pad.b);
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    if (!cv.dataset.bound) {
      cv.dataset.bound = "1";
      cv.addEventListener("pointermove", (e) => {
        const point = canvasPoint(cv, e);
        const activePad = cv._holotradeDepthPad || depthPad((cv._holotradeSize || {}).w || cv.clientWidth);
        const logicalW = (cv._holotradeSize || {}).w || cv.clientWidth;
        const wn = depthWindow(market.depth(ui.instrument, 120), ui.depthZoom);
        const frac = (point.x - activePad.l) / Math.max(1, logicalW - activePad.l - activePad.r);
        ui.depthHover = wn.lo + Math.max(0, Math.min(1, frac)) * (wn.hi - wn.lo);
        renderDepth();
      });
      cv.addEventListener("pointerleave", () => { ui.depthHover = null; renderDepth(); });
    }

    renderDepthReadout(fill, d, win);
  }

  function renderDepthReadout(fill, d, win) {
    const sp = market.spread(ui.instrument);
    const slipBps = Number.isFinite(fill.slipBps) ? fill.slipBps : null;
    let hoverCells = "";
    if (ui.depthHover != null) {
      const hv = ui.depthHover;
      // cumulative size resting at or better than the hovered price
      const askCum = d.asks.filter((a) => a.price <= hv).reduce((m, a) => Math.max(m, a.cum), 0);
      const bidCum = d.bids.filter((b) => b.price >= hv).reduce((m, b) => Math.max(m, b.cum), 0);
      hoverCells = '<div class="dr"><span class="dr-k">At ' + fmt.usd(hv, 2) + '</span>' +
        '<span class="dr-v up">' + fmt.int(bidCum) + ' bid</span> <span class="muted">/</span> ' +
        '<span class="dr-v down">' + fmt.int(askCum) + ' ask</span></div>';
    }

    $("depthReadout").innerHTML = hoverCells +
      '<div class="dr"><span class="dr-k">Your ' + fill.qty + ' fills</span>' +
        '<span class="dr-v ' + (fill.complete ? "" : "down") + '">' + fill.filled + '/' + fill.qty + '</span></div>' +
      '<div class="dr"><span class="dr-k">Average</span><span class="dr-v">' + fmt.usd(fill.avg, 3) + '</span></div>' +
      '<div class="dr"><span class="dr-k">Worst touched</span><span class="dr-v">' + fmt.usd(fill.worst, 3) + '</span></div>' +
      '<div class="dr"><span class="dr-k">Slippage</span><span class="dr-v ' +
        (slipBps == null ? "muted" : slipBps > 200 ? "down" : slipBps > 50 ? "" : "up") + '">' +
        (slipBps == null ? "—" : slipBps.toFixed(0) + " bps") + '</span></div>' +
      '<div class="dr"><span class="dr-k">Nodes touched</span><span class="dr-v">' + fill.touched + '</span></div>' +
      '<div class="dr"><span class="dr-k">Spread</span><span class="dr-v">' + (sp ? sp.bps.toFixed(0) + " bps" : "—") + '</span></div>' +
      '<div class="dr hint">Shaded band is where your order lands right now; the dashed line is its average price. Window ' +
        fmt.usd(win.lo, 2) + '–' + fmt.usd(win.hi, 2) + '.</div>';
  }

  // --------------------------------------------------------------------
  // Value frontier
  //
  // The honest answer to "why does the depth chart span forty-to-one".
  // It does because a node-hour is not a comparable unit across hardware
  // classes: a $4 CPU node and a $60 accelerator are not competing
  // offers, they are different products, and putting them on one price
  // axis was always going to look strange.
  //
  // Delivered throughput per dollar IS comparable. Plot every listed
  // node as (effective TFLOPs, $/hour) and the Pareto frontier -- the
  // set nothing else beats on BOTH axes at once -- is the real menu.
  // Everything above it is dominated: some other listed node is cheaper
  // AND faster, and an exchange that knows this should say so rather
  // than quietly let someone buy the worse one.
  // --------------------------------------------------------------------

  function renderFrontier() {
    const cv = $("frontierCanvas");
    const { ctx, w, h } = prepCanvas(cv);
    const pts = [];
    for (const node of fleet.listedNodes()) {
      const q = pricing.quotes.get(node.id);
      const price = Number(q && q.price);
      const tf = Number(node.effectiveTflops);
      if (!q || !q.serviceable || !(price > 0) || !(tf > 0)) continue;
      pts.push({ node, price, tflops: tf, kind: node.hardware.kind });
    }
    if (!pts.length) {
      chartEmpty(ctx, w, h, "No serviceable positive-price offers");
      $("frontierLegend").innerHTML = '<span class="muted">No comparable offers in this workload.</span>';
      cv._holotradeFrontierHits = [];
      return;
    }

    const pad = chartPad(w, { l: 54, narrowL: 44, r: 14, narrowR: 8, t: 14, b: 31 });
    // log axes: capacity spans four orders across the catalogue, so a
    // linear axis would stack every CPU node into one pixel column
    const lx = (v) => Math.log10(v);
    const ly = (v) => Math.log10(v);
    const xs = pts.map((p) => lx(p.tflops)), ys = pts.map((p) => ly(p.price));
    const [x0, x1] = chartDomain(xs, { minSpan: 0.5, padding: 0.08 });
    const [y0, y1] = chartDomain(ys, { minSpan: 0.35, padding: 0.08 });
    const X = (v) => pad.l + ((lx(v) - x0) / (x1 - x0)) * (w - pad.l - pad.r);
    const Y = (v) => h - pad.b - ((ly(v) - y0) / (y1 - y0)) * (h - pad.t - pad.b);
    const axisValue = (v) => {
      if (v >= 1000) return fmt.big(v);
      if (v >= 10) return v.toFixed(0);
      if (v >= 1) return v.toFixed(1).replace(/\.0$/, "");
      return v.toPrecision(2);
    };

    ctx.font = "10px " + css("--mono", "monospace");
    ctx.strokeStyle = css("--border", "#1c2740");
    ctx.fillStyle = css("--text-2", "#61708c");
    const ySteps = 4;
    for (let i = 0; i <= ySteps; i++) {
      const logV = y0 + (i / ySteps) * (y1 - y0);
      const value = Math.pow(10, logV), y = Y(value);
      ctx.globalAlpha = 0.45;
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.textAlign = "right";
      ctx.fillText("$" + axisValue(value), pad.l - 6, y + 3);
    }
    const xSteps = w < 430 ? 2 : 4;
    for (let i = 0; i <= xSteps; i++) {
      const logV = x0 + (i / xSteps) * (x1 - x0);
      const value = Math.pow(10, logV), x = X(value);
      ctx.globalAlpha = 0.3;
      ctx.beginPath(); ctx.moveTo(x, pad.t); ctx.lineTo(x, h - pad.b); ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.textAlign = "center";
      ctx.fillText(axisValue(value) + " TF", x, h - pad.b + 14);
    }
    axes(ctx, w, h, pad);

    // dominated points, dimmed
    const front = HolotradeMarket.paretoFrontier(pts).slice().sort((a, b) => a.tflops - b.tflops);
    const frontSet = new Set(front.map((p) => p.node.id));
    ctx.save();
    plotClip(ctx, w, h, pad);
    ctx.globalAlpha = 0.34;
    for (const p of pts) {
      if (frontSet.has(p.node.id)) continue;
      ctx.fillStyle = HW_COLOR[p.kind] || "#888";
      ctx.beginPath(); ctx.arc(X(p.tflops), Y(p.price), 2.4, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;

    // the frontier itself
    ctx.strokeStyle = css("--accent", "#38bdf8");
    ctx.lineWidth = 1.6; ctx.setLineDash([]);
    ctx.beginPath();
    front.forEach((p, i) => {
      const x = X(p.tflops), y = Y(p.price);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();
    for (const p of front) {
      ctx.fillStyle = HW_COLOR[p.kind] || "#888";
      ctx.beginPath(); ctx.arc(X(p.tflops), Y(p.price), 4, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = css("--accent", "#38bdf8"); ctx.lineWidth = 1.2; ctx.stroke();
    }

    // ring anything already held
    const held = new Set(market.positions.map((x) => x.nodeId));
    ctx.strokeStyle = css("--amber", "#f5a524"); ctx.lineWidth = 1.6;
    for (const p of pts) {
      if (!held.has(p.node.id)) continue;
      ctx.beginPath(); ctx.arc(X(p.tflops), Y(p.price), 6, 0, Math.PI * 2); ctx.stroke();
    }
    const hovered = pts.find((p) => p.node.id === ui.frontierHover);
    if (hovered) {
      ctx.strokeStyle = css("--text", "#dfe7f5");
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(X(hovered.tflops), Y(hovered.price), 7, 0, Math.PI * 2); ctx.stroke();
    }
    ctx.restore();

    if (hovered) {
      const hx = X(hovered.tflops), hy = Y(hovered.price);
      const tw = Math.min(210, w - 16), th = 48;
      const tx = Math.max(8, Math.min(w - tw - 8, hx + (hx > w * 0.62 ? -tw - 10 : 10)));
      const ty = Math.max(8, Math.min(h - th - 8, hy - th / 2));
      ctx.fillStyle = css("--bg-2", "#121826");
      ctx.strokeStyle = css("--border-hi", "#2e3d5e");
      ctx.lineWidth = 1;
      ctx.fillRect(tx, ty, tw, th); ctx.strokeRect(tx + 0.5, ty + 0.5, tw - 1, th - 1);
      ctx.font = "600 10px " + css("--mono", "monospace");
      ctx.fillStyle = css("--text", "#dfe7f5"); ctx.textAlign = "left";
      ctx.fillText(hovered.node.hardware.class + " · " + hovered.node.id.slice(-8), tx + 8, ty + 18);
      ctx.font = "10px " + css("--mono", "monospace");
      ctx.fillStyle = css("--text-1", "#93a3bd");
      ctx.fillText(fmt.usd(hovered.price, 2) + "/hr · " + fmt.big(hovered.tflops) + " TF", tx + 8, ty + 35);
    }

    const dominated = pts.length - front.length;
    $("frontierLegend").innerHTML =
      Object.entries(HW_COLOR).filter(([k]) => k !== "composite")
        .map(([k, v]) => '<span><i style="background:' + v + '"></i>' + k + '</span>').join("") +
      '<span class="legend-summary muted">' + front.length + ' on the frontier · ' +
      dominated + ' dominated' +
      (held.size ? ' · <span style="color:var(--amber)">◯ yours</span>' : '') + '</span>';

    // Refresh hit targets on every render. The listener is installed only
    // once, but must not close over the first workload/viewport it saw.
    cv._holotradeFrontierHits = pts.map((p) => ({
      nodeId: p.node.id,
      x: X(p.tflops),
      y: Y(p.price),
    }));
    if (!cv.dataset.bound) {
      cv.dataset.bound = "1";
      cv.addEventListener("pointermove", (e) => {
        const point = canvasPoint(cv, e);
        let bestNodeId = null, bestD = 14;
        for (const hit of cv._holotradeFrontierHits || []) {
          const dd = Math.hypot(hit.x - point.x, hit.y - point.y);
          if (dd < bestD) { bestD = dd; bestNodeId = hit.nodeId; }
        }
        if (bestNodeId !== ui.frontierHover) {
          ui.frontierHover = bestNodeId;
          cv.style.cursor = bestNodeId ? "pointer" : "crosshair";
          renderFrontier();
        }
      });
      cv.addEventListener("pointerleave", () => {
        if (ui.frontierHover != null) { ui.frontierHover = null; renderFrontier(); }
        cv.style.cursor = "crosshair";
      });
      cv.addEventListener("click", (e) => {
        const point = canvasPoint(cv, e);
        let bestNodeId = null, bestD = 18;
        for (const hit of cv._holotradeFrontierHits || []) {
          const dd = Math.hypot(hit.x - point.x, hit.y - point.y);
          if (dd < bestD) { bestD = dd; bestNodeId = hit.nodeId; }
        }
        if (bestNodeId) openNode(bestNodeId);
      });
    }
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
      ["E", "Energy", M.E, "seeded simulated $/MWh at this site, PUE-adjusted"],
      ["G", "Modeled specialization", M.G, "seeded class history and fitness inputs"],
      ["D", "Demand / wear", M.D, "premium if hot, discount if cold"],
      ["H", "Health", M.H, "derate × reliability × error drift"],
      ["Q", "Declared capability", M.Q, "illustrative 9^t dial; 1× classical baseline"],
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
        <span class="tag ${card.marketBreadthBand === "broad" ? "up" : card.marketBreadthBand === "site-bound" ? "down" : "amber"}">${card.marketBreadthBand}</span>
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
        <span class="card-note">policy-estimated mobility · not market liquidity</span></div>
        <div class="card-body"><dl class="kv">
          <dt>UOR address</dt><dd>${fmt.esc(card.uor)}</dd>
          <dt>Substrate point</dt><dd>${card.point} · 𝔽₃⁴ = ${card.vector}</dd>
          <dt>Canonical cell</dt><dd>${fmt.int(card.cell)} of 51,840</dd>
          <dt>Mobility policies</dt><dd>${card.policies.length ? card.policies.join(", ") : "none"}</dd>
          <dt>Policy mobility score</dt><dd>${fmt.num(card.policyMobilityScore, 3)}</dd>
          <dt>Estimated eligible regions</dt><dd>${fmt.int(card.marketBreadth)} / 40 reference regions</dd>
          <dt>Market-breadth band</dt><dd>${fmt.esc(card.marketBreadthBand)}</dd>
          <dt>Movement records</dt><dd>${fmt.int(card.moves)}</dd>
          <dt>History structure</dt><dd class="${card.provenance.structurallyValid ? "up" : "down"}">${card.provenance.structurallyValid ? "valid · not authenticated" : card.provenance.anomalies.length + " anomalies"}</dd>
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

  // --------------------------------------------------------------------
  // Optimal reservation shapes
  //
  // The spectral bounds in the scheduler say how dense a reservation of a
  // given size COULD be. This panel shows the sets that actually attain
  // them -- the classification in analysis/w33_shape_catalogue.js -- and
  // whether each is still placeable given how much of the fabric is busy.
  //
  // The placement is a real transport: an automorphism carries the
  // catalogue witness onto free nodes, preserving induced edges and
  // boundary exactly. It is not a re-optimisation and not an
  // approximation.
  // --------------------------------------------------------------------
  function renderShapes() {
    const SH = window.HolotradeShapes;
    const body = $("shapeMenuBody");
    if (!SH || !body) return;

    const busy = Math.max(0, Math.min(34, parseInt($("shapeBusy").value, 10) || 0));

    // Which points count as busy. Taken from the live simulation: each
    // point of the cell is scored by the mean utilisation of the fleet
    // nodes sitting on it, and the busiest are blocked first. A seeded
    // tiebreak keeps the order stable between renders so dragging the
    // slider reveals a monotone sequence rather than reshuffling.
    //
    // The earlier version topped up with a contiguous index prefix,
    // which is an unrealistic occupancy pattern. It happens not to
    // change the answers here -- a spread block of the same size leaves
    // just as few shapes placeable -- but a panel should not depend on
    // that coincidence.
    const load = new Array(SH.N).fill(0);
    const seen = new Array(SH.N).fill(0);
    for (const n of fleet.listedNodes()) {
      load[n.cellPoint] += n.utilisation;
      seen[n.cellPoint] += 1;
    }
    const tiebreak = Substrate.rng("shape-panel");
    const order = [...Array(SH.N).keys()]
      .map((v) => ({ v, score: seen[v] ? load[v] / seen[v] : 0, jitter: tiebreak() }))
      .sort((a, b) => (b.score - a.score) || (a.jitter - b.jitter))
      .map((x) => x.v);
    const blocked = new Set(order.slice(0, busy));

    $("shapeBusyLabel").textContent =
      `${blocked.size} busy · ${SH.N - blocked.size} free`;

    let menu;
    try { menu = SH.shapeMenu({ unavailable: blocked }); }
    catch (err) { console.error("[shapes]", err); return; }

    body.innerHTML = menu.densest.map((r) => {
      const place = r.placement
        ? `<span class="mono" style="font-size:10.5px">${r.placement.slice(0, 8).join(" ")}${r.placement.length > 8 ? " …" : ""}</span>`
        : `<span class="muted" style="font-size:10.5px">${fmt.esc(r.reason || "")}</span>`;
      return `<tr>
        <td><span class="tag accent">${r.m}</span></td>
        <td class="num">${r.maxInducedEdges}</td>
        <td class="num">${r.minBoundary}</td>
        <td class="num muted">${r.orbitSize == null ? "—" : fmt.int(r.orbitSize)}</td>
        <td><span class="tag ${r.placeable ? "up" : "down"}">${r.placeable ? "yes" : "no"}</span></td>
        <td class="wrap">${place}</td>
      </tr>`;
    }).join("");

    const aa = menu.antiAffinity;
    $("antiAffinityNote").innerHTML =
      `The largest set of nodes sharing <b>no link at all</b> has size <b>${aa.size}</b>. ` +
      `The Hoffman ratio bound suggests ${aa.ratioBound}, and a set attaining it would be an ovoid of this ` +
      `quadrangle &mdash; exhaustive search shows none exists. So <b>a scheduler cannot promise an eighth ` +
      `failure-independent replica</b>, at any price, on any fabric of this shape.` +
      (aa.witness ? `<br><span class="mono" style="font-size:10.5px">witness ${aa.witness.join(" ")}</span>` : "");

    const sp = menu.spread;
    $("spreadNote").innerHTML = sp.placeable
      ? `Every node outside the set sees exactly the same number of its members. This exists at <b>m = 20 only</b> ` +
        `&mdash; every other admissible size is impossible, not merely unfound.` +
        `<br><span class="mono" style="font-size:10.5px">${sp.placement.join(" ")}</span>`
      : `Exists at <b>m = 20 only</b>. Not placeable right now: <span class="muted">${fmt.esc(sp.reason || "")}</span>`;

    // How many of the 40 lines survive entirely inside the free region.
    // This is the sharpest operational reading of the panel: once it
    // hits zero, even the smallest optimal shape is gone, and it hits
    // zero well before the free-node count does.
    const freeLines = Substrate.LINES.filter((l) => l.every((v) => !blocked.has(v))).length;
    $("shapeNote").textContent =
      `${menu.densest.filter((r) => r.placeable).length}/${menu.densest.length} placeable · `
      + `${menu.freeNodes} free nodes · ${freeLines}/40 lines intact`;
  }

  function renderFabric() {
    const fs = fabric.fabricStats(market.positions);
    const listed = fleet.listedNodes();
    const inducedEdges = fabric.inducedEdges(listed);

    $("fabricStats").innerHTML = [
      tile("Fleet coherence", fmt.pct(fs.fleetCoherence), `${fmt.int(inducedEdges)} induced level-1 edges · normalised proxy`, "accent"),
      tile("Cells", fmt.int(fs.cells), `${fs.completeCells} complete · mean occupancy ${fmt.pct(fs.meanOccupancy, 0)}`),
      tile("Fabric level", "H" + fs.level, `recursive model bound ≤ ${fs.diameterAtLevel} hops`),
      tile("Your fragmentation", fmt.pct(fs.fragmentation), fs.fragmentation > 0.5 ? "swap book has proposals" : "positions are coherent", fs.fragmentation > 0.5 ? "down" : "up"),
    ].join("");

    drawW33();
    renderRouting();
    renderTower();
    renderCells();
    renderLadder();
    renderSwaps();
    renderShapes();

    const cp = fabric.clearingProfile();
    $("clearingStats").innerHTML = [
      tile("Cell diameter", cp.cellGraphDiameter, "exact for one W(3,3) cell"),
      tile("Averaging rounds", cp.rounds, "scalar disagreement below 10⁻⁹"),
      tile("Contraction / round", fmt.x(cp.contractionPerRound), "declared toy recurrence"),
      tile("Protocol status", "TOY MODEL", "not consensus or fault tolerance", "amber"),
    ].join("");
  }

  function drawW33() {
    const cv = $("w33Canvas");
    const { ctx, w, h } = prepCanvas(cv);
    const narrow = w < 480;
    const captionH = narrow ? 38 : 24;
    const margin = narrow ? 14 : 18;
    const plotH = Math.max(80, h - captionH - margin * 2);
    const cx = w / 2, cy = margin + plotH / 2;
    const R = Math.max(28, Math.min((w - margin * 2) / 2, plotH / 2) - 7);
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
        ctx.globalAlpha = hot ? 0.85 : (occupied.has(i) && occupied.has(j) ? 0.48 : 0.21);
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

    ctx.font = "10px " + css("--mono", "monospace");
    ctx.textAlign = "center";
    if (narrow) {
      ctx.fillStyle = css("--text-1", "#93a3bd");
      ctx.fillText("W(3,3) formal graph · 40 points · 240 edges", cx, h - 18);
      ctx.fillStyle = css("--text-2", "#61708c");
      ctx.fillText("SRG(40,12,2,4) · diameter 2 · bisection 100", cx, h - 5);
    } else {
      ctx.fillStyle = css("--text-1", "#93a3bd");
      ctx.fillText("W(3,3) formal graph · SRG(40,12,2,4) · 240 edges · diameter 2 · bisection 100", cx, h - 5);
    }

    cv._holotradeW33Hits = pos;
    if (!cv.dataset.bound) {
      cv.dataset.bound = "1";
      cv.addEventListener("click", (e) => {
        const point = canvasPoint(cv, e);
        let bestI = null, bestD = 16;
        for (const p of cv._holotradeW33Hits || []) {
          const d = Math.hypot(p.x - point.x, p.y - point.y);
          if (d < bestD) { bestD = d; bestI = p.i; }
        }
        if (bestI == null) return;
        ui.selectedPoint = ui.selectedPoint === bestI ? null : bestI;
        drawW33();
      });
    }
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
      <td class="num">${fmt.int(fabric.inducedEdges(c.nodes))}</td>
      <td class="num ${c.coherence > 0.9 ? "up" : ""}">${fmt.pct(c.coherence, 0)}</td>
    </tr>`).join("");
  }

  function renderLadder() {
    $("ladderBody").innerHTML = fabric.levelLadder(7).map((r) => `<tr>
      <td><span class="tag ${r.tradeable ? "accent" : ""}">H${r.level}</span></td>
      <td class="num">${fmt.big(r.leaves)}</td>
      <td class="num">${r.diameter}</td>
      <td class="num">${fmt.big(r.instances)}</td>
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
    ], { min: 0, max: Math.max(0.6, ...hist.map((h) => Math.max(h.gini, h.mean))) + 0.05, fmtY: (v) => v.toFixed(2), xCaption: "simulation history →" });

    // histogram of utilisation
    const bins = new Array(10).fill(0);
    for (const n of fleet.listedNodes()) bins[Math.min(9, Math.floor(n.utilisation * 10))]++;
    drawBars($("histCanvas"), bins.map((v, i) => ({
      label: (i * 10) + "%",
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
    const pad = chartPad(w, { l: 44, narrowL: 40, r: 12, narrowR: 8, t: 12, b: 27 });
    const probe = { utilisation: 0, utilisationEMA: 0.5, hardware: { thermalSensitivity: 1 } };
    const pts = [];
    for (let i = 0; i <= 100; i++) {
      probe.utilisation = i / 100;
      pts.push(pricing.demandMultiplier(probe));
    }
    const finitePts = pts.filter(Number.isFinite);
    if (!finitePts.length) { chartEmpty(ctx, w, h, "Demand curve unavailable"); return; }
    const min = 0.4, max = Math.max(2.2, ...finitePts);
    const X = (i) => pad.l + (i / 100) * (w - pad.l - pad.r);
    const Y = (v) => h - pad.b - ((v - min) / (max - min)) * (h - pad.t - pad.b);

    ctx.save();
    plotClip(ctx, w, h, pad);
    ctx.fillStyle = "rgba(45,212,167,0.10)";
    ctx.fillRect(X(55), pad.t, X(78) - X(55), h - pad.t - pad.b);
    ctx.restore();

    ctx.font = "10px " + css("--mono", "monospace");
    ctx.strokeStyle = css("--border", "#1c2740");
    ctx.fillStyle = css("--text-2", "#61708c");
    ctx.textAlign = "right";
    for (let i = 0; i <= 4; i++) {
      const v = min + (i / 4) * (max - min), y = Y(v);
      ctx.globalAlpha = 0.45;
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillText("×" + v.toFixed(1), pad.l - 6, y + 3);
    }
    ctx.setLineDash([3, 3]); ctx.beginPath();
    ctx.moveTo(pad.l, Y(1)); ctx.lineTo(w - pad.r, Y(1)); ctx.stroke(); ctx.setLineDash([]);
    axes(ctx, w, h, pad);

    ctx.save();
    plotClip(ctx, w, h, pad);
    ctx.strokeStyle = css("--accent", "#38bdf8"); ctx.lineWidth = 2.2;
    ctx.beginPath();
    pts.forEach((v, i) => { i === 0 ? ctx.moveTo(X(i), Y(v)) : ctx.lineTo(X(i), Y(v)); });
    ctx.stroke();
    ctx.restore();

    ctx.fillStyle = css("--text-2", "#61708c");
    ctx.font = "10px " + css("--mono", "monospace");
    ctx.textAlign = "center";
    ctx.fillText("0%", X(0) + 8, h - 9);
    ctx.fillText("55–78% target", (X(55) + X(78)) / 2, h - 9);
    ctx.fillText("100%", X(100) - 12, h - 9);
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
    const pad = chartPad(w, { l: 48, narrowL: 43, r: 12, narrowR: 8, t: 12, b: 28 });
    const kinds = [["gpu", HW_COLOR.gpu], ["cpu", HW_COLOR.cpu], ["photonic", HW_COLOR.photonic]];
    const series = kinds.map(([kind, color]) => {
      const hw = HARDWARE.find((x) => x.kind === kind);
      const data = [];
      for (let i = 0; i <= 100; i++) data.push(HolotradeFleet.weibullHazard(i / 100, hw));
      return { data, color, width: 1.8, label: kind };
    });
    const hazards = series.flatMap((s) => s.data).filter(Number.isFinite);
    const maxH = Math.max(1e-6, ...hazards);
    const X = (i) => pad.l + (i / 100) * (w - pad.l - pad.r);
    const Y = (v) => h - pad.b - (v / maxH) * (h - pad.t - pad.b);
    ctx.font = "9.5px " + css("--mono", "monospace");
    ctx.strokeStyle = css("--border", "#1c2740");
    ctx.fillStyle = css("--text-2", "#61708c");
    ctx.textAlign = "right";
    for (let i = 0; i <= 4; i++) {
      const value = (i / 4) * maxH, y = Y(value);
      ctx.globalAlpha = 0.45;
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillText(value < 0.1 ? value.toFixed(3) : value.toFixed(2), pad.l - 5, y + 3);
    }
    axes(ctx, w, h, pad);
    ctx.save();
    plotClip(ctx, w, h, pad);
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
    ctx.restore();
    ctx.fillStyle = css("--text-2", "#61708c");
    ctx.font = "10px " + css("--mono", "monospace");
    ctx.textAlign = "center";
    ctx.fillText("wear 0 → 100%", (pad.l + w - pad.r) / 2, h - 7);
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
      tile("Energy cost", fmt.usd(sum.totalCostPerHour) + "/hr", "at this simulation tick's marginal prices"),
      tile("Carbon", fmt.num(sum.totalCarbonPerHour, 1) + " kg/hr", `cheapest ${cheapest.id} · cleanest ${cleanest.id}`),
      tile("Price processes", DATACENTERS.length + " sites", "seeded stochastic inputs · not live feeds", "up"),
    ].join("");

    const colors = ["#38bdf8", "#f4526b", "#2dd4a7", "#f5a524", "#a78bfa", "#93a3bd"];
    drawLines($("energyCanvas"), DATACENTERS.map((d, i) => ({
      data: energy.historyFor(d.id).slice(-240), color: colors[i % colors.length], width: 1.5,
    })), { fmtY: (v) => "$" + v.toFixed(0), xCaption: "last 240 simulated ticks →" });
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

    $("floorBody").innerHTML = HARDWARE.map((hw) => `<tr>
      <td><span class="tag" style="color:${HW_COLOR[hw.kind]}">${fmt.esc(hw.class)}</span> <span class="muted" style="font-size:11px">${fmt.esc(hw.kind)}</span></td>
      <td class="num">${fmt.sci(hw.joulesPerOp, 1)}</td>
      <td><span class="tag amber">catalogue assumption</span></td>
    </tr>`).join("");
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
      <td><span class="tag ${p.status === "settled" ? "up" : p.status === "rejected" ? "down" : p.status === "running" ? "accent" : ""}">${p.status === "signed" ? "sealed demo" : p.status}</span></td>
    </tr>`).join("") : '<tr><td colspan="6" class="empty">no plans</td></tr>';

    $("auditBody").innerHTML = exec.auditLog.slice(0, 24).map((e) => `<tr>
      <td class="mono muted">${e.seq}</td>
      <td><span class="tag ${e.kind.includes("failed") ? "down" : e.kind.includes("settled") ? "up" : "accent"}">${fmt.esc(e.kind)}</span></td>
      <td class="wrap" style="font-size:11px">${fmt.esc(e.detail)}</td>
      <td class="mono muted" style="font-size:10px">${fmt.esc(e.prev.slice(0, 4))}→${fmt.esc(e.hash.slice(0, 6))}</td>
    </tr>`).join("") || '<tr><td colspan="4" class="empty">chain empty</td></tr>';
    $("chainNote").textContent = s.chain.ok ? "locally consistent — not externally authenticated" : `BROKEN at #${s.chain.brokenAt}`;

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
      <dt>Illustrative emulation factor</dt><dd>${w.magicBudget ? "9^" + w.magicBudget + " = " + fmt.sci(Substrate.magicMultiplier(w.magicBudget)) : "1× baseline — not zero compute cost"}</dd>
      <dt>Node-seconds requested</dt><dd>${fmt.int(secs * nodes)}</dd>
      <dt>Egress</dt><dd class="${grants ? "amber" : "up"}">${grants ? fmt.esc(grants) : "deny all — no network device"}</dd>
      <dt>Settlement granularity</dt><dd>1 second</dd>
      <dt>Boot overhead at 1s</dt><dd>${(HolotradeExecution.BOOT_MS.p50 / 1000 * 100).toFixed(1)}%</dd>`;
  }

  function renderPlacements() {
    const plan = ui.selectedPlan ? exec.plans.find((p) => p.id === ui.selectedPlan) : null;
    if (!plan || plan.status !== "signed") {
      $("placeBody").innerHTML = '<tr><td colspan="8" class="empty">seal a demo plan to see placements</td></tr>';
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
          <dt>Induced level-1 edges</dt><dd>${fmt.int(q.inducedEdges)}</dd>
          <dt>Edge-coherence proxy</dt><dd>${fmt.num(q.edgeCoherence, 1)} normalised units</dd>
          <dt>Graph components</dt><dd>${fmt.int(g.components)}</dd>
          <dt>Certified diameter</dt><dd>${g.certifiedDiameter == null ? "not connected" : g.certifiedDiameter}</dd>
          <dt>Minimum induced degree</dt><dd>${fmt.int(g.minInducedDegree)}</dd>
          <dt>Effective capacity</dt><dd>${fmt.big(q.effectiveTflops)} TF</dd>
        </dl>
        <hr class="sep">
        <div class="note ${g.connected ? "" : "amber"}"><b>Computed induced-graph facts</b> — not availability, throughput, or fault-tolerance SLAs:
          ${g.connected ? "connected" : "disconnected"} · ${g.components} component${g.components === 1 ? "" : "s"} ·
          ${g.certifiedDiameter == null ? "no finite whole-basket diameter" : "diameter " + g.certifiedDiameter} ·
          adjacency is computed directly from addresses.
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
    const prof = registry.marketBreadthProfile();
    const U = HolotradeUOR.UOR;

    $("assetStats").innerHTML = [
      tile("Assets registered", fmt.int(prof.count), "every listed node has a typed reference", "accent"),
      tile("Mean policy mobility", fmt.num(prof.meanMarketBreadthScore, 3), "configured estimate · not observed liquidity"),
      tile("Broad / site-bound", `${prof.bands.broad} / ${prof.bands["site-bound"]}`, `${prof.bands["multi-region"]} multi-region · ${prof.bands.restricted} restricted`),
      tile("Canonical cells", fmt.int(U.canonicalCells), "40 × 1,296 = |Aut(W(3,3))|", "violet"),
    ].join("");

    $("uorStats").innerHTML = [
      tile("Address width", U.bits + " bits", "one flat resolve, no lookup"),
      tile("Sylow choices", U.sylowChoices, "n₃(Sp(4,𝔽₃)) = v = 40"),
      tile("Normaliser order", fmt.int(U.normaliserOrder), "|N_G(P₃)| = μ² · q^(q+1) = 16 × 81"),
      tile("Payload", fmt.num(U.payloadBits, 2) + " bits", "64 − log₂(51,840), computed not quoted"),
    ].join("");

    drawBars($("liquidityCanvas"), [
      { label: "broad", value: prof.bands.broad, color: css("--up", "#2dd4a7") },
      { label: "multi", value: prof.bands["multi-region"], color: css("--accent", "#38bdf8") },
      { label: "restricted", value: prof.bands.restricted, color: css("--amber", "#f5a524") },
      { label: "site-bound", value: prof.bands["site-bound"], color: css("--down", "#f4526b") },
    ]);

    $("constraintBody").innerHTML = Object.entries(HolotradeUOR.POLICY_MOBILITY_SCORE).map(([k, score]) => {
      const breadth = Math.round(U.sylowChoices * score);
      const band = HolotradeUOR.marketBreadthBand(score);
      return `<tr>
        <td class="mono">${fmt.esc(k)}</td>
        <td class="num">${fmt.num(score, 3)}</td>
        <td class="num">${breadth} / ${U.sylowChoices}</td>
        <td><span class="tag ${band === "broad" ? "up" : band === "site-bound" ? "down" : "amber"}">${band}</span></td>
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
        ["identity", "self", sh.counts.identity, sh.ratios.identity, sh.geometryRatios.identity],
        ["intersecting", "collinear — 1 hop", sh.counts.intersecting, sh.ratios.intersecting, sh.geometryRatios.intersecting],
        ["disjoint", "2 hops via one of μ=4 relays", sh.counts.disjoint, sh.ratios.disjoint, sh.geometryRatios.disjoint],
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
    const tx = cap.illustrativeTransforms;
    $("capacityStats").innerHTML = [
      tile("Transaction rate", fmt.big(cap.tps) + " TPS", "drag the slider", "accent"),
      tile("Conjugacy-scaled display", fmt.sci(tx.conjugacyScaledRate) + "/s", `input × ${fmt.num(tx.conjugacyScale, 0)} · illustrative only`),
      tile("Logical-scaled display", fmt.sci(tx.logicalScaledRate) + "/s", `input × ${fmt.num(tx.logicalScale, 4)} · not a ceiling`, "violet"),
      tile("Full reference scan", fmt.num(cap.fullCellScanSeconds * 1000, 3) + " ms", "51,840 references ÷ supplied TPS"),
    ].join("");
  }

  // ====================================================================
  // RECEIPTS
  // ====================================================================

  function renderReceipts() {
    const rs = market.receipts;
    const substrate = rs.filter((r) => r.lane === "substrate");

    $("receiptStats").innerHTML = [
      tile("Quote receipts", fmt.int(rs.length), "issued at simulated fills", "accent"),
      tile("Evidence mode", "SYNTHETIC", "not execution or delivery evidence", "amber"),
      tile("Substrate-labelled", fmt.int(substrate.length), "model-generated contextual samples"),
      tile("Clifford-labelled", fmt.int(rs.length - substrate.length), "classification only · no verification", "violet"),
    ].join("");

    $("receiptNote").textContent = `${rs.length} simulated quote samples`;
    $("receiptBody").innerHTML = rs.length ? rs.slice(0, 120).map((r) => `<tr class="clickable" data-node="${fmt.esc(r.nodeId)}">
      <td class="mono" style="font-size:10.5px">${fmt.esc(r.id)}</td>
      <td class="mono">${fmt.esc(r.nodeId.slice(-12))}</td>
      <td class="mono muted">${fmt.esc(r.nodeAddress)}</td>
      <td><span class="tag ${r.lane === "substrate" ? "violet" : ""}">${r.lane}</span></td>
      <td class="num">${r.lane === "substrate" ? fmt.num(r.contextualFraction, 4) : "—"}</td>
      <td><span class="tag amber">${fmt.esc(r.verdict)}</span></td>
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
          <p>Selling only "a VM node for an hour" hides execution detail. This prototype makes three product hypotheses explicit so they can be measured rather than smuggled into one opaque rate.</p>
          <p><b>1. The hour is a billing convention.</b> This simulator declares a 171.5 ms median and 178 ms p99 cold-start distribution so boot overhead can be itemised. Those are model assumptions, not measurements of this host or a portable Firecracker benchmark.</p>
          <p><b>2. An hour hides time-varying inputs.</b> Energy and congestion can change inside a quote horizon. A node-second ledger can preserve the modeled interval used for delivery while still presenting hourly-equivalent quotes for comparison. Boot time and settlement granularity are independent policy choices.</p>
          <p><b>3. "A node for an hour" does not state execution intent.</b> This prototype plan names declared artifact digests, egress grants, secret references and a validity window before simulated launch. Its local integrity seal detects edits. It does not fetch or hash artifact bytes, sign the plan cryptographically, or remotely attest a host.</p>
          <div class="note"><b>So the atomic unit is the node-second and the contract is the execution plan.</b><br>
            <b>asset</b> — the node: durable, has a genome and a health record, is what you lease or own.<br>
            <b>contract</b> — the plan: demo-sealed, content-bound, scoped, and time-boxed <em>before</em> the simulated run.<br>
            <b>unit</b> — the node-second: what settles against the seeded energy model in this demo.</div>
        </div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">The price</h3><span class="card-note">P = P₀ × E × G × D × H × Q × L</span></div>
        <div class="card-body">
          <p>Multiplicative rather than additive, and that is a real decision: it keeps the terms independent, keeps every one auditable on its own line, and — once each is clamped — stops any single factor driving the price to zero or infinity on its own. The buyer sees the full decomposition on every quote. There is no opaque market rate.</p>
          <div class="tbl-wrap"><table class="tbl"><thead><tr><th>Term</th><th>What it prices</th><th>Where it comes from</th></tr></thead><tbody>
            <tr><td class="mono"><b>E</b></td><td>Energy</td><td>Seeded simulated $/MWh at that site for the current tick, PUE-adjusted through a clamped power law.</td></tr>
            <tr><td class="mono"><b>G</b></td><td>Genetics</td><td>Specialisation on <em>this</em> class × realised fitness × provenance depth. Never a nameplate figure.</td></tr>
            <tr><td class="mono"><b>D</b></td><td>Demand / wear</td><td>Two-sided. Premium above the target band, discount below. See below.</td></tr>
            <tr><td class="mono"><b>H</b></td><td>Health</td><td>Performance derate × Weibull reliability × correctable-error drift.</td></tr>
            <tr><td class="mono"><b>Q</b></td><td>Declared capability</td><td>1× is the classical baseline in this model. For declared non-Clifford budget <em>t</em>, 9<sup>t</sup> is an illustrative scarcity dial, not a universal runtime, memory, routing, or error-correction law.</td></tr>
            <tr><td class="mono"><b>L</b></td><td>Locality</td><td>Fabric distance, from one symplectic inner product per hop. Not an availability-zone heuristic.</td></tr>
          </tbody></table></div>
          <p style="margin-top:11px">The floor is <b>energy + maintenance reserve + capital recovery</b>. All three, because a discount that does not repay the machine is not a discount — it is a loss the operator has not noticed yet. The exchange refuses to clear below it.</p>
        </div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">Why D is two-sided</h3></div>
        <div class="card-body">
          <p>The naive version of a compute market prices scarcity only: busy node costs more. That leaves the cold half of the fleet idle, and an idle node still ages, still draws standby power, and still has to be serviced on the same calendar.</p>
          <p>So D charges a premium above the band and pays a discount below it. <b>The seeded wear function assumes utilisation swings add more wear than steady load at the same average.</b> That makes the premium and maintenance reserve internally consistent with this model; it is not a measured silicon-lifetime result.</p>
          <p>Within the simulation, demand migrates toward cheaper nodes, dispersion falls, and modelled service events spread out. Real fleet lifetime and staffing effects would require telemetry and validation.</p>
          <div class="note"><b>Seeded simulation result:</b> utilisation Gini is lower with the balancer on than off in the supplied reproducible model. Nothing in the loop pushes utilisation toward the band directly: a node's target is set by its price relative to the median of its own hardware class, and that price came from its utilisation. Toggle it on the Balance page and watch the current run.</div>
        </div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">Topology-aware capacity</h3></div>
        <div class="card-body">
          <p>In the exact level-1 W(3,3) address model, direct adjacency is one symplectic inner-product test and the software finds a relay by a bounded scan of forty points. That is a useful finite control primitive. It is not a claim that packet routing, gate application and memory addressing are already one deployed physical operation.</p>
          <p><b>The model therefore prices shapes, not counts alone.</b> A complete 40-point graph has diameter 2, an explicit balanced cut of 100 among 240 edges, and four common neighbours for each non-adjacent pair. A partial holding receives only its own induced edges, components, minimum degree and connected diameter; it cannot borrow unowned relays.</p>
          <p>Coherence enters the simulated price at basket level because it is not a property of one node. The superlinear multiplier is a market-design hypothesis about completing useful connectivity, not a theorem about bandwidth or deployed asset value.</p>
          <div class="note scope"><b>Recursive instrument design.</b> The prototype can feed leaves and simulated composites through the same quote interface — address, modeled specialization, health, utilisation and throughput. This makes a self-similar instrument ladder testable, but does not yet build atomic composite reservation, recursive physical routing, or campus-level delivery and settlement.</div>
        </div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">Defragmentation</h3></div>
        <div class="card-body">
          <p>Trading fragments ownership. After repeated spot fills the seeded portfolio can become confetti — a few points in each of many cells — and its induced-edge coherence falls even though every individual position looks fine. That is a coordination failure with a clean fix in the model: a swap book.</p>
          <p>I give you my orphan in your cell, you give me yours in mine. The prototype uses a small modeled adjustment for machine differences and proposes a swap only when both parties gain induced-edge coherence. It is a topology-defragmentation mechanism; physical bandwidth, delivery and legal exchange remain unimplemented.</p>
        </div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">Policy-estimated market breadth</h3></div>
        <div class="card-body">
          <p>Delivery policies constrain where an asset may remain eligible. The dashboard applies documented default mobility scores across forty reference regions and uses the tightest configured policy as a conservative estimate; it does not invent independence between policies.</p>
          <p>This score is a policy assumption unless a venue supplies measured eligibility. It is not a subgroup order, an orbit-stabilizer co-volume, a price, or observed order-book liquidity.</p>
        </div></div>

      <div class="card"><div class="card-head"><h3 class="card-title">Honest scope</h3></div>
        <div class="card-body">
          <div class="note scope">
            <b>Exact and computed here:</b> the level-1 W(3,3) graph — SRG(40,12,2,4), 240 edges, diameter 2, and an explicit 20|20 cut of size 100; |Sp(4,𝔽₃)| = 51,840; 40<sup>n</sup> address leaves; and the recursive model diameter bound 16n−14. Partial baskets report exact induced edges, connectivity, components, diameter when connected, and minimum induced degree.
          </div>
          <div class="note scope">
            <b>Modelled, not measured:</b> the fleet, grid prices, genomes, wear, order flow, J/op catalogue values, recursive fabric composition, policy mobility scores, and illustrative rate transforms. This is a seeded simulation; none of those displays is a live feed, benchmark, deployment ceiling, or SLA.
          </div>
          <div class="note scope">
            <b>Not built here:</b> a physical W(3,3) substrate, recursive product router, consensus protocol, fault-tolerance protocol, cryptographic plan signature, remote attestation, or quantum hardware. The finite level-1 graph calculations do not establish any of those systems.
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

  let resizeFrame = 0;
  function redrawAfterResize() {
    cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(() => {
      resizeFrame = 0;
      if (RENDERERS[ui.view]) render();
    });
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
    // One wall-clock tick advances one coherent simulation interval.  Every
    // subsystem receives the same elapsed duration in its native unit.
    const stepSeconds = 30 * ui.speed;
    const stepHours = stepSeconds / 3600;
    ui.simSeconds += stepSeconds;

    energy.tick(stepSeconds);
    pricing.applyDemandResponse(stepHours, { workloadId: ui.workload });
    fleet.tick(stepHours);
    exec.meter(stepSeconds).forEach((r) => {
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

    $("tkQty").addEventListener("input", () => {
      renderTicketPreview();
      if (ui.view === "exchange") renderDepth();
    });
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
      toast("Plan sealed (demo)", `${p.id} · integrity digest ${p.digest.slice(0, 12)} · not a cryptographic signature`, "up");
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

    const shapeBusy = $("shapeBusy");
    if (shapeBusy) shapeBusy.addEventListener("input", renderShapes);

    $("drawerClose").addEventListener("click", closeDrawer);
    $("drawerBack").addEventListener("click", closeDrawer);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeDrawer(); });

    $("menuBtn").addEventListener("click", () => $("sidebar").classList.toggle("open"));
    const mq = window.matchMedia("(max-width: 900px)");
    const applyMq = () => $("menuBtn").classList.toggle("hidden", !mq.matches);
    applyMq(); mq.addEventListener("change", applyMq);
    window.addEventListener("resize", redrawAfterResize, { passive: true });
    if (window.ResizeObserver) {
      const layoutObserver = new ResizeObserver(redrawAfterResize);
      layoutObserver.observe($("main"));
    }

    // warm the simulation so the first frame is not a cold fleet
    for (let i = 0; i < 220; i++) {
      energy.tick(30);
      pricing.applyDemandResponse(30 / 3600, { workloadId: ui.workload });
      fleet.tick(30 / 3600);
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
