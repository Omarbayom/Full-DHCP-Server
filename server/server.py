import socket
import struct
import threading
import time
import subprocess
import platform
import logging
from collections import deque
import heapq
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

# Convert IP pool to a deque for efficient IP allocation
ip_pool = deque(ip_pool)


def add_lease(client_address, ip, lease_duration, xid, mac_address):
    """
    Add or update a lease in the priority queue (min-heap) with expiry time.
    """
    expiry_time = time.time() + lease_duration
    heapq.heappush(lease_table, (expiry_time, client_address, xid, mac_address, ip))


def remove_expired_leases():
    """
    Remove expired leases from the heap and handle the expired clients.
    """
    current_time = time.time()
    expired_clients = []

    while lease_table and lease_table[0][0] < current_time:
        _, client_address, xid, mac_address, ip = heapq.heappop(lease_table)
        expired_clients.append((client_address, xid, mac_address, ip))
    
    # Handle expired leases
    for client_address, xid, mac_address, ip in expired_clients:
        with ip_pool_lock:
            ip_pool.append(ip)  # Append IP back to pool
        logging.info(f"Lease expired: Released IP {ip} for client {client_address} (MAC: {mac_address}) (XID: {xid})")
        
        # Remove the client from discover_cache
        with discover_cache_lock:
            for key in list(discover_cache.keys()):
                if discover_cache[key].get('mac_address') == mac_address:
                    del discover_cache[key]
                    logging.info(f"Removed client {client_address} (MAC: {mac_address}) from discover_cache")
                    break


def lease_expiry_checker():
    """
    Periodically checks for expired leases and removes them.
    """
    while True:
        remove_expired_leases()
        time.sleep(1)  # Check every second


def is_ip_in_use(ip):
    """
    Use a ping probe to check if an IP address is already in use.
    """
    try:
        if ip not in ip_pool:
            return True
        else:
            return False

    except Exception as e:
        logging.error(f"Error checking IP {ip}: {e}")
        return False


def handle_client(message, client_address, server_socket):
    """
    Handles incoming DHCP messages from clients.
    """
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

        # Check if requested IP is in use, if yes, select another IP
        if requested_ip and is_ip_in_use(requested_ip):
            logging.info(f"IP {requested_ip} is already in use. Selecting another IP.")
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
                add_lease(client_address, requested_ip, requested_lease, xid, mac_address)
                logging.info(f"Offering Requested IP {requested_ip} to {client_address} (MAC: {mac_address}) with lease duration {requested_lease} seconds")

                offer_message = struct.pack(
                    "!I B 4s 16s", xid, 2, socket.inet_aton(requested_ip), bytes.fromhex(mac_address.replace(":", ""))
                )
                offer_message_with_option = offer_message + struct.pack("!BB", 53, 1) + struct.pack("B", 2)  # Option 53: Message Type = 2 (Offer)
                server_socket.sendto(offer_message_with_option, client_address)
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

        # Check lease table for the requested IP and assign it
        with lease_table_lock:
            for lease in lease_table:
                if lease[4] == requested_ip and lease[1] == client_address:
                    # Renew the lease with the requested lease time
                    add_lease(client_address, requested_ip, requested_lease, lease[2], lease[3])

                    # Send DHCP Ack with the requested lease duration
                    ack_message = struct.pack(
                        "!I B 4s I", xid, 5, socket.inet_aton(requested_ip), requested_lease
                    )
                    server_socket.sendto(ack_message, client_address)
                    logging.info(f"Assigned IP {requested_ip} to {client_address} (MAC: {lease[3]}) with lease duration {requested_lease} seconds")
                    break
            else:
                # DHCP Nak if the requested IP does not match
                nak_message = struct.pack("!I B", xid, 6)
                server_socket.sendto(nak_message, client_address)
                logging.warning(f"Rejected IP request {requested_ip} from {client_address} (MAC: {lease[3]})")


def start_dhcp_server():
    """
    Starts the DHCP server, listens for incoming messages, and handles them.
    """
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
