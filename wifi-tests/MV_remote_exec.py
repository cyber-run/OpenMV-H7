import sensor
import time
import network
import socket
import errno
from machine import LED

led = LED("LED_BLUE")
led.on()

SSID = "OPENMV_AP"  # Network SSID GIVE THIS A UNIQUE NAME
KEY = "1234567890"  # Network key (must be 10 chars)
HOST = ""  # Use first available interface
PORT = 8080  # Arbitrary non-privileged port

# Init wlan module and connect to network
wlan = network.WLAN(network.AP_IF)
wlan.active(0)
wlan.config(ssid=SSID, key=KEY, channel=2)
wlan.active(1)
print("AP mode started. SSID: {} IP: {}".format(SSID, wlan.ifconfig()[0]))

# Initialize server socket for script execution
exec_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
exec_socket.bind((HOST, PORT))
exec_socket.listen(1)
print("Listening for script execution on port", PORT)

def execute_script(script):
    try:
        exec(script, globals())
        print("Script executed successfully.")
    except Exception as e:
        print("Error executing script:", e)

while True:
    print("Waiting for a script...")
    conn, addr = exec_socket.accept()
    print("Connected by", addr)

    # Receive the script
    script = ''
    while True:
        data = conn.recv(1024)
        if not data:
            break
        script += data.decode()

    print("Received script:", script)
    execute_script(script)
    conn.close()
    print("Connection closed")

    time.sleep(1)  # Sleep for a bit before next listen
