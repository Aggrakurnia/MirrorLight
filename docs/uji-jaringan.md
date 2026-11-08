# Laporan Uji Jaringan

Pengujian dilakukan pada lingkungan lokal (Docker: Mosquitto dan InfluxDB, FastAPI via uvicorn, gateway.py). Data dikirim manual lewat MQTT Explorer karena perangkat ESP32 belum tersedia saat pengujian.

## 1. Uji send_sample.py

| Hal | Hasil |
|---|---|
| Pesan dikirim | 5 (seq 1-5, jeda 1 detik) |
| Respons API | 5 x `200 {"ok":true}` |
| Data di InfluxDB | seq 1-5 tersimpan |

## 2. Uji mqtt_stats.py (simulasi celah seq)

Pesan dikirim manual dengan seq 1, 2, 3, 5 (seq 4 sengaja dilewati) selama penghitung berjalan.

| Hal | Hasil |
|---|---|
| Diterima | 4 |
| Hilang | 1 |
| Restart | 0 |
| Packet loss | 20,00% |

Hasil ini membuktikan alat mendeteksi celah nomor seq. Pengukuran packet loss sungguhan (10 menit) menunggu ESP32.

## 3. Uji store-and-forward

| Hal | Hasil |
|---|---|
| Pesan dikirim saat API mati | 7 (seq 421-427) |
| Isi antrean saat API mati | 7 |
| API dimatikan / dinyalakan | 18:57 / 18:58 WIB |
| Isi antrean setelah API hidup | 0 |
| Respons API setelah hidup | 7 x `200 OK` |
| Pesan hilang | 0 |
| Waktu data di InfluxDB | sesuai waktu kirim asli, tersebar 18:57 sampai 18:58 WIB |

Selama API mati, gateway mencetak `API tidak terjangkau, data ditahan`. Setelah API hidup, seluruh pesan terkirim dan antrean kosong. Gateway mengisi `ts` dengan waktu penerimaan pesan, sehingga data tersimpan dengan waktu aslinya, bukan waktu pengiriman ulang.

## 4. Pengukuran yang belum dilakukan

Menunggu ESP32 dari Anggota 1:

| Uji | Cara | Hasil |
|---|---|---|
| Packet loss 10 menit | mqtt_stats.py 600 | belum diukur |
| Packet loss saat sinyal lemah | jauhkan ESP32 dari router | belum diukur |
| Selang pesan | mqtt_stats.py | belum diukur (target sekitar 2 s) |
| Latensi perintah | kirim cmd, ukur sampai lampu berubah | belum diukur |

## 5. Catatan

`ts` dari NTP hanya beresolusi 1 detik, sehingga latensi telemetri tidak bisa diukur lebih teliti dari itu. Dua pesan dengan tag dan `ts` yang sama saling menimpa di InfluxDB.