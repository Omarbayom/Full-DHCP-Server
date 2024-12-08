import socket
import struct
import time

client_mac = "00:1A:2B:3C:4D:5E"  # Example MAC address

# Send a DHCP Discover message to the server
def send_dhcp_discover(client_socket):
    xid = 12345  # Unique transaction ID
    msg_type = 1  # DHCP Discover
    discover_message = struct.pack("!I B", xid, msg_type)

    client_socket.sendto(discover_message, ("255.255.255.255", 67))
    print("Sent DHCP Discover...")

# Start the DHCP client
def start_dhcp_client():
    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_socket.bind(("", 68))  # Bind to DHCP client port

    # Send DHCP Discover
    send_dhcp_discover(client_socket)

    while True:
        # Receive DHCP messages
        message, server_address = client_socket.recvfrom(1024)
        xid, msg_type = struct.unpack("!I B", message[:5])

        if msg_type == 2:  # DHCP Offer
            offered_ip = socket.inet_ntoa(message[5:9])
            print(f"Received DHCP Offer: {offered_ip} from {server_address}")

            # Send DHCP Request
            request_message = struct.pack("!I B 4s", xid, 3, socket.inet_aton(offered_ip))
            client_socket.sendto(request_message, server_address)
            print(f"Requested IP: {offered_ip}")

        elif msg_type == 5:  # DHCP Ack
            lease_duration = struct.unpack("!I", message[9:13])[0]  # Extract lease duration from DHCP Ack
            print(f"Received DHCP Ack: Lease successful! Lease duration: {lease_duration} seconds")
            
            # Wait for lease duration to expire before requesting a new IP
            time.sleep(lease_duration + 1)  # Wait for lease to expire
            print("Lease expired, requesting a new IP...")
            print("Closing the connection.")
            client_socket.close()
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            client_socket.bind(("", 68))
            # Send a new DHCP Discover after the lease expires
            send_dhcp_discover(client_socket)

        elif msg_type == 6:  # DHCP Nak
            print("Received DHCP Nak: Request rejected.")
            break

        time.sleep(1)  # Small delay to avoid flooding

if __name__ == "__main__":
    start_dhcp_client()