# AscentIntegrity

Cybersecurity-focused evidence integrity platform built with React + TypeScript, FastAPI, PostgreSQL, SHA-256, and a Solidity blockchain anchor.

> Integrity verification is not factual-truth certification. A matching digest only shows that bytes match a recorded digest; it does not prove the contents are true, the author is genuine, the collection was lawful, or that evidence is admissible.

## Project status
Initial scaffold. The application and tests must be run and reviewed before operational use. Blockchain anchoring remains incomplete until a contract is deployed and configured. Do not upload real sensitive evidence to a public blockchain.

## Planned stack
- Frontend: React, TypeScript, Vite
- Backend: FastAPI, SQLAlchemy, Alembic
- Database: local PostgreSQL
- Private evidence storage: local development storage outside the public web root
- Integrity: SHA-256, versioned evidence records, audit events
- Blockchain: Solidity contract and Hardhat local development network
- CI: backend, frontend and contract checks

## Local development
See the project files and `.env.example`. Start PostgreSQL with `docker compose up -d db`, configure `.env`, install backend dependencies, run `alembic upgrade head`, then start FastAPI and the Vite frontend.

## Security caveats
This is a development foundation, not a certified forensic product. Production requires case-level authorization, strong identity management, protected object storage, key management, independent audit export, malware scanning, backups, legal review, and security testing.