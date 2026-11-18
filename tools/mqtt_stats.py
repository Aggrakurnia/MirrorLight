import json, os, statistics, sys, time
import paho.mqtt.client as mqtt

DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 300
HOST = sys.argv[2] if len(sys.argv) > 2 else 'localhost'

received = lost = restarts = 0
last_seq = None
arrivals = []

def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe('unib/glowlight/+/+/telemetry', qos=1)

def on_message(client, userdata, msg):
    global received, lost, restarts, last_seq
    try:
        seq = json.loads(msg.payload)['seq']
    except (ValueError, KeyError):
        return
    received += 1
    arrivals.append(time.time())
    if last_seq is not None:
        if seq > last_seq + 1:
            lost += seq - last_seq - 1
        elif seq <= last_seq:
            restarts += 1            # ESP32 reset, seq mulai dari 1 lagi
    last_seq = seq

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
if os.getenv('MQTT_USER'):
    client.username_pw_set(os.getenv('MQTT_USER'), os.getenv('MQTT_PASS', ''))
client.on_connect = on_connect
client.on_message = on_message
client.connect(HOST, 1883)
client.loop_start()
time.sleep(DURATION)
client.loop_stop()

total = received + lost
gaps = [b - a for a, b in zip(arrivals, arrivals[1:])]
print(f'Durasi: {DURATION} detik')
print(f'Diterima: {received}, hilang: {lost}, restart: {restarts}')
if total:
    print(f'Packet loss: {lost * 100 / total:.2f}%')
if gaps:
    print(f'Selang antar pesan: rata-rata {statistics.mean(gaps):.2f} s, maks {max(gaps):.2f} s')