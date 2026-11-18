import pytest
from pydantic import ValidationError

from main import Telemetry

def valid():
    return dict(device_id='glowlight-01', seq=1, ts=0, uptime_ms=1000,
                ldr_raw=1000, ldr_pct=24, presence=True, lamp_on=True,
                duty=100, mode='auto')

def test_valid():
    Telemetry(**valid())

def test_ldr_raw_out_of_range():
    d = valid()
    d['ldr_raw'] = 5000
    with pytest.raises(ValidationError):
        Telemetry(**d)

def test_missing_field():
    d = valid()
    del d['mode']
    with pytest.raises(ValidationError):
        Telemetry(**d)