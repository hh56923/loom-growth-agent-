# 🧵 Loom — Autonomous Growth-Marketer Agent
AMD Developer Hackathon: ACT II — Track 3 (Unicorn)

Paste a product URL and a goal. Loom acts as a one-agent growth team: researches
the audience, writes copy + ad concepts, builds landing-page variants, simulates
an A/B audience, and recommends what to ship.

## AMD / Fireworks usage
- Seed headline generation: Qwen2-7B-Instruct served locally via vLLM on the
  **AMD Developer Cloud GPU notebook** (see /proof/amd_notebook_vllm.png and
  /proof/amd_notebook_output.png). Output is loaded into the app as
  `headlines_seed.json` and blended into results.
- Runtime reasoning/generation: **Google Gemma** served via **Fireworks AI**,
  which hosts models on **AMD Instinct GPUs**. Every app run calls Fireworks;
  token usage is shown live.

## Run it
1. `pip install -r requirements.txt`
2. Set `FIREWORKS_API_KEY`, `FIREWORKS_MODEL`
3. `streamlit run app.py`

## Status
Working prototype. Research, copy, ad-concept, audience-simulation, and
recommendation loop are live. Native FLUX/SDXL ad-image rendering on AMD GPUs
is the next milestone — not implemented yet.

## License
MIT
