import socket
import logging
# Server configuration
SERVER_PORT = 67
CLIENT_PORT = 68
BUFFER_SIZE = 1024

# Example IP pool from which the DHCP server can assign IPs
ip_pool = [
    "192.168.1.100",
    "192.168.1.101",
    "192.168.1.102",
    "192.168.1.103",
    "192.168.1.104",
]

blocked_mac_addresses = [
    "00:00:00:00:00:00",
    "00:00:00:00:00:01",
    "00:00:00:00:00:02",
    "00:00:00:00:00:03",
    "00:00:00:00:00:04",
    # "a0:b3:cc:49:fc:d7",
]

# Lease duration (time in seconds that the client can use the assigned IP address)
lease_duration = 60  # Default lease time set to 1 hour (3600 seconds)

# Server's IP address, retrieved dynamically
# Get the local IP address of the server
server_ip = socket.gethostbyname(socket.gethostname())

# Lease table: Keeps track of active leases and expiry times
# Example format: lease_table = {client_address: (ip, lease_expiry, xid, mac_address)}
lease_table = {}  # 'mac_address':(requested_id,lease_time,xid)
discover_cache = {}

# Logging configurations (Optional for better debugging)
log_file = "dhcp_server.log"  # Path to log file
log_level = "INFO"  # Log level: INFO, DEBUG, ERROR, etc.


def log_message(message, level="info"):
    if level == "info":
        logging.info(message)
    elif level == "debug":
        logging.debug(message)
    elif level == "error":
        logging.error(message)
    elif level == "warning":
        logging.warning(message)
    else:
        logging.info(message)
