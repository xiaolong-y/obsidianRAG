# Obsidian‑LLM Integration System

This repository contains a modular, production‑ready system for
integrating Obsidian vaults with large language models (LLMs).  It
combines research and entrepreneurial workflows (SPARK and LEAP), a
TypeScript plugin for Obsidian, a vector search backend, and a
monitoring dashboard.  The system is designed to run on macOS with
optional Dropbox synchronisation and automation.

## Features

* **Vault scanning and indexing** via `obskg.core.vault`.
* **Semantic embedding** generation using multiple providers, stored in
  a FAISS vector store (`obskg.core.vectorstore`).
* **Semantic and response caching** to minimise LLM calls
  (`obskg.core.cache`).
* **SPARK research workflow** for scanning, processing, analysing,
  refining and producing knowledge (`obskg.workflows.spark`).
* **LEAP entrepreneurial framework** for learning, experimenting,
  adapting and productising (`obskg.workflows.leap`).
* **Cost optimisation** and task routing between AI and humans.
* **Obsidian plugin** for seamless integration and UI commands.
* **Visual knowledge graphs** and dashboard for monitoring.

## Installation

1. Ensure Python 3.9+ is installed.
2. Clone this repository and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create `config.json` from `config.example.json` and set your vault
   paths and API keys.
4. Run the deployment script:

   ```bash
   bash deploy.sh
   ```

## End‑to‑End Workflow

Follow these steps to analyze and organize your Obsidian vault.

1) Configure
- Copy `config.example.json` → `config.json`, set `vault_paths`, API keys, and any optional Dropbox paths.

2) Index Your Vault (Embeddings + Metadata)
- Build or update your retrieval index (FAISS) and metadata store:
  ```bash
  python scripts/update_embeddings.py \
    --vault ~/Documents/Obsidian/MyVault \
    --index index.faiss --meta meta.sqlite3 \
    --openai-key $OPENAI_API_KEY
  ```
- Embeddings are cached to avoid reprocessing unchanged notes.

3) Analyze With SPARK (Research Workflow)
- Run the SPARK pipeline to scan, process, analyze, refine, and produce insights:
  ```bash
  python -c "import asyncio; from obskg.workflows.spark import SPARKPipeline;\
  print(asyncio.run(SPARKPipeline(vault_path='~/Documents/Obsidian/MyVault').run()))"
  ```
- Typical outputs include time‑to‑insight metrics and produced artifacts.

4) Organize With LEAP (Entrepreneurial Workflow)
- Identify gaps, experiments, and actions to improve your knowledge base:
  ```bash
  python -c "from obskg.workflows.leap import LEAPPipeline;\
  print(LEAPPipeline().run())"
  ```

5) Use the Obsidian Plugin (UI Commands)
- The plugin is copied by `deploy.sh` to `~/.obsidian/plugins/obsidian-llm-plugin`.
- In Obsidian → Settings → Community Plugins, enable “Obsidian LLM Plugin”.
- Commands: Process Inbox, Generate Synthesis, Create Visual Map, Batch Process.
  - Configure the plugin’s `API Endpoint` and `Default Model` in the plugin settings.

6) Monitor Progress (Dashboard)
- Open `dashboard/index.html` in a browser to view metrics panels.
- Replace placeholders with live data as you wire in your backend.

7) Automate Updates
- Schedule embeddings refresh (cron example, runs hourly):
  ```cron
  0 * * * * /usr/bin/python3 /path/to/repo/scripts/update_embeddings.py \
    --vault /Users/me/Documents/Obsidian/MyVault \
    --index /path/to/repo/index.faiss --meta /path/to/repo/meta.sqlite3 \
    --openai-key $OPENAI_API_KEY >> /tmp/obskg_cron.log 2>&1
  ```

## Development
## Development

* Python modules live under `obskg/`.  See `obskg/workflows/spark` and
  `obskg/workflows/leap` for workflow implementations.
* The Obsidian plugin lives under `obsidian-llm-plugin/`.  Build with
  TypeScript to generate `main.js`.
* The dashboard resides in `dashboard/`.  Serve `index.html` over
  HTTP or open it directly in a browser.

## Troubleshooting
- Python version: verify `python3 --version` is ≥ 3.9.
- Missing config: ensure `config.json` exists and contains correct vault paths.
- API errors: confirm `OPENAI_API_KEY` is set and not rate‑limited.
- Obsidian plugin not visible: confirm the folder exists under `~/.obsidian/plugins/` and restart Obsidian.

## License

This project is provided for educational purposes and is not intended
for commercial use.  See the `LICENSE` file for details.
