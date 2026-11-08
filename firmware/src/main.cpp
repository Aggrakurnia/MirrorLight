#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <time.h>
#include "config.h"
#include "secrets.h"

WiFiClient espClient;
PubSubClient mqtt(espClient);

const int N = 10;
int buf[N], idx = 0, cnt = 0, ldrAvg = 0;
long sum = 0;
unsigned long tLdr = 0, tTele = 0, tRamp = 0, tReconnect = 0;
unsigned long lastMotionMs = 0, seq = 0;
bool presence = false, manualMode = false;
int manualDuty = 128, targetDuty = 0, currentDuty = 0;

void pwmBegin() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(PIN_LED, 5000, 8);
#else
  ledcSetup(0, 5000, 8);
  ledcAttachPin(PIN_LED, 0);
#endif
}

void pwmWrite(int d) {
  d = constrain(d, 0, 255);
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(PIN_LED, d);
#else
  ledcWrite(0, d);
#endif
}

void onMessage(char* topic, byte* payload, unsigned int len) {
  JsonDocument doc;
  if (deserializeJson(doc, payload, len)) return;     // abaikan JSON rusak
  const char* mode = doc["mode"] | "";
  if (strcmp(mode, "manual") == 0) {
    manualMode = true;
    manualDuty = constrain((int)(doc["brightness"] | 128), 0, 255);
  } else if (strcmp(mode, "auto") == 0) {
    manualMode = false;
  }
}

void reconnectMqtt() {
  if (mqtt.connected() || WiFi.status() != WL_CONNECTED) return;
  if (millis() - tReconnect < 5000) return;           // coba tiap 5 detik
  tReconnect = millis();
  String cid = String(DEVICE_ID) + "-" + String((uint32_t)ESP.getEfuseMac(), HEX);
  const char* u = strlen(MQTT_USER) ? MQTT_USER : nullptr;
  const char* p = strlen(MQTT_USER) ? MQTT_PASS : nullptr;
  if (mqtt.connect(cid.c_str(), u, p, T_STATUS, 1, true, "offline")) {
    mqtt.publish(T_STATUS, "online", true);
    mqtt.subscribe(T_CMD, 1);
  }
}

void sendTelemetry(unsigned long now) {
  time_t t = time(nullptr);
  JsonDocument doc;
  doc["device_id"] = DEVICE_ID;
  doc["seq"] = ++seq;
  doc["ts"] = (t > 1700000000) ? (long)t : 0L;
  doc["uptime_ms"] = now;
  doc["ldr_raw"] = ldrAvg;
  doc["ldr_pct"] = map(ldrAvg, 0, 4095, 0, 100);
  doc["presence"] = presence;
  doc["lamp_on"] = currentDuty > 0;
  doc["duty"] = currentDuty;
  doc["mode"] = manualMode ? "manual" : "auto";
  char out[256];
  size_t n = serializeJson(doc, out, sizeof(out));
  Serial.println(out);                                // selalu dicetak ke serial
  if (mqtt.connected()) mqtt.publish(T_TELE, (const uint8_t*)out, n, false);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_PIR, INPUT);
  pwmBegin();
  pwmWrite(0);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASS);                   // dipanggil sekali saja
  configTime(7 * 3600, 0, "pool.ntp.org");            // WIB
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setBufferSize(512);
  mqtt.setCallback(onMessage);
  Serial.println("GlowLight siap");
}

void loop() {
  unsigned long now = millis();
  reconnectMqtt();
  mqtt.loop();

  if (now - tLdr >= INTERVAL_LDR_MS) {
    tLdr = now;
    int raw = analogRead(PIN_LDR);
    if (cnt == N) sum -= buf[idx]; else cnt++;
    buf[idx] = raw;
    sum += raw;
    idx = (idx + 1) % N;
    ldrAvg = sum / cnt;
    presence = digitalRead(PIN_PIR) == HIGH;
    if (presence) lastMotionMs = now;
  }

  bool aktif = lastMotionMs != 0 && (now - lastMotionMs < HOLD_AFTER_MOTION_MS);
  if (manualMode) targetDuty = manualDuty;
  else if (aktif) targetDuty = map(constrain(ldrAvg, ADC_GELAP, ADC_TERANG),
                                   ADC_GELAP, ADC_TERANG, DUTY_MAX, DUTY_MIN);
  else targetDuty = 0;

  if (now - tRamp >= 15) {
    tRamp = now;
    if (currentDuty < targetDuty) currentDuty = min(currentDuty + 3, targetDuty);
    else if (currentDuty > targetDuty) currentDuty = max(currentDuty - 3, targetDuty);
    pwmWrite(currentDuty);
  }

  if (now - tTele >= INTERVAL_TELE_MS) {
    tTele = now;
    sendTelemetry(now);
  }
}