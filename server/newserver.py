from pprint import pprint
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


def construct_dhcp_message(
    xid, client_mac, msg_type, server_ip, client_ip="0.0.0.0", your_ip="0.0.0.0", gateway_ip="0.0.0.0",
    options=None, lease_time=60, subnet_mask="255.255.255.0", dns_servers=None, domain_name="example.com",
    broadcast_address=None, t1_time=0, t2_time=0, option_overload=None, time_offset=0, time_servers=None, name_servers=None,
    log_servers=None, cookie_servers=None, lpr_servers=None, impress_servers=None, rlp_servers=None, max_message_size=1500
):
    """
    Constructs a DHCP message with specified options, including additional network configuration options.
    """
    # Fixed-length fields
    op = 2 if msg_type in (2, 5, 6) else 1  # BOOTREPLY for OFFER, ACK, NAK
    htype = 1  # Hardware type: 1 = Ethernet
    hlen = 6  # Hardware address length: 6 bytes for MAC
    hops = 0  # Hops: 0
    secs = 0  # Seconds elapsed: 0
    flags = 0x8000  # Broadcast flag
    chaddr = bytes.fromhex(client_mac.replace(":", "")) + \
        b'\x00' * 10  # Pad to 16 bytes
    sname = b'\x00' * 64  # Server name: 64 bytes, zero-padded
    file = b'\x00' * 128  # Boot filename: 128 bytes, zero-padded

    # Default DHCP Options
    magic_cookie = b'\x63\x82\x53\x63'  # DHCP magic cookie
    default_options = b'\x35\x01' + bytes([msg_type])  # DHCP Message Type

    # Standard Options
    lease_time_option = b'\x33\x04' + struct.pack('!I', lease_time)
    subnet_mask_option = b'\x01\x04' + socket.inet_aton(subnet_mask)
    router_option = b'\x03\x04' + socket.inet_aton(gateway_ip)
    dns_server_option = b""
    if dns_servers:
        dns_list = b"".join(socket.inet_aton(ip) for ip in dns_servers)
        dns_server_option = b'\x06' + \
            len(dns_list).to_bytes(1, 'big') + dns_list
    domain_name_option = b'\x0f' + \
        len(domain_name).to_bytes(1, 'big') + domain_name.encode()
    broadcast_address_option = b""
    if broadcast_address:
        broadcast_address_option = b'\x1c\x04' + \
            socket.inet_aton(broadcast_address)
    t1_option = b'\x3a\x04' + struct.pack('!I', t1_time)
    t2_option = b'\x3b\x04' + struct.pack('!I', t2_time)

    max_message_size_option = b'\x39\x02' + struct.pack('!H', max_message_size)

    #     # Add Option Overload (Option 52)
    option_overload_option = b""
    if option_overload is not None:
        option_overload_option = b'\x34\x01' + bytes([option_overload])

    # Additional Network Configuration Options
    time_offset_option = b'\x02\x04' + struct.pack('!I', time_offset)
    time_server_option = b""
    if time_servers:
        time_list = b"".join(socket.inet_aton(ip) for ip in time_servers)
        time_server_option = b'\x04' + \
            len(time_list).to_bytes(1, 'big') + time_list
    name_server_option = b""
    if name_servers:
        name_list = b"".join(socket.inet_aton(ip) for ip in name_servers)
        name_server_option = b'\x05' + \
            len(name_list).to_bytes(1, 'big') + name_list
    log_server_option = b""
    if log_servers:
        log_list = b"".join(socket.inet_aton(ip) for ip in log_servers)
        log_server_option = b'\x07' + \
            len(log_list).to_bytes(1, 'big') + log_list
    cookie_server_option = b""
    if cookie_servers:
        cookie_list = b"".join(socket.inet_aton(ip) for ip in cookie_servers)
        cookie_server_option = b'\x08' + \
            len(cookie_list).to_bytes(1, 'big') + cookie_list
    lpr_server_option = b""
    if lpr_servers:
        lpr_list = b"".join(socket.inet_aton(ip) for ip in lpr_servers)
        lpr_server_option = b'\x09' + \
            len(lpr_list).to_bytes(1, 'big') + lpr_list
    impress_server_option = b""
    if impress_servers:
        impress_list = b"".join(socket.inet_aton(ip) for ip in impress_servers)
        impress_server_option = b'\x0a' + \
            len(impress_list).to_bytes(1, 'big') + impress_list
    rlp_server_option = b""
    if rlp_servers:
        rlp_list = b"".join(socket.inet_aton(ip) for ip in rlp_servers)
        rlp_server_option = b'\x0b' + \
            len(rlp_list).to_bytes(1, 'big') + rlp_list

    # Combine all options
    additional_options = (
        lease_time_option +
        subnet_mask_option +
        router_option +
        dns_server_option +
        domain_name_option +
        broadcast_address_option +
        t1_option +
        t2_option +
        option_overload_option +
        time_offset_option +
        time_server_option +
        name_server_option +
        log_server_option +
        cookie_server_option +
        lpr_server_option +
        impress_server_option +
        rlp_server_option +
        max_message_size_option
    )

    # Merge options with defaults
    if options:
        options_data = default_options + additional_options + \
            options + b'\xff'  # End option
    else:
        options_data = default_options + additional_options + b'\xff'

    # Construct the DHCP message
    dhcp_message = struct.pack(
        "!BBBBIHHIIII16s64s128s",
        op, htype, hlen, hops, xid, secs, flags,
        int.from_bytes(socket.inet_aton(client_ip),
                       byteorder='big'),  # Client IP
        int.from_bytes(socket.inet_aton(your_ip), byteorder='big'),  # Your IP
        int.from_bytes(socket.inet_aton(server_ip),
                       byteorder='big'),  # Server IP
        int.from_bytes(socket.inet_aton(gateway_ip),
                       byteorder='big'),  # Gateway IP
        chaddr, sname, file
    ) + magic_cookie + options_data

    return dhcp_message


