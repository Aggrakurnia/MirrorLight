import json, os, time

import requests
import paho.mqtt.publish as publish

TOKEN = os.getenv('TG_TOKEN', '')
OWNER = int(os.getenv('TG_CHAT', '0'))
API_URL = os.getenv('API_URL', 'http://localhost:8000')
API_KEY = os.getenv('API_KEY', '')
MQTT_HOST = os.getenv('MQTT_HOST', 'localhost')
MQTT_USER = os.getenv('MQTT_USER', '')
MQTT_PASS = os.getenv('MQTT_PASS', '')
TOPIC_CMD = 'unib/glowlight/kelompok-02/cermin01/cmd'
TG = f'https://api.telegram.org/bot{TOKEN}'

def send(text):
    requests.post(f'{TG}/sendMessage', json={'chat_id': OWNER, 'text': text}, timeout=10)

def publish_cmd(payload):
    auth = {'username': MQTT_USER, 'password': MQTT_PASS} if MQTT_USER else None
    publish.single(TOPIC_CMD, json.dumps(payload), qos=1,
                   hostname=MQTT_HOST, port=1883, auth=auth)

def status_text():
    r = requests.get(f'{API_URL}/api/latest', headers={'X-API-Key': API_KEY}, timeout=5)
    d = r.json()
    if not d:
        return 'Belum ada data dalam 10 menit terakhir.'
    pct = round(d.get('duty', 0) * 100 / 255)
    lampu = 'menyala' if d.get('lamp_on') else 'mati'
    orang = 'ya' if d.get('presence') else 'tidak'
    return (f"GlowLight {d.get('device_id', '')}\n"
            f"Mode: {d.get('mode')}\n"
            f"Lampu: {lampu} (kecerahan {pct}%)\n"
            f"Cahaya ruangan: {d.get('ldr_pct')}%\n"
            f"Ada orang: {orang}")

def handle(text):
    parts = text.strip().split()
    if not parts:
        return
    cmd = parts[0].lower()
    if cmd == '/status':
        send(status_text())
    elif cmd == '/nyala':
        publish_cmd({'mode': 'manual', 'brightness': 200})
        send('Lampu dinyalakan (manual).')
    elif cmd == '/mati':
        publish_cmd({'mode': 'manual', 'brightness': 0})
        send('Lampu dimatikan (manual).')
    elif cmd == '/terang' and len(parts) > 1 and parts[1].isdigit():
        pct = min(int(parts[1]), 100)
        publish_cmd({'mode': 'manual', 'brightness': round(pct * 255 / 100)})
        send(f'Kecerahan diatur ke {pct}% (manual).')
    elif cmd == '/auto':
        publish_cmd({'mode': 'auto'})
        send('Kembali ke mode otomatis.')
    else:
        send('Perintah: /status /nyala /mati /terang 80 /auto')

def main():
    offset = 0
    while True:
        try:
            r = requests.get(f'{TG}/getUpdates',
                             params={'timeout': 30, 'offset': offset}, timeout=40).json()
            for u in r.get('result', []):
                offset = u['update_id'] + 1
                m = u.get('message', {})
                if m.get('chat', {}).get('id') != OWNER:
                    continue                 # abaikan selain pemilik
                handle(m.get('text', ''))
        except (requests.RequestException, OSError) as e:
            print('error:', e)
            time.sleep(5)

if __name__ == '__main__':
    main()