#!/usr/bin/env bash
set -e

BOARD_FQBN="arduino:avr:uno"
SERIAL_PORT="/dev/ttyACM0"
SKETCH_DIR="$HOME/MagstripeSpoofer"
VENV_DIR="$HOME/MagstripeSpoofer/venv"

log() { echo "[setup] $*"; }

if [ "$(id -u)" -eq 0 ] && [ -n "$SUDO_USER" ]; then
  REAL_USER="$SUDO_USER"
else
  REAL_USER="$(id -un)"
fi

# Function to check if a user is in a group
user_in_group() {
  local user="$1"
  local group="$2"
  if id -nG "$user" | grep -qw "$group"; then
    return 0
  else
    return 1
  fi
}

# 1. Ensure user is in dialout group
if user_in_group "$REAL_USER" "dialout"; then
  log "User '$REAL_USER' is already in 'dialout' group."
else
  log "User '$REAL_USER' is not in 'dialout'. Adding now..."
  if sudo usermod -aG dialout "$REAL_USER"; then
    log "Added '$REAL_USER' to 'dialout' group. You must log out and log back in, then re-run this script."
    exit 0
  else
    echo "[setup] ERROR: failed to add $REAL_USER to dialout group" >&2
    exit 1
  fi
fi

# 2. Ensure arduino-cli is installed
if ! command -v arduino-cli &>/dev/null; then
  log "arduino-cli not found. Installing..."
  TMP=$(mktemp -d)
  pushd "$TMP"
  curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
  sudo mv bin/arduino-cli /usr/local/bin/
  popd
  rm -rf "$TMP"
  log "arduino-cli installed."
else
  log "arduino-cli already installed."
fi

# 3. Update core index and install AVR core if needed
log "Updating Arduino core index..."
arduino-cli core update-index
if ! arduino-cli core list | grep -q "^arduino:avr"; then
  log "Installing arduino:avr core..."
  arduino-cli core install arduino:avr
else
  log "arduino:avr core already installed."
fi

# 4. Check sketch directory
if [ ! -d "$SKETCH_DIR" ]; then
  echo "[setup] ERROR: Sketch directory not found: $SKETCH_DIR" >&2
  exit 1
fi

# 5. Compile
log "Compiling sketch in $SKETCH_DIR..."
arduino-cli compile --fqbn "$BOARD_FQBN" "$SKETCH_DIR"

# 6. Upload
log "Uploading sketch to $SERIAL_PORT..."
arduino-cli upload -p "$SERIAL_PORT" --fqbn "$BOARD_FQBN" "$SKETCH_DIR"
log "Upload complete."
