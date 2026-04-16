# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] — 2025-04-16

### Added
- Interactive ATLAS matrix with all 16 tactics and 101 techniques (v5.5.0)
- 66 sub-techniques with expandable detail panels
- Technique sorting matching official atlas.mitre.org alphabetical layout
- Hover effects with dynamic scaling and glow
- Search functionality across technique names, IDs, and sub-techniques
- Kill-chain phase grouping bar (Preparation → Objectives)
- Tactic header tooltips with edge-aware positioning
- AI-powered attack simulation with multi-provider support:
  - Local Ollama with dynamic model discovery and advanced tuning
  - Anthropic Claude with dynamic model listing
  - OpenAI GPT with dynamic model listing and max_completion_tokens compatibility
- Enhanced few-shot prompting for local models (AI-native attack scenarios)
- Hard-enforcement: selected technique is guaranteed in the attack path
- Auto-correction with transparent "AUTO-CORRECTED" warnings
- Settings modal with provider configuration and security disclosure
- Dynamic model dropdowns for all providers (fetched live from APIs)
- localStorage persistence for all settings
- Standalone single-file HTML — no build tools required
- GitHub Pages compatible (deploy as index.html)

### Security
- API keys stored only in browser localStorage
- Direct browser-to-provider HTTPS communication
- Transparent security disclosure in settings modal
- No server-side components or data collection
