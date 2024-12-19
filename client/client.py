import socket
import struct
import time
import random

# Function to generate a unique MAC address
def generate_unique_mac():
    """Generate a unique MAC address."""
    mac = [0x00, 0x1A, 0x2B, random.randint(0x00, 0xFF),
           random.randint(0x00, 0xFF), random.randint(0x00, 0xFF)]
    return ":".join(f"{octet:02X}" for octet in mac)

# Function to generate a unique transaction ID
def generate_transaction_id():
    """Generate a unique transaction ID."""
    return random.randint(1, 0xFFFFFFFF)

# Send a DHCP Discover message to the server with options
def send_dhcp_discover(client_socket, xid, mac_address, requested_ip=None, lease_duration=None):
    msg_type = 1  # DHCP Discover
    mac_bytes = bytes.fromhex(mac_address.replace(":", ""))  # Convert MAC address to bytes

    # Pad MAC address to 16 bytes (if shorter)
    mac_bytes = mac_bytes.ljust(16, b'\x00')

    # Start building the DHCP Discover message
    discover_message = struct.pack("!I B 16s", xid, msg_type, mac_bytes)

    # Optional DHCP Options: Requested IP and Lease Duration
    options = b''

    if requested_ip:
        requested_ip_bytes = socket.inet_aton(requested_ip)
        options += struct.pack("!BB4s", 50, 4, requested_ip_bytes)  # Option 50 (Requested IP)

    if lease_duration:
        options += struct.pack("!BBI", 51, 4, lease_duration)  # Option 51 (Lease Time)

    # Append end of options field (Option 255)
    options += struct.pack("!B", 255)

    # Final message: DHCP Discover + Options
    discover_message += options

    # Send the message to the broadcast address on port 67 (DHCP Server)
    client_socket.sendto(discover_message, ("255.255.255.255", 67))
    print(f"Sent DHCP Discover from MAC {mac_address} with options: IP {requested_ip}, Lease Duration {lease_duration}...")

# Send DHCP Request message to the server
def send_dhcp_request(client_socket, xid, mac_address, server_identifier, offered_ip,server_address):
    msg_type = 3  # DHCP Request
    mac_bytes = bytes.fromhex(mac_address.replace(":", ""))  # Convert MAC address to bytes

    # Pad MAC address to 16 bytes (if shorter)
    mac_bytes = mac_bytes.ljust(16, b'\x00')

    # Start building the DHCP Request message
    request_message = struct.pack("!I B 16s 4s 4s", xid, msg_type, mac_bytes, socket.inet_aton(server_identifier), socket.inet_aton(offered_ip))

    # Append end of options field (Option 255)
    request_message += struct.pack("!B", 255)

    # Send the message to the server
    client_socket.sendto(request_message, (str(server_address[0]), 67))
    print(f"Sent DHCP Request for IP {offered_ip} to server {server_address}")

# Start the DHCP client
def start_dhcp_client(mac_address=None,requested_ip=None,lease_duration=None):
    # Generate unique identifiers for the client


    xid = generate_transaction_id()

    # Bind to a unique port for each instance
    port = random.randint(10000, 65000)

    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_socket.bind(("", port))  # Bind to a unique port for each client

    # Set timeout for the socket
    client_socket.settimeout(10)  # Timeout in seconds

    print(f"Starting DHCP client on port {port} with MAC {mac_address} and XID {xid}...")

    # Define optional DHCP Discover parameters (requested IP and lease duration)


    # Send DHCP Discover with options
    send_dhcp_discover(client_socket, xid, mac_address, requested_ip, lease_duration)

    try:
        while True:
            # Receive DHCP messages
            message, server_address = client_socket.recvfrom(1024)
            xid_received, msg_type = struct.unpack("!I B", message[:5])

            if xid_received != xid:
                # Ignore messages not meant for this client
                continue

            if msg_type == 2:  # DHCP Offer
                offered_ip = socket.inet_ntoa(message[5:9])
                server_identifier = socket.inet_ntoa(message[9:13])
                print(f"Received DHCP Offer: {offered_ip} from {server_address}")

                # Send DHCP Request
                send_dhcp_request(client_socket, xid, mac_address, server_identifier, offered_ip,server_address)

            elif msg_type == 5:  # DHCP Ack
                # Extract lease duration from DHCP Ack
                lease_duration = struct.unpack("!I", message[9:13])[0]
                print(f"Received DHCP Ack: Lease successful! Lease duration: {lease_duration} seconds")
                break

            elif msg_type == 6:  # DHCP Nak
                print("Received DHCP Nak: Request rejected.")
                break

            time.sleep(1)  # Small delay to avoid flooding

    except socket.timeout:
        print("Timeout: No response from DHCP server.")
        # Optionally retry or exit
        print("Retry sending DHCP Discover...")
        start_dhcp_client(mac_address=mac_address,requested_ip=requested_ip,lease_duration=lease_duration)
    finally:
        client_socket.close()

if __name__ == "__main__":
    requested_ip = "192.168.1.101"  # Example requested IP
    lease_duration = 15  
    mac_address = generate_unique_mac()
    start_dhcp_client(mac_address=mac_address)