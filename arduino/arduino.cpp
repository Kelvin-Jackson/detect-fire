#include <HTTPClient.h>

// Wi-Fi credentials
const char* ssid = "TECNO-TR109-CDBB";
const char* password = "30585069";

// Sensor and server configuration
const int smokeSensorPin = 34;   // GPIO34 (ADC input only)
const int smokeThreshold = 300;  // Set your threshold value accordingly
const char* serverName = "https://127.0.0.1/5001:log";

// LED and Buzzer pins
const int redLedPin = 19;
const int blueLedPin = 5;
const int buzzerPin = 18;

WiFiServer server(80);  // Web server on port 80

unsigned long lastPostTime = 0;
const unsigned long postInterval = 10000;  // Post interval (10 seconds)

void setup() {
  Serial.begin(115200);
  pinMode(smokeSensorPin, INPUT);
  pinMode(redLedPin, OUTPUT);
  pinMode(blueLedPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);

  digitalWrite(redLedPin, LOW);
  digitalWrite(blueLedPin, LOW);
  digitalWrite(buzzerPin, LOW);

  Serial.println("\nBooting ESP32...");
  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n Connected to WiFi!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    server.begin();
  } else {
    Serial.println("\nFailed to connect to WiFi.");
  }
}

void loop() {
  unsigned long currentMillis = millis();

  // Send data to Flask server at fixed interval
  if (currentMillis - lastPostTime > postInterval && WiFi.status() == WL_CONNECTED) {
    int sensorValue = analogRead(smokeSensorPin);
    Serial.print("Sensor Value: ");
    Serial.println(sensorValue);

    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    String requestBody = "{\"smoke\":" + String(sensorValue) + "}";
    int httpResponseCode = http.POST(requestBody);

    Serial.println("HTTP Status Code: " + String(httpResponseCode));
    http.end();

    lastPostTime = currentMillis;
  }

  // Web server response and local alert logic
  int sensorValue = analogRead(smokeSensorPin);
  bool smokeDetected = sensorValue > smokeThreshold;

  if (smokeDetected) {
    digitalWrite(redLedPin, HIGH);
    digitalWrite(blueLedPin, LOW);
    digitalWrite(buzzerPin, HIGH);
  } else {
    digitalWrite(redLedPin, LOW);
    digitalWrite(blueLedPin, HIGH);
    digitalWrite(buzzerPin, LOW);
  }

  WiFiClient client = server.available();
  if (client) {
    Serial.println("Client connected.");

    String request = client.readStringUntil('\r');
    client.flush();

    // HTML response
    String html = "<!DOCTYPE html><html><head><meta http-equiv='refresh' content='5'>";
    html += "<title>ESP32 Smoke Monitor</title>";
    html += "<style>body{font-family:Arial;text-align:center;}";
    html += ".alert{color:red;font-size:24px;}</style></head><body>";
    html += "<h1> MQ-2 Smoke Monitor</h1>";
    html += "<p>Sensor Value: <strong>" + String(sensorValue) + "</strong></p>";

    if (smokeDetected) {
      html += "<p class='alert'>Smoke Detected!</p>";
    } else {
      html += "<p style='color:green;'>Normal</p>";
    }

    html += "<p>Auto-refreshes every 5 seconds.</p></body></html>";

    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: text/html");
    client.println("Connection: close");
    client.println();
    client.println(html);

    delay(1);
    client.stop();
    Serial.println("Client disconnected.");
  }
}