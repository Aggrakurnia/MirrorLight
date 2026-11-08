import time
import requests

URL = 'http://localhost:8000/api/telemetry'
HEADERS = {'X-API-Key': 'ganti-api-key'}

for i in range(1, 6):
    body = {'device_id': 'glowlight-01', 'seq': i, 'ts': int(time.time()),
            'uptime_ms': i * 2000, 'ldr_raw': 1800 + i, 'ldr_pct': 44,
            'presence': True, 'lamp_on': True, 'duty': 140, 'mode': 'auto'}
    r = requests.post(URL, json=body, headers=HEADERS, timeout=5)
    print(i, r.status_code, r.text)
    time.sleep(1)