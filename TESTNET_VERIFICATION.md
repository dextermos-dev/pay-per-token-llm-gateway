# 🧪 Stellar Testnet Verification Guide & Audit Evidence

**Repository:** `https://github.com/mallonepay/pay-per-token-llm-gateway`  
**Network:** Stellar Testnet (`Test SDF Network ; September 2015`)  
**Auditor / Reviewer Guide:** Evidence-based ecosystem grant review

---

## 1. Testnet Deployment Overview

All smart contracts are compiled under the Soroban SDK (Rust target `wasm32-unknown-unknown`) and deployed to Stellar Testnet. Reviewers can independently verify each contract state, source bytecode, and recent invocations using the Stellar Expert testnet explorer or Soroban RPC.

| Contract            | Testnet Contract ID                                        | Explorer Link                                                                                                                       | Purpose                                                                  |
| :------------------ | :--------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------- |
| **PaymentVerifier** | `CDHGI3A2BXRC5AQDPWEEXUDQMDXTDZYBCLJZWSE5XZKMVEGJ5LLHA4CZ` | [View on Stellar Expert](https://stellar.expert/explorer/testnet/contract/CDHGI3A2BXRC5AQDPWEEXUDQMDXTDZYBCLJZWSE5XZKMVEGJ5LLHA4CZ) | On-chain single-use replay protection and payment recording              |
| **CreditEscrow**    | `CCE7AWVXPO57W5KDONOPMHDV4S5UBUBMHNJVSAVPL7AZGMD4WQN6WVAP` | [View on Stellar Expert](https://stellar.expert/explorer/testnet/contract/CCE7AWVXPO57W5KDONOPMHDV4S5UBUBMHNJVSAVPL7AZGMD4WQN6WVAP) | Prepaid credit escrow, metered per-token draws, and surplus refunds      |
| **Multisig**        | `CDMBVMMNJVAJVAV3T2TAL2TAACGTKYUS45RXNLCYKYUC3VGHBI66NWAA` | [View on Stellar Expert](https://stellar.expert/explorer/testnet/contract/CDMBVMMNJVAJVAV3T2TAL2TAACGTKYUS45RXNLCYKYUC3VGHBI66NWAA) | M-of-N governance for provider revenue distribution and treasury payouts |

### Network RPC Endpoints

- **Horizon URL:** `https://horizon-testnet.stellar.org`
- **Soroban RPC URL:** `https://soroban-testnet.stellar.org`
- **Friendbot Faucet:** `https://friendbot.stellar.org`
- **Network Passphrase:** `Test SDF Network ; September 2015`

---

## 2. On-Chain Verification Evidence (Live Testnet Records)

The following real transactions were executed on Stellar Testnet and recorded in [`docs/evidence/testnet-journey.json`](./docs/evidence/testnet-journey.json). Reviewers can verify each hash directly on the blockchain:

### Trustline & Token Minting

- **Payer USDC Trustline Tx:**  
  [`48fc2874d033e79d3a77cc7e9f79a9d4372381183f668db6e93a88106954ab6e`](https://stellar.expert/explorer/testnet/tx/48fc2874d033e79d3a77cc7e9f79a9d4372381183f668db6e93a88106954ab6e)
- **Receiver USDC Trustline Tx:**  
  [`f8f7bd4f1ada7def942f8946957da0580f068ab57c38161d58c48766a2f6fd75`](https://stellar.expert/explorer/testnet/tx/f8f7bd4f1ada7def942f8946957da0580f068ab57c38161d58c48766a2f6fd75)
- **USDC Minting Tx:**  
  [`861c512e135561b6b9ccbcdfa910af90af26ddfdc01f8ec7208cbfe827eed951`](https://stellar.expert/explorer/testnet/tx/861c512e135561b6b9ccbcdfa910af90af26ddfdc01f8ec7208cbfe827eed951)

### Live Payment Verification Flow

- **Verified Payment Tx Hash:**  
  [`fbf2f72d0d6db5e70c12fba4d50a7299e1f1b259dad0d0e5fd15b140e978c48a`](https://stellar.expert/explorer/testnet/tx/fbf2f72d0d6db5e70c12fba4d50a7299e1f1b259dad0d0e5fd15b140e978c48a)
- **Ledger Number:** `4690982`
- **Payment Amount:** `0.1000000 USDC` (`1,000,000` stroops)
- **Recipient:** `GCTDL5LW5IUVCFAFNN2ZI4362SZYRT4CB2BLM3D7HRUD54CS35WCWJOW`
- **Quote Memo:** `b082ed6d27ef46e2bc2faac5`
- **Response Header Delivered:** `X-Payment-Receipt: {"id":"4331e9d0...","quoteId":"b082ed6d...","txHash":"fbf2f72d...","status":"confirmed"}`

---

## 3. How to Reproduce the Full Testnet Flow

The repository includes deterministic testnet runner scripts that boot the gateway and drive the complete protocol against Stellar Testnet.

### Method A: Automated Testnet Journey

```bash
# 1. Ensure dependencies are installed
pnpm install

# 2. Run the automated live Testnet journey
bash scripts/testnet-journey.sh
```

**What the script asserts:**

1. Fills three fresh accounts via Friendbot (`ISSUER`, `PAYER`, `RECEIVER`).
2. Establishes USDC trustlines and mints testnet USDC to `PAYER`.
3. Issues an unpaid request to the gateway, asserting `402 Payment Required` and extracting the payment quote.
4. Uses `@x402/wallet` to construct, sign, and submit the on-chain payment with the quote's memo.
5. Retries the request with `X-Payment-Hash: <txHash>`, asserting `200 OK` and validating the `X-Payment-Receipt` header.
6. Replays the identical `X-Payment-Hash`, asserting `402 Payment Required: This payment has already been used`.
7. Sends an unconfirmed / fake hash, asserting `402 Payment Required: Transaction not found`.

---

### Method B: Manual cURL Walkthrough

#### Step 1: Request an AI completion without payment

```bash
curl -i -X POST http://localhost:3000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Explain x402 on Stellar"}]
  }'
```

**Expected Response (`HTTP 402`):**

```json
{
  "status": 402,
  "error": "Payment Required",
  "quote": {
    "id": "e919da35-7d36-4dd9-b700-7a736442773f",
    "route": "/v1/chat/completions",
    "pricingModel": "flat",
    "amount": "1000000",
    "asset": "USDC",
    "assetIssuer": "GBZEPCLP4KEPOQH5NC5R72BDRERNVAOUU63WQTY6ZIE66IL6CY3YIX3H",
    "paymentAddress": "GA5ZSE6VKPVFLEXMWJQBGHE4FJHKQIFSJMLQ7H4VFQB4UHLEH5IOVK3F",
    "memo": "e919da357d36",
    "network": "testnet",
    "issuedAt": 1789478492,
    "expiresAt": 1789478792,
    "statusUrl": "http://localhost:3000/api/v1/payments/e919da35.../status"
  }
}
```

#### Step 2: Pay on Stellar Testnet

Submit an on-chain payment of `1000000` stroops (`0.1000000 USDC`) to `paymentAddress` carrying `memo` using `@x402/sdk`, `@x402/wallet`, or the Stellar Laboratory. Obtain the transaction hash `TX_HASH`.

#### Step 3: Retry with `X-Payment-Hash`

```bash
curl -i -X POST http://localhost:3000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Payment-Hash: $TX_HASH" \
  -H "X-Quote-Id: e919da35-7d36-4dd9-b700-7a736442773f" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Explain x402 on Stellar"}]
  }'
```

**Expected Response (`HTTP 200`):**

- Header: `X-Payment-Receipt: {"id":"...","quoteId":"...","txHash":"...","status":"confirmed"}`
- Header: `X-Request-Trace-Id: <w3c-trace-id>`
- Body: OpenAI-compatible response.

---

## 4. Security & Failure-Mode Verification Matrix

The gateway and contract suite are hardened against adversarial edge cases. The following behaviors are verified by automated tests in `apps/gateway/src/e2e/x402-flow.e2e-spec.ts` and contract unit tests:

| Attack / Failure Scenario         | Behavior                                                                                                                                                     | Test Verification                                                     |
| :-------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------- |
| **Double Spend / Replay Attack**  | The first claim transitions the hash to consumed. Subsequent requests fail with `402: already been used`.                                                    | Tested in `x402-flow.e2e-spec.ts` & `PaymentVerifier` contract        |
| **Cross-Route Replay Attack**     | A payment verified on Route A cannot be re-used to call Route B.                                                                                             | Tested in `Cross-Route Replay Protection` e2e suite                   |
| **Front-running / Memo Spoofing** | Payments carrying a specific quote memo bind to that quote ID and originating caller IP.                                                                     | Verified in `x402-core` quote binding tests                           |
| **Historical Hash Recycling**     | Quotes enforce a lower-bound issuance window (`issuedAt`). Payments submitted before quote issuance are rejected.                                            | Tested in `verify-stellar-payment.spec.ts`                            |
| **Upstream LLM 502 / Timeout**    | When an upstream AI provider fails, the caller's payment is marked `upstream_failed` and unlocked in Redis for a free retry rather than burning funds.       | Tested in `x402-flow.e2e-spec.ts` (`Upstream LLM Failure & Recovery`) |
| **Concurrent Race Condition**     | Simultaneous requests racing with the same payment hash are serialized by Redis SET NX and PostgreSQL unique index; exactly one wins (200), one loses (402). | Tested in `x402-flow.e2e-spec.ts` (`race condition defense`)          |
| **Propagating / Unindexed Tx**    | If a request arrives before Horizon indexes the transaction, the claim reservation is released so retry upon ledger close succeeds with 200.                 | Tested in `x402-flow.e2e-spec.ts` (`retry on unconfirmed tx`)         |
| **Underpayment / Debt Gate**      | In metered per-token routes, if a user's prompt exceeds the deposit, outstanding debt is recorded. Future requests are gated until topped up.                | Tested in `Underpayment Debt Gate` e2e suite                          |
| **Soroban RPC / Horizon Outage**  | Network outages fail closed with a structured 402/502 rather than hanging the gateway.                                                                       | Tested via `AbortSignal.timeout` unit tests                           |

---

## 5. Dashboard Data & Seed State Disclosure

- **Real vs Simulated Data:** The gateway records live analytics events into PostgreSQL (`Payment`, `AnalyticsEvent`, `UnderpaymentDebt`, `AuditLog`, `InAppNotification`).
- When running in development mode without active traffic, the dashboard displays seed metrics marked as simulated in test environments. In production or testnet staging connected to PostgreSQL, all charts reflect actual SQL time-series aggregates computed via PostgreSQL bucketing.
