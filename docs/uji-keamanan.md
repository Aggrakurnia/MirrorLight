# Laporan Uji Keamanan GlowLight (MirrorLight)

Kelompok 2, Mata Kuliah Teknologi IoT, Prodi S1 Informatika FT UNIB.

Dokumen ini mencatat hasil pengujian kontrol keamanan yang dibuat Anggota 3. Kolom **Hasil** hanya diisi dari pengujian yang benar-benar dijalankan. Uji yang belum dijalankan ditulis **Belum diuji**.

## 1. Lingkungan Uji

| Item | Nilai |
|---|---|
| Tanggal uji | 8 November 2026 |
| Broker | Mosquitto 2.1.2 (`eclipse-mosquitto:2`) dengan Docker Compose |
| Port broker | 8883 (TLS) |
| Sertifikat | Self-signed, dibuat oleh `docker/gen-certs.sh` |
| Akun MQTT | `esp32_cermin01`, `gateway`, `bot` |
| Topik uji | `unib/glowlight/kelompok-02/cermin01/...` |

## 2. Ringkasan Hasil

| No | Uji | Hasil yang diharapkan | Hasil | Status |
|---|---|---|---|---|
| 1 | Publish MQTT tanpa login | Ditolak | | Belum diuji |
| 2 | Login MQTT dengan sandi salah | Ditolak | | Belum diuji |
| 3 | ESP32 publish ke `cmd` | Tidak sampai ke subscriber | | Belum diuji |
| 4 | Gateway publish ke `telemetry` | Tidak sampai ke subscriber | | Belum diuji |
| 5 | Subscribe TLS tanpa CA | Gagal | Klien ditolak dengan `Error: Protocol error` | **Lulus** |
| 6 | API tanpa kredensial | 401 | | Belum diuji (menunggu `main` terisi) |
| 7 | API dengan token ngawur | 401 | | Belum diuji (menunggu `main` terisi) |
| 8 | Login API dengan sandi salah | 401 | | Belum diuji (menunggu `main` terisi) |
| 9 | `device_id` berisi karakter aneh pada `/api/latest` | 422 | | Belum diuji (menunggu `main` terisi) |
| 10 | `git ls-files` tidak memuat `.env`, `secrets.h`, `passwd`, `certs` | Tidak ada | | Belum diuji |

Setelah sebuah uji dijalankan, ganti "Belum diuji" dengan **Lulus** atau **Gagal**, isi kolom Hasil dengan apa yang teramati, dan bila gagal catat perbaikannya di bagian 5.

## 3. Cara Menguji

Perintah dijalankan dari folder `docker/` di PowerShell. Ganti `SANDI_GATEWAY`, `SANDI_ESP32`, dan `SANDI_BOT` dengan sandi akun masing-masing (jangan ditulis ke dokumen ini). Tidak memakai tanda `<` dan `>`.

### 3.1 Uji broker MQTT (uji 1 sampai 5)

Terminal 1, subscriber sebagai `gateway` (biarkan berjalan):

```
docker compose --env-file ../.env exec mosquitto mosquitto_sub -h localhost -p 8883 --cafile /mosquitto/certs/ca.crt -u gateway -P SANDI_GATEWAY -t "unib/glowlight/#" -v
```

Terminal 2, publisher:

```
# Uji 1: tanpa login (harus ditolak)
docker compose --env-file ../.env exec mosquitto mosquitto_pub -h localhost -p 8883 --cafile /mosquitto/certs/ca.crt -t "unib/glowlight/kelompok-02/cermin01/telemetry" -m "tanpa-login"

# Uji 2: sandi salah (harus ditolak)
docker compose --env-file ../.env exec mosquitto mosquitto_pub -h localhost -p 8883 --cafile /mosquitto/certs/ca.crt -u esp32_cermin01 -P sandisalah -t "unib/glowlight/kelompok-02/cermin01/telemetry" -m "sandi-salah"

# Kontrol positif: ESP32 ke telemetry (pesan harus muncul di terminal 1)
docker compose --env-file ../.env exec mosquitto mosquitto_pub -h localhost -p 8883 --cafile /mosquitto/certs/ca.crt -u esp32_cermin01 -P SANDI_ESP32 -t "unib/glowlight/kelompok-02/cermin01/telemetry" -m "dari-esp32"

# Uji 3: ESP32 ke cmd (pesan TIDAK boleh muncul di terminal 1)
docker compose --env-file ../.env exec mosquitto mosquitto_pub -h localhost -p 8883 --cafile /mosquitto/certs/ca.crt -u esp32_cermin01 -P SANDI_ESP32 -t "unib/glowlight/kelompok-02/cermin01/cmd" -m "esp32-dilarang"

# Uji 4: gateway ke telemetry (pesan TIDAK boleh muncul di terminal 1)
docker compose --env-file ../.env exec mosquitto mosquitto_pub -h localhost -p 8883 --cafile /mosquitto/certs/ca.crt -u gateway -P SANDI_GATEWAY -t "unib/glowlight/kelompok-02/cermin01/telemetry" -m "gateway-dilarang"

# Kontrol positif: bot ke cmd (pesan harus muncul di terminal 1)
docker compose --env-file ../.env exec mosquitto mosquitto_pub -h localhost -p 8883 --cafile /mosquitto/certs/ca.crt -u bot -P SANDI_BOT -t "unib/glowlight/kelompok-02/cermin01/cmd" -m "dari-bot"
```

