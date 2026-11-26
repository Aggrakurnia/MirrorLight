#pragma once
#define DEVICE_ID "glowlight-01"
#define T_TELE   "unib/glowlight/kelompok-02/cermin01/telemetry"
#define T_CMD    "unib/glowlight/kelompok-02/cermin01/cmd"
#define T_STATUS "unib/glowlight/kelompok-02/cermin01/status"

#define PIN_LDR 34
#define PIN_PIR 27
#define PIN_LED 25

#define ADC_GELAP 400            // kalibrasi di ruangan Anda (Tahap G)
#define ADC_TERANG 3000
#define DUTY_MIN 64              // kecerahan minimum saat ruangan terang
#define DUTY_MAX 255
#define HOLD_AFTER_MOTION_MS 60000UL
#define INTERVAL_LDR_MS 100UL
#define INTERVAL_TELE_MS 2000UL
