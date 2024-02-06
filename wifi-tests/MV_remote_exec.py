import sensor
import time
import network
import socket
import errno
import pyb

led = pyb.LED(1)
led.on()

# Network settings
SSID = 'charlie'  # Network SSID
KEY = 'password123'  # Network key

# Script execution settings
HOST_EXEC = ''  # Use first available interface for script execution
PORT_EXEC = 8081  # Port for script execution

# Initialize and connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, KEY)
while not wlan.isconnected():
    time.sleep_ms(100)

print("WiFi Connected. IP:", wlan.ifconfig()[0])

# Initialize server socket for script execution
exec_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
exec_socket.bind((HOST_EXEC, PORT_EXEC))
exec_socket.listen(1)
print("Listening for script execution on port", PORT_EXEC)

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
