import socket
import struct
import threading
import time
import subprocess
import platform
import logging
from config import ip_pool, lease_duration, server_ip, lease_table, discover_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("dhcp_server.log"),
        logging.StreamHandler()
    ]
)

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
                    expired_clients.append((client_address, xid, mac_address))

            for client_address, xid, mac_address in expired_clients:
                ip, _, _, _ = lease_table.pop(client_address)
                
                # Return the IP to the pool
                with ip_pool_lock:
                    ip_pool.append(ip)
                
                logging.info(f"Lease expired: Released IP {ip} for client {client_address} (MAC: {mac_address}) (XID: {xid})")
                
                # Remove the client from discover_cache
                with discover_cache_lock:  # Ensure thread safety if discover_cache is shared across threads
                    for key in list(discover_cache.keys()):
                        logging.debug(f"Checking {mac_address} with {discover_cache[key].get('mac_address')}")
                        if discover_cache[key].get('mac_address') == mac_address:
                            del discover_cache[key]
                            logging.info(f"Removed client {client_address} (MAC: {mac_address}) from discover_cache")
                            break  # Exit loop once the entry is found and removed
        time.sleep(1)  # Check every 5 seconds


# Handles incoming DHCP messages from clients
def handle_client(message, client_address, server_socket):
    xid, msg_type = struct.unpack("!I B", message[:5])

    if msg_type == 1:  # DHCP Discover
        logging.info(f"Received DHCP Discover from {client_address}")

        # Extract MAC address from the message (starting from byte 5)
        mac_address = ':'.join(['%02x' % b for b in message[5:11]])  # MAC is 6 bytes
        logging.info(f"Client MAC Address: {mac_address}")

        # Extract requested IP and lease duration if present
        options = message[11:]  # DHCP options start after the MAC address
        requested_ip = None
        requested_lease = lease_duration
        if not ip_pool:
            logging.warning("IP pool is empty. Cannot assign IP to client.")
            nak_message = struct.pack("!I B", xid, 6)  # DHCP NAK (Not Acknowledged)
            server_socket.sendto(nak_message, client_address)
            return

        i = 0
        while i + 1 < len(options):
            option_type = options[i]
            option_length = options[i + 1]
            option_value = options[i + 2:i + 2 + option_length]
            if option_type == 50:  # Requested IP (Option 50)
                requested_ip = socket.inet_ntoa(option_value)
                logging.info(f"Requested IP: {requested_ip}")
            elif option_type == 51:  # Lease Duration (Option 51)
                requested_lease = struct.unpack("!I", option_value)[0]
                logging.info(f"Requested Lease Duration: {requested_lease} seconds")
            i += 2 + option_length

        if requested_ip and requested_ip not in ip_pool:
            logging.warning(f"Requested IP {requested_ip} is not available.")
            requested_ip = ip_pool[0]
        
        if not requested_ip:
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
                logging.info(f"Offering Requested IP {requested_ip} to {client_address} (MAC: {mac_address}) with lease duration {requested_lease} seconds")

                offer_message = struct.pack(
                    "!I B 4s 16s", xid, 2, socket.inet_aton(requested_ip), bytes.fromhex(mac_address.replace(":", ""))
                )
                server_socket.sendto(offer_message, client_address)
            else:
                logging.warning(f"Requested IP {requested_ip} is not available.")
                nak_message = struct.pack("!I B", xid, 6)  # DHCP NAK (Not Acknowledged)
                server_socket.sendto(nak_message, client_address)

    elif msg_type == 3:  # DHCP Request
        requested_lease = lease_duration
        requested_ip = socket.inet_ntoa(message[5:9])

        # Retrieve saved Discover data from cache
        with discover_cache_lock:
            discover_data = discover_cache.get(client_address)
            if discover_data:
                requested_ip = discover_data['requested_ip'] or requested_ip
                requested_lease = discover_data['requested_lease'] or requested_lease
                logging.info(f"Received DHCP Request from {client_address} for IP {requested_ip} with lease duration {requested_lease} seconds")

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
                logging.info(f"Assigned IP {requested_ip} to {client_address} (MAC: {lease_table[client_address][3]}) with lease duration {requested_lease} seconds")
            else:
                # DHCP Nak if the requested IP does not match
                nak_message = struct.pack("!I B", xid, 6)
                server_socket.sendto(nak_message, client_address)
                logging.warning(f"Rejected IP request {requested_ip} from {client_address} (MAC: {lease_table.get(client_address, ('',))[3]})")
                
    elif msg_type == 4:  # DHCP Decline
        xid, msg_type, mac_bytes, server_identifier, leased_ip = struct.unpack("!I B 16s 4s 4s", message[:29])
        declined_ip = socket.inet_ntoa(leased_ip)
        logging.info(f"Received DHCP Decline for IP {declined_ip} from {client_address}")
        if client_address in lease_table:
            lease_record = lease_table[client_address]
            lease_record = list(lease_record)
            if lease_record[0] == declined_ip:
                # Update the expiry time to the current time
                lease_record[1] = time.time()
                lease_record = tuple(lease_record)
                lease_table[client_address] = lease_record  # Update the record in the table
                logging.info(f"Updated lease expiry for IP {declined_ip} to current time")

    elif msg_type == 7:  # DHCP Release
        xid, msg_type, mac_bytes, server_identifier, leased_ip = struct.unpack("!I B 16s 4s 4s", message[:29])
        released_ip = socket.inet_ntoa(leased_ip)
        logging.info(f"Received DHCP Release for IP {released_ip} from {client_address}")
        if client_address in lease_table:
            lease_record = lease_table[client_address]
            lease_record = list(lease_record)
            if lease_record[0] == released_ip:
                # Update the expiry time to the current time
                lease_record[1] = time.time()
                lease_record = tuple(lease_record)
                lease_table[client_address] = lease_record  # Update the record in the table
                logging.info(f"Updated lease expiry for IP {released_ip} to current time")



# Starts the DHCP server
def start_dhcp_server():
    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((server_ip, 67))  # DHCP server listens on port 67
    logging.info(f"DHCP Server started on {server_ip}, waiting for clients...")

    # Start the lease expiry checker in a separate thread
    threading.Thread(target=lease_expiry_checker, daemon=True).start()

    while True:
        # Receive DHCP messages
        message, client_address = server_socket.recvfrom(1024)
        threading.Thread(target=handle_client, args=(message, client_address, server_socket)).start()

if __name__ == "__main__":
    start_dhcp_server()
