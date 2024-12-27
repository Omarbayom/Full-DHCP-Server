import socket

try:
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    test_socket.bind(('', 67))
    print("Binding successful!")
except Exception as e:
    print(f"Binding failed: {e}")
