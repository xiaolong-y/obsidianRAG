#!/bin/bash

set -e

echo "🚀 Obsidian‑LLM Deployment Script"

# 1. Check Python 3.9+
python_ok=$(python3 -c "import sys; print(sys.version_info >= (3,9))")
if [[ "$python_ok" != "True" ]]; then
  echo "❌ Python 3.9+ required"
  exit 1
fi

# 2. Install dependencies
echo "📦 Installing Python dependencies"
pip install -r requirements.txt

# 3. Set up configuration
CONFIG_FILE="config.json"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "⚙️ Creating $CONFIG_FILE from template"
  cp config.example.json "$CONFIG_FILE"
fi

# 4. Initialize database (placeholder)
python3 - <<'PY'
from pathlib import Path
db_path = Path('obskg_cache.db')
db_path.touch()
print('📁 Initialized cache database at', db_path)
PY

# 5. Build initial index (placeholder)
echo "🔍 Building initial index (placeholder)"
python3 scripts/update_embeddings.py --help || echo "Indexing script not implemented in this example"

# 6. Install Obsidian plugin
echo "🔌 Installing Obsidian plugin"
OBSIDIAN_PLUGIN_DIR="$HOME/.obsidian/plugins/obsidian-llm-plugin"
mkdir -p "$OBSIDIAN_PLUGIN_DIR"
cp -r obsidian-llm-plugin/. "$OBSIDIAN_PLUGIN_DIR" || true

# 7. Set up automation (placeholder)
echo "⏱️ Setting up automation (placeholder)"

# 8. Start dashboard (instructions)
echo "📊 Dashboard available in dashboard/index.html"

# 9. Run tests
echo "🧪 Running test suite"
pytest tests/ -q

echo "✅ Deployment complete!"