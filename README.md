# MirrorLight

# GlowLight: Lampu Cermin Rias Otomatis

Proyek Teknologi IoT, Prodi S1 Informatika FT UNIB.  
**Tema:** Solusi IoT untuk Bengkulu Tangguh dan Cerdas.

---

## Tim Kelompok 2
| No | Nama | Peran |
|---|---|---|
| 1 | Aisyah | Device & Firmware Engineer |
| 2 | Nurul | Back-End & Data Engineer |
| 3 | Gellael | Security & DevOps Engineer |
| 4 | Aggra | Dashboard Engineer & Project Manager |

---

## Ringkasan Proyek
GlowLight adalah sistem lampu cermin rias otomatis berbasis ESP32. Sensor PIR mendeteksi kehadiran pengguna, sementara sensor LDR mengukur intensitas cahaya ruangan untuk menyesuaikan kecerahan LED strip secara otomatis (PWM). Data telemetri dikirim via MQTT ke gateway, diproses oleh API FastAPI, disimpan di InfluxDB, dan divisualisasikan melalui Grafana. Sistem juga dilengkapi dengan notifikasi deteksi anomali serta fitur kontrol manual via Bot Telegram.

---

## Arsitektur 5 Lapis
1. **Persepsi & Perangkat:** Sensor LDR, Sensor PIR, LED Strip, MOSFET IRLZ44N, ESP32 DevKit V1.
2. **Transpor & Edge:** Wi-Fi, MQTT Broker (Mosquitto), Edge Gateway (Python & SQLite Queue).
3. **Pemrosesan & Data:** FastAPI Backend Service, InfluxDB (Time-series Database).
4. **Aplikasi & Visualisasi:** Dashboard Grafana, Bot & Alert Telegram (Z-score anomaly detection).
5. **Bisnis & Tata Kelola:** Efisiensi energi lampu rias, integrasi UMKM salon/rias, kepatuhan data (UU PDP).

---

## Struktur Repositori
```text
MirrorLight/
├── firmware/       # Kode PlatformIO / C++ ESP32
├── edge-gateway/   # Script Gateway MQTT-to-HTTP (Python)
├── backend-api/    # API Telemetri FastAPI & logika Alert
├── bot/            # Bot Telegram untuk kontrol & status
├── docker/         # Docker Compose & konfigurasi Mosquitto/InfluxDB/Grafana
├── grafana/        # Dashboard JSON Grafana
└── docs/           # Proposal, threat model, dan dokumentasi pengujian
