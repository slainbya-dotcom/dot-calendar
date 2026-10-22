"""Inlines CSS/JS into single-file HTML previews (with a fake Tauri bridge and
sample progress bars) so the UI can be checked in any browser without building.

  python3 tools/build_preview.py [out_dir] [path/to/world-time]

If the World Time project is given, also writes calendar-side-by-side.html showing both
widgets together, with Dot Timer matching World Time's look."""
import html, json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "preview")
WT_ROOT = sys.argv[2] if len(sys.argv) > 2 else None
os.makedirs(OUT, exist_ok=True)

WORLD_TIME_SAMPLE = {
    "clocks": [
        {"id": "h", "label": "London, UK", "tz": "Europe/London", "lat": 51.51, "lng": -0.13, "home": True},
        {"id": "a", "label": "New York, USA", "tz": "America/New_York", "lat": 40.71, "lng": -74.01},
        {"id": "b", "label": "Tokyo, Japan", "tz": "Asia/Tokyo", "lat": 35.68, "lng": 139.69},
    ],
    "use24h": True, "dotColor": "#ffb000", "dotSize": 3, "bgColor": "#101010", "bgOpacity": 0.85,
}

TIMER_SAMPLE_JS = """({ matchWorldTime: %(match)s, trackers: [
  { kind: 'minute', label: 'MINUTE', show: 'value' },
  { kind: 'hour', label: 'HOUR', show: 'value' },
  { kind: 'day', label: '{WEEKDAY}', show: 'value', color: '#5ad1ff' },
  { kind: 'week', label: 'WEEK', show: 'value', steps: true },
  { kind: 'month', label: '{MONTH}', show: 'count', direction: 'drain' },
  { kind: 'year', label: '{YEAR}', show: 'percent', color: '#39ff7a' } ] })"""


def shim(match=True):
    state_js = TIMER_SAMPLE_JS % {"match": "true" if match else "false"}
    return """<script>
var __state = JSON.stringify(%s);
window.__TAURI__ = {
  core: { invoke: async (cmd, args) => {
    if (cmd === 'load_state') return __state;
    if (cmd === 'read_world_time') return %s;
    if (cmd === 'save_state') { __state = args.json; return; }
  } },
  event: { listen: async () => () => {} },
  window: { getCurrentWindow: () => ({ setSize: async () => {}, setAlwaysOnTop: async () => {}, startDragging: async () => {} }) },
  dpi: { LogicalSize: function (w, h) { this.width = w; this.height = h; } },
};
</script>""" % (state_js, json.dumps(json.dumps(WORLD_TIME_SAMPLE)))


def inline(root, name, head=""):
    src = open(os.path.join(root, "src", name), encoding="utf-8").read()
    src = re.sub(r'<link rel="stylesheet" href="([^"]+)">',
                 lambda m: "<style>" + open(os.path.join(root, "src", m.group(1)), encoding="utf-8").read() + "</style>", src)
    src = re.sub(r'<script src="([^"]+)"></script>',
                 lambda m: "<script>" + open(os.path.join(root, "src", m.group(1)), encoding="utf-8").read()
                 .replace("</script", "<\\/script") + "</script>", src)
    return src.replace("</head>", head + "</head>", 1)


DESK = "<style>body{min-height:100vh;padding:24px;background:linear-gradient(135deg,#3a6186,#89253e)!important}</style>"
open(os.path.join(OUT, "calendar-widget-preview.html"), "w", encoding="utf-8").write(inline(ROOT, "index.html", DESK + shim()))
open(os.path.join(OUT, "calendar-settings-preview.html"), "w", encoding="utf-8").write(inline(ROOT, "settings.html", shim()))

if WT_ROOT:
    wt_shim = """<script>window.__TAURI__ = { core: { invoke: async (c) => c === 'load_state' ? %s : undefined },
      event: { listen: async () => () => {} },
      window: { getCurrentWindow: () => ({ setSize: async () => {}, setAlwaysOnTop: async () => {}, startDragging: async () => {} }) },
      dpi: { LogicalSize: function () {} } };</script>""" % json.dumps(json.dumps(WORLD_TIME_SAMPLE))
    wt_doc = inline(WT_ROOT, "index.html", wt_shim)
    timer_doc = inline(ROOT, "index.html", shim())
    page = """<!doctype html><html><head><meta charset="utf-8"><title>Side by side</title>
<style>body{margin:0;min-height:100vh;padding:24px;box-sizing:border-box;background:linear-gradient(135deg,#3a6186,#89253e);
font:12px system-ui;color:#fff}iframe{border:0;display:block;background:transparent;width:100%%;}
.cap{opacity:.75;margin:14px 0 6px}</style></head><body>
<div class="cap">World Time</div><iframe id="a" style="height:100px" srcdoc="%s"></iframe>
<div class="cap">Dot Calendar (matching World Time)</div><iframe id="b" style="height:420px" srcdoc="%s"></iframe>
</body></html>""" % (html.escape(wt_doc, quote=True), html.escape(timer_doc, quote=True))
    open(os.path.join(OUT, "calendar-side-by-side.html"), "w", encoding="utf-8").write(page)

print("previews written to", os.path.abspath(OUT))
