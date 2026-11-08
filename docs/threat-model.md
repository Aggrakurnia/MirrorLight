# Threat Model GlowLight (MirrorLight)

Proyek "GlowLight: Lampu Cermin Rias Otomatis", Kelompok 2, Mata Kuliah Teknologi IoT, Prodi S1 Informatika FT UNIB.

Dokumen ini dikelola oleh Anggota 3 (Security & DevOps Engineer). Status pada tabel diperbarui seiring kemajuan proyek, dan hanya ditandai "Ditangani" bila kontrolnya sudah dibuat dan diuji (lihat `docs/uji-keamanan.md`).

## 1. Gambaran Sistem

```
ESP32 (lampu cermin)
   |  MQTT over TLS (port 8883, login + ACL)
   v
Broker Mosquitto
   |
   +--> Gateway (Python) --> API FastAPI (API key / JWT) --> InfluxDB --> Grafana
   |
   +--> Bot Telegram (publish perintah ke topik cmd)
```

Semua layanan berjalan dengan Docker Compose (`docker/docker-compose.yml`). Rahasia disimpan di `.env` dan `firmware/include/secrets.h` yang tidak di-commit.

## 2. Aset

| No | Aset | Alasan perlu dilindungi |
|---|---|---|
| 1 | Perangkat ESP32 dan lampu | Dapat dikendalikan atau diambil alih |
| 2 | Broker MQTT | Jalur semua telemetri dan perintah |
| 3 | API dan token JWT / API key | Pintu akses ke data dan fungsi sistem |
| 4 | Database InfluxDB | Menyimpan riwayat telemetri dan kehadiran |
| 5 | Token bot Telegram | Memberi kendali atas bot |
| 6 | Data kehadiran pengguna | Dapat mengungkap kebiasaan pribadi |
| 7 | Rahasia (`.env`, `secrets.h`, `passwd`, `server.key`) | Kebocoran membuka akses ke semua aset di atas |

## 3. Analisis STRIDE

| No | Ancaman | Contoh pada GlowLight | Dampak | Mitigasi | Status |
|---|---|---|---|---|---|
| 1 | **S**poofing | Pihak lain berpura-pura menjadi ESP32 atau pemilik | Telemetri atau perintah palsu | Login MQTT per akun (`esp32_cermin01`, `gateway`, `bot`), TLS pada broker, API key / JWT pada API | Sebagian: login dan TLS broker aktif; klien belum dipindah ke TLS |
| 2 | **S**poofing | Chat Telegram dari orang lain menyalakan lampu | Kontrol tidak sah | Bot memeriksa `chat_id` pemilik | Menunggu verifikasi (komponen Anggota 4) |
| 3 | **T**ampering | Payload diubah di jaringan | Data salah tersimpan | TLS, validasi Pydantic pada API | Sebagian: TLS broker aktif; klien belum TLS |
| 4 | **T**ampering | Firmware ESP32 diganti | Perangkat dikuasai | Akses fisik dibatasi; OTA aman sebagai pengembangan | Risiko terbuka |
| 5 | **R**epudiation | Tidak ada jejak siapa mengubah mode lampu | Sulit ditelusuri | Log perintah di bot/API | Sebagian |
| 6 | **I**nformation disclosure | Topik MQTT dibaca pihak luar | Pola kehadiran bocor | ACL per topik, TLS, tidak memakai broker publik | Sebagian: ACL dan TLS broker aktif; klien belum TLS |
| 7 | **I**nformation disclosure | `.env` atau `secrets.h` ter-commit | Rahasia bocor | `.gitignore`, `.env.example` tanpa nilai, rotasi rahasia bila bocor | Perlu verifikasi akhir (`git ls-files`, uji no. 10) |
| 8 | **D**enial of service | Banjir pesan ke broker atau API | Layanan lumpuh | Batas koneksi, ACL, antrean gateway | Sebagian |
| 9 | **E**levation of privilege | Perangkat mem-publish ke topik `cmd` | Mengendalikan lampu | ACL: ESP32 hanya `read` pada `cmd` | Ditangani di konfigurasi ACL; pengujian tercatat di `docs/uji-keamanan.md` |
| 10 | **E**levation of privilege | Token JWT dicuri | Akses API | Kedaluwarsa 1 jam, perbandingan waktu konstan (`compare_digest`), TLS | Sebagian |

