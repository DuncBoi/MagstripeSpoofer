#include "MagSpoof.h"

#define PIN_A 3
#define PIN_B 4
#define PIN_ENABLE 13
#define CLOCK_US 400

MagSpoof magSpoof(PIN_A, PIN_B, PIN_ENABLE, CLOCK_US, MagSpoof::BPC7, MagSpoof::Odd);

char trackBuffer[128];
int scanCount = 1;
unsigned long delayMs = 2000;

void setup() {
  magSpoof.setup();
  Serial.begin(9600);
  Serial.setTimeout(1000);

  Serial.println("READY");
  while (Serial.available() == 0);

  scanCount = Serial.parseInt();
  delayMs = Serial.parseInt();
  Serial.read();

  int len = Serial.readBytesUntil('\n', trackBuffer, sizeof(trackBuffer) - 1);
  trackBuffer[len] = '\0';

  Serial.print("CONFIG RECEIVED: ");
  Serial.println(trackBuffer);
}

void loop() {
  for (int i = 0; i < scanCount; i++) {
    magSpoof.playTrack(trackBuffer);
    delay(delayMs);
  }

  // Loop forever doing nothing
  while (true);
}
}
