import os, json, re, requests
import streamlit as st
from openai import OpenAI

FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY", "")
# Paste the EXACT Gemma model ID you copied from the Fireworks Models page:
MODEL = os.environ.get("FIREWORKS_MODEL", "accounts/fireworks/models/gemma-4-31b-it")

client = OpenAI(api_key=FIREWORKS_API_KEY,
                base_url="https://api.fireworks.ai/inference/v1")

# Seed headlines generated on the AMD Developer Cloud GPU (Qwen2-7B via vLLM).
# Optional: if the file isn't present, the app still runs fine.
try:
    with open("headlines_seed.json") as f:
        seed_headlines = json.load(f)
        if isinstance(seed_headlines, dict):
            seed_headlines = seed_headlines.get("headlines", [])
except Exception:
    seed_headlines = []

st.set_page_config(page_title="Loom — Autonomous Growth Marketer", page_icon="🧵", layout="wide")
st.title("🧵 Loom — Autonomous Growth Marketer")
st.caption("Paste a product URL + goal. Loom researches the audience, writes copy + ad concepts, "
           "builds landing-page variants, simulates an A/B audience, and tells you what to ship. "
           "Powered by Google Gemma on AMD Instinct GPUs via Fireworks AI.")

def fetch_text(url):
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        t = r.text
        t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S|re.I)
        t = re.sub(r"<[^>]+>", " ", t)
        return re.sub(r"\s+", " ", t)[:4000]
    except Exception:
        return ""

def extract_json(s):
    s = re.sub(r"^```json|^```|```$", "", s, flags=re.M).strip()
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{": depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(s[start:i+1])
                except Exception:
                    return None
    return None

TEMPLATE = """You are Loom, an autonomous growth-marketing team in a single agent.
Given a product and a goal, produce a complete go-to-market package.

PRODUCT CONTEXT:
<<CONTEXT>>

GOAL: <<GOAL>>

Return ONLY valid JSON, no markdown, with EXACTLY this shape:
{
 "audience": {"primary": "...", "pains": ["...","..."], "channels": ["...","..."]},
 "headlines": ["...","...","...","...","..."],
 "ads": [
   {"concept":"...","headline":"...","body":"...","cta":"..."},
   {"concept":"...","headline":"...","body":"...","cta":"..."},
   {"concept":"...","headline":"...","body":"...","cta":"..."}
 ],
 "landing_variants": [
   {"name":"Variant A","angle":"...","hero":"...","subhead":"...","cta":"..."},
   {"name":"Variant B","angle":"...","hero":"...","subhead":"...","cta":"..."}
 ],
 "ab_simulation": [
   {"persona":"...","prefers":"Variant A","why":"..."},
   {"persona":"...","prefers":"Variant B","why":"..."},
   {"persona":"...","prefers":"Variant A","why":"..."}
 ],
 "recommendation": {"ship":"Variant A","reason":"...","next_steps":["...","..."]}
}"""

def ad_card(a):
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#6d28d9,#db2777);padding:18px;
        border-radius:14px;color:white;height:100%">
        <div style="opacity:.8;font-size:12px;text-transform:uppercase">{a['concept']}</div>
        <div style="font-size:20px;font-weight:700;margin:6px 0">{a['headline']}</div>
        <div style="font-size:14px;opacity:.95">{a['body']}</div>
        <div style="margin-top:12px;display:inline-block;background:white;color:#6d28d9;
        padding:6px 14px;border-radius:20px;font-weight:600">{a['cta']}</div></div>""",
        unsafe_allow_html=True)

def landing_page(v):
    st.markdown(
        f"""<div style="background:#0f172a;border:1px solid #1e293b;border-radius:16px;
        padding:34px 26px;text-align:center;color:#f8fafc;min-height:280px">
        <div style="display:inline-block;background:#1e293b;color:#94a3b8;font-size:11px;
        padding:4px 12px;border-radius:20px;text-transform:uppercase;letter-spacing:1px">
        {v['name']} · {v['angle']}</div>
        <div style="font-size:30px;font-weight:800;line-height:1.15;margin:20px 0 12px">
        {v['hero']}</div>
        <div style="font-size:15px;color:#cbd5e1;max-width:460px;margin:0 auto 24px">
        {v['subhead']}</div>
        <div style="display:inline-block;background:linear-gradient(135deg,#6d28d9,#db2777);
        color:white;padding:12px 30px;border-radius:10px;font-weight:700;font-size:16px">
        {v['cta']} →</div></div>""",
        unsafe_allow_html=True)

with st.form("f"):
    url = st.text_input("Product URL", "https://www.notion.so")
    goal = st.text_input("Goal", "Drive free-trial signups from indie startup founders")
    go = st.form_submit_button("Run Loom 🚀")

if go:
    with st.spinner("Loom's growth team is working (research → write → design → simulate)…"):
        ctx = fetch_text(url) or f"Product page: {url}"
        prompt = TEMPLATE.replace("<<CONTEXT>>", ctx).replace("<<GOAL>>", goal)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role":"system","content":"You output only raw JSON. No thinking, no explanation, no markdown. Your entire response must start with { and end with }."},
                {"role":"user","content":prompt}
            ],
            temperature=0.7, max_tokens=1600)
        raw = resp.choices[0].message.content.strip()

    d = extract_json(raw)
    if d is None:
        st.error("Couldn't parse the model output — just hit Run again.")
        st.code(raw); st.stop()

    st.success(f"Done. Fireworks tokens used: {resp.usage.total_tokens} "
               "(inference ran on AMD Instinct GPUs).")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🎯 Audience")
        st.write(f"**Primary:** {d['audience']['primary']}")
        st.write("**Pains:** " + ", ".join(d['audience']['pains']))
        st.write("**Channels:** " + ", ".join(d['audience']['channels']))
        st.subheader("✍️ Headlines")
        for h in d["headlines"]: st.write("• " + h)
        if seed_headlines:
            with st.expander("🔬 AMD-GPU seed ideas (Qwen2-7B via vLLM on AMD Developer Cloud)"):
                for h in seed_headlines[:15]:
                    st.write("• " + str(h))
    with c2:
        st.subheader("🧪 Simulated A/B audience")
        for p in d["ab_simulation"]:
            st.write(f"**{p['persona']}** → {p['prefers']} — {p['why']}")
        r = d["recommendation"]
        st.subheader("🏆 Ship this")
        st.info(f"**{r['ship']}** — {r['reason']}")
        for n in r["next_steps"]: st.write("→ " + n)

    st.subheader("🎨 Ad creatives")
    cols = st.columns(3)
    for col, a in zip(cols, d["ads"]):
        with col: ad_card(a)

    st.subheader("🖥️ Landing-page variants")
    lc = st.columns(2)
    for col, v in zip(lc, d["landing_variants"]):
        with col: landing_page(v)
