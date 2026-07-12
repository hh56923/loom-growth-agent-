import os, json, re, requests
import streamlit as st
from openai import OpenAI
import json
try:
    with open("headlines_seed.json") as f:
        seed_headlines = json.load(f)
except Exception:
    seed_headlines = []

FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY", "")
# Paste the EXACT Gemma model ID you copied from the Fireworks Models page:
MODEL = os.environ.get("FIREWORKS_MODEL", "accounts/fireworks/models/gemma-4-31b-it")

client = OpenAI(api_key=FIREWORKS_API_KEY,
                base_url="https://api.fireworks.ai/inference/v1")

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
            messages=[{"role":"user","content":prompt}],
            temperature=0.7, max_tokens=1600)
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```json|^```|```$", "", raw, flags=re.M).strip()
    try:
        d = json.loads(raw)
    except Exception:
        st.error("Model didn't return clean JSON. Raw output below — just re-run.")
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
        with col:
            st.markdown(f"**{v['name']} — {v['angle']}**")
            st.markdown(f"### {v['hero']}")
            st.write(v["subhead"])
            st.button(v["cta"], key=v["name"])
