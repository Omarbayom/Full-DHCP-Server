import socket
import struct
import time
import random


def generate_unique_mac():
    """Generate a unique MAC address."""
    mac = [0x00, 0x1A, 0x2B, random.randint(0x00, 0xFF),
           random.randint(0x00, 0xFF), random.randint(0x00, 0xFF)]
    return ":".join(f"{octet:02X}" for octet in mac)


def generate_transaction_id():
    """Generate a unique transaction ID."""
    return random.randint(1, 0xFFFFFFFF)

# Send a DHCP Discover message to the server


def send_dhcp_discover(client_socket, xid, mac_address):
    msg_type = 1  # DHCP Discover
    mac_bytes = bytes.fromhex(mac_address.replace(
        ":", ""))  # Convert MAC address to bytes

    mac_bytes = mac_bytes.ljust(16, b'\x00')

    discover_message = struct.pack("!I B 16s", xid, msg_type, mac_bytes)

    client_socket.sendto(discover_message, ("255.255.255.255", 67))
    print(f"Sent DHCP Discover from MAC {mac_address}...")

# Start the DHCP client


def start_dhcp_client():
    # Generate unique identifiers for the client
    mac_address = generate_unique_mac()
    xid = generate_transaction_id()
    # Bind to a unique port for each instance
    port = random.randint(10000, 65000)

    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_socket.bind(("", port))  # Bind to a unique port for each client

    # Set timeout for the socket
    client_socket.settimeout(10)  # Timeout in seconds

    print(f"Starting DHCP client on port {
          port} with MAC {mac_address} and XID {xid}...")

    # Send DHCP Discover
    send_dhcp_discover(client_socket, xid, mac_address)

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
                print(f"Received DHCP Offer: {
                      offered_ip} from {server_address}")

                # Send DHCP Request
                request_message = struct.pack(
                    "!I B 4s", xid, 3, socket.inet_aton(offered_ip))
                client_socket.sendto(request_message, server_address)
                print(f"Requested IP: {offered_ip}")

            elif msg_type == 5:  # DHCP Ack
                # Extract lease duration from DHCP Ack
                lease_duration = struct.unpack("!I", message[9:13])[0]
                print(f"Received DHCP Ack: Lease successful! Lease duration: {
                      lease_duration} seconds")
                time.sleep(lease_duration)  # Wait for the lease duration
                start_dhcp_client()  # Renew the lease after lease expiry
                break

            elif msg_type == 6:  # DHCP Nak
                print("Received DHCP Nak: Request rejected.")
                break

            time.sleep(1)  # Small delay to avoid flooding

    except socket.timeout:
        print("Timeout: No response from DHCP server.")
        # Optionally retry or exit
    finally:
        client_socket.close()


if __name__ == "__main__":
    start_dhcp_client()
