#include "MagSpoof.h"

#define PIN_A 3
#define PIN_B 4
#define PIN_ENABLE 13
#define CLOCK_US 400

MagSpoof magSpoof(PIN_A, PIN_B, PIN_ENABLE, CLOCK_US, MagSpoof::BPC7, MagSpoof::Odd);

char trackBuffer[128];
int scanCount = 0;
bool infiniteMode = false;
unsigned long delayMs = 2000;

void setup() {
  magSpoof.setup();
  Serial.begin(9600);
  Serial.setTimeout(1000);

  Serial.println("READY");
  String first = Serial.readStringUntil('\n');
  first.trim();
  if (first == "INF") {
    infiniteMode = true;
  } else {
    scanCount = first.toInt();
    infiniteMode = false;
  }
  // Read delay line
  String dstr = Serial.readStringUntil('\n'); dstr.trim();
  delayMs = dstr.toInt();
  // Read track line
  int len = Serial.readBytesUntil('\n', trackBuffer, sizeof(trackBuffer)-1);
  trackBuffer[len] = '\0';
  Serial.print("CONFIG RECEIVED: count=");
  Serial.print(infiniteMode ? "INF" : String(scanCount));
  Serial.print(" delay=");
  Serial.print(delayMs);
  Serial.print(" track=");
  Serial.println(trackBuffer);
}

void loop() {
if (infiniteMode) {
        while (true) {
            magSpoof.playTrack(trackBuffer);
            delay(delayMs);
            // Check for STOP command:
            if (Serial.available()) {
                String cmd = Serial.readStringUntil('\n');
                cmd.trim();
                if (cmd == "STOP") {
                    Serial.println("Stopping infinite loop");
                    return; 
                }
            }
        }
    } else {
        for (int i = 0; i < scanCount; i++) {
            magSpoof.playTrack(trackBuffer);
            delay(delayMs);
            if (Serial.available()) {
                String cmd = Serial.readStringUntil('\n');
                cmd.trim();
                if (cmd == "STOP") {
                    Serial.println("Stopped early");
                    break;
                }
            }
        }
    }

  while (true){
    delay(1000); 
  };
}
