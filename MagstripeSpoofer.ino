#include "MagSpoof.h"

#define PIN_A       3
#define PIN_B       4
#define PIN_ENABLE  13
#define CLOCK_US    400

MagSpoof *magSpoofPtr = nullptr;

char trackBuffer[128];
int scanCount = 0;
bool infiniteMode = false;
unsigned long delayMs = 2000;

void setup() {
    Serial.begin(9600);
    Serial.setTimeout(2000);
    while (!Serial) { ; }  // wait if needed
    Serial.println("READY");

    // 1) Read count or "INF"
    String first = Serial.readStringUntil('\n');
    first.trim();
    if (first == "INF") {
        infiniteMode = true;
    } else {
        scanCount = first.toInt();
        infiniteMode = false;
    }

    // 2) Read delay
    String dstr = Serial.readStringUntil('\n');
    dstr.trim();
    delayMs = dstr.toInt();

    // 3) Read track_type line
    String trackType = Serial.readStringUntil('\n');
    trackType.trim(); // expects "track1", "track2", or "track3"

    // 4) Read track data line
    int len = Serial.readBytesUntil('\n', (uint8_t*)trackBuffer, sizeof(trackBuffer)-1);
    trackBuffer[len] = '\0';

    Serial.print("CONFIG RECEIVED: count=");
    Serial.print(infiniteMode ? "INF" : String(scanCount));
    Serial.print(" delay=");
    Serial.print(delayMs);
    Serial.print(" type=");
    Serial.print(trackType);
    Serial.print(" track=");
    Serial.println(trackBuffer);

    // 5) Construct the appropriate MagSpoof instance via new
    if (trackType == "track1") {
        // Track 1: alphanumeric, 7-bit, odd parity
        magSpoofPtr = new MagSpoof(PIN_A, PIN_B, PIN_ENABLE, CLOCK_US,
                                   MagSpoof::BPC7, MagSpoof::Odd);
    }
    else if (trackType == "track2") {
        // Track 2: numeric, 5-bit, odd parity
        magSpoofPtr = new MagSpoof(PIN_A, PIN_B, PIN_ENABLE, CLOCK_US,
                                   MagSpoof::BPC5, MagSpoof::Odd);
    }
    else if (trackType == "track3") {
        // Track 3: often numeric; here we default to same as Track 2
        magSpoofPtr = new MagSpoof(PIN_A, PIN_B, PIN_ENABLE, CLOCK_US,
                                   MagSpoof::BPC5, MagSpoof::Odd);
    }
    else {
        // Fallback: default to Track 2 encoding
        magSpoofPtr = new MagSpoof(PIN_A, PIN_B, PIN_ENABLE, CLOCK_US,
                                   MagSpoof::BPC5, MagSpoof::Odd);
    }

    if (!magSpoofPtr) {
        Serial.println("ERROR: failed to allocate MagSpoof");
        while (true) { delay(1000); }
    }
    magSpoofPtr->setup();
}

void loop() {
    if (!magSpoofPtr) return;

    if (infiniteMode) {
        while (true) {
            magSpoofPtr->playTrack(trackBuffer);
            delay(delayMs);
            if (Serial.available()) {
                String cmd = Serial.readStringUntil('\n');
                cmd.trim();
                if (cmd == "STOP") {
                    Serial.println("Stopping infinite loop");
                    break;
                }
            }
        }
    } else {
        for (int i = 0; i < scanCount; i++) {
            magSpoofPtr->playTrack(trackBuffer);
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
    // Idle after finishing
    while (true) {
        delay(1000);
    }
}
