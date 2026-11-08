# Skema Data InfluxDB (MirrorLight / GlowLight)

Dokumen ini menjelaskan cara data telemetri disimpan di InfluxDB, alasan memilih database time-series, dan kebijakan retensinya.

## 1. Pemetaan Istilah InfluxDB

InfluxDB adalah **database time-series**: dioptimalkan untuk data yang datang terus-menerus dengan stempel waktu.

| Istilah | Arti | Pada GlowLight |
| --- | --- | --- |
| Organization | Ruang kerja pengguna | `unib` |
| Bucket | Wadah data (mirip database) | `glowlight` |
| Measurement | Jenis data (mirip tabel) | `glowlight` |
| Tag | Label untuk memfilter, diindeks | `device_id` |
| Field | Nilai yang diukur | `ldr_raw`, `ldr_pct`, `presence`, `lamp_on`, `duty`, `mode`, `seq` |
| Timestamp | Waktu data | dari `ts` (atau waktu terima gateway bila `ts` = 0) |

## 2. Rincian Field

| Field | Tipe | Rentang | Keterangan |
| --- | --- | --- | --- |
| `seq` | integer | >= 0 | Nomor urut pesan dari ESP32, dipakai untuk menghitung packet loss |
| `ldr_raw` | integer | 0-4095 | Pembacaan mentah ADC 12-bit dari sensor LDR |
| `ldr_pct` | integer | 0-100 | Intensitas cahaya ruangan dalam persen |
| `presence` | boolean | true/false | Ada orang terdeteksi oleh sensor PIR |
| `lamp_on` | boolean | true/false | Status lampu LED strip |
| `duty` | integer | 0-255 | Duty cycle PWM, menentukan kecerahan lampu |
| `mode` | string | `auto` / `manual` | Mode kerja lampu |

Tag `device_id` (contoh: `glowlight-01`) membedakan perangkat. Hanya satu tag yang dipakai agar kardinalitas data tetap rendah.

## 3. Contoh Data

Telemetri JSON dari ESP32:

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

Titik data yang tersimpan di InfluxDB (line protocol, disederhanakan):

```
glowlight,device_id=glowlight-01 seq=42i,ldr_raw=1850i,ldr_pct=45i,presence=true,lamp_on=true,duty=140i,mode="auto" 1767000000
```

Catatan: `uptime_ms` hanya divalidasi API dan tidak disimpan sebagai field.

## 4. Mengapa Time-Series Database

InfluxDB dipilih dibanding database relasional biasa (misalnya MySQL) karena:

- **Penulisan sangat sering dan berurutan waktu.** Telemetri datang tiap sekitar 2 detik dan terus bertambah, sehingga throughput penulisan yang tinggi dibutuhkan.
- **Retensi dan agregasi waktu bawaan.** Data lama dapat dihapus otomatis, dan agregasi seperti rata-rata per menit tersedia langsung di kueri.
- **Kueri berbasis rentang waktu sangat cepat.** Pola kueri utama proyek ini ("data 10 menit terakhir", "grafik 1 jam terakhir") sesuai dengan keunggulan database time-series.
- **Integrasi langsung dengan Grafana.** Dashboard dapat membaca InfluxDB tanpa lapisan tambahan.

## 5. Penanganan Pesan Duplikat

InfluxDB menimpa titik data yang memiliki **measurement, tag, dan timestamp yang sama**. Karena itu, pengiriman ulang pesan oleh gateway (store-and-forward) tidak membuat data ganda, dan pengiriman berulang bersifat aman (idempoten).

## 6. Kebijakan Retensi

- Bucket `glowlight` dibatasi **30 hari** agar penyimpanan tidak penuh.
- Pengaturan: Load Data, Buckets, `glowlight`, Settings, Delete Data: **Older Than 30 days**.
- Untuk analisis jangka panjang, data dapat diagregasi (misalnya rata-rata per menit) sebelum data mentah kedaluwarsa.

## 7. Contoh Kueri Flux

Data terakhir perangkat dalam 10 menit terakhir:

```
from(bucket: "glowlight")
  |> range(start: -10m)
  |> filter(fn: (r) => r._measurement == "glowlight" and r.device_id == "glowlight-01")
  |> last()
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
```

Rata-rata cahaya ruangan per menit selama 1 jam terakhir:

```
from(bucket: "glowlight")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "glowlight" and r._field == "ldr_pct")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
```
