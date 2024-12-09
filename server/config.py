import socket

SERVER_PORT = 67
CLIENT_PORT = 68
BUFFER_SIZE = 1024

ip_pool = ["192.168.1.100", "192.168.1.101",
           "192.168.1.102"]  # Example IP pool
lease_duration = 15  # Lease time in seconds
server_ip = socket.gethostbyname(socket.gethostname())
lease_table = {}  # Tracks active leases: {client_address: (ip, lease_expiry)}
