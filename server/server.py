import socket
import struct
import threading
import time

from config import ip_pool, lease_duration, server_ip, lease_table


# Lock for synchronizing access to shared data
lease_table_lock = threading.Lock()
ip_pool_lock = threading.Lock()

# Periodically checks for expired leases


def lease_expiry_checker():
    while True:
        current_time = time.time()
        expired_clients = []

        with lease_table_lock:
            for client_address, (ip, lease_expiry,_,_) in lease_table.items():
                if lease_expiry < current_time:
                    expired_clients.append(client_address)

            for client_address in expired_clients:
                woh=lease_table[client_address]
                print(lease_table[client_address])
                ip, _,_,_ = lease_table.pop(client_address)
                with ip_pool_lock:
                    ip_pool.append(ip)  # Return IP to the pool
                print(f"Lease expired: Released IP {
                      ip} for client {woh}")

        time.sleep(5)  # Check every 5 seconds

# Handles incoming DHCP messages from clients


def handle_client(message, client_address, server_socket):
    xid, msg_type = struct.unpack("!I B", message[:5])

    if msg_type == 1:  # DHCP Discover
        print(f"Received DHCP Discover from {client_address}")

        # Extract MAC address from the message (starting from byte 5)
        mac_address = ':'.join(
            ['%02x' % b for b in message[5:11]])  # MAC is 6 bytes
        print(f"Client MAC Address: {mac_address}")

        with ip_pool_lock:
            if ip_pool:
                offered_ip = ip_pool.pop(0)
                with lease_table_lock:
                    lease_table[client_address] = (
                        offered_ip, time.time() + lease_duration,xid,mac_address)
                print(f"Offering IP {offered_ip} to {client_address}")

                # DHCP Offer: Include MAC address in the offer
                offer_message = struct.pack(
                    "!I B 4s 16s", xid, 2, socket.inet_aton(
                        offered_ip), bytes.fromhex(mac_address.replace(":", ""))
                )
                server_socket.sendto(offer_message, client_address)
            else:
                print("No IPs available in the pool.")
                nak_message = struct.pack("!I B", xid, 6)
                server_socket.sendto(nak_message, client_address)

    elif msg_type == 3:  # DHCP Request
        requested_ip = socket.inet_ntoa(message[5:9])
        print(f"Received DHCP Request for {
              requested_ip} from {client_address}")

        with lease_table_lock:
            if client_address in lease_table and lease_table[client_address][0] == requested_ip:
                # Renew the lease
                lease_table[client_address] = (
                    requested_ip, time.time() + lease_duration,lease_table[client_address][2],lease_table[client_address][3])

                # DHCP Ack
                ack_message = struct.pack(
                    "!I B 4s I", xid, 5, socket.inet_aton(requested_ip), lease_duration)
                server_socket.sendto(ack_message, client_address)
                print(f"Assigned IP {requested_ip} to {
                      client_address} with lease duration {lease_duration} seconds")
            else:
                # DHCP Nak
                nak_message = struct.pack("!I B", xid, 6)
                server_socket.sendto(nak_message, client_address)
                print(f"Rejected IP request {
                      requested_ip} from {client_address}")

# Starts the DHCP server


def start_dhcp_server():
    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((server_ip, 67))  # DHCP server listens on port 67
    print(f"DHCP Server started on {server_ip}, waiting for clients...")

    # Start the lease expiry checker in a separate thread
    threading.Thread(target=lease_expiry_checker, daemon=True).start()

    while True:
        # Receive DHCP messages
        message, client_address = server_socket.recvfrom(1024)
        threading.Thread(target=handle_client, args=(
            message, client_address, server_socket)).start()


if __name__ == "__main__":
    start_dhcp_server()
