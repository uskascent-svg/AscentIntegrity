# AscentIntegrity

Cybersecurity-focused evidence integrity platform: secure evidence intake, SHA-256 verification, version records, audit events and optional EVM blockchain digest anchoring.

> **Integrity is not factual truth.** A matching hash means bytes match a previously recorded digest. It does not prove document contents are true, the author is genuine, collection was lawful, or evidence is admissible.

## Current implementation

- React + TypeScript + Vite dashboard with API-backed evidence upload, register and verification results.
- FastAPI REST API with development registration, password hashing, bearer tokens and role-aware audit access.
- PostgreSQL models and Alembic initial migration for users, evidence, versions, audit events and blockchain anchors.
- SHA-256 digest calculation at intake and re-hashing of private stored files during verification.
- Solidity `EvidenceAnchor` contract and Web3 JSON-RPC integration. Anchoring uses a transaction, waits for a receipt, then reads the contract back.
- Certificate endpoint refuses issuance unless stored bytes match the intake digest and the configured chain confirms the matching digest.
- Initial backend, frontend and contract CI jobs.

This is a development scaffold, not a production-ready forensic platform. Review limitations below before using it with real evidence.

## Run locally

Requirements: Docker Compose, Python 3.11+, Node.js 20+.

1. Clone the repository and create the environment file:
   ```bash
   cp .env.example .env
   ```
   Replace the database password and `SECRET_KEY` with private values.
2. Start PostgreSQL:
   ```bash
   docker compose up -d db
   ```
3. Install and start the API:
   ```bash
   cd backend
   python -m venv .venv
   # Windows: .venv\\Scripts\\activate
   # macOS/Linux: source .venv/bin/activate
   pip install -e ".[dev]"
   alembic upgrade head
   uvicorn app.main:app --reload
   ```
4. In a second terminal, start the web UI:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
5. Open http://localhost:5173 for the UI and http://127.0.0.1:8000/docs for API documentation.
6. Create a development account using `POST /api/v1/auth/register` in the API docs, then sign in in the UI.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | API liveness |
| POST | `/api/v1/auth/register` | Development-only account creation |
| POST | `/api/v1/auth/token` | Issue bearer token |
| GET | `/api/v1/auth/me` | Current authenticated user |
| POST | `/api/v1/evidence` | Upload evidence; calculate SHA-256 |
| GET | `/api/v1/evidence` | List evidence records |
| GET | `/api/v1/evidence/{id}` | Read evidence metadata |
| POST | `/api/v1/evidence/{id}/verify` | Re-hash stored object and check configured anchor |
| POST | `/api/v1/evidence/{id}/anchor` | Submit digest to configured blockchain contract |
| GET | `/api/v1/evidence/{id}/certificate` | Issue integrity certificate only when checks pass |
| GET | `/api/v1/audit` | List audit events for analysts/admins |

## Local blockchain setup

The contract lives in `contracts/contracts/EvidenceAnchor.sol`. Run a local node and deploy the contract using Hardhat before enabling anchoring. The API expects all three settings in `.env`:

- `BLOCKCHAIN_RPC_URL`: local JSON-RPC endpoint, usually `http://127.0.0.1:8545`.
- `BLOCKCHAIN_CONTRACT_ADDRESS`: deployed contract address.
- `BLOCKCHAIN_PRIVATE_KEY`: development-only funded signer key. Never use a real wallet key in source control or production env files.

Contract project commands:

```bash
cd contracts
npm install
npx hardhat compile
npx hardhat test
```

Run a local node with `npx hardhat node`. Deploy the contract to that local network with a Hardhat deployment script before using `POST /api/v1/evidence/{id}/anchor`. The contract stores digests and opaque IDs only; do not put personal data or evidence contents on-chain.

## Security and known limitations

- Development registration must be disabled outside local development.
- This initial release does **not** implement case-level tenant memberships; authenticated users can list/read each other's evidence metadata. Do not use real sensitive evidence until authorization is implemented and tested.
- Local filesystem storage is not immutable storage. Use private versioned object storage/object lock and independent backups in production.
- JWT signing secret and blockchain signer are development settings; production requires managed secrets, OIDC/MFA, key rotation and least privilege.
- File upload scanning, isolated parser workers, signed manifests, ML-DSA-65 signing, rate limiting, robust key management, custody transfer workflows, and external tamper-evident audit export remain future work.
- Blockchain outage, missing configuration or read-back errors must remain incomplete/unavailable—not be represented as verified.
- A blockchain anchor confirms a digest was recorded on that chain. It does not independently prove who originally created a document or whether the document's claims are true.

## Test and CI

Backend tests: `cd backend && pytest -q`. Contract tests: `cd contracts && npm test`. CI is configured in `.github/workflows/ci.yml`. A green build is necessary but does not replace a security review or end-to-end tamper testing.
