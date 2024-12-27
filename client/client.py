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

# Function to send a DHCP Discover message
def send_dhcp_discover(client_socket, xid, mac_address, requested_ip=None, lease_duration=None):
    """Send a DHCP Discover message with optional parameters."""
    msg_type = 1  # DHCP Discover

    mac_bytes = bytes.fromhex(mac_address.replace(":", ""))  # Convert MAC address to bytes
    mac_bytes = mac_bytes.ljust(16, b'\x00')  # Pad MAC address to 16 bytes

    # Build the DHCP Discover message
    discover_message = struct.pack("!I B 16s", xid, msg_type, mac_bytes)

    # Optional DHCP Options
    options = b''
    if requested_ip:
        requested_ip_bytes = socket.inet_aton(requested_ip)
        options += struct.pack("!BB4s", 50, 4, requested_ip_bytes)  # Option 50: Requested IP
    if lease_duration:
        options += struct.pack("!BBI", 51, 4, lease_duration)  # Option 51: Lease Time

    # Append end of options field (Option 255)
    options += struct.pack("!B", 255)

    # Final message: DHCP Discover + Options
    discover_message += options

    # Send the message to the broadcast address on port 67 (DHCP Server)
    client_socket.sendto(discover_message, ("255.255.255.255", 67))
    print(f"Sent DHCP Discover from MAC {mac_address} with options: IP {requested_ip}, Lease Duration {lease_duration}...")

# Function to send a DHCP Request or Decline message
def send_dhcp_request_or_decline(client_socket, xid, mac_address, server_identifier, offered_ip, server_address, requested_ip):
    """Send a DHCP Request or Decline message based on the conditions."""
    if (requested_ip and offered_ip == requested_ip) or not requested_ip:
        msg_type = 3  # DHCP Request
        action = "Request"
    else:
        actions = input("Enter Action Needed (R for Request, D for Decline): ")
        if actions.upper() == "R":
            msg_type = 3  # DHCP Request
            action = "Request"
        else:
            msg_type = 4  # DHCP Decline
            action = "Decline"

    mac_bytes = bytes.fromhex(mac_address.replace(":", ""))
    mac_bytes = mac_bytes.ljust(16, b'\x00')  # Pad MAC address to 16 bytes

    # Build the message
    message = struct.pack("!I B 16s 4s 4s", xid, msg_type, mac_bytes, socket.inet_aton(server_identifier), socket.inet_aton(offered_ip))
    message += struct.pack("!B", 255)  # Append end of options field

    # Send the message to the server
    client_socket.sendto(message, (server_address[0], 67))
    print(f"Sent DHCP {action} for IP {offered_ip} to server {server_address}")
    return action

# Function to send a DHCP Release message
def send_dhcp_release(client_socket, xid, mac_address, server_identifier, leased_ip, server_address):
    """Send a DHCP Release message to the server."""
    msg_type = 7  # DHCP Release

    mac_bytes = bytes.fromhex(mac_address.replace(":", ""))
    mac_bytes = mac_bytes.ljust(16, b'\x00')

    # Build the message
    release_message = struct.pack("!I B 16s 4s 4s", xid, msg_type, mac_bytes, socket.inet_aton(server_identifier), socket.inet_aton(leased_ip))
    release_message += struct.pack("!B", 255)  # Append end of options field

    # Send the message to the server
    client_socket.sendto(release_message, (server_address[0], 67))
    print(f"Sent DHCP Release for IP {leased_ip} to server {server_address}")

# Function to start the DHCP client
def start_dhcp_client(mac_address=None, requested_ip=None, lease_duration=None):
    """Start the DHCP client."""
    xid = generate_transaction_id()
    port = random.randint(10000, 65000)

    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_socket.bind(("", 68))  # Bind to a unique port
    client_socket.settimeout(10)  # Set socket timeout

    print(f"Starting DHCP client on port {port} with MAC {mac_address} and XID {xid}...")

    # Send DHCP Discover
    send_dhcp_discover(client_socket, xid, mac_address, requested_ip, lease_duration)
    try:
        while True:
            # Receive DHCP messages
            message, server_address = client_socket.recvfrom(1024)
            xid_received, msg_type = struct.unpack("!I B", message[:5])

            if xid_received != xid:
                continue  # Ignore messages not meant for this client

            if msg_type == 2:  # DHCP Offer
                offered_ip = socket.inet_ntoa(message[5:9])
                server_identifier = socket.inet_ntoa(message[9:13])
                print(f"Received DHCP Offer: {offered_ip} from {server_address}")

                # Send DHCP Request or Decline
                action = send_dhcp_request_or_decline(client_socket, xid, mac_address, server_identifier, offered_ip, server_address, requested_ip)
                if action == "Decline":
                    return [-1]

            elif msg_type == 5:  # DHCP Ack
                lease_duration = struct.unpack("!I", message[9:13])[0]
                leased_ip = socket.inet_ntoa(message[5:9])
                print(f"Received DHCP Ack: Lease successful! Lease duration: {lease_duration} seconds for IP {leased_ip}")
                return [lease_duration, client_socket, xid, mac_address, server_identifier, leased_ip, server_address]

            elif msg_type == 6:  # DHCP Nak
                print("Received DHCP Nak: Request rejected.")
                return [-1]

    except socket.timeout:
        print("Timeout: No response from DHCP server.")
        return [-1]
    finally:
        client_socket.close()

if __name__ == "__main__":
    requested_ip = "192.168.1.101"  # Example requested IP
    lease_duration = 15  # Example lease duration
    mac_address = generate_unique_mac()

    lease_info = start_dhcp_client(mac_address=mac_address, requested_ip=requested_ip, lease_duration=lease_duration)
    if len(lease_info) > 1:
        duration, client_socket, xid, mac_address, server_identifier, leased_ip, server_address = lease_info
        try:
            for _ in range(duration):
                time.sleep(1)
        except KeyboardInterrupt:
            send_dhcp_release(client_socket, xid, mac_address, server_identifier, leased_ip, server_address)
    elif lease_info == [-1]:
        print("Error: DHCP Client failed.")
