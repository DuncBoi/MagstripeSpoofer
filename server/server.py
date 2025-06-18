import cherrypy
import netifaces as ni
import time
import os
import serial
import urllib.parse

# Paths: adjust if needed
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML = os.path.join(BASE_DIR, "index.html")
STATUS_HTML = os.path.join(BASE_DIR, "status.html")

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600
TRACK_DEFAULT = ""  # default track data if any

def get_ip():
    for iface in ni.interfaces():
        try:
            ip = ni.ifaddresses(iface)[ni.AF_INET][0]['addr']
            if ip != "127.0.0.1":
                return ip
        except (KeyError, IndexError):
            continue
    return "0.0.0.0"

ip_address = get_ip()

class MagSpoofWeb:
    @cherrypy.expose
    def index(self):
        return open(INDEX_HTML)

    @cherrypy.expose
    def run(self, num_times=None, delay=None, track=None, infinite=None, track_type=None, mode=None):
        # 1. Validate delay
        if not delay:
            return "Missing delay"
        try:
            delay_int = int(delay)
            if delay_int < 50:
                return "Delay must be ≥50 ms"
        except ValueError:
            return "Invalid delay"

        # 2. Validate run count if fixed
        if infinite == "1":
            count_str = "INF"
        else:
            if not num_times:
                return "Missing num_times"
            try:
                n = int(num_times)
                if n < 1:
                    return "num_times must be ≥1"
                count_str = str(n)
            except ValueError:
                return "Invalid num_times"

        # 3. Validate track_type
        if track_type not in ("track1", "track2", "track3"):
            return "Invalid track_type"

        # 4. Validate track data presence
        track_val = track or TRACK_DEFAULT
        if not track_val:
            return "Missing track data"

        # 5. Optional: rough format checks
        # Python syntax: use .startswith and .endswith, not JS style
        if track_type == "track1":
            if not (track_val.startswith("%") and track_val.endswith("?")):
                # just warn or ignore; here we proceed but you could return an error or warning
                cherrypy.log("Warning: track data may not match Track 1 format")
        if track_type in ("track2", "track3"):
            if not (track_val.startswith(";") and track_val.endswith("?")):
                cherrypy.log("Warning: track data may not match Track 2/3 format")

        # 6. Send to Arduino via serial
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                # Opening resets Arduino
                time.sleep(2)
                line = ser.readline().decode(errors="ignore")
                if "READY" not in line:
                    return f"Arduino not ready. Got: {line.strip()}"

                # send count or INF
                ser.write((count_str + "\n").encode())
                # send delay
                ser.write((delay + "\n").encode())
                # send track_type
                ser.write((track_type + "\n").encode())
                # send track data
                ser.write((track_val + "\n").encode())
        except Exception as e:
            return f"Serial communication failed: {e}"

        # 7. Build redirect query for status page
        qs = []
        if infinite == "1":
            qs.append("infinite=1")
        else:
            qs.append(f"num_times={int(num_times)}")
            qs.append("infinite=0")
        qs.append(f"delay={int(delay)}")
        qs.append("track_type=" + urllib.parse.quote(track_type))
        qs.append("track=" + urllib.parse.quote(track_val, safe=''))
        query = "&".join(qs)
        raise cherrypy.HTTPRedirect(f"/status?{query}")

    @cherrypy.expose
    def status(self, num_times=None, delay=None, track=None, infinite=None, track_type=None):
        # Serve status.html; JS will read query params to display info and timer
        return open(STATUS_HTML)

    @cherrypy.expose
    def stop(self):
        # Reset Arduino: zero-run
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                time.sleep(2)
                ser.readline()  # consume READY
                ser.write(b"0\n5000\n\n")
        except Exception as e:
            return f"Stop failed: {e}"
        raise cherrypy.HTTPRedirect("/")

if __name__ == '__main__':
    cherrypy.config.update({
        'server.socket_host': ip_address,
        'server.socket_port': 8080
    })
    cherrypy.quickstart(MagSpoofWeb())
