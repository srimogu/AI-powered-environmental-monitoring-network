import network
import time
import ujson
from machine import Pin, ADC
import dht
from umqtt.simple import MQTTClient
from wildfire_model import predict_risk

# ---- WiFi (Wokwi's simulated WiFi with real internet access) ----
# NOTE: WiFi/MQTT here is OPTIONAL - only used to report the verdict to the
# dashboard. The risk decision itself (predict_risk) runs locally on this
# device and works even if WiFi is unavailable.
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""

# ---- MQTT (public broker - no account needed) ----
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = b"hackathon/disaster/wildfire"
CLIENT_ID = "wokwi-wildfire"

# ---- Sensors (pins match diagram.json) ----
dht_sensor = dht.DHT22(Pin(32))
smoke_adc = ADC(Pin(33))
smoke_adc.atten(ADC.ATTN_11DB)
wind_adc = ADC(Pin(35))
wind_adc.atten(ADC.ATTN_11DB)

MAX_WIND_SPEED_KMH = 70
MAX_SMOKE_INDEX = 100

# ---- RGB LED (common cathode) - local, no-connectivity-required indicator ----
led_r = Pin(14, Pin.OUT)
led_g = Pin(27, Pin.OUT)
led_b = Pin(26, Pin.OUT)


def set_led(risk):
    # Common cathode: HIGH turns each color ON
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


# Try to get connectivity, but don't block forever if it's unavailable -
# the device must keep working (edge AI) even without it.
mqtt = None
try:
    connect_wifi()
    mqtt = connect_mqtt()
except Exception as e:
    print("WiFi/MQTT unavailable, continuing in offline edge mode:", e)

while True:
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
    except OSError:
        print("DHT read error, skipping cycle")
        time.sleep(2)
        continue

    smoke = (smoke_adc.read() / 4095) * MAX_SMOKE_INDEX
    wind = (wind_adc.read() / 4095) * MAX_WIND_SPEED_KMH

    # ---- EDGE AI: decision happens right here, on-device ----
    risk = predict_risk(temp, humidity, wind, smoke)

    # Local, instant, no-connectivity-required response
    set_led(risk)

    print("Temp: {:.1f}C Hum: {:.1f}% Wind: {:.1f}km/h Smoke: {:.1f} -> Risk: {}".format(
        temp, humidity, wind, smoke, risk))

    # OPTIONAL: report the verdict upstream if connectivity exists
    if mqtt:
        payload = ujson.dumps({
            "temperature_C": round(temp, 2),
            "humidity_percent": round(humidity, 2),
            "wind_speed_kmh": round(wind, 2),
            "smoke_index": round(smoke, 2),
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
