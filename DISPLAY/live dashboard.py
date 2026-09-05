"""
Multi-Disaster Live Dashboard (Edge AI version)
-------------------------------------------------
Each ESP32 (wildfire, landslide, ...) already decides its own risk level
locally (edge AI) and publishes {"risk": "...", <sensor values>} over MQTT.
This script just subscribes to each topic and displays the latest reading
from every device - no ML model runs on the laptop.

SETUP:
    pip install flask paho-mqtt

USAGE:
    python dashboard.py
    Open http://localhost:5000

Make sure each Wokwi simulator is running and connected to WiFi
("Wokwi-GUEST") so it can publish to the broker.
"""

import json
import threading
import time

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

BROKER = "broker.hivemq.com"
PORT = 1883

TOPICS = {
    "wildfire": "hackathon/disaster/wildfire",
    "landslide": "hackathon/disaster/landslide",
    # Add more here later, e.g.:
    "air_pollution": "hackathon/disaster/air_pollution",
}

state = {
    key: {"data": {}, "risk": None, "updated_at": None, "connected": False}
    for key in TOPICS
}


def on_connect(client, userdata, flags, rc, properties=None):
    print("[*] MQTT connected, subscribing...")
    for key, topic in TOPICS.items():
        client.subscribe(topic)
        print(f"    subscribed: {topic}")


def on_message(client, userdata, msg):
    for key, topic in TOPICS.items():
        if msg.topic == topic:
            try:
                payload = json.loads(msg.payload.decode())
            except Exception as e:
                print("Bad payload:", e)
                return

            risk = payload.get("risk", "N/A")
            sensor_data = {k: v for k, v in payload.items() if k != "risk"}

            state[key].update({
                "data": sensor_data,
                "risk": risk,
                "updated_at": time.strftime("%H:%M:%S"),
                "connected": True,
            })
            print(f"[{key}] {sensor_data} -> {risk}")


def mqtt_thread():
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    while True:
        try:
            client.connect(BROKER, PORT, 60)
            client.loop_forever()
        except Exception as e:
            print("[!] MQTT connection error, retrying in 3s:", e)
            time.sleep(3)


PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Disaster Risk Dashboard</title>
<meta charset="utf-8">
<style>
  body { font-family: system-ui, sans-serif; background: #0f1115; color: #eee; padding: 40px; }
  h1 { text-align: center; margin-bottom: 30px; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; }
  .card { background: #1a1d24; border-radius: 16px; padding: 24px; }
  .card h2 { margin-top: 0; font-size: 18px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }
  .risk-badge { display: inline-block; padding: 10px 24px; border-radius: 10px;
                font-size: 26px; font-weight: 700; margin: 10px 0 16px; }
  .risk-Low { background: #1e5631; }
  .risk-Medium { background: #8a6d1e; }
  .risk-High { background: #7a1e1e; }
  .risk-unknown { background: #333; }
  .metric-row { display: flex; justify-content: space-between; font-size: 14px;
                padding: 4px 0; border-top: 1px solid #2a2d35; }
  .status { font-size: 12px; color: #888; margin-top: 12px; }
</style>
</head>
<body>
<h1>🚨 Disaster Risk Dashboard</h1>
<div class="cards" id="cards"></div>

<script>
const labels = {
  wildfire: "🔥 Wildfire",
  landslide: "⛰️ Landslide",
  air_pollution: "🏭 Air Pollution"
};

async function refresh() {
  try {
    const res = await fetch('/api/latest');
    const state = await res.json();
    const container = document.getElementById('cards');
    container.innerHTML = '';
    for (const key of Object.keys(state)) {
      const s = state[key];
      const label = labels[key] || key;
      const riskClass = 'risk-' + (s.risk === 'Low' ? 'Low' : s.risk === 'Medium' ? 'Medium' : s.risk === 'High' ? 'High' : 'unknown');
      let metrics = '';
      for (const [k, v] of Object.entries(s.data || {})) {
        metrics += `<div class="metric-row"><span>${k}</span><span>${v}</span></div>`;
      }
      container.innerHTML += `
        <div class="card">
          <h2>${label}</h2>
          <div class="risk-badge ${riskClass}">${s.risk ?? '--'}</div>
          ${metrics}
          <div class="status">${s.connected ? '🟢' : '🔴'} last update: ${s.updated_at ?? 'never'}</div>
        </div>`;
    }
  } catch (e) {
    console.error(e);
  }
}
setInterval(refresh, 1500);
refresh();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/api/latest")
def api_latest():
    return jsonify(state)


if __name__ == "__main__":
    t = threading.Thread(target=mqtt_thread, daemon=True)
    t.start()
    print("[*] Dashboard running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000)