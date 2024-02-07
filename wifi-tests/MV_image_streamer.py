import sensor
import time
import network
import socket
import errno
from machine import LED

led = LED("LED_BLUE")
led.on()

# Network settings
SSID = 'charlie'  # Network SSID
KEY = 'password123'  # Network key

# Video streaming settings
HOST_STREAM = ''  # Use first available interface for streaming
PORT_STREAM = 8080  # Port for video streaming

# Script execution settings
HOST_EXEC = ''  # Use first available interface for script execution
PORT_EXEC = 8081  # Port for script execution

# Initialize the camera sensor
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)

# Initialize and connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, KEY)
while not wlan.isconnected():
    time.sleep_ms(100)

print("WiFi Connected. IP:", wlan.ifconfig()[0])

# Create server sockets
stream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
exec_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Set sockets to non-blocking
stream_socket.setblocking(False)
exec_socket.setblocking(False)

# Bind and listen on both sockets
stream_socket.bind((HOST_STREAM, PORT_STREAM))
exec_socket.bind((HOST_EXEC, PORT_EXEC))
stream_socket.listen(1)
exec_socket.listen(1)

# Variables for clients
stream_client = None

def execute_script(script):
    try:
        exec(script, globals())
        print("Script executed successfully.")
    except Exception as e:
        print("Error executing script:", e)

while True:
    # Accept new video streaming connection
    if not stream_client:
        try:
            stream_client, _ = stream_socket.accept()
            stream_client.sendall(
                b"HTTP/1.1 200 OK\r\n"
                b"Server: OpenMV\r\n"
                b"Content-Type: multipart/x-mixed-replace;boundary=openmv\r\n"
                b"Cache-Control: no-cache\r\n"
                b"Pragma: no-cache\r\n\r\n"
            )
        except Exception as e:
            if str(e) != '[Errno 11] EAGAIN' and str(e) != '[Errno 11] EWOULDBLOCK':
                pass  # No new connection

    # Accept new script execution connection
    try:
        exec_client, _ = exec_socket.accept()
        script = exec_client.recv(2048)  # Adjust buffer size as needed
        print("Received script:", script)  # Print the received script for debugging
        execute_script(script)
        exec_client.close()
        exec_client = None
    except Exception as e:
        if str(e) != '[Errno 11] EAGAIN' and str(e) != '[Errno 11] EWOULDBLOCK':
            pass  # No new connection

    # Stream the framebuffer content
    if stream_client:
        try:
            fb = sensor.get_fb()  # Get the framebuffer
            if fb is not None:
                jpg = fb.compress(quality=35)  # Compress the framebuffer
                header = b"--openmv\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(jpg.size()).encode() + b"\r\n\r\n"
                stream_client.sendall(header + jpg)
        except Exception as e:
            if 'EWOULDBLOCK' in str(e) or 'EAGAIN' in str(e):
                continue
            else:
                stream_client.close()
                stream_client = None

    time.sleep_ms(10)  # Small delay to prevent a busy loop
