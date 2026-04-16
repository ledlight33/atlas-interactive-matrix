# Contributing to ATLAS Interactive Matrix

Thank you for your interest in contributing. This project aims to make the MITRE ATLAS™ framework more accessible and educational for the AI security community.

## How to Contribute

1. **Open an issue first** — Describe the change you'd like to make. This helps avoid duplicate work and ensures alignment with the project's direction.

2. **Fork the repository** and create a branch for your changes.

3. **Make your changes** — Keep modifications focused. One feature or fix per pull request.

4. **Test locally** — Open `index.html` in a browser and verify:
   - The matrix renders correctly
   - Hover effects work on technique tiles
   - Tactic tooltips are visible (especially at the edges)
   - AI simulation works (if you have Ollama or an API key)
   - Settings modal opens and saves correctly

5. **Submit a pull request** with a clear description of what changed and why.

## Areas Where Help is Welcome

- **OWASP Top 10 integration** — Cross-referencing OWASP LLM risks with ATLAS techniques
- **Better prompts for local models** — If you find prompt variations that improve Ollama output quality
- **Accessibility** — Screen reader support, keyboard navigation, ARIA labels
- **Mobile responsiveness** — The matrix is currently optimized for desktop
- **Translations** — Especially for technique descriptions
- **Case study mappings** — Linking ATLAS case studies to the appropriate techniques

## Guidelines

- This is a single-file application (`index.html`). Keep it that way for simplicity.
- All ATLAS technique data, IDs, and names must exactly match the official MITRE ATLAS™ data.
- Do not commit API keys, tokens, or credentials.
- Follow the existing code style (React functional components, inline styles).

## ATLAS Data Updates

When MITRE releases a new version of ATLAS:

1. Clone the [atlas-data repository](https://github.com/mitre-atlas/atlas-data)
2. Parse the updated `dist/ATLAS.yaml`
3. Update the `ATLAS_DATA` constant in `index.html`
4. Verify all technique IDs, names, and tactic mappings
5. Update the version reference in the README and footer

## Code of Conduct

Be respectful. This is a security education project — accuracy matters more than speed. If you're not sure about a tactic-technique mapping, ask.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