def parse_dhcp_message(message):
    # Unpack fixed header fields (240 bytes)
    header_format = "!BBBBIHHIIII16s64s128s4s"
    header_size = struct.calcsize(header_format)
    unpacked_data = struct.unpack(header_format, message[:header_size])

    # Map unpacked header fields to meaningful names
    dhcp_data = {
        "op": unpacked_data[0],
        "htype": unpacked_data[1],
        "hlen": unpacked_data[2],
        "hops": unpacked_data[3],
        "xid": unpacked_data[4],
        "secs": unpacked_data[5],
        "flags": unpacked_data[6],
        "ciaddr": unpacked_data[7],
        "yiaddr": unpacked_data[8],
        "siaddr": unpacked_data[9],
        "giaddr": unpacked_data[10],
        # Extract only MAC address (first 6 bytes)
        "chaddr": unpacked_data[11][:6],
        "sname": unpacked_data[12].decode(errors="ignore").strip("\x00"),
        "file": unpacked_data[13].decode(errors="ignore").strip("\x00"),
        "magic_cookie": unpacked_data[14],
    }

    # Parse options
    options = message[header_size:]
    dhcp_data["options"] = parse_dhcp_options(options)

    return dhcp_data


def parse_dhcp_options(options):
    parsed_options = {}
    i = 0

    while i < len(options):
        option_type = options[i]
        if option_type == 255:  # End option
            break
        if option_type == 0:  # Padding
            i += 1
            continue
        option_length = options[i + 1]
        option_value = options[i + 2: i + 2 + option_length]

        parsed_options[option_type] = option_value
        i += 2 + option_length

    return parsed_options

# Periodically checks for expired leases


