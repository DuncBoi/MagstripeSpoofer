import cherrypy
import netifaces as ni
import time 
import os
import subprocess
import serial

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600
PROJECT_DIR = os.path.expanduser("~/MagstripeSpoofer")
HTML_PATH = os.path.join(PROJECT_DIR, "server/index.html")
TRACK_DEFAULT = ";4242004800500=0123456789?"

# ---- Get IP Address ----
def get_ip():
    while True:
        try:
            ip = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
            return ip
        except (KeyError, IndexError):
            time.sleep(1)

ip_address = get_ip()

# ---- Main Web App ----
class MagSpoofWeb:
    @cherrypy.expose
    def index(self):
        return open(HTML_PATH)

    @cherrypy.expose
    def run(self, num_times=None, delay=None, track=None):
        if not (num_times and delay):
            return "Missing num_times or delay"

        track = track or TRACK_DEFAULT

        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                time.sleep(2)  # Wait for Arduino reset
                line = ser.readline().decode()
                if "READY" not in line:
                    return f"Arduino not ready. Got: {line.strip()}"

                ser.write(f"{num_times}\n".encode())
                ser.write(f"{delay}\n".encode())
                ser.write(f"{track}\n".encode())

                return f"Sent {num_times} scans with {delay}ms delay and track: {track}"

        except Exception as e:
            return f"Serial communication failed: {e}"

    @cherrypy.expose
    def stop(self):
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                time.sleep(2)
                ser.readline()
                ser.write("0\n5000\n\n".encode())  # Stop the loop
            return "Spoofer stopped."
        except Exception as e:
            return f"Stop failed: {e}"

if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': ip_address, 'server.socket_port': 8080})
    cherrypy.quickstart(MagSpoofWeb())
