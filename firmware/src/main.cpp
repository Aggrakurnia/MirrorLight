#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>   // Library Manager: PubSubClient (Nick O'Leary)

#include "secrets.h"   // berisi nama Wi-Fi, password, dan nama topik
const char* MQTT_HOST = "broker.hivemq.com";   // server perantara gratis (untuk uji coba)

constexpr uint8_t PIR_PIN = 27, MOSFET_PIN = 13, LDR_PIN = 34;
constexpr uint8_t PWM_CH = 0;                  // kanal PWM untuk MOSFET
constexpr uint32_t PWM_FREQ = 5000;            // 5 kHz
constexpr uint8_t PWM_BITS = 8;                // duty 0-255
constexpr bool RAW_NAIK_SAAT_GELAP = true;
constexpr unsigned long WARMUP_MS = 60000UL, TAHAN_NYALA_MS = 3000UL, STABIL_CAHAYA_MS = 2000UL;

int ambangGelap = 3000, ambangTerang = 2600;   // bisa diubah dari dashboard
uint8_t mode = 0;                              // 0 = otomatis, 1 = ON paksa, 2 = OFF paksa
int kecerahan = 100;                           // 0-100 persen, bisa diubah dari dashboard

unsigned long mulai, gerakTerakhir = 0, calonSejak = 0;
unsigned long waktuBaca = 0, waktuLaporan = 0, waktuMqtt = 0;
bool siap = false, lampu = false, gelap = false, calonGelap = false, pernahGerak = false, gerak = false;
int rawLdr = 0, skorGelap = 0;

WiFiClient wifi;
PubSubClient mqtt(wifi);
char tTel[80], tStat[80], tCmd[80];

// Terapkan kecerahan ke MOSFET. Kurva kuadrat supaya redupnya terasa merata di mata.
void terapkanLampu() {
  uint32_t duty = 0;
  if (lampu && kecerahan > 0) {
    duty = (uint32_t)kecerahan * kecerahan * 255UL / 10000UL;
    if (duty < 1) duty = 1;
  }
  ledcWrite(PWM_CH, duty);
}

void onCmd(char*, byte* p, unsigned int n) {
  char b[160]; n = min(n, 159u); memcpy(b, p, n); b[n] = 0;
  if (strstr(b, "\"mode\":\"auto\"")) mode = 0;
  else if (strstr(b, "\"mode\":\"on\"")) mode = 1;
  else if (strstr(b, "\"mode\":\"off\"")) mode = 2;
  char* s;
  if ((s = strstr(b, "\"ag\":"))) { int v = atoi(s + 5); if (v > 0 && v <= 4095) ambangGelap = v; }
  if ((s = strstr(b, "\"at\":"))) { int v = atoi(s + 5); if (v > 0 && v < ambangGelap) ambangTerang = v; }
  if ((s = strstr(b, "\"br\":"))) { int v = atoi(s + 5); if (v >= 0 && v <= 100) { kecerahan = v; terapkanLampu(); } }
  Serial.printf("CMD: %s\n", b);
}

void jagaMqtt(unsigned long now) {
  if (WiFi.status() != WL_CONNECTED) return;
  if (mqtt.connected()) { mqtt.loop(); return; }
  if (now - waktuMqtt < 5000UL) return;
  waktuMqtt = now;
  char id[32]; snprintf(id, sizeof(id), "cermin-%04X", (uint16_t)ESP.getEfuseMac());
  if (mqtt.connect(id, nullptr, nullptr, tStat, 1, true, "offline")) {
    mqtt.publish(tStat, "online", true);
    mqtt.subscribe(tCmd, 1);
  }
}

void setup() {
  ledcSetup(PWM_CH, PWM_FREQ, PWM_BITS);
  ledcAttachPin(MOSFET_PIN, PWM_CH);
  ledcWrite(PWM_CH, 0);                        // lampu mati saat awal
  pinMode(PIR_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(LDR_PIN, ADC_11db);
  Serial.begin(115200);
  snprintf(tTel, sizeof(tTel), "%s/telemetry", BASE);
  snprintf(tStat, sizeof(tStat), "%s/status", BASE);
  snprintf(tCmd, sizeof(tCmd), "%s/cmd", BASE);
  WiFi.mode(WIFI_STA);
  delay(100);
  int n = WiFi.scanNetworks();
  Serial.printf("Ditemukan %d jaringan:\n", n);
  for (int i = 0; i < n; i++) {
    Serial.printf("  [%s] sinyal=%d\n", WiFi.SSID(i).c_str(), WiFi.RSSI(i));
  }
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  mqtt.setServer(MQTT_HOST, 1883);
  mqtt.setCallback(onCmd);
  mqtt.setSocketTimeout(2);
  mulai = millis();
  Serial.println("Stabilisasi PIR 60 detik; lampu OFF.");
}

void loop() {
  const unsigned long now = millis();
  jagaMqtt(now);
  static unsigned long tDiag = 0;
  if (now - tDiag >= 5000UL) {
    tDiag = now;
    Serial.printf("WiFi=%d IP=%s | MQTT=%d state=%d\n", WiFi.status(),
                  WiFi.localIP().toString().c_str(), mqtt.connected(), mqtt.state());
  }
  if (now - waktuBaca < 50UL) return;
  waktuBaca = now;

  long total = 0;
  for (int i = 0; i < 16; ++i) total += analogRead(LDR_PIN);
  rawLdr = total / 16;
  skorGelap = RAW_NAIK_SAAT_GELAP ? rawLdr : 4095 - rawLdr;
  gerak = digitalRead(PIR_PIN) == HIGH;

  if (!siap && now - mulai >= WARMUP_MS) { siap = true; Serial.println("PIR siap."); }

  bool hasilGelap = gelap;
  if (skorGelap >= ambangGelap) hasilGelap = true;
  else if (skorGelap <= ambangTerang) hasilGelap = false;
  if (hasilGelap != calonGelap) { calonGelap = hasilGelap; calonSejak = now; }
  if (now - calonSejak >= STABIL_CAHAYA_MS) gelap = calonGelap;

  if (siap && gerak) { gerakTerakhir = now; pernahGerak = true; }
  if (pernahGerak && now - gerakTerakhir >= TAHAN_NYALA_MS) pernahGerak = false;

  bool inginNyala = siap && (pernahGerak || gelap);   // mode otomatis
  if (mode == 1) inginNyala = true;                   // ON paksa
  if (mode == 2) inginNyala = false;                  // OFF paksa
  if (inginNyala != lampu) {
    lampu = inginNyala;
    terapkanLampu();
    Serial.println(lampu ? "Lampu ON" : "Lampu OFF");
  }

  if (now - waktuLaporan >= 1000UL) {
    waktuLaporan = now;
    Serial.printf("RAW=%d | Skor=%d | PIR=%d | Gelap=%d | Lampu=%s | Terang=%d%% | %s\n", rawLdr, skorGelap,
                  gerak, gelap, lampu ? "ON" : "OFF", kecerahan, siap ? "SIAP" : "PEMANASAN");
    if (mqtt.connected()) {
      char buf[240];
      snprintf(buf, sizeof(buf),
        "{\"raw\":%d,\"skor\":%d,\"pir\":%d,\"gelap\":%d,\"lampu\":%d,\"siap\":%d,\"mode\":%d,\"ag\":%d,\"at\":%d,\"br\":%d,\"up\":%lu,\"rssi\":%d}",
        rawLdr, skorGelap, gerak, gelap, lampu, siap, mode, ambangGelap, ambangTerang, kecerahan, now / 1000UL, WiFi.RSSI());
      mqtt.publish(tTel, buf);
    }
  }
}