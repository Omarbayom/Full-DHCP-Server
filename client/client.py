import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 8080))  # Use localhost
client.send("I am Salah\n".encode())
from_server = client.recv(4096)
client.close()
print(from_server.decode())
