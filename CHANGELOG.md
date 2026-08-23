# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-08-23

### Data: MITRE ATLAS v5.5.0 (content 2026.03) to v2026.07

Upstream moved to CalVer and to schema format-version 6.0.0, which replaces
per-object arrays with keyed dicts and a top-level relationship graph.

- Sub-techniques 66 to 77, mitigations 35 to 37, mitigation coverage 244 to 338 links
- Retired `AML.T0019`, `AML.T0058` and `AML.T0104`, consolidated into the new `AML.T0115` Publish Poisoned AI Artifacts
- Added `AML.T0113` Steal Web Session Cookie, `AML.T0114` AI Service Web Interface, `AML.T0115` Publish Poisoned AI Artifacts
- Added mitigations `AML.M0035` AI Red Team and `AML.M0036` Limit AI Workload Resource Consumption
- Renamed `AML.T0020` to Training Data Poisoning, plus 7 mitigation renames (the new "Predictive AI" family)
- Corrected two technique-to-tactic mappings that were rendering cards in the wrong column: `AML.T0020` (Resource Development dropped) and `AML.T0053` (Lateral Movement added)
- Technique descriptions are now the full MITRE text with working cross-reference links, instead of one-line summaries

### Added: documented incident replay

Every attack chain MITRE has recorded now ships with the matrix, rendered from
data with no model involved. 68 case studies, 571 steps, 122 source references.

- Incident browser to search all 68 cases by name, actor or target, filtered by real incident (18) or exercise (50)
- Timeline view replaying a case step by step with tactic, technique and MITRE's record of what was observed, plus source links. Opening one highlights its techniques on the matrix through the same path-highlight mechanism a generated simulation uses, so real and invented chains are directly comparable.
- Per-technique case list in the detail panel, resolving sub-technique hits up to the parent so `T0051` surfaces cases that used `T0051.001`
- Clicking a technique inside a timeline opens it on the matrix, so incidents and techniques navigate to each other in both directions
- Dates render only as precisely as MITRE recorded them, so a case with Year granularity shows the year rather than an invented day

### Added: evidence grading, focus filters and provenance

- Evidence grading from the ATLAS maturity field (Realized, Demonstrated, Feasible) as a coloured dot on each tile and a badge in the detail panel. The 45 Realized techniques are exactly the 45 appearing in an Incident-type case study, verified as identical sets at build time.
- Focus filters for Agentic AI (65), Generative AI (53), Predictive AI (35), Enterprise (38), plus a "Seen in the wild" filter for the 45 Realized techniques. Filters dim rather than hide, so nothing disappears silently.
- Retired technique IDs resolve to their replacement in search, so older reports and casework remain navigable
- ATT&CK cross-reference links on the 37 techniques with an Enterprise counterpart
- Mitigation category and ML lifecycle phase surfaced on mitigation chips
- `tools/build_data.py`, a reproducible data pipeline that pins a release, verifies its SHA-256, transforms the v6 schema, writes a readable copy to `data/`, and injects a compressed payload into `index.html`
- A `--diff-from` flag reporting added, removed and renamed objects, and technique-to-tactic mapping changes, between any two ATLAS releases
- Provenance recorded in `data/provenance.json` and embedded in the page, with the version badge exposing source URL, upstream hash and build date
- Google Gemini as a fourth AI provider with live model discovery. The key is sent in the `x-goog-api-key` header rather than the `?key=` query parameter Google's quickstart uses, so the credential stays out of history and proxy logs.

### Changed

- The dataset is embedded as gzip and base64, inflated with the native `DecompressionStream` before first render. `index.html` stays a single self-contained file that still opens by double-click, and Babel parses a string literal instead of a large object literal.
- Simulation severity is labelled `model: <rating>` and shown beside the ATLAS evidence grade, so an unsourced model judgement is never presented as a MITRE finding
- The simulation prompt now carries each technique's maturity and platforms, and prefers Realized techniques when building a chain
- Cloud providers are described by a single `CLOUD_PROVIDERS` map instead of per-provider branches threaded through the settings UI
- CSP `connect-src` extended to `generativelanguage.googleapis.com`

### Fixed

- Build reproducibility: `technique_incidents` sorted a set by date alone, but several case studies share a date, so ties fell to set iteration order and varied between runs. Sorting by (date, id) makes the order total. Without this the embedded payload differed on every build and could not be checked against `data/`.
- Selecting a multi-tactic technique from a different matrix column enforced the previously selected tactic in the simulation. `DetailPanel` was reused across selections and `handleSimulate` closed over a stale `tacticId`.
- `extractJSON` matched greedily to the last brace in the response, over-capturing when a model appended prose containing a brace or emitted a second object. It now scans for the first balanced object, ignoring braces inside strings.
- Switching cloud provider kept the previous provider's model selected, so moving from Claude to OpenAI or Gemini would send an unrecognised model id and 404. The model now resets to the new provider's default, and the saved choice is restored when switching back.
- The QR code is embedded as a data URI instead of loaded from a sibling `qr.png`. The relative image meant the page silently lost its QR whenever it was opened on its own, and under `file://` the page's own `img-src 'self'` policy blocks a relative image outright. Recompressed from 1230px RGB to 410px 16-colour, so the fix costs 9 KB rather than 66 KB.
- Ollama connection failures now name the actual cause. The page checks its own protocol: served over HTTPS, plain-HTTP requests to Ollama are blocked as mixed content and no Ollama setting can help; opened via `file://`, requests carry `Origin: null` and need `OLLAMA_ORIGINS="*"`. Both are surfaced before "Test connection" is pressed.
- One `innerHTML` sink in the dataset-load error handler that interpolated an error message. The messages are browser-generated rather than attacker-controlled, but a page holding an API key in `localStorage` should contain no HTML-injection sink at all. Rebuilt with DOM nodes and `textContent`.

### Documentation

- Documented incident replay, evidence grading, focus filters, retired-ID resolution and ATT&CK cross-references in the README
- Troubleshooting section covering Ollama connectivity by context, and the shared-origin caveat on GitHub Pages where `localStorage` is scoped to the origin rather than the path
- Noted that the model comparison predates Gemini support, so its absence is not a result

## [1.0.0] - 2025-04-16

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
- Standalone single-file HTML, no build tools required
- GitHub Pages compatible (deploy as index.html)

### Security
- API keys stored only in browser localStorage
- Direct browser-to-provider HTTPS communication
- Transparent security disclosure in settings modal
- No server-side components or data collection
