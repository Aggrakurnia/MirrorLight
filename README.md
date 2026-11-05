# GlowLight: Lampu Cermin Rias Otomatis

Proyek Teknologi IoT, Prodi S1 Informatika FT UNIB. Tema: Solusi IoT untuk Bengkulu Tangguh dan Cerdas.

## Tim
| Anggota | Nama | Peran |
|---|---|---|
| 1 | (isi) | Device & Firmware Engineer |
| 2 | (isi) | Back-End & Data Engineer |
| 3 | (isi) | Security & DevOps Engineer |
| 4 | (isi) | Dashboard Engineer & Project Manager |

## Ringkasan
Sensor PIR dan LDR mengatur kecerahan LED strip lewat ESP32. Data dikirim via MQTT ke gateway, API, InfluxDB, dan dashboard Grafana. Kontrol dan alert lewat Telegram.

## Arsitektur 5 lapis
(tempel diagram dan tabel pemetaan lapisan)

## Struktur repositori
firmware/, edge-gateway/, backend-api/, bot/, docker/, grafana/, docs/

## Cara menjalankan
1. Salin .env.example menjadi .env lalu isi nilainya.
2. cd docker lalu docker compose --env-file ../.env up -d --build
3. Jalankan gateway: python edge-gateway/gateway.py
4. Jalankan bot: python bot/telegram_bot.py
5. Unggah firmware dari folder firmware/ dengan PlatformIO.

## Aturan kontribusi
Branch per fitur, Pull Request, review silang, jangan commit rahasia.

