import cherrypy
import netifaces as ni
import time
import os
import serial
import urllib.parse

# Path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # ~/MagstripeSpoofer/server
INDEX_HTML = os.path.join(BASE_DIR, "index.html")
STATUS_HTML = os.path.join(BASE_DIR, "status.html")

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600
TRACK_DEFAULT = ";4242004800500=0123456789?"

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
        # Serve index.html
        return open(INDEX_HTML)

    @cherrypy.expose
    def run(self, num_times=None, delay=None, track=None, infinite=None, mode=None):
        # Validate delay
        if not delay:
            return "Missing delay"
        try:
            delay_int = int(delay)
            if delay_int < 50:
                return "Delay must be ≥50 ms"
        except:
            return "Invalid delay"
        track_val = track or TRACK_DEFAULT

        # Determine count_str
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
            except:
                return "Invalid num_times"

        # Send to Arduino via serial
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                # Opening the port resets Arduino via DTR
                time.sleep(2)
                line = ser.readline().decode(errors="ignore")
                if "READY" not in line:
                    return f"Arduino not ready. Got: {line.strip()}"
                # Write lines
                ser.write((count_str + "\n").encode())
                ser.write((delay + "\n").encode())
                ser.write((track_val + "\n").encode())
        except Exception as e:
            return f"Serial communication failed: {e}"

        # Build query string for status.html
        qs = []
        if infinite == "1":
            qs.append("infinite=1")
        else:
            qs.append(f"num_times={int(num_times)}")
            qs.append("infinite=0")
        qs.append(f"delay={int(delay)}")
        if track_val:
            qs.append("track=" + urllib.parse.quote(track_val, safe=''))
        query = "&".join(qs)

        raise cherrypy.HTTPRedirect(f"/status?{query}")

    @cherrypy.expose
    def stop(self):
        # Reset Arduino into idle
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                time.sleep(2)
                ser.readline()
                ser.write(b"0\n5000\n\n")
        except Exception as e:
            return f"Stop failed: {e}"
        # Redirect back to main form
        raise cherrypy.HTTPRedirect("/")

if __name__ == '__main__':
    # CherryPy config to serve status.html at /status
    conf = {
        '/status': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': STATUS_HTML
        }
    }
    cherrypy.config.update({
        'server.socket_host': ip_address,
        'server.socket_port': 8080
    })
    cherrypy.quickstart(MagSpoofWeb(), '/', conf)
