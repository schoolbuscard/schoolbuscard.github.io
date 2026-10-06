import json, os, urllib.request, datetime, html, sys
TOKEN = os.environ["GC_TOKEN"]
API = "https://schoolbuscard.goatcounter.com/api/v0/"
BASE = os.environ.get("STATS_BASE", "2026-10-06T15:10:00Z")
OUT = os.environ["STATS_OUT"]
def get(path, **q):
    qs = "&".join(f"{k}={v}" for k, v in q.items())
    req = urllib.request.Request(API + path + ("?" + qs if qs else ""), headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)
now = datetime.datetime.now(datetime.timezone.utc)
iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
base = datetime.datetime.strptime(BASE, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
et = now - datetime.timedelta(hours=4)
today_start = max(base, (et.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(hours=4)))
week_start = max(base, now - datetime.timedelta(days=7))
end = iso(now + datetime.timedelta(days=1))
day = lambda d: d.strftime("%Y-%m-%d")
def total(start):
    return int(get("stats/total", start=day(start), end=end).get("total", 0))
bp0 = os.path.join(os.path.dirname(OUT), "baseline.json")
_b = json.load(open(bp0)) if os.path.exists(bp0) else {}
BT = _b.get("t", 9); BE = _b.get("e", {"download-pdf": 1})
visits = max(0, total(base) - BT); today = max(0, total(today_start) - BT); week = max(0, total(week_start) - BT)
browsers = get("stats/browsers", start=iso(base), end=end).get("stats", [])
systems = get("stats/systems", start=iso(base), end=end).get("stats", [])
bpath = os.path.join(os.path.dirname(OUT), "baseline.json")
cur = {"b": {x["name"]: int(x["count"]) for x in browsers}, "s": {x["name"]: int(x["count"]) for x in systems}}
if not os.path.exists(bpath):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(cur, open(bpath, "w"))
bl = json.load(open(bpath))
browsers = [{"name": k, "count": v - bl["b"].get(k, 0)} for k, v in cur["b"].items() if v - bl["b"].get(k, 0) > 0]
systems = [{"name": k, "count": v - bl["s"].get(k, 0)} for k, v in cur["s"].items() if v - bl["s"].get(k, 0) > 0]
hits = get("stats/hits", start=day(base), end=end, limit=100).get("hits", [])
ev = {h["path"]: max(0, int(h.get("count", 0)) - BE.get(h["path"], 0)) for h in hits if h.get("event")}
img = ev.get("download-image", 0); pdf = ev.get("download-pdf", 0); req = ev.get("color-request", 0)
dev = {"iPhone / iPad": 0, "Android": 0, "Computer": 0, "Other": 0}
for s in systems:
    n = s["name"]; c = int(s["count"])
    if n == "iOS": dev["iPhone / iPad"] += c
    elif n == "Android": dev["Android"] += c
    elif n in ("Windows", "macOS", "Mac OS X", "Linux", "ChromeOS", "Chrome OS"): dev["Computer"] += c
    else: dev["Other"] += c
def big(label, n, i=''): return f'<div class="b"><div class="n" id="{i}">{n}</div><div class="l">{html.escape(label)}</div></div>'
LIVEJS = '\n<script>\n(function(){\nvar C="https://schoolbuscard.goatcounter.com/counter/",BT=%BT%,BE=%BE%,BD="2026-10-06";\nfunction d(n){var x=new Date(Date.now()+n*864e5);return x.toLocaleDateString("en-CA",{timeZone:"America/New_York"});}\nfunction g(p,s){return fetch(C+p+".json?start="+s+"&end="+d(2)).then(function(r){return r.json()}).then(function(j){return parseInt(String(j.count).replace(/[^0-9]/g,""),10)||0});}\nfunction set(id,n){var e=document.getElementById(id);if(e)e.textContent=Math.max(0,n);}\nvar td=d(0),wk=d(-7);\ng("TOTAL",BD).then(function(n){set("v-total",n-BT)});\ng("TOTAL",wk<BD?BD:wk).then(function(n){set("v-week",n-BT)});\ng("TOTAL",td).then(function(n){set("v-today",td==BD?n-BT:n)});\n[["download-image","v-img"],["download-pdf","v-pdf"],["color-request","v-req"]].forEach(function(a){g(encodeURIComponent(a[0]),BD).then(function(n){set(a[1],n-(BE[a[0]]||0))});});\n})();\n</script>'.replace("%BT%", str(BT)).replace("%BE%", json.dumps(BE))
def rows(items):
    if not items: return '<p class="m">Nothing yet</p>'
    return "".join(f'<div class="r"><span>{html.escape(str(a))}</span><b>{b}</b></div>' for a, b in items)
page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Card maker stats</title>
<style>body{{margin:0;background:#faf9f7;color:#231f20;font:17px/1.4 -apple-system,system-ui,sans-serif}}main{{max-width:560px;margin:0 auto;padding:20px 16px 40px}}h1{{font-size:22px;margin:0 0 4px}}h2{{font-size:15px;text-transform:uppercase;letter-spacing:.05em;opacity:.7;margin:28px 0 8px}}.g{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}.b{{background:#fff;border:1px solid #ddd;border-radius:10px;padding:14px}}.n{{font-size:40px;font-weight:800;line-height:1.1}}.l{{opacity:.7;font-size:14px}}.r{{display:flex;justify-content:space-between;background:#fff;border:1px solid #ddd;border-radius:10px;padding:12px 14px;margin-bottom:8px}}.m{{opacity:.6}}small{{opacity:.6}}</style></head><body><main>
<h1>Bus/Van card maker</h1><small>Visits and downloads are live. Devices and browsers update about every 30 min (last {now.astimezone(datetime.timezone(datetime.timedelta(hours=-4))).strftime("%b %-d, %-I:%M %p")} ET). Counts start Oct 6 at 11:25 AM.</small>
<h2>Visits</h2><div class="g">{big("Total visits", visits, "v-total")}{big("This week", week, "v-week")}{big("Today", today, "v-today")}{big("Color requests", req, "v-req")}</div>
<h2>Downloads</h2><div class="g">{big("Image", img, "v-img")}{big("PDF", pdf, "v-pdf")}</div>
<h2>Devices</h2>{rows([(k, v) for k, v in dev.items() if v])}
<h2>Browsers</h2>{rows([(b["name"], b["count"]) for b in browsers])}
</main>'''+LIVEJS+'''</body></html>'''
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(page)
print("ok", visits, today, week, img, pdf, req)
