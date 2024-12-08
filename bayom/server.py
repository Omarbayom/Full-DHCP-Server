import socket
import struct
import threading
import time

# Lease data structure
lease_table = {}
ip_pool = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]  # Example IP pool
lease_duration = 3600  # Lease time in seconds (1 hour)
server_ip = "192.168.1.10"  # DHCP server IP address


def handle_client(message, client_address, server_socket):
    global ip_pool
    xid, msg_type = struct.unpack("!I B", message[:5])

    if msg_type == 1:  # DHCP Discover
        print(f"Received DHCP Discover from {client_address}")
        
        if ip_pool:
            offered_ip = ip_pool.pop(0)
            lease_table[client_address] = (offered_ip, time.time() + lease_duration)
            print(f"Offering IP {offered_ip} to {client_address}")

            # DHCP Offer
            offer_message = struct.pack(
                "!I B 4s", xid, 2, socket.inet_aton(offered_ip)
            )
            server_socket.sendto(offer_message, client_address)
        else:
            print("No IPs available in the pool.")

    elif msg_type == 3:  # DHCP Request
        requested_ip = socket.inet_ntoa(message[5:])
        print(f"Received DHCP Request for {requested_ip} from {client_address}")

        if client_address in lease_table and lease_table[client_address][0] == requested_ip:
            # DHCP Ack
            ack_message = struct.pack("!I B", xid, 5)
            server_socket.sendto(ack_message, client_address)
            print(f"Assigned IP {requested_ip} to {client_address}")
        else:
            # DHCP Nak
            nak_message = struct.pack("!I B", xid, 6)
            server_socket.sendto(nak_message, client_address)
            print(f"Rejected IP request {requested_ip} from {client_address}")


def start_dhcp_server():
    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((server_ip, 67))  # DHCP server listens on port 67
    print(f"DHCP Server started on {server_ip}, waiting for clients...")

    while True:
        # Receive DHCP messages
        message, client_address = server_socket.recvfrom(1024)
        threading.Thread(target=handle_client, args=(message, client_address, server_socket)).start()


if __name__ == "__main__":
    start_dhcp_server()
