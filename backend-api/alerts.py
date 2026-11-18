import os, statistics, time
from collections import defaultdict, deque

import requests

TG_TOKEN = os.getenv('TG_TOKEN', '')
TG_CHAT = os.getenv('TG_CHAT', '')
LAMP_MAX_SECONDS = 2 * 3600

ldr_hist = defaultdict(lambda: deque(maxlen=60))
lamp_since = {}
last_alert = defaultdict(float)

def notify(text):
    if not TG_TOKEN or not TG_CHAT:
        print('ALERT:', text)
        return
    try:
        requests.post(f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage',
                      json={'chat_id': TG_CHAT, 'text': text}, timeout=5)
    except requests.RequestException:
        pass                  # alert tidak boleh menggagalkan penyimpanan data

def cooldown_ok(key, seconds=600):
    now = time.time()
    if now - last_alert[key] > seconds:
        last_alert[key] = now
        return True
    return False

def check(t):
    dev = t['device_id']

    # 1) Lampu menyala terlalu lama
    if t['lamp_on']:
        start = lamp_since.setdefault(dev, time.time())
        if time.time() - start > LAMP_MAX_SECONDS and cooldown_ok(dev + ':lama', 3600):
            notify(f'GlowLight {dev}: lampu menyala lebih dari 2 jam. Kirim /mati untuk mematikan.')
    else:
        lamp_since.pop(dev, None)

    # 2) Anomali cahaya (z-score)
    hist = ldr_hist[dev]
    if len(hist) >= 20:
        sd = statistics.pstdev(hist)
        if sd > 0:
            z = (t['ldr_pct'] - statistics.mean(hist)) / sd
            if abs(z) >= 3 and cooldown_ok(dev + ':anomali'):
                notify(f'GlowLight {dev}: pembacaan cahaya tidak wajar (z={z:.1f}). Cek sensor LDR.')
    hist.append(t['ldr_pct'])