def lease_expiry_checker():
    while True:
        current_time = time.time()
        expired_clients = []

        with lease_table_lock:
            for mac_address, (ip, lease_expiry, xid) in lease_table.items():
                if lease_expiry < current_time:
                    expired_clients.append((mac_address, xid, mac_address))

            for mac_address, xid, mac_address in expired_clients:
                ip, _, _ = lease_table.pop(mac_address)

                # Return the IP to the pool
                with ip_pool_lock:
                    ip_pool.append(ip)

                logging.info(f"Lease expired: Released IP {
                             ip} for client(MAC: {mac_address})(XID: {xid})")

                # Remove the client from discover_cache
                with discover_cache_lock:  # Ensure thread safety if discover_cache is shared across threads
                    for key in list(discover_cache.keys()):
                        logging.debug(f"Checking {mac_address} with {
                                      discover_cache[key].get('mac_address')}")
                        if discover_cache[key].get('mac_address') == mac_address:
                            del discover_cache[key]
                            logging.info(f"Removed client(MAC: {
                                         mac_address}) from discover_cache")
                            break  # Exit loop once the entry is found and removed
        time.sleep(1)  # Check every 5 seconds


# Handles incoming DHCP messages from clients
def handle_client(message, client_address, server_socket):
    # print(message)
    parsed_message = parse_dhcp_message(message)
    client_tuple = (client_address, 68) if client_address != "0.0.0.0" else (
        "255.255.255.255", 68)
    mac_address = ':'.join(
        ['%02x' % b for b in parsed_message['chaddr']])
    # client_address = client_address[0]
    msg_type = parsed_message['options'][53][0]
    xid = int(parsed_message['xid'])
    # xid, msg_type = struct.unpack("!I B", message[:5])
    if msg_type == 1:  # DHCP Discover
        logging.info(f"Received DHCP Discover from {mac_address}")

        # Extract MAC address from the message (starting from byte 5)
        # MAC is 6 bytes
        logging.info(f"Client MAC Address: {mac_address}")

        # Extract requested IP and lease duration if present
        # DHCP options start after the MAC address
        options = parsed_message['options']
        # print("OPTIONS : ", options)
        requested_ip = None
        requested_lease = lease_duration

        if not ip_pool and (mac_address not in lease_table.keys()):
            logging.warning(
                "IP pool is empty. Cannot assign IP to client.")

            # DHCP NAK (Not Acknowledged)
            # nak_message = struct.pack("!I B", xid, 6)
            # Server Identifier Option

            nak_options = b'\x36\x04' + socket.inet_aton(server_ip)

            nak_message = construct_dhcp_message(
                xid=xid,
                client_mac=mac_address,
                msg_type=6,  # DHCP NAK message type
                server_ip=server_ip,
                client_ip="0.0.0.0",  # No IP assigned to the client
                gateway_ip="192.168.1.2",
                domain_name="example.com",
                dns_servers=["208.67.222.222", "208.67.220.220"],
                broadcast_address="192.167",
                time_offset=0,  # Default time offset
                time_servers=["192.168.1.10"],  # Example Time Server
                name_servers=["192.168.1.20"],  # Example Name Server
                log_servers=["192.168.1.30"],  # Example Log Server
                cookie_servers=["192.168.1.40"],  # Example Cookie Server
                lpr_servers=["192.168.1.50"],  # Example LPR Server
                impress_servers=["192.168.1.60"],  # Example Impress Server
                rlp_servers=["192.168.1.70"]  # Example RLP Server
            )
            server_socket.sendto(nak_message, client_tuple)
            return

        # while i + 1 < len(options):
        '''
        'options': {
        53: b'\x01',
        61: b'\x01\xec\xf4\xbb\x80\x87\x8c',
        12: b'PC-2',
        60: b'MSFT 5.0',
        55: b'\x01\x03\x06\x0f\x1f!+,./wy\xf9\xfc'}
        '''
        i = 0
        for i in options.keys():
            option_value = options[i]
            if i == 50:  # Requested IP (Option 50)
                requested_ip = socket.inet_ntoa(option_value)
                logging.info(f"Requested IP: {requested_ip}")
            elif i == 51:  # Lease Duration (Option 51)
                requested_lease = struct.unpack("!I", option_value)[0]
                logging.info(f"Requested Lease Duration: {
                    requested_lease} seconds")

        if requested_ip and requested_ip not in ip_pool:
            logging.warning(
                f"Requested IP {requested_ip} is not available.")
            if mac_address not in lease_table.keys():
                pass
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
                with lease_table_lock:
                    lease_table[mac_address] = (
                        requested_ip, time.time() + 5, xid)
                logging.info(f"Offering Requested IP {requested_ip} to {client_address}(MAC: {
                    mac_address}) with lease duration {5} seconds")

                offer_message = construct_dhcp_message(
                    xid=xid,
                    client_mac=mac_address,
                    msg_type=2,  # DHCP Offer
                    server_ip=server_ip,
                    your_ip=requested_ip,
                    gateway_ip="192.168.1.2",
                    lease_time=20,
                    subnet_mask="255.255.255.0",
                    dns_servers=["208.67.222.222", "208.67.220.220"],
                    domain_name="example.com",
                    broadcast_address="192.168.1.255",
                    t1_time=0,
                    t2_time=0,
                    option_overload=1,  # Option Overload for file and sname fields
                    max_message_size=1500  # Maximum DHCP message size
                )

                # print("Hello Client Address : ", client_address)
                server_socket.sendto(offer_message, client_tuple)
            else:
                if mac_address not in lease_table.keys():
                    logging.warning(
                        f"Requested IP {requested_ip} is not available.")
                    # DHCP NAK (Not Acknowledged)
                    # Server Identifier Option
                    nak_options = b'\x36\x04' + socket.inet_aton(server_ip)
                    nak_message = construct_dhcp_message(
                        xid=xid,
                        client_mac=mac_address,
                        msg_type=6,  # DHCP NAK message type
                        server_ip=server_ip,
                        options=nak_options
                    )
                    server_socket.sendto(nak_message, client_tuple)
                else:
                    #     offer_message = construct_dhcp_message(
                    #     xid=xid,
                    #     client_mac=mac_address,
                    #     msg_type=2,  # DHCP Offer
                    #     server_ip=server_ip,
                    #     your_ip=lease_table[mac_address][0],
                    #     gateway_ip="192.168.1.2",
                    #     lease_time=20,
                    #     subnet_mask="255.255.255.0",
                    #     dns_servers=["208.67.222.222", "208.67.220.220"],
                    #     domain_name="example.com",
                    #     broadcast_address="192.168.1.255",
                    #     t1_time=0,
                    #     t2_time=0,
                    #     option_overload=1,  # Option Overload for file and sname fields
                    #     max_message_size=1500  # Maximum DHCP message size
                    # )

                    # # print("Hello Client Address : ", client_address)
                    # server_socket.sendto(offer_message, client_tuple)
                    pass
    elif msg_type == 3:  # DHCP Request
        requested_lease = lease_duration
        if 50 in parsed_message['options']:
            requested_ip = parsed_message['options'][50]
        else:
            requested_ip = client_address

        # logging.info(f"Welcome to request messages")
        mac_address = ':'.join(
            ['%02x' % b for b in parsed_message['chaddr']])  # MAC is 6 bytes
        # logging.info(f"Client MAC Address: {mac_address}")

        # Retrieve saved Discover data from cache
        with discover_cache_lock:
            discover_data = discover_cache.get(client_address)
            if discover_data:
                requested_ip = discover_data['requested_ip'] or requested_ip
                requested_lease = discover_data['requested_lease'] or requested_lease
                logging.info(f"Received DHCP Request from {client_address} for IP {
                             requested_ip} with lease duration {requested_lease} seconds")

        with lease_table_lock:

            if mac_address in lease_table and lease_table[mac_address][0] == requested_ip:

                # Renew the lease with the requested lease time
                # lease_table
                lease_table[mac_address] = (
                    requested_ip, time.time() +
                    requested_lease, lease_table[mac_address][2]
                )
                with ip_pool_lock:
                    if requested_ip in ip_pool:
                        ip_pool.remove(requested_ip)
                ack_message = construct_dhcp_message(
                    xid=xid,
                    client_mac=mac_address,
                    msg_type=5,  # DHCP ACK
                    server_ip=server_ip,
                    your_ip=requested_ip,
                    gateway_ip="192.168.1.2",
                    lease_time=requested_lease,
                    subnet_mask="255.255.255.0",
                    dns_servers=["208.67.222.222", "208.67.220.220"],
                    domain_name="example.com",
                    broadcast_address="192.168.1.255",
                    t1_time=requested_lease // 2,
                    t2_time=(requested_lease * 7) // 8,
                    option_overload=0,  # No option overload
                    max_message_size=1500  # Maximum DHCP message size
                )

                server_socket.sendto(ack_message, client_tuple)
                logging.info(f"Assigned IP {requested_ip} to(MAC: {
                             mac_address}) with lease duration {requested_lease} seconds")
            else:

                # DHCP Nak if the requested IP does not match
                nak_message = construct_dhcp_message(
                    xid=xid,
                    client_mac=mac_address,
                    msg_type=6,  # DHCP NAK
                    server_ip=server_ip,
                    # Server Identifier Option
                    # nak_message = struct.pack("!I B", xid, 6)
                    options=b'\x36\x04' + socket.inet_aton(server_ip))

                server_socket.sendto(nak_message, client_tuple)
                logging.warning(f"Rejected IP request {requested_ip} from {
                                client_tuple}(MAC: {mac_address})")

    elif msg_type == 4:  # DHCP Decline
        declined_ip = lease_table[mac_address][0]
        logging.info(f"Received DHCP Decline for IP {
                     declined_ip} from {client_address}")
        if mac_address in lease_table:
            lease_record = lease_table[mac_address]
            lease_record = list(lease_record)
            if lease_record[0] == declined_ip:
                # Update the expiry time to the current time
                lease_record[1] = time.time()
                lease_record = tuple(lease_record)
                # Update the record in the table
                lease_table[mac_address] = lease_record
                logging.info(f"Updated lease expiry for IP {
                             declined_ip} to current time")

    elif msg_type == 7:  # DHCP Release
        if mac_address in lease_table:
            lease_record = lease_table[mac_address]
            lease_record = list(lease_record)
            released_ip = lease_record[0]
            logging.info(f"Received DHCP Release for IP {
                released_ip} from {mac_address}")
            lease_record[1] = time.time()
            lease_record = tuple(lease_record)
            # Update the record in the table
            lease_table[mac_address] = lease_record
            logging.info(f"Updated lease expiry for / IP {
                         released_ip} to current time")
    else:
        print("Hello Hello")

# Starts the DHCP server


# def setup_socket(self):
#     self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#     self.socket.bind(('', 67))


def start_dhcp_server():
    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server_socket.bind((server_ip, 67))  # DHCP server listens on port 67
    logging.info(f"DHCP Server started on {server_ip}, waiting for clients...")

    # Start the lease expiry checker in a separate thread
    threading.Thread(target=lease_expiry_checker, daemon=True).start()
    while True:
        # Receive DHCP messages
        message, client_address = server_socket.recvfrom(1024)
        client_address = client_address[0]
        threading.Thread(target=handle_client, args=(
            message, client_address, server_socket)).start()


if __name__ == "__main__":
    try:
        start_dhcp_server()
    except KeyboardInterrupt:
        logging.info("\033[91mKEYBOARD INTERRUPT DHCP Server stopped\033[0m")
