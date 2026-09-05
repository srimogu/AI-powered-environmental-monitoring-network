import network
import time
import ujson
from machine import Pin, ADC, I2C
from umqtt.simple import MQTTClient
from mpu6050 import MPU6050
from landslide_model import predict_risk

# WiFi/MQTT are OPTIONAL - the risk decision runs locally on-device (edge AI)
# and keeps working even without connectivity.
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""

MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = b"hackathon/disaster/landslide"
CLIENT_ID = "wokwi-landslide"

# ---- Sensors ----
soil_adc = ADC(Pin(34))
soil_adc.atten(ADC.ATTN_11DB)

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
mpu = MPU6050(i2c)

# ---- RGB LED (common cathode) ----
led_r = Pin(27, Pin.OUT)
led_g = Pin(26, Pin.OUT)
led_b = Pin(25, Pin.OUT)


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
    soil_moisture = (soil_adc.read() / 4095) * 100  # 0-100%
    tilt = mpu.read_tilt_deg()                       # 0-90 degrees

    # ---- EDGE AI: decision happens on-device ----
    risk = predict_risk(soil_moisture, tilt)
    set_led(risk)

    print("Soil moisture: {:.1f}%  Tilt: {:.1f}deg -> Risk: {}".format(
        soil_moisture, tilt, risk))

    if mqtt:
        payload = ujson.dumps({
            "soil_moisture_percent": round(soil_moisture, 2),
            "tilt_deg": round(tilt, 2),
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