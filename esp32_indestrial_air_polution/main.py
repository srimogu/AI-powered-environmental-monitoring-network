import network
import time
import ujson
from machine import Pin, ADC
from umqtt.simple import MQTTClient
from air_polution import predict_risk
 
# WiFi/MQTT are OPTIONAL - the risk decision runs locally on-device (edge AI)
# and keeps working even without connectivity.
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""
 
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = b"hackathon/disaster/air_pollution"
CLIENT_ID = "wokwi-air-pollution"
 
# ---- Sensors (pins match diagram.json) ----
nox_adc = ADC(Pin(32))   # gas2 -> NOx
so2_adc = ADC(Pin(33))   # gas1 -> SO2
co_adc = ADC(Pin(34))    # gas3 -> CO
for a in (nox_adc, so2_adc, co_adc):
    a.atten(ADC.ATTN_11DB)
 
# Scaling ranges in mg/Nm3, set above each pollutant's "High" threshold
# so the full sensor range can express both safe and hazardous readings.
MAX_SO2 = 200   # High threshold: 150
MAX_NOX = 400   # High threshold: 300
MAX_CO = 150    # High threshold: 100
 
# ---- RGB LED (common cathode) ----
led_r = Pin(27, Pin.OUT)
led_g = Pin(26, Pin.OUT)
led_b = Pin(14, Pin.OUT)
 
 
def set_led(risk):
    led_r.value(0)
    led_g.value(0)
    led_b.value(0)
    if risk == "Low":
        led_g.value(1)
    elif risk == "Medium":
        led_r.value(1)
        led_g.value(1)
    elif risk == "High":
        led_r.value(1)
 
 
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("WiFi connected:", wlan.ifconfig())
    return wlan
 
 
def connect_mqtt():
    client = MQTTClient(CLIENT_ID, MQTT_BROKER, keepalive=60)
    client.connect()
    print("MQTT connected to", MQTT_BROKER)
    return client
 
 
mqtt = None
try:
    connect_wifi()
    mqtt = connect_mqtt()
except Exception as e:
    print("WiFi/MQTT unavailable, continuing in offline edge mode:", e)
 
while True:
    so2 = (so2_adc.read() / 4095) * MAX_SO2
    nox = (nox_adc.read() / 4095) * MAX_NOX
    co = (co_adc.read() / 4095) * MAX_CO
 
    # ---- EDGE AI: decision happens on-device ----
    risk = predict_risk(so2, nox, co)
    set_led(risk)
 
    print("SO2: {:.1f} mg/Nm3  NOx: {:.1f} mg/Nm3  CO: {:.1f} mg/Nm3 -> Risk: {}".format(
        so2, nox, co, risk))
 
    if mqtt:
        payload = ujson.dumps({
            "so2_mg_per_Nm3": round(so2, 2),
            "nox_mg_per_Nm3": round(nox, 2),
            "co_mg_per_Nm3": round(co, 2),
            "risk": risk,
        })
        try:
            mqtt.publish(MQTT_TOPIC, payload.encode())
        except Exception as e:
            print("MQTT publish failed:", e)
            try:
                mqtt = connect_mqtt()
            except Exception:
                mqtt = None
 
    time.sleep(2)