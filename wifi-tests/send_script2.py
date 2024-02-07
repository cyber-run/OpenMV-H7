import socket

def send_script_to_openmv(script, ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip, port))
        s.sendall(script.encode())

# Usage
openmv_ip = '192.168.4.1'  # Replace with your OpenMV camera's IP address
openmv_port = 8080         # The port for script execution
script = "print('Hello from remote script!')"  # Simple script to send

send_script_to_openmv(script, openmv_ip, openmv_port)