Catatan: klien `mosquitto_pub` yang dilarang ACL tidak menerima pesan error. Broker hanya membuang pesannya, jadi hasil dinilai dari ada atau tidaknya pesan di terminal subscriber.

Uji 5, tanpa CA:

```
docker compose --env-file ../.env exec mosquitto mosquitto_sub -h localhost -p 8883 -u gateway -P SANDI_GATEWAY -t "unib/glowlight/#" -v
```

Uji tambahan, port tanpa TLS tidak lagi aktif:

```
docker compose --env-file ../.env exec mosquitto mosquitto_sub -h localhost -p 1883 -u gateway -P SANDI_GATEWAY -t "unib/glowlight/#" -v
```

### 3.2 Uji API (uji 6 sampai 9)

Dijalankan setelah `main.py`, `requirements.txt`, dan `auth.py` final berada di `main`, lalu API dibangun dengan `docker compose --env-file ../.env up -d --build api`. Di PowerShell pakai `curl.exe`.

```
# Uji 6: tanpa kredensial (harus 401)
curl.exe -i http://localhost:8000/api/latest

# Kontrol positif: API key benar (harus 200)
curl.exe -i -H "X-API-Key: API_KEY_ANDA" http://localhost:8000/api/latest

# Uji 7: token ngawur (harus 401)
curl.exe -i -H "Authorization: Bearer tokenngawur" http://localhost:8000/api/latest

# Uji 8: login dengan sandi salah (harus 401)
curl.exe -i -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"salah\"}"

# Kontrol positif: login benar (harus 200 berisi access_token)
curl.exe -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d "{\"username\":\"ADMIN_USER\",\"password\":\"ADMIN_PASS\"}"
```

Uji 9 (nilai `device_id` yang tidak valid, harus 422) mengikuti definisi parameter pada `main.py` milik Anggota 2. Lihat `http://localhost:8000/docs` untuk nama parameter dan aturan validasinya.

### 3.3 Uji repositori (uji 10)

```
git ls-files | Select-String -Pattern "\.env$|secrets\.h|passwd|certs"
```

Hasil yang diharapkan: tidak ada baris. `.env.example` dan `secrets.example.h` boleh ada, dan tidak cocok dengan pola di atas.

## 4. Temuan

| No | Temuan | Dampak | Tindak lanjut |
|---|---|---|---|
| 1 | File `passwd` dibuat `mosquitto_passwd` dengan izin hanya untuk root, sehingga broker gagal membukanya | Broker berhenti saat start | Izin diubah ke pemilik `1883:1883`, mode `0640` |
| 2 | Peringatan Mosquitto: grup file `acl` bukan `mosquitto` | Versi mendatang dapat menolak memuat file | Ubah pemilik file `acl` dengan cara yang sama seperti `passwd` |
| 3 | Klien (gateway, bot, ESP32) belum memakai TLS | Lalu lintas klien belum dienkripsi | Dikerjakan pada PR `feat/klien-tls` |

## 5. Catatan Perbaikan

Isi bagian ini bila ada uji yang berstatus Gagal: uraikan penyebab, perbaikan yang dilakukan, dan hasil uji ulang.

## 6. Kesimpulan Sementara

Pada tanggal pengujian, kontrol TLS pada broker terbukti menolak klien yang tidak memakai TLS dengan CA (uji 5). Uji lain pada tabel di atas belum dijalankan dan akan dilengkapi sebelum laporan final.