## 4. Pemetaan OWASP IoT Top 10 (2018)

| Kode | Risiko | Tanggapan GlowLight | Status |
|---|---|---|---|
| I1 | Kata sandi lemah atau tertanam | Sandi acak, disimpan di `.env` dan `secrets.h` yang di-ignore | Sebagian: bergantung pada `.gitignore` di `main` |
| I2 | Layanan jaringan tidak aman | Login, ACL, dan TLS pada broker | Ditangani di broker |
| I3 | Antarmuka ekosistem tidak aman | API memakai API key / JWT, input divalidasi | Sebagian: uji API menunggu `main` terisi |
| I4 | Tanpa mekanisme pembaruan aman | Belum ada (OTA aman sebagai pengembangan) | Risiko terbuka |
| I5 | Komponen usang | Image Docker bertag (`eclipse-mosquitto:2`, `influxdb:2.7`); `requirements.txt` belum menyematkan versi | Sebagian |
| I6 | Privasi kurang terlindungi | Minimalkan data, retensi 30 hari, akses terbatas | Sebagian |
| I7 | Transfer dan penyimpanan data tidak aman | TLS saat transfer, token untuk database | Sebagian: TLS broker aktif; klien belum TLS |
| I8 | Tanpa manajemen perangkat | Status online/offline lewat LWT | Bergantung firmware |
| I9 | Pengaturan default tidak aman | `allow_anonymous false`, tanpa kredensial bawaan | Ditangani di broker |
| I10 | Perangkat tidak diperkeras secara fisik | Dicatat sebagai risiko; port USB terbuka | Risiko terbuka |

## 5. Risiko Terbuka

1. **Firmware dapat diganti** lewat akses fisik (port USB) karena belum ada firmware bertanda tangan.
2. **Tidak ada pembaruan jarak jauh yang aman** (OTA). Perlu dirancang sebagai pengembangan.
3. **Sertifikat TLS self-signed terikat ke IP laptop broker.** Bila IP berubah, sertifikat harus dibuat ulang dengan `docker/gen-certs.sh` dan `ca.crt` dibagikan ulang ke klien.
4. **Klien (gateway, bot, ESP32) belum dipindah ke TLS.** Pekerjaan ini ada di PR `feat/klien-tls`. Selama belum selesai, lalu lintas klien belum terlindungi enkripsi.
5. **Versi pustaka Python belum disematkan** pada `requirements.txt`.
6. Bila `setInsecure()` terpaksa dipakai pada ESP32 untuk pengembangan, catat di sini sebagai risiko terbuka.

## 6. Catatan Privasi

Data kehadiran (presence) dan jam penggunaan lampu dapat mengungkap kebiasaan seseorang. Bila data itu dapat dikaitkan dengan individu, perlakukan sebagai data pribadi sesuai **UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi**:

- kumpulkan seperlunya (minimalisasi data),
- simpan secukupnya (retensi 30 hari),
- batasi akses (login MQTT per akun, ACL, API key / JWT),
- beri tahu pengguna data apa yang dikumpulkan.

## 7. Pengelolaan Rahasia

| Rahasia | Lokasi | Di-commit? |
|---|---|---|
| `API_KEY`, `JWT_SECRET`, `INFLUX_TOKEN`, `ADMIN_PASS` | `.env` | Tidak |
| Template variabel | `.env.example` | Ya (tanpa nilai) |
| Sandi akun MQTT (hash) | `docker/mosquitto/passwd` | Tidak |
| Kunci privat TLS | `docker/certs/server.key` | Tidak |
| Sertifikat CA publik | `docker/certs/ca.crt` | Tidak (dibagikan lewat chat pribadi) |
| Kredensial ESP32 | `firmware/include/secrets.h` | Tidak |

Bila ada rahasia yang terlanjur ter-commit, **ganti rahasia itu** (sandi, token, API key). Menghapus file pada commit berikutnya tidak menghapus riwayatnya.