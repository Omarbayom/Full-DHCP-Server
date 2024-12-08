import socket
import struct
import threading
import time

# Lease data structure
lease_table = {}
ip_pool = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]  # Example IP pool
lease_duration = 10  # Lease time in seconds (1 hour)
server_ip = "192.168.1.10"  # DHCP server IP address

def check_expired_leases():
    """Periodically checks and cleans up expired leases"""
    while True:
        current_time = time.time()
        expired_clients = [client for client, (ip, lease_time) in lease_table.items() if lease_time <= current_time]

        for client in expired_clients:
            print(f"Lease expired for {client}, releasing IP")
            ip = lease_table[client][0]
            ip_pool.append(ip)  # Add expired IP back to the pool
            del lease_table[client]  # Remove expired lease from the lease table

        time.sleep(lease_duration)  # Sleep for lease_duration before checking again

def handle_client(message, client_address, server_socket):
    global ip_pool
    xid, msg_type = struct.unpack("!I B", message[:5])

    # Clean expired leases (run this check in the background)
    threading.Thread(target=check_expired_leases, daemon=True).start()

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

            # DHCP Nak (Negative Acknowledgment) to inform client there are no IPs available
            nak_message = struct.pack("!I B", xid, 6)  # DHCP NAK message
            server_socket.sendto(nak_message, client_address)
            print(f"Sent DHCP Nak to {client_address} - No IPs available")

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
