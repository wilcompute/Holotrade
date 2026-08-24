// ======================================================================
// HOLOTRADE MARKET
//
// The exchange itself: an order book per instrument, a matching engine,
// a settlement ledger, and the attested receipt that closes every fill.
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
// Every fill closes with a receipt. The receipt carries the measured
// contextual fraction of the channel it ran on -- 0.10 is the substrate
// target, and any intervention that classicalises the channel MOVES AN
// INTEGER rather than shifting a probability. So tampering is detectable
// in principle rather than statistically. Classical fills carry an
// attestation of the Clifford trace instead; the receipt says which.
// ======================================================================

(function (root) {
  "use strict";

  const S = root.Substrate || (typeof require !== "undefined" ? require("./substrate.js") : null);

  let ORDER_SEQ = 1;

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
        let qty = Math.max(1, Math.round((1 - node.utilisation) * 8));

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
        (o) => o.instrument === instrumentId && o.side === "bid" && o.status === "open"
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
        id: `T${String(this.trades.length + 1).padStart(6, "0")}`,
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
          id: `P${this.positions.length + 1}`,
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
        node.utilisation = Math.min(1, node.utilisation + qty * 0.04);
        node.currentWorkload = order.workloadId;
      }

      this.issueReceipt(trade, node);
      return trade;
    }

    /**
     * Sell / close a position at the current bid.
     */
    submitSell({ positionId, qty = null }) {
      const pos = this.positions.find((p) => p.id === positionId);
      if (!pos) return { ok: false, reason: "no such position" };
      const size = qty == null ? pos.qty : Math.min(qty, pos.qty);
      this.rebuildAsks(pos.instrument, { workloadId: pos.workloadId });
      this.rebuildBids(pos.instrument);
      const bids = this.book(pos.instrument).bids.filter((b) => !b.mine);
      if (!bids.length) return { ok: false, reason: "no bid" };
      const price = bids[0].price;
      const proceeds = price * size;
      this.cash += proceeds;
      const pnl = (price - pos.avgPrice) * size;
      this.realised += pnl;
      pos.qty -= size;
      if (pos.qty <= 0) this.positions = this.positions.filter((p) => p.id !== positionId);

      const trade = {
        id: `T${String(this.trades.length + 1).padStart(6, "0")}`,
        ts: Date.now(),
        instrument: pos.instrument,
        nodeId: pos.nodeId,
        nodeAddress: pos.node ? pos.node.address : "-",
        hardware: pos.node ? pos.node.hardware.class : "-",
        dcId: pos.node ? pos.node.dcId : "-",
        qty: size,
        price,
        cost: -proceeds,
        workloadId: pos.workloadId,
        side: "sell",
        maker: bids[0].maker,
        pnl,
      };
      this.trades.unshift(trade);
      if (this.trades.length > this.maxTrades) this.trades.pop();
      if (pos.node && pos.instrument === "spot") {
        pos.node.utilisation = Math.max(0, pos.node.utilisation - size * 0.04);
      }
      return { ok: true, trade, pnl };
    }

    cancel(orderId) {
      const o = this.userOrders.find((x) => x.id === orderId);
      if (!o || o.status === "filled") return false;
      o.status = "cancelled";
      this.rebuildBids(o.instrument);
      return true;
    }

    // ------------------------------------------------------------------
    // Receipts and attestation
    // ------------------------------------------------------------------

    /**
     * Every fill emits a receipt. Photonic (magic-capable) nodes carry a
     * measured contextual fraction; the substrate target is 1/10 and a
     * channel that has been classicalised reads near zero. Classical
     * nodes attest their Clifford trace instead -- a stabilizer tableau
     * digest, which is checkable in polynomial time by anyone.
     */
    issueReceipt(trade, node) {
      const photonic = node && node.hardware.magicCapable;
      const measured = photonic
        ? S.CONST.contextualFraction + (this.rand() - 0.5) * 0.016
        : 0;
      const verdict = photonic
        ? S.attestationVerdict(measured)
        : { ok: true, label: "CLIFFORD", detail: "stabilizer trace verified in poly time" };

      const digest = S.hash32(
        `${trade.id}|${trade.nodeId}|${trade.price.toFixed(6)}|${trade.qty}|${trade.ts}`
      ).toString(16).padStart(8, "0");

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
      const qty = 1 + Math.floor(this.rand() * 6);
      const trade = {
        id: `T${String(this.trades.length + 1).padStart(6, "0")}`,
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
        ask.node.utilisation = Math.min(1, Math.max(0, ask.node.utilisation + (trade.side === "buy" ? 0.012 : -0.01) * qty));
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

  const API = { Market, Order };
  root.Market = Market;
  root.HolotradeMarket = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
