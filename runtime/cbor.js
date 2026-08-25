"use strict";

// Minimal deterministic CBOR for the delivery-receipt profile. It supports
// integers, byte/text strings, arrays, maps, booleans, null and explicit tags.
// Floating point and indefinite-length encodings are intentionally excluded.

class CborTag {
  constructor(tag, value) {
    if (!Number.isSafeInteger(tag) || tag < 0) throw new RangeError("CBOR tag must be a non-negative safe integer");
    this.tag = tag;
    this.value = value;
    Object.freeze(this);
  }
}

function head(major, value) {
  if (!Number.isSafeInteger(value) || value < 0) throw new RangeError("CBOR length must be a non-negative safe integer");
  if (value < 24) return Buffer.from([(major << 5) | value]);
  if (value <= 0xff) return Buffer.from([(major << 5) | 24, value]);
  if (value <= 0xffff) {
    const out = Buffer.alloc(3);
    out[0] = (major << 5) | 25;
    out.writeUInt16BE(value, 1);
    return out;
  }
  if (value <= 0xffffffff) {
    const out = Buffer.alloc(5);
    out[0] = (major << 5) | 26;
    out.writeUInt32BE(value, 1);
    return out;
  }
  const out = Buffer.alloc(9);
  out[0] = (major << 5) | 27;
  out.writeBigUInt64BE(BigInt(value), 1);
  return out;
}

function entries(value) {
  if (value instanceof Map) return [...value.entries()];
  return Object.keys(value).filter((key) => value[key] !== undefined).map((key) => [key, value[key]]);
}

function encode(value) {
  if (value === null) return Buffer.from([0xf6]);
  if (value === false) return Buffer.from([0xf4]);
  if (value === true) return Buffer.from([0xf5]);
  if (Buffer.isBuffer(value) || value instanceof Uint8Array) {
    const bytes = Buffer.from(value);
    return Buffer.concat([head(2, bytes.length), bytes]);
  }
  if (typeof value === "string") {
    const bytes = Buffer.from(value, "utf8");
    return Buffer.concat([head(3, bytes.length), bytes]);
  }
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value)) throw new TypeError("delivery CBOR accepts safe integers only");
    return value >= 0 ? head(0, value) : head(1, -1 - value);
  }
  if (Array.isArray(value)) {
    return Buffer.concat([head(4, value.length), ...value.map(encode)]);
  }
  if (value instanceof CborTag) {
    return Buffer.concat([head(6, value.tag), encode(value.value)]);
  }
  if (value && typeof value === "object") {
    const encoded = entries(value).map(([key, item]) => [encode(key), encode(item)]);
    encoded.sort((a, b) => a[0].length - b[0].length || Buffer.compare(a[0], b[0]));
    return Buffer.concat([head(5, encoded.length), ...encoded.flat()]);
  }
  throw new TypeError(`unsupported CBOR type: ${typeof value}`);
}

function decode(bytes) {
  const input = Buffer.from(bytes);
  let offset = 0;

  function uint(additional) {
    if (additional < 24) return additional;
    if (additional === 24) return input.readUInt8(offset++);
    if (additional === 25) {
      const value = input.readUInt16BE(offset);
      offset += 2;
      return value;
    }
    if (additional === 26) {
      const value = input.readUInt32BE(offset);
      offset += 4;
      return value;
    }
    if (additional === 27) {
      const value = input.readBigUInt64BE(offset);
      offset += 8;
      if (value > BigInt(Number.MAX_SAFE_INTEGER)) return value;
      return Number(value);
    }
    throw new Error("indefinite or reserved CBOR length is unsupported");
  }

  function item() {
    if (offset >= input.length) throw new Error("truncated CBOR");
    const initial = input[offset++];
    const major = initial >> 5;
    const additional = initial & 31;
    if (major === 7) {
      if (additional === 20) return false;
      if (additional === 21) return true;
      if (additional === 22) return null;
      throw new Error("unsupported CBOR simple or floating-point value");
    }
    const value = uint(additional);
    if (typeof value === "bigint" && major >= 2) throw new RangeError("CBOR collection is too large");
    if (major === 0) return value;
    if (major === 1) return typeof value === "bigint" ? -1n - value : -1 - value;
    if (major === 2 || major === 3) {
      const end = offset + value;
      if (end > input.length) throw new Error("truncated CBOR string");
      const result = input.subarray(offset, end);
      offset = end;
      return major === 2 ? Buffer.from(result) : result.toString("utf8");
    }
    if (major === 4) {
      const result = [];
      for (let i = 0; i < value; i++) result.push(item());
      return result;
    }
    if (major === 5) {
      const result = new Map();
      for (let i = 0; i < value; i++) result.set(item(), item());
      return result;
    }
    if (major === 6) return new CborTag(value, item());
    throw new Error(`unsupported CBOR major type ${major}`);
  }

  const result = item();
  if (offset !== input.length) throw new Error("trailing bytes after CBOR value");
  return result;
}

function mapToObject(value) {
  if (value instanceof CborTag) return { tag: value.tag, value: mapToObject(value.value) };
  if (value instanceof Map) {
    const out = Object.create(null);
    for (const [key, item] of value) out[String(key)] = mapToObject(item);
    return out;
  }
  if (Array.isArray(value)) return value.map(mapToObject);
  if (Buffer.isBuffer(value)) return Buffer.from(value);
  return value;
}

module.exports = { CborTag, encode, decode, mapToObject };
