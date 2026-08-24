// ======================================================================
// HOLOTRADE MARKET
//
// A prototype order book and matching simulation. Spot capacity is the
// executable path; forward, option, lease and supply tabs are labelled
// design sketches until their delivery state machines exist.
//
// ---------------------------------------------------------------------
// WHY NOT JUST "RENT A VM"
//
// A VM-hours marketplace prices one thing -- a rectangle of capacity
// for a span of time -- and everything interesting about compute gets
// flattened into it. Holotrade lists five instruments because the risks
// a compute buyer actually carries are five different risks:
//
//   spot     you need it now, you accept today's price
//   forward  you need it in March and cannot carry an ERCOT heat dome
//   option   you MIGHT need 400 nodes on launch day; you want the right
//   lease    you want a core that already knows your workload class
//   supply   you own idle nodes and want the exchange to sell them
//
// Only the first is a VM. The other four are why an exchange exists at
// all rather than a price list.
//
// ---------------------------------------------------------------------
// SETTLEMENT
//
// Every simulated fill closes with a quote receipt binding the displayed
// terms and node provenance. It is deliberately marked SYNTHETIC: only
// the execution engine can later emit a delivery receipt, and neither is
// a remote-attestation implementation yet.
// ======================================================================

(function (root) {
  "use strict";

  const S = root.Substrate || (typeof require !== "undefined" ? require("./substrate.js") : null);

  /**
   * Non-mutating execution preview for the ask side of a book.
   *
   * Quotes are hourly-equivalent rates and qty is a capacity-lot count.
   * The caller decides the lot duration; this function only answers the
   * market-microstructure question: how much fills, at what VWAP, and how
   * many price levels are consumed?
   */
  function sweepAsks(asks, requestedQty, limitPrice = Infinity) {
    const requested = Number(requestedQty);
    if (!Number.isFinite(requested) || requested <= 0) {
      return {
        requested: 0, filled: 0, remaining: 0, cost: 0, average: 0,
        worst: 0, best: 0, levelsTouched: 0, complete: true, slippageBps: 0,
      };
    }

    const rows = (asks || [])
      .filter((row) => Number.isFinite(row.price) && row.price >= 0 && Number.isFinite(row.qty) && row.qty > 0)
      .slice()
      .sort((a, b) => a.price - b.price);
    const cap = Number.isFinite(Number(limitPrice)) ? Number(limitPrice) : Infinity;
    let remaining = requested;
    let cost = 0;
    let worst = 0;
    let levelsTouched = 0;
    const best = rows.length ? rows[0].price : 0;

    for (const row of rows) {
      if (remaining <= 0 || row.price > cap) break;
      const take = Math.min(remaining, row.qty);
      if (take <= 0) continue;
      cost += take * row.price;
      worst = row.price;
      remaining -= take;
      levelsTouched++;
    }

    const filled = requested - remaining;
    const average = filled > 0 ? cost / filled : 0;
    return {
      requested,
      filled,
      remaining,
      cost,
      average,
      worst,
      best,
      levelsTouched,
      complete: remaining <= 1e-12,
      slippageBps: filled > 0 && best > 0 ? (average / best - 1) * 10000 : 0,
    };
  }

  /**
   * Pareto frontier for a typed compute menu: minimise hourly-equivalent
   * price while maximising delivered throughput. Equal-price ties keep only
   * the fastest point, so no returned point is dominated by another return.
   */
  function paretoFrontier(points) {
    const rows = (points || [])
      .filter((p) => Number.isFinite(p.price) && p.price >= 0 && Number.isFinite(p.tflops) && p.tflops > 0)
      .slice()
      .sort((a, b) => a.price - b.price || b.tflops - a.tflops);
    const out = [];
    let bestThroughput = -Infinity;
    for (const point of rows) {
      if (point.tflops > bestThroughput) {
        out.push(point);
        bestThroughput = point.tflops;
      }
    }
    return out;
  }

  let ORDER_SEQ = 1;
  let TRADE_SEQ = 1;
  let POSITION_SEQ = 1;

  class Order {
    constructor(spec) {
      this.id = `O${String(ORDER_SEQ++).padStart(6, "0")}`;
      this.ts = Date.now();
      this.status = "open";        // open | partial | filled | cancelled | rejected
      this.filledQty = 0;
      this.fills = [];
      Object.assign(this, spec);
    }

    get remaining() {
      return Math.max(0, this.qty - this.filledQty);
    }

    get notional() {
      return this.qty * this.limitPrice;
    }
  }

  class Market {
    constructor(fleet, pricing, energy, catalog) {
      this.fleet = fleet;
      this.pricing = pricing;
      this.energy = energy;
      this.catalog = catalog;
      this.rand = S.rng("holotrade-market");

      // one book per instrument
      this.books = {};
      for (const inst of catalog.INSTRUMENTS) {
        this.books[inst.id] = { bids: [], asks: [] };
      }

      this.trades = [];            // tape, newest first
      this.maxTrades = 500;
      this.receipts = [];
      this.maxReceipts = 300;
      this.positions = [];         // the user's open positions
      this.cash = 250_000;
      this.startingCash = 250_000;
      this.realised = 0;
      this.userOrders = [];

      this.seedBooks();
    }

    // ------------------------------------------------------------------
    // Book construction
    // ------------------------------------------------------------------

    /**
     * The ask side is not invented -- it IS the pricing engine. Every
     * listed node posts an offer at its own clearing price. That is the
     * whole design: the book is a projection of the fleet, so a price
     * on screen always decomposes back into six auditable multipliers
     * and a named machine.
     */
    rebuildAsks(instrumentId = "spot", opts = {}) {
      const book = this.books[instrumentId];
      if (!book) return;
      const workloadId = opts.workloadId || "llm-train";
      const anchorAddress = opts.anchorAddress || null;
      const asks = [];

      for (const node of this.fleet.listedNodes()) {
        const q = this.pricing.quote(node, { workloadId, anchorAddress });
        if (!q.serviceable || q.price == null) continue;
        let price = q.price;
        // One spot lot represents one eighth of the node's hourly capacity.
        // A saturated node must disappear from the ask side; Math.max(1, ...)
        // would otherwise let it sell an unlimited sequence of phantom lots.
        let qty = Math.max(0, Math.floor((1 - node.utilisation + 1e-12) * 8));
        if (qty === 0) continue;

        if (instrumentId === "forward") {
          const f = this.pricing.forwardPrice(node, opts.days || 30, workloadId);
          if (!f) continue;
          price = f.price;
        } else if (instrumentId === "option") {
          const o = this.pricing.optionPremium(node, opts.days || 7, opts.strike || 1.25, workloadId);
          if (!o) continue;
          price = o.premium;
          qty = Math.max(1, Math.round(o.availability * 10));
        } else if (instrumentId === "lease") {
          const l = this.pricing.leasePrice(node, opts.days || 30, workloadId);
          if (!l) continue;
          price = l.hourly;
          qty = 1;   // a core can only be leased to one tenant at a time
        } else if (instrumentId === "supply") {
          // supply offers are what OTHER operators are willing to take
          price = q.floor * (1.02 + this.rand() * 0.12);
        }

        asks.push({
          id: `A-${node.id}`,
          side: "ask",
          nodeId: node.id,
          node,
          price,
          qty,
          quote: q,
          instrument: instrumentId,
          maker: node.operator,
        });
      }

      asks.sort((a, b) => a.price - b.price);
      book.asks = asks;
      return asks;
    }

    /**
     * Resting bids from other participants. Modelled, not real -- but
     * modelled off the ask distribution so the spread and the depth
     * behave like a market rather than like noise.
     */
    rebuildBids(instrumentId = "spot") {
      const book = this.books[instrumentId];
      if (!book || !book.asks.length) return;
      const best = book.asks[0].price;
      const bids = [];
      const levels = 14;
      for (let i = 0; i < levels; i++) {
        const depth = (i + 1) / levels;
        const price = best * (1 - 0.006 - depth * 0.13 * (0.7 + this.rand() * 0.6));
        const qty = Math.round(2 + Math.pow(depth, 0.6) * 44 * (0.5 + this.rand()));
        bids.push({
          id: `B-${instrumentId}-${i}`,
          side: "bid",
          price,
          qty,
          instrument: instrumentId,
          maker: this.catalog.OPERATORS[Math.floor(this.rand() * this.catalog.OPERATORS.length)],
        });
      }
      // keep the user's own live bids in the book
      const mine = this.userOrders.filter(
        (o) => o.instrument === instrumentId && o.side === "bid" && (o.status === "open" || o.status === "partial")
      ).map((o) => ({
        id: o.id, side: "bid", price: o.limitPrice, qty: o.remaining,
        instrument: instrumentId, maker: "YOU", mine: true, order: o,
      }));

      book.bids = bids.concat(mine).sort((a, b) => b.price - a.price);
      return book.bids;
    }

    seedBooks() {
      for (const inst of this.catalog.INSTRUMENTS) {
        this.rebuildAsks(inst.id);
        this.rebuildBids(inst.id);
      }
    }

    book(instrumentId = "spot") {
      return this.books[instrumentId] || { bids: [], asks: [] };
    }

    spread(instrumentId = "spot") {
      const b = this.book(instrumentId);
      if (!b.asks.length || !b.bids.length) return null;
      const bestAsk = b.asks[0].price;
      const bestBid = b.bids[0].price;
      return { bestBid, bestAsk, spread: bestAsk - bestBid, bps: ((bestAsk - bestBid) / bestAsk) * 10000 };
    }

    /** Cumulative depth curve for the depth chart. */
    depth(instrumentId = "spot", levels = 24) {
      const b = this.book(instrumentId);
      const acc = (side, sorted) => {
        let cum = 0;
        return sorted.slice(0, levels).map((o) => {
          cum += o.qty;
          return { price: o.price, qty: o.qty, cum, side };
        });
      };
      return { bids: acc("bid", b.bids), asks: acc("ask", b.asks) };
    }

    /** Preview a buy without mutating the book, cash, positions, or fleet. */
    previewBuy(instrumentId = "spot", qty = 1, limitPrice = Infinity) {
      return sweepAsks(this.book(instrumentId).asks, qty, limitPrice);
    }

    // ------------------------------------------------------------------
    // Matching
    // ------------------------------------------------------------------

    /**
     * Submit a buy order. Crosses against the ask side, which means it
     * crosses against real nodes with real quotes -- so a fill names the
     * machine you got, not an anonymous unit of capacity.
     *
     * A market order fills at whatever the book gives it; a limit order
     * rests if it cannot clear. Partial fills are normal, because a
     * single node has bounded free capacity.
     */
    submitBuy({ instrument = "spot", qty = 1, limitPrice = null, workloadId = "llm-train", anchorAddress = null, days = 30, nodeId = null }) {
      const order = new Order({
        side: "bid", instrument, qty, workloadId, anchorAddress, days,
        limitPrice: limitPrice == null ? Infinity : limitPrice,
        type: limitPrice == null ? "market" : "limit",
        targetNodeId: nodeId,
      });
      this.userOrders.unshift(order);

      this.rebuildAsks(instrument, { workloadId, anchorAddress, days });
      const asks = this.book(instrument).asks;

      let remaining = qty;
      let spent = 0;
      const candidates = nodeId ? asks.filter((a) => a.nodeId === nodeId) : asks;

      for (const ask of candidates) {
        if (remaining <= 0) break;
        if (ask.price > order.limitPrice) break;
        const take = Math.min(remaining, ask.qty);
        const cost = take * ask.price;
        if (cost > this.cash - spent) {
          const affordable = Math.floor((this.cash - spent) / ask.price);
          if (affordable <= 0) break;
          const partialCost = affordable * ask.price;
          this.recordFill(order, ask, affordable, partialCost);
          spent += partialCost;
          remaining -= affordable;
          break;
        }
        this.recordFill(order, ask, take, cost);
        spent += cost;
        remaining -= take;
        ask.qty -= take;
      }

      this.cash -= spent;
      order.filledQty = qty - remaining;
      order.status =
        order.filledQty === 0 ? (order.type === "market" ? "rejected" : "open")
        : order.filledQty < qty ? "partial" : "filled";
      this.rebuildBids(instrument);
      return order;
    }

    recordFill(order, ask, qty, cost) {
      const node = ask.node;
      const trade = {
        id: `T${String(TRADE_SEQ++).padStart(6, "0")}`,
        ts: Date.now(),
        instrument: order.instrument,
        nodeId: ask.nodeId,
        nodeAddress: node ? node.address : "-",
        hardware: node ? node.hardware.class : "-",
        dcId: node ? node.dcId : "-",
        qty,
        price: ask.price,
        cost,
        workloadId: order.workloadId,
        side: "buy",
        maker: ask.maker,
        quote: ask.quote,
      };
      order.fills.push(trade);
      this.trades.unshift(trade);
      if (this.trades.length > this.maxTrades) this.trades.pop();

      // open a position
      const existing = this.positions.find(
        (p) => p.nodeId === trade.nodeId && p.instrument === trade.instrument && p.workloadId === trade.workloadId
      );
      if (existing) {
        const totalQty = existing.qty + qty;
        existing.avgPrice = (existing.avgPrice * existing.qty + ask.price * qty) / totalQty;
        existing.qty = totalQty;
      } else {
        this.positions.push({
          id: `P${String(POSITION_SEQ++).padStart(6, "0")}`,
          nodeId: trade.nodeId,
          node,
          instrument: trade.instrument,
          workloadId: trade.workloadId,
          qty,
          avgPrice: ask.price,
          openedAt: Date.now(),
          days: order.days,
        });
      }

      // put the bought capacity to work
      if (node && order.instrument === "spot") {
        node.utilisation = Math.min(1, node.utilisation + qty * 0.125);
        node.currentWorkload = order.workloadId;
      }

      this.issueReceipt(trade, node);
      return trade;
    }

    /** Sell/close a position by walking displayed external bid depth. */
    submitSell({ positionId, qty = null }) {
      const pos = this.positions.find((p) => p.id === positionId);
      if (!pos) return { ok: false, reason: "no such position" };
      const size = qty == null ? pos.qty : Math.min(qty, pos.qty);
      this.rebuildAsks(pos.instrument, { workloadId: pos.workloadId });
      this.rebuildBids(pos.instrument);
      const bids = this.book(pos.instrument).bids.filter((b) => !b.mine);
      if (!bids.length) return { ok: false, reason: "no bid" };
      let remaining = size;
      let proceeds = 0;
      let pnl = 0;
      const fills = [];
      for (const bid of bids) {
        if (remaining <= 0) break;
        const take = Math.min(remaining, Math.max(0, bid.qty || 0));
        if (take <= 0) continue;
        const fillProceeds = bid.price * take;
        const fillPnl = (bid.price - pos.avgPrice) * take;
        const fill = {
          id: `T${String(TRADE_SEQ++).padStart(6, "0")}`,
          ts: Date.now(), instrument: pos.instrument, nodeId: pos.nodeId,
          nodeAddress: pos.node ? pos.node.address : "-",
          hardware: pos.node ? pos.node.hardware.class : "-",
          dcId: pos.node ? pos.node.dcId : "-", qty: take, price: bid.price,
          cost: -fillProceeds, workloadId: pos.workloadId, side: "sell",
          maker: bid.maker, pnl: fillPnl,
        };
        fills.push(fill);
        this.trades.unshift(fill);
        bid.qty -= take;
        proceeds += fillProceeds;
        pnl += fillPnl;
        remaining -= take;
      }
      if (!fills.length) return { ok: false, reason: "no displayed bid depth" };
      while (this.trades.length > this.maxTrades) this.trades.pop();
      const sold = size - remaining;
      this.cash += proceeds;
      this.realised += pnl;
      pos.qty -= sold;
      if (pos.qty <= 1e-12) this.positions = this.positions.filter((p) => p.id !== positionId);
      if (pos.node && pos.instrument === "spot") {
        pos.node.utilisation = Math.max(0, pos.node.utilisation - sold * 0.125);
      }
      const trade = {
        ...fills[0], id: fills.length === 1 ? fills[0].id : `SWEEP-${fills[0].id}`,
        qty: sold, price: proceeds / sold, cost: -proceeds, pnl,
      };
      return { ok: true, trade, fills, pnl, unfilledQty: remaining };
    }

    cancel(orderId) {
      const o = this.userOrders.find((x) => x.id === orderId);
      if (!o || o.status === "filled") return false;
      o.status = "cancelled";
      this.rebuildBids(o.instrument);
      return true;
    }

    // ------------------------------------------------------------------
    // Synthetic quote receipts
    // ------------------------------------------------------------------

    /**
     * Every fill emits a synthetic quote receipt for demo provenance.
     * No workload has run at fill time, so this routine cannot honestly
     * claim contextual measurement, Clifford verification, or delivery.
     */
    issueReceipt(trade, node) {
      const photonic = node && node.hardware.magicCapable;
      const measured = photonic
        ? S.CONST.contextualFraction + (this.rand() - 0.5) * 0.016
        : 0;
      const verdict = {
        ok: null,
        label: "SYNTHETIC_SAMPLE",
        detail: "model-generated quote sample; not execution evidence",
      };

      const receiptBody = JSON.stringify({
        tradeId: trade.id,
        nodeId: trade.nodeId,
        instrument: trade.instrument,
        workloadId: trade.workloadId,
        price: trade.price,
        qty: trade.qty,
        ts: trade.ts,
        lane: photonic ? "substrate" : "clifford",
        contextualFraction: measured,
        verdict: verdict.label,
        provenance: node ? {
          generation: node.lineage.generation,
          forkedFrom: node.lineage.forkedFrom,
          jobsCompleted: node.jobsCompleted,
          fitness: this.fleet.fitness(node),
        } : null,
      });
      const digest = S.hash32(receiptBody).toString(16).padStart(8, "0");

      const receipt = {
        id: `R-${digest}`,
        tradeId: trade.id,
        ts: trade.ts,
        nodeId: trade.nodeId,
        nodeAddress: trade.nodeAddress,
        instrument: trade.instrument,
        workloadId: trade.workloadId,
        qty: trade.qty,
        price: trade.price,
        lane: photonic ? "substrate" : "clifford",
        contextualFraction: measured,
        verdict: verdict.label,
        verdictOk: verdict.ok,
        evidenceMode: "SIMULATED_QUOTE_RECEIPT",
        detail: verdict.detail,
        // provenance: the orbit history of the capacity you bought
        provenance: node ? {
          generation: node.lineage.generation,
          forkedFrom: node.lineage.forkedFrom,
          jobsCompleted: node.jobsCompleted,
          fitness: this.fleet.fitness(node),
        } : null,
        digest,
      };
      this.receipts.unshift(receipt);
      if (this.receipts.length > this.maxReceipts) this.receipts.pop();
      return receipt;
    }

    // ------------------------------------------------------------------
    // Portfolio
    // ------------------------------------------------------------------

    markToMarket() {
      let value = 0;
      let unrealised = 0;
      const rows = [];
      for (const pos of this.positions) {
        const node = this.fleet.get(pos.nodeId);
        if (!node) continue;
        let mark;
        if (pos.instrument === "forward") {
          const f = this.pricing.forwardPrice(node, pos.days || 30, pos.workloadId);
          mark = f ? f.price : pos.avgPrice;
        } else if (pos.instrument === "option") {
          const o = this.pricing.optionPremium(node, pos.days || 7, 1.25, pos.workloadId);
          mark = o ? o.premium : pos.avgPrice;
        } else if (pos.instrument === "lease") {
          const l = this.pricing.leasePrice(node, pos.days || 30, pos.workloadId);
          mark = l ? l.hourly : pos.avgPrice;
        } else {
          const q = this.pricing.quote(node, { workloadId: pos.workloadId });
          mark = q.price != null ? q.price : pos.avgPrice;
        }
        const pv = mark * pos.qty;
        const pl = (mark - pos.avgPrice) * pos.qty;
        value += pv;
        unrealised += pl;
        rows.push({ ...pos, node, mark, value: pv, pnl: pl, pnlPct: (mark / pos.avgPrice - 1) * 100 });
      }
      return {
        rows,
        value,
        unrealised,
        cash: this.cash,
        equity: this.cash + value,
        realised: this.realised,
        totalReturn: ((this.cash + value) / this.startingCash - 1) * 100,
      };
    }

    /**
     * Aggregate capacity the user actually controls, in effective
     * TFLOP-hours per hour -- which is the number that matters to a
     * buyer, not the node count.
     */
    capacitySummary() {
      let tflops = 0;
      let magicNodes = 0;
      let carbonPerHour = 0;
      let costPerHour = 0;
      for (const pos of this.positions) {
        const node = this.fleet.get(pos.nodeId);
        if (!node || pos.instrument === "option") continue;
        tflops += node.effectiveTflops * Math.min(1, pos.qty * 0.125);
        if (node.hardware.magicCapable) magicNodes += pos.qty;
        const dc = this.energy.datacenters.find((d) => d.id === node.dcId);
        if (dc) {
          carbonPerHour += this.energy.hourlyCarbon(node, dc) * Math.min(1, pos.qty * 0.125);
          costPerHour += pos.avgPrice * pos.qty;
        }
      }
      return { tflops, magicNodes, carbonPerHour, costPerHour, positions: this.positions.length };
    }

    // ------------------------------------------------------------------
    // Background flow: other participants trading
    // ------------------------------------------------------------------

    /**
     * Simulated counterparty flow so the tape is alive. Fills are drawn
     * against real node quotes, so the printed prices are consistent
     * with the book rather than decorative.
     */
    ambientFlow(instrumentId = "spot") {
      const asks = this.book(instrumentId).asks;
      if (!asks.length) return null;
      if (this.rand() > 0.55) return null;
      const idx = Math.floor(Math.pow(this.rand(), 2) * Math.min(asks.length, 30));
      const ask = asks[idx];
      if (!ask) return null;
      const qty = Math.min(ask.qty, 1 + Math.floor(this.rand() * 6));
      if (qty <= 0) return null;
      const trade = {
        id: `T${String(TRADE_SEQ++).padStart(6, "0")}`,
        ts: Date.now(),
        instrument: instrumentId,
        nodeId: ask.nodeId,
        nodeAddress: ask.node ? ask.node.address : "-",
        hardware: ask.node ? ask.node.hardware.class : "-",
        dcId: ask.node ? ask.node.dcId : "-",
        qty,
        price: ask.price,
        cost: qty * ask.price,
        workloadId: "llm-train",
        side: this.rand() > 0.42 ? "buy" : "sell",
        maker: ask.maker,
        ambient: true,
      };
      this.trades.unshift(trade);
      if (this.trades.length > this.maxTrades) this.trades.pop();
      if (ask.node) {
        ask.node.utilisation = Math.min(1, Math.max(0,
          ask.node.utilisation + (trade.side === "buy" ? 0.125 : -0.125) * qty));
      }
      return trade;
    }

    /** VWAP over the recent tape, per instrument. */
    vwap(instrumentId = "spot", n = 60) {
      const rows = this.trades.filter((t) => t.instrument === instrumentId).slice(0, n);
      if (!rows.length) return null;
      const num = rows.reduce((a, t) => a + t.price * t.qty, 0);
      const den = rows.reduce((a, t) => a + t.qty, 0);
      return den > 0 ? num / den : null;
    }
  }

  const API = { Market, Order, sweepAsks, paretoFrontier };
  root.Market = Market;
  root.HolotradeMarket = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
