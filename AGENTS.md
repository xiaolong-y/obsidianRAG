# Repository Guidelines

## Project Structure & Modules
- `obskg/`: Python library (vault scanning, embeddings, vectorstore, workflows).
- `scripts/`: CLI utilities (e.g., `update_embeddings.py`).
- `tests/`: Pytest suite for SPARK/LEAP workflows.
- `obsidian-llm-plugin/`: TypeScript Obsidian plugin (`src/main.ts`, builds to `main.js`).
- `dashboard/`: Static monitoring UI (`index.html`, `js/dashboard.js`).
- Root files: `requirements.txt`, `deploy.sh`, `config.example.json`.

## Build, Test, Run
- Install deps: `pip install -r requirements.txt`.
- Run tests: `pytest -q tests/`.
- Deploy locally: `bash deploy.sh` (installs deps, seeds config, copies plugin, runs tests).
- Update embeddings example:
  `python scripts/update_embeddings.py --vault ~/Vault --index index.faiss --meta meta.sqlite3 --openai-key $OPENAI_API_KEY`.
- Plugin build (from `obsidian-llm-plugin/`): `npm install && npm run build`.
- Dashboard: open `dashboard/index.html` in a browser.

## Coding Style & Naming
- Python: PEP 8, 4‑space indents, type hints where practical.
  - Modules/functions: `snake_case`; classes: `CamelCase`.
  - Keep `obskg` modules focused and import‑light; prefer small, pure functions.
- TypeScript: standard TS, keep `main.ts` lean and register commands via Obsidian API.
- Tests: files named `test_*.py`, focused, deterministic.

## Testing Guidelines
- Framework: `pytest`.
- Add unit tests alongside features; cover SPARK/LEAP happy paths and basic error handling.
- Run locally with `pytest -q`; prefer fixtures and tmp paths for vaults (see `tests/test_complete_system.py`).

## Commit & PR Guidelines
- Commits: imperative, concise subject; scope by area (e.g., `obskg/vectorstore:`).
  - Example: `obskg/cache: add TTL to embedding cache`.
- PRs: include summary, rationale, screenshots for dashboard/plugin changes, and steps to test.
  - Link related issues; ensure `pytest` passes and `npm run build` (plugin) if touched.

## Security & Config
- Copy `config.example.json` to `config.json` and set API keys and vault paths. Do not commit secrets.
- Dropbox and automation are optional; validate paths before running `deploy.sh`.
