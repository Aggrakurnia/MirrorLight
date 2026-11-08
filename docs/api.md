# Dokumentasi API GlowLight

Base URL pengembangan: `http://localhost:8000`. Dokumentasi interaktif (Swagger) tersedia di `/docs`.

## Autentikasi

Semua endpoint di bawah `/api` memerlukan salah satu dari:

- Header `X-API-Key: <kunci>`
- Header `Authorization: Bearer <JWT>`

Tanpa kredensial yang sah, API menjawab `401`. `GET /health` tidak memerlukan autentikasi.

## Ringkasan endpoint

| Metode | Path | Fungsi | Autentikasi |
|---|---|---|---|
| GET | `/health` | Cek layanan hidup | Tidak ada |
| POST | `/api/telemetry` | Menyimpan satu telemetri | Ya |
| GET | `/api/latest` | Data terbaru dalam 10 menit terakhir | Ya |
| GET | `/api/history` | Riwayat satu field, rata-rata per menit | Ya |

## GET /health

Respons `200`:

```json
{"status": "ok"}
```

## POST /api/telemetry

Menyimpan satu telemetri ke InfluxDB (measurement `glowlight`, tag `device_id`).

Body JSON:

| Field | Tipe | Batas | Keterangan |
|---|---|---|---|
| device_id | string | wajib | Pengenal perangkat, menjadi tag |
| seq | integer | wajib | Nomor urut pesan |
| ts | integer | opsional, default 0 | Waktu Unix (detik). Jika 0, dipakai waktu server |
| uptime_ms | integer | wajib | Lama perangkat menyala (ms) |
| ldr_raw | integer | 0 sampai 4095 | Nilai mentah sensor cahaya |
| ldr_pct | integer | 0 sampai 100 | Tingkat cahaya (%) |
| presence | boolean | wajib | Ada orang atau tidak |
| lamp_on | boolean | wajib | Status lampu |
| duty | integer | 0 sampai 255 | Duty cycle PWM |
| mode | string | wajib | Mode kerja, misalnya `auto` |

Contoh permintaan:

```json
{
  "device_id": "glowlight-01",
  "seq": 42,
  "ts": 1767000000,
  "uptime_ms": 84000,
  "ldr_raw": 1850,
  "ldr_pct": 45,
  "presence": true,
  "lamp_on": true,
  "duty": 140,
  "mode": "auto"
}
```

Respons `200`:

```json
{"ok": true}
```

Respons `422` jika payload tidak valid (misalnya `ldr_raw` 5000). Isinya menjelaskan field yang salah.

Catatan: dua pesan dengan `device_id` dan `ts` yang sama saling menimpa di InfluxDB karena resolusi waktu 1 detik.

## GET /api/latest

Mengambil data terbaru satu perangkat dalam 10 menit terakhir.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| device_id | string | `glowlight-01` | Pola `^[A-Za-z0-9_-]{1,40}$` |

Contoh: `GET /api/latest?device_id=glowlight-01`

Respons `200`:

```json
{
  "_time": "2026-11-08T11:58:03+00:00",
  "device_id": "glowlight-01",
  "duty": 140,
  "lamp_on": true,
  "ldr_pct": 45,
  "ldr_raw": 1850,
  "mode": "auto",
  "presence": true,
  "seq": 426
}
```

Jika tidak ada data dalam 10 menit terakhir, respons berupa objek kosong `{}`.

## GET /api/history

Mengambil riwayat satu field, dirata-ratakan per menit.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| device_id | string | wajib | Pola `^[A-Za-z0-9_-]{1,40}$` |
| field | string | `ldr_pct` | Salah satu dari `ldr_pct`, `ldr_raw`, `duty` |
| minutes | integer | 60 | Rentang waktu ke belakang, 1 sampai 1440 |

Contoh: `GET /api/history?device_id=glowlight-01&field=ldr_raw&minutes=1440`

Respons `200`:

```json
{
  "device_id": "glowlight-01",
  "field": "ldr_raw",
  "points": [
    {"time": "2026-11-08T08:39:00+00:00", "value": 1850.0},
    {"time": "2026-11-08T08:50:00+00:00", "value": 1850.0}
  ]
}
```

Catatan:

- Beberapa pesan dalam menit yang sama digabung menjadi satu titik (rata-rata), sehingga `value` bertipe desimal.
- Menit tanpa data tidak muncul di `points`.
- Nilai `field` atau `minutes` di luar batas ditolak dengan `422`.

## Kode status

| Kode | Arti |
|---|---|
| 200 | Berhasil |
| 401 | Kredensial tidak ada atau tidak cocok |
| 422 | Parameter atau body tidak valid |