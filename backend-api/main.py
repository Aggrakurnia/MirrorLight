import os
from datetime import datetime, timezone

from fastapi import Depends, FastAPI
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from pydantic import BaseModel, Field

import alerts                                   # milik Anggota 4
from auth import require_auth, router as auth_router   # milik Anggota 3

BUCKET = os.getenv('INFLUX_BUCKET', 'glowlight')
influx = InfluxDBClient(url=os.getenv('INFLUX_URL', 'http://localhost:8086'),
                        token=os.getenv('INFLUX_TOKEN', ''),
                        org=os.getenv('INFLUX_ORG', 'unib'))
write_api = influx.write_api(write_options=SYNCHRONOUS)

app = FastAPI(title='GlowLight API', version='1.0')
app.include_router(auth_router)

class Telemetry(BaseModel):
    device_id: str
    seq: int
    ts: int = 0
    uptime_ms: int
    ldr_raw: int = Field(ge=0, le=4095)
    ldr_pct: int = Field(ge=0, le=100)
    presence: bool
    lamp_on: bool
    duty: int = Field(ge=0, le=255)
    mode: str

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/api/telemetry')
def ingest(t: Telemetry, user: str = Depends(require_auth)):
    when = (datetime.fromtimestamp(t.ts, tz=timezone.utc) if t.ts > 0
            else datetime.now(timezone.utc))
    point = (Point('glowlight')
             .tag('device_id', t.device_id)
             .field('seq', t.seq)
             .field('ldr_raw', t.ldr_raw)
             .field('ldr_pct', t.ldr_pct)
             .field('presence', t.presence)
             .field('lamp_on', t.lamp_on)
             .field('duty', t.duty)
             .field('mode', t.mode)
             .time(when, WritePrecision.S))
    write_api.write(bucket=BUCKET, record=point)
    alerts.check(t.model_dump())
    return {'ok': True}