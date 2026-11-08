import json, os, sqlite3, threading, time
import requests
import paho.mqtt.client as mqtt

API_URL = os.getenv('API_URL', 'http://localhost:8000/api/telemetry')
API_KEY = os.getenv('API_KEY', 'ganti-api-key')
MQTT_HOST = os.getenv('MQTT_HOST', 'localhost')
MQTT_USER = os.getenv('MQTT_USER', '')
MQTT_PASS = os.getenv('MQTT_PASS', '')

lock = threading.Lock()
db = sqlite3.connect('buffer.db', check_same_thread=False)
db.execute('CREATE TABLE IF NOT EXISTS q (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT, received REAL)')
db.commit()

def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe('unib/glowlight/+/+/telemetry', qos=1)

def on_message(client, userdata, msg):
    try:
        json.loads(msg.payload)
    except ValueError:
        return
    with lock:
        db.execute('INSERT INTO q(payload, received) VALUES (?, ?)',
                   (msg.payload.decode(), time.time()))
        db.commit()

def flush():
    with lock:
        rows = db.execute('SELECT id, payload, received FROM q ORDER BY id LIMIT 50').fetchall()
    for row_id, payload, received in rows:
        data = json.loads(payload)
        if not data.get('ts'):
            data['ts'] = int(received)
        try:
            r = requests.post(API_URL, json=data, headers={'X-API-Key': API_KEY}, timeout=5)
        except requests.RequestException as e:
            print('API tidak terjangkau, data ditahan:', e)
            return
        if r.status_code in (200, 422):          # 422 = payload tidak valid, dibuang
            with lock:
                db.execute('DELETE FROM q WHERE id = ?', (row_id,))
                db.commit()
        else:
            print('API menolak data, status', r.status_code)
            return

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
if MQTT_USER:
    client.username_pw_set(MQTT_USER, MQTT_PASS)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, 1883)
client.loop_start()

while True:
    flush()
    time.sleep(2)