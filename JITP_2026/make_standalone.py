import json
from pathlib import Path

print("Creating standalone dashboard...")
html = Path("static/pas_strategy_dashboard.html").read_text()
data = json.loads(Path("static/pas_dashboard_data.json").read_text())
insights = json.loads(Path("static/pas_ai_insights.json").read_text())

data_js = f"const EMBEDDED_DASHBOARD_DATA = {json.dumps(data, ensure_ascii=False)};"
insights_js = f"const EMBEDDED_AI_INSIGHTS = {json.dumps(insights, ensure_ascii=False)};"

html = html.replace("fetch('pas_dashboard_data.json')", "Promise.resolve({json:()=>Promise.resolve(EMBEDDED_DASHBOARD_DATA)})")
html = html.replace("fetch('pas_ai_insights.json')", "Promise.resolve({json:()=>Promise.resolve(EMBEDDED_AI_INSIGHTS)})")

pos = html.find('<script>') + 8
html = html[:pos] + f"\n{data_js}\n{insights_js}\n" + html[pos:]

out = Path("JITP_2026/PAS_Dashboard_STANDALONE.html")
out.write_text(html, encoding='utf-8')
print(f"Done! File: {out} ({out.stat().st_size/1024:.0f} KB)")
