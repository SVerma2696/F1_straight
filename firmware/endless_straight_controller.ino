/*
  Endless Straight -- a 4-button race car controller
  =====================================================
  This little program runs on an ESP32 board. It watches 4 buttons and
  tells the computer, many times every second, which ones are being
  held down right now. The game on the computer listens for that and
  moves the race car.

  What each button does in the game
  ------------------------------------
    JUMP -- hop over things (also restarts the race after a crash)
    DUCK -- duck under things
    DRS  -- speed boost (only works inside a green zone in the game)
    HOME -- after a crash, go back to the team-picking menu

  How to wire it up
  --------------------
  Each button needs two wires: one going to a GPIO pin listed below, and
  the other going to GND (ground). We use the ESP32's own built-in
  "pull-up" helper, so you do NOT need any extra resistors -- just the
  button and two wires per button.

    JUMP button  ->  GPIO 32  and GND
    DUCK button  ->  GPIO 33  and GND
    DRS  button  ->  GPIO 25  and GND
    HOME button  ->  GPIO 26  and GND

  These four pins were picked because the pull-up trick works well with
  them. Don't use pins 34-39 (they can't do pull-ups) or pins 0, 2, 12,
  15 (the board needs those free while it's starting up).

  Because of the pull-up trick: a pin reads HIGH when the button is NOT
  pressed, and LOW the moment it IS pressed (since pressing connects the
  pin straight to GND).

  Optional: a DRS-ready LED
  ------------------------------
  Wire an LED (with a resistor, like any LED) to GPIO 27 and GND, and it
  will light up whenever the game says a DRS zone is ready to boost in
  -- a real-world echo of the on-screen "DRS READY" badge. This is
  completely optional; the game works fine without it.

    DRS LED  ->  GPIO 27  and GND (through a resistor)

  How it talks to the computer
  --------------------------------
  Once every loop, this program sends one line of text over the USB
  cable, like this:

      1,0,1,0

  The four numbers are always in this order: jump, duck, drs, home.
  A 1 means "this button is being held down right now," a 0 means
  "it's not." The game reads these lines and moves the car.

  The game also sends messages BACK to us, to control the DRS LED:

      LED,1     (turn the LED on -- DRS is ready right now)
      LED,0     (turn the LED off)

  How to put this onto the board
  -----------------------------------
  Open this file in the Arduino IDE, pick your ESP32 board and the USB
  port from the Tools menu, then click Upload.
*/

// Which GPIO pin each button is wired to
const int PIN_JUMP = 32;
const int PIN_DUCK = 33;
const int PIN_DRS  = 25;
const int PIN_HOME = 26;

// The optional LED that lights up when DRS is ready to use
const int PIN_DRS_LED = 27;

const int NUM_BUTTONS = 4;
const int BUTTON_PINS[NUM_BUTTONS] = {PIN_JUMP, PIN_DUCK, PIN_DRS, PIN_HOME};

// "Debouncing" means: after a button's reading changes, wait a tiny
// moment before believing it. Real buttons wiggle electrically for a
// few milliseconds when pressed, and without this, one press could
// look like several fast presses in a row.
const unsigned long DEBOUNCE_MS = 20;

bool stableState[NUM_BUTTONS];        // the reading we currently trust
bool lastRawReading[NUM_BUTTONS];     // the very last reading we saw, before trusting it
unsigned long lastChangeTime[NUM_BUTTONS];   // when that raw reading last changed

String incomingLine = "";   // the message from the game we're still building up, one letter at a time


void setup() {
  Serial.begin(115200);

  for (int i = 0; i < NUM_BUTTONS; i++) {
    // INPUT_PULLUP turns on the pin's built-in pull-up helper, so it
    // reads HIGH by default and LOW once the button is pressed
    pinMode(BUTTON_PINS[i], INPUT_PULLUP);
    bool reading = digitalRead(BUTTON_PINS[i]);
    stableState[i] = reading;
    lastRawReading[i] = reading;
    lastChangeTime[i] = millis();
  }

  pinMode(PIN_DRS_LED, OUTPUT);
  digitalWrite(PIN_DRS_LED, LOW);
}


void readFeedbackFromGame() {
  // Read whatever the game has sent us so far, one letter at a time, so
  // we never sit around waiting for a message that hasn't finished
  // arriving yet -- if nothing's here, this just does nothing at all.
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      if (incomingLine.startsWith("LED,")) {
        bool ledOn = incomingLine.charAt(4) == '1';
        digitalWrite(PIN_DRS_LED, ledOn ? HIGH : LOW);
      }
      incomingLine = "";
    } else if (c != '\r') {
      incomingLine += c;
    }
  }
}


void loop() {
  // Step 1: read every button and debounce it
  for (int i = 0; i < NUM_BUTTONS; i++) {
    bool reading = digitalRead(BUTTON_PINS[i]);

    if (reading != lastRawReading[i]) {
      // the reading just changed -- start (or restart) its little timer
      lastChangeTime[i] = millis();
      lastRawReading[i] = reading;
    }

    if (millis() - lastChangeTime[i] > DEBOUNCE_MS) {
      // the reading has held steady long enough now -- trust it
      stableState[i] = reading;
    }
  }

  // Step 2: send one line of "1,0,1,0" text over USB. Remember, the
  // pins read LOW when pressed, so we flip that around before sending,
  // so "1" always means "pressed" to keep things simple for the game.
  for (int i = 0; i < NUM_BUTTONS; i++) {
    Serial.print(stableState[i] == LOW ? "1" : "0");
    if (i < NUM_BUTTONS - 1) {
      Serial.print(",");
    }
  }
  Serial.println();

  // Step 3: check if the game sent us anything back, like a DRS-ready
  // LED command
  readFeedbackFromGame();

  delay(10);   // a tiny pause -- about 100 lines a second, plenty fast for a game
}
