"use strict";

// W33 TPM credential-enrollment ceremony using the real tpm2-tools protocol.
//
// Production path:
//   tpm2_makecredential (off-TPM, TCTI none)
//   tpm2_startauthsession --policy-session
//   tpm2_policysecret -c endorsement
//   tpm2_activatecredential -c AK -C EK
//   compare recovered secret in constant time
//   tpm2_flushcontext
//
// A successful ceremony is stronger than AK/EK X.509 provenance alone: it
// demonstrates that the credentialed AK can activate a secret protected for the
// credential key/EK under the TPM authorization policy.  The signed transcript
// is evidence of this executed ceremony; it is not itself a TPM quote.

const crypto = require("node:crypto");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

function sha256Bytes(bytes) {
  return `sha256:${crypto.createHash("sha256").update(bytes).digest("hex")}`;
}
function sha256File(p) { return sha256Bytes(fs.readFileSync(p)); }
function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function defaultRunner(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd,
    env: options.env || process.env,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
  return { status: result.status, stdout: result.stdout || "", stderr: result.stderr || "", error: result.error || null };
}
function runChecked(runner, command, args, cwd, trace) {
  const result = runner(command, args, { cwd });
  trace.push({ command, args: [...args], status: result.status, stdout: result.stdout || "", stderr: result.stderr || "" });
  if (result.error || result.status !== 0) {
    const err = new Error(`${command} failed: ${result.error ? result.error.message : result.stderr}`);
    err.command = command; err.args = args; err.result = result; throw err;
  }
  return result;
}
function validatePath(p, name) {
  if (typeof p !== "string" || !p.length) throw new TypeError(`${name} path required`);
  return path.resolve(p);
}
function signTranscript(body, privateKey, keyId = "w33-enrollment") {
  if (!privateKey) return null;
  const key = privateKey.type === "private" ? privateKey : crypto.createPrivateKey(privateKey);
  if (key.asymmetricKeyType !== "ed25519") throw new TypeError("enrollment transcript signing key must be Ed25519");
  const bytes = Buffer.from(stable(body));
  const signature = crypto.sign(null, bytes, key);
  return Object.freeze({
    schema: "holotrade.w33-tpm-activation-receipt.v1",
    keyId,
    body,
    bodyDigest: sha256Bytes(bytes),
    signatureBase64: signature.toString("base64"),
    publicKeySpkiBase64: crypto.createPublicKey(key).export({ type: "spki", format: "der" }).toString("base64"),
  });
}
function verifyTranscriptReceipt(receipt, trustedPublicKey) {
  if (!receipt || receipt.schema !== "holotrade.w33-tpm-activation-receipt.v1" || !trustedPublicKey) return false;
  try {
    const bytes = Buffer.from(stable(receipt.body));
    if (sha256Bytes(bytes) !== receipt.bodyDigest) return false;
    return crypto.verify(null, bytes, trustedPublicKey, Buffer.from(receipt.signatureBase64, "base64"));
  } catch (_) { return false; }
}

function executeCredentialActivation({
  ekPublicPath,
  akNamePath,
  akContext,
  ekContext,
  akAuth = null,
  tcti = null,
  secret = null,
  runner = defaultRunner,
  enrollmentSigningKey = null,
  enrollmentKeyId = "w33-enrollment",
  workDir = null,
} = {}) {
  const ekPub = validatePath(ekPublicPath, "EK public");
  const akName = validatePath(akNamePath, "AK name");
  if (!fs.existsSync(ekPub) || !fs.existsSync(akName)) throw new Error("EK public and AK name files must exist");
  if (!akContext || !ekContext) throw new TypeError("AK and EK TPM contexts/handles are required");
  const ownTmp = !workDir;
  const cwd = workDir ? path.resolve(workDir) : fs.mkdtempSync(path.join(os.tmpdir(), "w33-tpm-activate-"));
  fs.mkdirSync(cwd, { recursive: true });
  const trace = [];
  const secretBytes = secret ? Buffer.from(secret) : crypto.randomBytes(32);
  if (secretBytes.length < 16) throw new RangeError("credential activation secret must be at least 128 bits");
  const secretPath = path.join(cwd, "secret.bin");
  const credPath = path.join(cwd, "credential.blob");
  const recoveredPath = path.join(cwd, "recovered.bin");
  const sessionPath = path.join(cwd, "endorsement-policy.ctx");
  fs.writeFileSync(secretPath, secretBytes, { mode: 0o600 });
  const tctiArgs = tcti ? ["-T", String(tcti)] : [];
  let activated = false;
  try {
    runChecked(runner, "tpm2_makecredential", ["-Q", "-T", "none", "-u", ekPub, "-s", secretPath, "-n", akName, "-o", credPath], cwd, trace);
    runChecked(runner, "tpm2_startauthsession", [...tctiArgs, "--policy-session", "-S", sessionPath], cwd, trace);
    runChecked(runner, "tpm2_policysecret", [...tctiArgs, "-S", sessionPath, "-c", "endorsement"], cwd, trace);
    const activateArgs = [...tctiArgs, "-Q", "-c", String(akContext), "-C", String(ekContext), "-i", credPath, "-o", recoveredPath, "-P", `session:${sessionPath}`];
    if (akAuth) activateArgs.push("-p", String(akAuth));
    runChecked(runner, "tpm2_activatecredential", activateArgs, cwd, trace);
    if (!fs.existsSync(recoveredPath)) throw new Error("ActivateCredential did not produce recovered secret");
    const recovered = fs.readFileSync(recoveredPath);
    activated = recovered.length === secretBytes.length && crypto.timingSafeEqual(recovered, secretBytes);
    if (!activated) throw new Error("ActivateCredential returned the wrong secret");
  } finally {
    try {
      if (fs.existsSync(sessionPath)) runChecked(runner, "tpm2_flushcontext", [...tctiArgs, sessionPath], cwd, trace);
    } catch (_) { /* transcript records primary outcome; cleanup failure is non-authorizing */ }
  }
  const body = Object.freeze({
    schema: "holotrade.w33-tpm-credential-activation.v1",
    activated,
    ekPublicDigest: sha256File(ekPub),
    akNameDigest: sha256File(akName),
    secretDigest: sha256Bytes(secretBytes),
    recoveredSecretDigest: sha256File(recoveredPath),
    credentialBlobDigest: sha256File(credPath),
    akContext: String(akContext),
    ekContext: String(ekContext),
    tcti: tcti || "DEFAULT",
    commands: trace.map(x => ({ command: x.command, args: x.args, status: x.status })),
    proves: "AK_ACTIVATED_CREDENTIAL_PROTECTED_TO_EK_CONTEXT",
    hardwareBacked: runner === defaultRunner,
    honestyBoundary: runner === defaultRunner
      ? "The ceremony invoked tpm2-tools against the configured TPM/TCTI and recovered the registrar secret. TPM key provenance still depends on separately authenticated EK/AK material."
      : "A custom command runner was supplied; this result is protocol-fixture evidence and must not be labeled hardware-backed.",
  });
  const receipt = signTranscript(body, enrollmentSigningKey, enrollmentKeyId);
  if (ownTmp) {
    for (const p of [secretPath, recoveredPath]) { try { fs.rmSync(p, { force: true }); } catch (_) {} }
  }
  return Object.freeze({ ok: activated, code: activated ? "TPM_CREDENTIAL_ACTIVATION_VERIFIED" : "TPM_CREDENTIAL_ACTIVATION_FAILED", body, receipt });
}

module.exports = { sha256Bytes, stable, defaultRunner, signTranscript, verifyTranscriptReceipt, executeCredentialActivation };
