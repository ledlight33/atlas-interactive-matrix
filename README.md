# ATLAS Interactive Matrix

**An interactive visualization of the [MITRE ATLAS™](https://atlas.mitre.org) framework with AI-powered attack simulation.**

Explore 16 tactics, 101 techniques, and 66 sub-techniques — then simulate realistic AI attack kill chains using your choice of AI provider.

> **MITRE ATLAS™** (Adversarial Threat Landscape for AI Systems) catalogs adversary tactics and techniques targeting AI and machine learning systems. This project makes it interactive and educational.

---

## Features

### Interactive Matrix
- Full ATLAS v5.5.0 matrix with all 16 tactics in kill-chain order
- 101 techniques with 66 sub-techniques, sorted alphabetically to match the official atlas.mitre.org layout
- Hover to preview — tiles scale up with glow effects
- Click any technique for details, descriptions, and sub-techniques
- Search across all techniques by name or ID
- Kill-chain phase grouping (Preparation → Objectives)
- Direct links to official ATLAS documentation for each technique

### AI Attack Simulation
- Select any technique → click **⚡ Attack Simulation**
- AI generates a complete attack scenario including:
  - **Attack Kill Chain** — step-by-step path through ATLAS tactics/techniques
  - **Practical Example** — realistic scenario with specific tools, targets, and methods
  - **Defense Recommendation** — actionable mitigation strategies
  - **Severity Rating** — Critical / High / Medium
- Attack path techniques are highlighted on the matrix with pulse animation
- Hard-enforcement ensures the selected technique is always included in the generated path

### Multi-Provider AI Support

| Provider | Setup | Best For |
|----------|-------|----------|
| **Local Ollama** | Free, offline, private | Security professionals who need data privacy |
| **Anthropic Claude** | Your API key, ~$0.01/sim | Highest quality attack scenarios |
| **OpenAI GPT** | Your API key, ~$0.01/sim | Good balance of quality and cost |

---

## Quick Start

### Option 1 — Open locally (simplest)

1. Download `index.html`
2. Double-click to open in your browser
3. That's it — the matrix works immediately without any AI setup

### Option 2 — GitHub Pages (share with the world)

1. Fork this repository
2. Go to **Settings → Pages → Deploy from main branch**
3. Your matrix is live at `https://yourusername.github.io/atlas-interactive-matrix/`

### Option 3 — Local HTTP server (recommended for Ollama)

```bash
cd atlas-interactive-matrix
python -m http.server 8080
```
Open `http://localhost:8080` in your browser.

---

## AI Simulation Setup

The matrix works perfectly without AI — simulation is optional. Click the **⚙** button in the header to configure.

### Local Ollama (Recommended for privacy)

**Requirements:** [Ollama](https://ollama.com) installed with a compatible model.

**Step 1 — Install a model:**
```bash
ollama pull qwen2.5:7b
```

**Step 2 — Enable browser access (CORS):**

Windows (PowerShell as Administrator):
```powershell
[System.Environment]::SetEnvironmentVariable("OLLAMA_ORIGINS", "*", "User")
```

macOS / Linux:
```bash
OLLAMA_ORIGINS="*" ollama serve
```

> **Important:** Restart Ollama after setting the environment variable.

**Step 3 — Verify it's running:**

Open `http://localhost:11434` in your browser — you should see "Ollama is running".

**Step 4 — Configure in the matrix:**

Click **⚙** → Select **🦙 Local Ollama** → Click **↻ Test connection** → Choose your model from the dropdown → **Save**.

#### Recommended Models

| Model | Size | VRAM | JSON Quality | Speed | Command |
|-------|------|------|-------------|-------|---------|
| `qwen2.5:7b` | 4.7 GB | 8 GB | ⭐⭐⭐⭐⭐ | Good | `ollama pull qwen2.5:7b` |
| `llama3.1:8b` | 4.9 GB | 8 GB | ⭐⭐⭐⭐ | Good | `ollama pull llama3.1:8b` |
| `dolphin-mixtral` | 26 GB | 16+ GB | ⭐⭐⭐⭐ | Slow | `ollama pull dolphin-mixtral` |
| `mistral:7b` | 4.4 GB | 8 GB | ⭐⭐⭐ | Fast | `ollama pull mistral:7b` |
| `llama3.2:3b` | 2.0 GB | 4 GB | ⭐⭐ | Very fast | `ollama pull llama3.2:3b` |

> **Note:** Ollama mode uses enhanced few-shot prompting to guide smaller models toward AI-native attack scenarios. The prompt includes guidance on MLOps, RAG, LLM-specific targets — not generic IT attacks.

#### Advanced Tuning

Ollama settings include an **Advanced Tuning** section (collapsed by default) with:

- **Temperature** (0.0–2.0, default 0.6) — Lower = more deterministic JSON output
- **Top P** (0.0–1.0, default 0.9) — Nucleus sampling threshold
- **Num Context** (2048–32768, default 8192) — Context window size
- **Num Predict** (500–8192, default 2000) — Maximum response length

### Cloud Providers (Claude / OpenAI)

**Step 1 — Get an API key:**
- Anthropic: [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
- OpenAI: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

**Step 2 — Configure in the matrix:**

Click **⚙** → Select provider → Paste your API key → Click **↻ Load available models** → Choose a model → **Save**.

#### How your API key is handled

- Saved **only** in your browser's `localStorage` (persists across sessions)
- Sent **directly** from your browser to the provider over HTTPS — no server in between
- **Not encrypted** at rest — standard `localStorage` behavior, same as any web app session
- Use "Clear all data" in settings to remove it anytime

---

## Model Comparison

We tested the same technique (T0054 LLM Jailbreak) across multiple models. Results reflect real-world quality differences:

| Criterion | Qwen 2.5 7B | Dolphin Mixtral | GPT-4o-mini | Claude Sonnet |
|-----------|-------------|-----------------|-------------|---------------|
| Selected technique in path | ⚠️ Needs retry | ✅ | ✅ | ✅ |
| Tactic mapping accuracy | 2/5 | 4/5 | 5/5 | 6/6 |
| AI-native specificity | Basic | Good | Good | Excellent |
| Jailbreak techniques named | None | DAN | Generic | DAN, Unicode, multi-turn |
| Concrete impact numbers | No | No | No | "1,000+ customers" |
| Defense quality | Generic MFA | OK | OK | Red teaming + audit logs |

> **Key finding:** Local models benefit significantly from the built-in few-shot prompting but still lag behind frontier models in instruction-following and domain-specific reasoning. This tool transparently flags when auto-correction was applied.

---

## Known Limitations

- **Local model quality:** Smaller models (≤7B parameters) may occasionally misclassify tactic-technique mappings or generate generic (non-AI-native) attack scenarios. The tool includes auto-correction with transparent warnings when this happens.
- **Attack path enforcement:** When a model fails to include the selected technique, the system retries once with stricter parameters and auto-injects the technique if needed, clearly labeling it as "AUTO-CORRECTED."
- **Browser-only:** API keys are stored in `localStorage` without encryption. Do not use on shared or public computers.
- **ATLAS data freshness:** Technique data is bundled from ATLAS v5.5.0. Updates require a new release.

---

## Data Sources

| Source | Version | License |
|--------|---------|---------|
| [MITRE ATLAS™](https://atlas.mitre.org) | v5.5.0 | Apache 2.0 |
| [atlas-data repository](https://github.com/mitre-atlas/atlas-data) | v5.5.0 | Apache 2.0 |

---

## Legal

**MITRE ATLAS™** is a trademark of The MITRE Corporation. This project reproduces ATLAS data with permission under the Apache License 2.0. This visualization is an independent community project and is **not endorsed by, affiliated with, or sponsored by The MITRE Corporation**.

© 2025 The MITRE Corporation. ATLAS data reproduced and distributed with the permission of The MITRE Corporation.

See [LICENSE](LICENSE) and [NOTICE](NOTICE) for full details.

---

## Contributing

Contributions are welcome. Please open an issue first to discuss what you would like to change.

Areas where contributions would be valuable:
- Additional ATLAS case study mappings
- OWASP Top 10 for LLMs integration (planned for v2)
- Improved prompts for specific local models
- Accessibility improvements
- Mobile responsiveness

---

## Roadmap

- [x] v1.0 — Interactive ATLAS matrix with AI attack simulation
- [ ] v1.1 — OWASP Top 10 for LLMs section with cross-referenced ATLAS techniques


---

## Author

Built by a Digital Forensics Investigator and AI Security researcher exploring the intersection of DFIR methodology and adversarial AI.

## Star History

If this project is useful, consider giving it a ⭐ — it helps others discover it.
