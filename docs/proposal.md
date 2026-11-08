Pencahayaan sangat berpengaruh pada hasil rias. Cahaya ruangan yang berubah-ubah (siang, sore, malam, atau ruangan yang gelap) membuat warna riasan tampak berbeda dari aslinya, sehingga pengguna sering harus menyesuaikan lampu secara manual. Selain itu, lampu cermin rias sering lupa dimatikan setelah dipakai, sehingga energi listrik terbuang.



Masalah utama yang diangkat proyek ini adalah pencahayaan cermin rias yang tidak konsisten dan lampu yang tidak mati otomatis.



1\. Membangun lampu cermin rias yang kecerahannya menyesuaikan cahaya ruangan secara otomatis.

2\. Menyalakan lampu hanya ketika ada orang di depan cermin.

3\. Menampilkan data sensor dan status lampu secara real-time pada dashboard Grafana.

4\. Memberi notifikasi dan kontrol jarak jauh lewat bot Telegram.

5\. Menerapkan arsitektur IoT 5 lapis dengan pengamanan dasar (login, ACL, TLS).



GlowLight adalah lampu cermin rias otomatis berbasis ESP32. Sensor LDR mengukur cahaya ruangan dan sensor PIR mendeteksi kehadiran, lalu ESP32 mengatur kecerahan LED strip lewat MOSFET dengan PWM. Data dikirim lewat MQTT ke gateway, diteruskan ke API, disimpan di InfluxDB, dan ditampilkan di dashboard Grafana. Pengguna dapat memantau dan mengontrol lampu lewat bot Telegram, serta menerima peringatan bila lampu menyala terlalu lama atau pembacaan cahaya tidak wajar.



\### Jadwal



| Milestone | Waktu | Target |

| --- | --- | --- |

| M1 | Minggu 4 | Proposal, matriks pemilihan, BoM, pitching, simulasi Wokwi |

| M2 | Minggu 9 | Rangkaian berjalan, MQTT, gateway, API, InfluxDB, dashboard dasar |

| M3 | Minggu 15 | Keamanan (login, ACL, TLS, JWT), alert, bot Telegram, dashboard final |

| M4 | Minggu 16 | Artikel IEEE, poster atau video, skrip demo, expo |



\### Pembagian Peran



| Anggota | Nama | Peran | Tanggung jawab utama |

| --- | --- | --- | --- |

| 1 | (Aisyah) | Device \& Firmware Engineer | Rangkaian, sensor, firmware ESP32, MQTT |

| 2 | (Nurul) | Back-End \& Data Engineer | Gateway, API, InfluxDB |

| 3 | (Gellael) | Security \& DevOps Engineer | Docker, login dan ACL, TLS, CI, threat model |

| 4 | (Aggra) | Dashboard Engineer \& Project Manager | Dashboard Grafana, alert dan bot Telegram, repositori, dokumen |



| Risiko | Dampak | Mitigasi |

| --- | --- | --- |

| Akses tanpa izin ke broker MQTT | Orang lain bisa mengirim perintah atau membaca data | Login Mosquitto dan ACL per akun |

| Penyadapan data di jaringan | Data telemetri dan perintah bisa dibaca | TLS pada broker dan klien |

| Token atau password bocor di repositori | Bot atau API bisa disalahgunakan | .env dan file rahasia masuk .gitignore, tidak di-commit |

| Bot Telegram dikendalikan orang lain | Lampu bisa dinyalakan atau dimatikan pihak lain | Bot hanya menuruti chat ID pemilik, akun MQTT bot dibatasi ke topik cmd |

| Jaringan atau API terputus | Data telemetri hilang | Antrean SQLite di gateway (store-and-forward) |

| Pembacaan LDR terganggu cahaya LED sendiri | Alert anomali palsu | LDR diposisikan terlindung dari cahaya LED strip |

| Data pengguna disalahgunakan | Pelanggaran privasi | Kebijakan data sesuai UU PDP, data seminimal mungkin |



Analisis ancaman lengkap (STRIDE) disusun oleh Anggota 3 pada docs/.

