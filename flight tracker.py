#!/usr/bin/env python3
"""
Flight Tracker Proxy Server
Run: python flight_server.py
Then open: http://localhost:8080
"""

import http.server
import urllib.request
import urllib.parse
import json
import math
import os

LAT = 28.6139
LNG = 77.2090

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>✈ Flight Tracker Delhi</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Arial, sans-serif; background: #0a0f1e; color: #e0e6f0; height: 100vh; display: flex; flex-direction: column; }
#header { padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; background: #111827; border-bottom: 1px solid #1f2d40; }
#header h1 { font-size: 16px; font-weight: 600; color: #60a5fa; }
#status { font-size: 12px; padding: 4px 10px; border-radius: 20px; background: #1f2937; }
#stats { display: flex; gap: 28px; padding: 10px 20px; background: #0d1424; border-bottom: 1px solid #1f2d40; align-items: center; }
.stat-val { font-size: 20px; font-weight: 700; color: #60a5fa; }
.stat-label { font-size: 11px; color: #6b7280; }
#map { flex: 1; position: relative; }
#leaflet-map { width: 100%; height: 100%; }
#panel {
  position: absolute; bottom: 16px; right: 16px;
  background: #111827dd; border: 1px solid #1f2d40;
  border-radius: 12px; padding: 14px 16px;
  font-size: 13px; color: #9ca3af; z-index: 1000;
  min-width: 240px; display: none;
  backdrop-filter: blur(8px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}
#panel h3 { font-size: 14px; font-weight: 700; color: #60a5fa; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
#close-panel { cursor: pointer; color: #6b7280; font-size: 18px; line-height: 1; }
#close-panel:hover { color: white; }
.row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #1f2d3088; }
.row:last-child { border: none; }
.val { color: #e0e6f0; font-weight: 600; }
#controls { padding: 10px 20px; background: #111827; border-top: 1px solid #1f2d40; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
#controls label { font-size: 12px; color: #9ca3af; white-space: nowrap; }
#radius-slider { flex: 1; min-width: 120px; accent-color: #3b82f6; }
#radius-val { font-size: 12px; font-weight: 700; color: #60a5fa; min-width: 55px; }
button { font-size: 12px; padding: 6px 16px; cursor: pointer; background: #1d4ed8; color: white; border: none; border-radius: 6px; font-weight: 600; transition: background 0.2s; }
button:hover { background: #2563eb; }
button:disabled { background: #374151; color: #6b7280; cursor: not-allowed; }
#auto-label { font-size: 11px; color: #6b7280; }
.legend { position: absolute; bottom: 16px; left: 16px; background: #111827cc; border: 1px solid #1f2d40; border-radius: 8px; padding: 8px 12px; font-size: 11px; color: #9ca3af; z-index: 1000; }
.legend div { display: flex; align-items: center; gap: 6px; margin: 2px 0; }
.dot { width: 10px; height: 10px; border-radius: 50%; border: 1px solid white; display: inline-block; }
</style>
</head>
<body>
<div id="header">
  <h1>✈ Live Flight Tracker — Delhi</h1>
  <span id="status" style="color:#6b7280">Starting…</span>
</div>
<div id="stats">
  <div><div class="stat-val" id="s-count">—</div><div class="stat-label">aircraft</div></div>
  <div><div class="stat-val" id="s-radius">150</div><div class="stat-label">km radius</div></div>
  <div><div class="stat-val" id="s-updated">—</div><div class="stat-label">last updated</div></div>
  <div style="margin-left:auto;font-size:11px;color:#374151;background:#0d1424;padding:4px 10px;border-radius:6px;border:1px solid #1f2d40">
    🟢 Local proxy active
  </div>
</div>
<div id="map">
  <div id="leaflet-map"></div>
  <div id="panel">
    <h3><span>✈ <span id="p-callsign">—</span></span><span id="close-panel" onclick="closePanel()">×</span></h3>
    <div class="row"><span>Callsign</span><span class="val" id="p-cs">—</span></div>
    <div class="row"><span>Country</span><span class="val" id="p-country">—</span></div>
    <div class="row"><span>Altitude</span><span class="val" id="p-alt">—</span></div>
    <div class="row"><span>Speed</span><span class="val" id="p-speed">—</span></div>
    <div class="row"><span>Heading</span><span class="val" id="p-heading">—</span></div>
    <div class="row"><span>Vertical</span><span class="val" id="p-vrate">—</span></div>
    <div class="row"><span>On ground</span><span class="val" id="p-ground">—</span></div>
    <div class="row"><span>ICAO24</span><span class="val" id="p-icao">—</span></div>
    <div style="margin-top:8px;text-align:center">
      <a id="p-fr24" href="https://www.flightradar24.com" target="_blank" style="font-size:11px;color:#60a5fa">View on Flightradar24 ↗</a>
    </div>
  </div>
  <div class="legend">
    <div><span class="dot" style="background:#3b82f6"></span> Flying</div>
    <div><span class="dot" style="background:#6b7280"></span> On ground</div>
    <div><span class="dot" style="background:#3b82f6;width:14px;height:14px;border-radius:50%;border:3px solid white;box-shadow:0 0 0 2px #3b82f6"></span> You</div>
  </div>
</div>
<div id="controls">
  <label>Radius</label>
  <input type="range" id="radius-slider" min="50" max="500" value="150" step="10">
  <span id="radius-val">150 km</span>
  <button id="refresh-btn" onclick="loadFlights()">↻ Refresh</button>
  <span id="auto-label">Auto: 30s</span>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const LAT = 28.6139, LNG = 77.2090;
let map, markers = [], radiusCircle, autoTimer, countdown = 30;
let currentRadius = 150;

function initMap() {
  map = L.map('leaflet-map').setView([LAT, LNG], 7);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, attribution: '© OpenStreetMap | OpenSky Network'
  }).addTo(map);
  L.marker([LAT, LNG], {
    icon: L.divIcon({
      html: '<div style="width:14px;height:14px;background:#3b82f6;border-radius:50%;border:3px solid white;box-shadow:0 0 0 3px #3b82f6;"></div>',
      iconSize:[14,14], iconAnchor:[7,7]
    })
  }).addTo(map).bindTooltip('📍 Aapki Location (Delhi)', {permanent:true, direction:'right'});
  radiusCircle = L.circle([LAT,LNG], {radius:currentRadius*1000, color:'#3b82f6', weight:1, fillColor:'#3b82f6', fillOpacity:0.05}).addTo(map);
  loadFlights();
  startAutoRefresh();
}

function planeIcon(heading, onGround) {
  const c = onGround ? '#6b7280' : '#3b82f6';
  return L.divIcon({
    html: `<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" style="transform:rotate(${heading||0}deg);filter:drop-shadow(0 1px 3px rgba(0,0,0,.7))"><path d="M21 16l-9-4V4a1 1 0 0 0-2 0v8L1 16l1 2 8-2.5V20l-2 1.5V23l3-1 3 1v-1.5L12 20v-4.5l8 2.5z" fill="${c}" stroke="white" stroke-width="0.8"/></svg>`,
    iconSize:[26,26], iconAnchor:[13,13], className:''
  });
}

async function loadFlights() {
  const btn = document.getElementById('refresh-btn');
  btn.disabled = true; btn.textContent = '⏳ Loading…';
  document.getElementById('status').textContent = 'Fetching…';
  document.getElementById('status').style.color = '#6b7280';
  try {
    const res = await fetch(`/api/flights?radius=${currentRadius}`);
    if (!res.ok) throw new Error('Server error ' + res.status);
    const planes = await res.json();
    clearMarkers();
    planes.forEach(p => {
      if (!p.lat || !p.lng) return;
      const m = L.marker([p.lat,p.lng], {icon: planeIcon(p.heading, p.on_ground)}).addTo(map);
      m.on('click', () => showPanel(p));
      markers.push(m);
    });
    document.getElementById('s-count').textContent = planes.length;
    document.getElementById('s-radius').textContent = currentRadius;
    document.getElementById('s-updated').textContent = new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});
    document.getElementById('status').textContent = '✓ ' + planes.length + ' aircraft';
    document.getElementById('status').style.color = '#34d399';
  } catch(e) {
    document.getElementById('status').textContent = '✗ Error: ' + e.message;
    document.getElementById('status').style.color = '#f87171';
  }
  btn.disabled = false; btn.textContent = '↻ Refresh';
}

function clearMarkers() { markers.forEach(m => map.removeLayer(m)); markers = []; }

function showPanel(p) {
  document.getElementById('p-callsign').textContent = p.callsign || p.icao24 || '—';
  document.getElementById('p-cs').textContent = p.callsign || '—';
  document.getElementById('p-country').textContent = p.country || '—';
  document.getElementById('p-alt').textContent = p.on_ground ? 'On ground' : (p.baro_alt ? Math.round(p.baro_alt)+'m / '+Math.round(p.baro_alt*3.281)+'ft' : '—');
  document.getElementById('p-speed').textContent = p.velocity ? Math.round(p.velocity*1.944)+' kts' : '—';
  document.getElementById('p-heading').textContent = p.heading != null ? Math.round(p.heading)+'°' : '—';
  document.getElementById('p-vrate').textContent = p.vert_rate ? (p.vert_rate>0?'↑ ':'↓ ')+Math.abs(Math.round(p.vert_rate))+'m/s' : '—';
  document.getElementById('p-ground').textContent = p.on_ground ? 'Yes' : 'No';
  document.getElementById('p-icao').textContent = p.icao24 || '—';
  const cs = (p.callsign||'').trim();
  document.getElementById('p-fr24').href = cs ? 'https://www.flightradar24.com/'+cs : 'https://www.flightradar24.com';
  document.getElementById('p-fr24').textContent = cs ? 'View '+cs+' on Flightradar24 ↗' : 'View on Flightradar24 ↗';
  document.getElementById('panel').style.display = 'block';
}

function closePanel() { document.getElementById('panel').style.display='none'; }

function startAutoRefresh() {
  clearInterval(autoTimer); countdown = 30;
  autoTimer = setInterval(() => {
    countdown--;
    document.getElementById('auto-label').textContent = 'Auto: '+countdown+'s';
    if (countdown<=0) { countdown=30; loadFlights(); }
  }, 1000);
}

document.getElementById('radius-slider').addEventListener('input', function() {
  currentRadius = parseInt(this.value);
  document.getElementById('radius-val').textContent = currentRadius+' km';
  radiusCircle.setRadius(currentRadius*1000);
  map.setZoom(currentRadius<80?10:currentRadius<150?8:currentRadius<250?7:6);
});
document.getElementById('radius-slider').addEventListener('change', () => { loadFlights(); startAutoRefresh(); });

window.onload = initMap;
</script>
</body>
</html>"""


class FlightProxy(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == '/' or parsed.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML.encode())

        elif parsed.path == '/api/flights':
            params = urllib.parse.parse_qs(parsed.query)
            radius = int(params.get('radius', [150])[0])
            data = self.fetch_flights(radius)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def fetch_flights(self, radius_km):
        R = 6371
        import math
        dLat = (radius_km / R) * (180 / math.pi)
        dLng = dLat / math.cos(math.radians(LAT))
        lamin = round(LAT - dLat, 4)
        lamax = round(LAT + dLat, 4)
        lomin = round(LNG - dLng, 4)
        lomax = round(LNG + dLng, 4)

        url = f"https://opensky-network.org/api/states/all?lamin={lamin}&lamax={lamax}&lomin={lomin}&lomax={lomax}"
        print(f"  Fetching: radius={radius_km}km, bbox=({lamin},{lomin})->({lamax},{lomax})")

        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'FlightTracker/1.0',
                'Accept': 'application/json'
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = json.loads(resp.read())
                states = raw.get('states') or []
                planes = []
                for s in states:
                    if s[5] is None or s[6] is None:
                        continue
                    planes.append({
                        'icao24':   s[0],
                        'callsign': (s[1] or '').strip(),
                        'country':  s[2],
                        'lng':      s[5],
                        'lat':      s[6],
                        'baro_alt': s[7],
                        'on_ground':s[8],
                        'velocity': s[9],
                        'heading':  s[10],
                        'vert_rate':s[11],
                    })
                print(f"  ✓ OpenSky returned {len(planes)} aircraft")
                return planes
        except Exception as e:
            print(f"  ✗ OpenSky failed: {e}")
            return []


if __name__ == '__main__':
    PORT = 8080
    server = http.server.HTTPServer(('localhost', PORT), FlightProxy)
    print("=" * 50)
    print("  ✈  Flight Tracker Server")
    print("=" * 50)
    print(f"  Server chal raha hai: http://localhost:{PORT}")
    print(f"  Browser mein yeh open karo:")
    print(f"  👉  http://localhost:{PORT}")
    print()
    print("  Band karne ke liye: Ctrl+C")
    print("=" * 50)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server band ho gaya.")
