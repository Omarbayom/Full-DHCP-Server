import socket
import struct
import threading
import time
from config import ip_pool, lease_duration, server_ip, lease_table, discover_cache

# Lock for synchronizing access to shared data
lease_table_lock = threading.Lock()
ip_pool_lock = threading.Lock()
discover_cache_lock = threading.Lock()

# Periodically checks for expired leases
def lease_expiry_checker():
    while True:
        current_time = time.time()
        expired_clients = []

        with lease_table_lock:
            for client_address, (ip, lease_expiry, xid, mac_address) in lease_table.items():
                if lease_expiry < current_time:
                    expired_clients.append(client_address)

            for client_address in expired_clients:
                ip, _, xid, mac_address = lease_table.pop(client_address)
                with ip_pool_lock:
                    ip_pool.append(ip)  # Return IP to the pool
                print(f"Lease expired: Released IP {ip} for client {client_address} (MAC: {mac_address})")

        time.sleep(5)  # Check every 5 seconds

# Function to check if an IP address is in use (ping probe)
def is_ip_in_use(ip):
    try:
        # Send an ICMP Echo Request (ping) to the offered IP address
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        sock.settimeout(1)
        sock.sendto(b'\x08\x00\x7f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', (ip, 0))  # ICMP Echo Request
        sock.recvfrom(1024)  # Wait for the response
        sock.close()
        return True  # IP is in use
    except socket.timeout:
        return False  # No response, IP is free
    except Exception:
        return False  # Handle other exceptions

# Handles incoming DHCP messages from clients
def handle_client(message, client_address, server_socket):
    xid, msg_type = struct.unpack("!I B", message[:5])

    if msg_type == 1:  # DHCP Discover
        print(f"Received DHCP Discover from {client_address}")

        # Extract MAC address from the message (starting from byte 5)
        mac_address = ':'.join(['%02x' % b for b in message[5:11]])  # MAC is 6 bytes
        print(f"Client MAC Address: {mac_address}")

        # Extract requested IP and lease duration if present
        options = message[11:]  # DHCP options start after the MAC address
        requested_ip = None
        requested_lease = lease_duration

        i = 0
        while i+1 < len(options):
            option_type = options[i]
            option_length = options[i + 1]
            option_value = options[i + 2:i + 2 + option_length]
            if option_type == 50:  # Requested IP (Option 50)
                requested_ip = socket.inet_ntoa(option_value)
                print(f"Requested IP: {requested_ip}")
            elif option_type == 51:  # Lease Duration (Option 51)
                requested_lease = struct.unpack("!I", option_value)[0]
                print(f"Requested Lease Duration: {requested_lease} seconds")
            i += 2 + option_length

        if requested_ip and is_ip_in_use(requested_ip):
            print(f"IP {requested_ip} is already in use. Selecting another IP.")
            requested_ip = ip_pool[0]

        # Save the Discover message options for later use in Request
        with discover_cache_lock:
            discover_cache[client_address] = {
                'mac_address': mac_address,
                'requested_ip': requested_ip,
                'requested_lease': requested_lease or lease_duration
            }

        # Send DHCP Offer
        with ip_pool_lock:
            if requested_ip and requested_ip in ip_pool:
                ip_pool.remove(requested_ip)
                with lease_table_lock:
                    lease_table[client_address] = (
                        requested_ip, time.time() + requested_lease, xid, mac_address
                    )
                print(f"Offering Requested IP {requested_ip} to {client_address} (MAC: {mac_address}) with lease duration {requested_lease} seconds")

                offer_message = struct.pack(
                    "!I B 4s 16s", xid, 2, socket.inet_aton(requested_ip), bytes.fromhex(mac_address.replace(":", ""))
                )
                server_socket.sendto(offer_message, client_address)
            else:
                print(f"Requested IP {requested_ip} is not available.")
                nak_message = struct.pack("!I B", xid, 6)  # DHCP NAK (Not Acknowledged)
                server_socket.sendto(nak_message, client_address)

    elif msg_type == 3:  # DHCP Request
        requested_lease = lease_duration
        requested_ip = socket.inet_ntoa(message[5:9])

        # Retrieve saved Discover data from cache
        with discover_cache_lock:
            discover_data = discover_cache.get(client_address)
            if discover_data:
                requested_ip =  discover_data['requested_ip'] or requested_ip
                requested_lease =   discover_data['requested_lease']or requested_lease
                print(f"Received DHCP Request from {client_address} for IP {requested_ip} with lease duration {requested_lease} seconds")

        with lease_table_lock:
            if client_address in lease_table and lease_table[client_address][0] == requested_ip:
                # Renew the lease with the requested lease time
                lease_table[client_address] = (
                    requested_ip, time.time() + requested_lease, lease_table[client_address][2], lease_table[client_address][3]
                )

                # DHCP Ack with the requested lease duration
                ack_message = struct.pack(
                    "!I B 4s I", xid, 5, socket.inet_aton(requested_ip), requested_lease
                )
                server_socket.sendto(ack_message, client_address)
                print(f"Assigned IP {requested_ip} to {client_address} (MAC: {lease_table[client_address][3]}) with lease duration {requested_lease} seconds")
            else:
                # DHCP Nak if the requested IP does not match
                nak_message = struct.pack("!I B", xid, 6)
                server_socket.sendto(nak_message, client_address)
                print(f"Rejected IP request {requested_ip} from {client_address} (MAC: {lease_table.get(client_address, ('',))[3]})")

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
        threading.Thread(target=handle_client, args=(message, client_address, server_socket)).start()

if __name__ == "__main__":
    start_dhcp_server()
