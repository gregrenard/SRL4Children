# 🚀 SRL4Children - Quick Start Guide

Get started with SRL4Children in less than 10 minutes.

---

## 📋 Prerequisites

- **Python 3.8+** installed on your machine
- **Ollama** (optional but recommended for local execution)
- **OpenAI API Key** (for guardrail generation)

---

## ⚡ Quick Installation

### 1. Clone the project

```bash
git clone <your-repo-url>
cd SRL4Children
```

### 2. Create Python environment

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
# Copy the template
cp .env.template .env

# Edit the .env file with nano (recommended)
nano .env
```

**In the `.env` file, add at minimum:**
```env
OPENAI_API_KEY=your-openai-api-key-here
```

To get an OpenAI API key: https://platform.openai.com/api-keys

**Save**: `Ctrl+O` then `Enter`, then `Ctrl+X` to exit nano.

---

## 🎯 Basic Usage

### Option A: Run a benchmark

```bash
python start_SRL4Children.py
```

The script reads all configuration from `config.yml` (no interactive prompts):
- **Test mode**: attack / defensive (default: attack)
- **Execution mode**: phased / inline (default: phased)
- **Test prompts limit**: N for quick test, -1 for all prompts (default: 3)
- **Ollama preset**: local / ssh_tunnel / custom (default: local)

**Quick test** (default: 3 prompts, ~5 minutes):
```bash
# Default config.yml settings
python start_SRL4Children.py
```

**Full benchmark** (all prompts, ~30 minutes):
```bash
# Edit config.yml first:
# execution:
#   test_prompts_limit: -1  # -1 = all prompts
python start_SRL4Children.py
```

**Results**: Check the `outputs/` folder for generated JSON files.

### Option B: Generate guardrails for an existing record

```bash
python tools/generate_guardrails.py \
  --record outputs/YYYY-MM-DD__attack__model/record_X.json \
  --provider openai \
  --model gpt-5-mini
```

**Useful options:**
- `--skip-passing`: Ignore criteria with score = 0 (already compliant)
- `--debug`: Show detailed process information
- `--max-rules 3`: Limit to 3 guardrails per criterion

**Results**: Guardrails are saved in `outputs/.../guardrails/guardrails_X.json`

---

## 🔧 Ollama Configuration (optional)

If you want to use local models (Qwen, Phi, Gemma, etc.):

### 1. Install Ollama

Follow instructions: https://ollama.ai/

### 2. Download a model

```bash
ollama pull qwen3:8b
ollama pull phi4:14b
ollama pull gemma3:27b
```

### 3. Verify Ollama server is running

```bash
curl http://localhost:11434/api/tags
```

If you get a list of models, you're good!

### 4. Configure in config.yml

The `config.yml` file already contains default presets. You can adjust:
- Judge models (qwen3:8b, phi4:14b, etc.)
- Hyperparameters (temperature, top_p, etc.)
- Criteria weights

---

## 📊 Visualization Interface

To explore results interactively:

### 1. Open the web interface

```bash
cd review
# Open index.html in your browser
open index.html  # macOS
# or double-click the file
```

### 2. Load a benchmark folder

- Click **"Select the outputs folder"**
- Choose a subfolder in `outputs/`
- Explore prompts, scores, generated guardrails

**Features:**
- 🔍 Keyword search
- 📈 Radar charts of scores
- 📝 Before/After guardrails comparison
- 📊 CSV export

---

## 📖 File Structure

```
SRL4Children/
├── assets/                    # Criteria and Design Principles
│   ├── criteria/              # Evaluation prompts by category
│   └── personas.json          # Configurations by age band
├── data/                      # Test datasets
├── outputs/                   # Benchmark results (JSON)
├── review/                    # Web visualization interface
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── src/                       # Main source code
│   ├── connectors/            # LLM clients (OpenAI, Anthropic, Ollama, etc.)
│   ├── core/                  # Judgment system and weighting
│   └── utils/                 # Utilities
├── tools/                     # Guardrail generation tools
├── config.yml                 # Main configuration (⚙️ all settings here)
├── start_SRL4Children.py      # Benchmark execution script
└── requirements.txt           # Python dependencies
```

---

## 🎓 Next Steps

1. **Read the full README**: `README.md`
2. **Understand Design Principles**: `assets/Design_Principles.md`
3. **Create your own criteria**: `documentation/HOWTO_Create_Criteria.md`
4. **Check presentations**: `documentation/SRL4Children - Presentation v3_EN.pdf`

---

## 🆘 Help and Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution**: Verify your virtual environment is activated:
```bash
source venv/bin/activate  # macOS/Linux
```

### Issue: "OPENAI_API_KEY environment variable is not set"
**Solution**: Verify your `.env` file contains your API key.

### Issue: Ollama not responding
**Solution**:
```bash
# Start Ollama
ollama serve

# In another terminal, test
ollama list
```

### Issue: Guardrails not generating
**Solution**: Verify you have records with scores > 0:
```bash
python tools/generate_guardrails.py \
  --record outputs/.../record_X.json \
  --debug
```

---

## 📞 Support

For questions or issues, consult:
- 📚 **Complete documentation**: `README.md`
- 🔧 **Troubleshooting guide**: `documentation/TROUBLESHOOTING.md` (if available)
- 🌐 **Website**: https://www.everyone.ai

---

**SRL4Children v1.1.0** - Safety Readiness Level for Children
*Designed by Freedom.AI | Greg Renard*
