import server_config as config
import sys
import logging
import time
import threading
import struct
import socket
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

lease_duration, server_ip, lease_table, discover_cache, log_message, discover_table = config.lease_duration, config.server_ip, config.lease_table, config.discover_cache, config.log_message, config.discover_table

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================
"""
+----------------------------------+
|   Team Members   |      ID       |
|------------------|---------------|
| Omar Ahmed       | 22P0109       |
| Seif Yasser      | 21P0102       |
| Mohammed Salah   | 21P0117       |
| Youssef Tamer    | 21P0138       |
+----------------------------------+
"""

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================
"""
# ====================================================================================================
# ================================ DHCP Server Message Types ==========================================
# ====================================================================================================

# MESSAGE TYPES:
+-----------------------------------------------------------------------------------------+
| Message Type     | Description                                                          |
|------------------|----------------------------------------------------------------------|
| DHCPDISCOVER     | Client broadcasts to locate DHCP servers.                            |
| DHCPOFFER        | Server responds with an offer of IP address and configuration.       |
| DHCPREQUEST      | Client requests specific IP address or renews lease.                 |
| DHCPACK          | Server acknowledges the lease and configuration.                     |
| DHCPNAK          | Server denies the request or lease renewal.                          |
| DHCPDECLINE      | Client informs the server that the offered IP is already in use.     |
| DHCPRELEASE      | Client releases the IP address.                                      |
| DHCPINFORM       | Client requests additional configuration parameters.                 |
+-----------------------------------------------------------------------------------------+

"""

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================
"""
# ====================================================================================================
# ================================ DHCP Packet Format ================================================
# ====================================================================================================

# DHCP Packet Format
+--------------------------------------------------------------------------------------------------------------------+
| Field          | Size (bytes)     | Description                                                                    |
|----------------|------------------|--------------------------------------------------------------------------------|
| op             | 1                | Message type: 1 for request, 2 for reply.                                      |
| htype          | 1                | Hardware type (e.g., Ethernet = 1).                                            |
| hlen           | 1                | Hardware address length (e.g., 6 for MAC).                                     |
| hops           | 1                | Hops (used by relay agents).                                                   |
| xid            | 4                | Transaction ID to match requests and replies.                                  |
| secs           | 2                | Seconds elapsed since client began the request process.                        |
| flags          | 2                | Flags: 1 for broadcast, 0 for unicast.                                         |
| ciaddr         | 4                | Client IP address (if already assigned).                                       |
| yiaddr         | 4                | 'Your' IP address assigned to the client by the server.                        |
| siaddr         | 4                | Server IP address to assist in the next step of the boot process.              |
| giaddr         | 4                | Gateway IP address (used by relay agents).                                     |
| chaddr         | 16               | Client hardware address (e.g., MAC address).                                   |
| sname          | 64               | Optional server hostname (null-terminated string).                             |
| file           | 128              | Boot file name to be used by the client.                                       |
| options        | Variable         | DHCP options (e.g., message type, subnet mask, lease time).                    |
+--------------------------------------------------------------------------------------------------------------------+
"""

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

"""
# ====================================================================================================
# ================================ DHCP Options ======================================================
# ====================================================================================================

# Option 1: Subnet Mask
# - Provides the subnet mask the client should use.

# Option 2: Time Offset
# - Specifies the time offset from UTC in seconds.

# Option 3: Router (Default Gateway)
# - Lists the IP addresses of the default gateways.

# Option 4: Time Server
# - Specifies the IP addresses of the time servers.

# Option 5: Name Server
# - Provides the IP addresses of IEN 116 name servers.

# Option 6: Domain Name Server (DNS)
# - Specifies the IP addresses of DNS servers.

# Option 7: Log Server
# - Lists the IP addresses of log servers.

# Option 8: Cookie Server
# - Specifies the IP addresses of cookie servers.

# Option 9: LPR Server
# - Lists the IP addresses of Line Printer Remote (LPR) servers.

# Option 10: Impress Server
# - Specifies the IP addresses of Impress servers.

# Option 11: Resource Location Server (RLP)
# - Provides the IP addresses of Resource Location Protocol servers.

# Option 12: Hostname
# - Specifies the hostname for the client.

# Option 15: Domain Name
# - Indicates the domain name the client should use.

# Option 28: Broadcast Address
# - Specifies the broadcast address for the client's subnet.

# Option 50: Requested IP Address
# - Allows the client to request a specific IP address.

# Option 51: IP Address Lease Time
# - Indicates the duration of the IP address lease in seconds.

# Option 52: Option Overload
# - Indicates if additional options are stored in the file or sname fields.

# Option 53: DHCP Message Type
# - Specifies the type of DHCP message (e.g., Discover, Offer, Request).

# Option 54: DHCP Server Identifier
# - Provides the IP address of the DHCP server.

# Option 55: Parameter Request List
# - Lists the options the client requests from the server.

# Option 57: Maximum DHCP Message Size
# - Specifies the maximum size of a DHCP message the client can accept.

# Option 56: Message (Error Message)
# - Contains an error message in case of a DHCP failure.

# Option 58: Renewal (T1) Time Value
# - Indicates the time interval (in seconds) before the client renews the lease.

# Option 59: Rebinding (T2) Time Value
# - Specifies the time interval (in seconds) before the client attempts rebinding.

# Option 60: Vendor Class Identifier
# - Identifies the vendor type and configuration of a DHCP client.

# Option 61: Client Identifier
# - Specifies a unique identifier for the client, often based on the MAC address.

# Option 255: End
# - Indicates the end of the options field in the DHCP message.

"""

# ====================================================================================================
# ==================================== Class Server ==================================================
# ====================================================================================================


class Server:

    # ====================================================================================================
    # ================================ Initiate Server ===================================================
    # ====================================================================================================
    def __init__(self):
        """
        Initializes the Server class by setting up locks for lease table, IP pool, and discover cache.
        Also configures logging to output to both a file and the console.

        Attributes:
            lease_table_lock (threading.Lock): Lock for synchronizing access to the lease table.
            ip_pool_lock (threading.Lock): Lock for synchronizing access to the IP pool.
            discover_cache_lock (threading.Lock): Lock for synchronizing access to the discover cache.
        """
        # self.ip_pool_file_path
        # Server.IP_GUI.keys == Server.ip_pool
        Server.lease_table_lock = threading.Lock()
        Server.ip_pool_lock = threading.Lock()
        Server.discover_cache_lock = threading.Lock()
        Server.ip_pool = []
        Server.IP_GUI = {}

        Server.ip_pool_file_path = os.path.join(
            os.getcwd(), "src/server/ip_pool.txt")
        Server.blocked_mac_addresses = []
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("output/log.log"),
                logging.StreamHandler()
            ]
        )

    # ====================================================================================================
    # ==================== Initiate connection between client and Server =================================
    # ====================================================================================================
    @staticmethod
    def setup_socket():
        """
        Sets up a UDP socket for the DHCP server.

        This function creates a UDP socket, sets socket options to allow address reuse
        and enable broadcasting, and binds the socket to the server's IP address on port 67,
        which is the standard port for DHCP servers.

        Returns:
            socket.socket: The configured UDP socket ready for use by the DHCP server.
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # DHCP server listens on port 67
        server_socket.bind((server_ip, 67))
        return server_socket

    # ====================================================================================================
    # =================================== Load Ip Pool ===================================================
    # ====================================================================================================
    @staticmethod
    def load_ip_pool(file_path):
        """
        Loads the IP pool from a text file.

        Args:
            file_path (str): The path to the text file containing the IP pool.

        Returns:
            list: A list of IP addresses.
        """
        # while not file.closed:
        #     pass
        with open(file_path, 'r') as file:
            ip_pool = [line.strip() for line in file if line.strip()]
        return ip_pool

    # ====================================================================================================
    # =================================== Append Ip Pool =================================================
    # ====================================================================================================
    @staticmethod
    def append_ip_pool(file_path, ip_pool):
        """
        Appends IP addresses to the IP pool text file if they do not already exist.

        Args:
            file_path (str): The path to the text file where the IP pool will be saved.
            ip_pool (list): A list of IP addresses to be written to the file.
        """
        existing_ips = set()
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                existing_ips = set(line.strip()
                                   for line in file if line.strip())

        with open(file_path, 'a') as file:
            for ip in ip_pool:
                if ip not in existing_ips:
                    file.write(f"{ip}\n")

    # ====================================================================================================
    # =================================== Write Ip Pool ==================================================
    # ====================================================================================================
    @staticmethod
    def write_ip_pool(file_path, ip_pool):
        """
        Writes the IP pool to a text file from the beginning, avoiding duplicates.

        Args:
            file_path (str): The path to the text file where the IP pool will be saved.
            ip_pool (list): A list of IP addresses to be written to the file.
        """
        # Check if the directory exists
        if not os.path.exists(os.path.dirname(file_path)):
            raise FileNotFoundError(f"Directory does not exist: { os.path.dirname(file_path)}")

        # Use a set to eliminate duplicates within the provided IP pool
        # unique_ips = set(ip_pool)

        # Write the unique IPs to the file
        with open(file_path, 'w') as file:
            for ip in ip_pool:
                file.write(f"{ip}\n")

    # ====================================================================================================
    # ============================ Delete from Ip Pool ===================================================
    # ====================================================================================================

    @staticmethod
    def delete_ip_from_pool(ip_address, file_path):
        """
        Deletes a specific IP address from the IP pool and updates the text file.

        Args:
            ip_address (str): The IP address to be deleted.
            file_path (str): The path to the text file containing the IP pool.
        """
        with Server.ip_pool_lock:
            if ip_address in Server.ip_pool:
                Server.ip_pool.remove(ip_address)
                Server.append_ip_pool(file_path, Server.ip_pool)
                log_message(f"Deleted IP address { ip_address} from the IP pool.", "info")
            else:
                log_message(
                    f"IP address {ip_address} not found in the IP pool.", "warning")

    # ====================================================================================================
    # =================================== Load Ip Pool ===================================================
    # ====================================================================================================
    @staticmethod
    def load_blocked_mac_addresses(file_path):
        """
        Loads the IP pool from a text file.

        Args:
            file_path (str): The path to the text file containing the IP pool.

        Returns:
            list: A list of IP addresses.
        """
        with open(file_path, 'r') as file:
            blocked_mac_addresses = [line.strip()
                                     for line in file if line.strip()]
        return blocked_mac_addresses

    # ====================================================================================================
    # ================================ Block Client's MAC Address ========================================
    # ====================================================================================================
    @staticmethod
    def dhcp_block_client(mac_address):
        Server.blocked_mac_addresses.add(mac_address)

    # ====================================================================================================
    # ================================ UnBlock Client's MAC Address ======================================
    # ====================================================================================================
    @staticmethod
    def dhcp_unblock_client(mac_address):
        if mac_address in Server.blocked_mac_addresses:
            Server.blocked_mac_addresses.remove(mac_address)
        else:
            log_message(f"Client with MAC address { mac_address} is not blocked.", "warning")

    # ====================================================================================================
    # ========================================= Send Blocked NACK ========================================
    # ====================================================================================================
    @staticmethod
    def dhcp_send_block_nack(xid, mac_address, server_socket, client_tuple):
        Server.dhcp_send_nack(
            xid, mac_address, server_socket, client_tuple)
        log_message(
            f"Client with MAC address {mac_address} is blocked.", "warning")

    # ====================================================================================================
    # ============================ Get the client's MAC Address ==========================================
    # ====================================================================================================
    @staticmethod
    def get_mac_address(parsed_message):
        return ':'.join(['%02x' % b for b in parsed_message['chaddr']])

    # ====================================================================================================
    # ==================== Constructing the client tuple for socket ======================================
    # ====================================================================================================
    @staticmethod
    def get_client_tuple(client_address):
        return (client_address, 68) if client_address != "0.0.0.0" else ("255.255.255.255", 68)

    # ====================================================================================================
    # ============================= Get the Message Type =================================================
    # ====================================================================================================
    @staticmethod
    def get_msg_type(parsed_message):
        return parsed_message['options'][53][0]

    # ====================================================================================================
    # ============================= Get the Transaction's ID =============================================
    # ====================================================================================================
    @staticmethod
    def get_xid(parsed_message):
        return int(parsed_message['xid'])

    # ====================================================================================================
    # ==================== Get the client's current IP address ===========================================
    # ====================================================================================================
    @staticmethod
    def get_client_address(client_address):
        return client_address[0]

    # ====================================================================================================
    # ==================== Constructing the DHCP Message Format ==========================================
    # ====================================================================================================
    @staticmethod
    def construct_dhcp_message(
        xid, client_mac, msg_type, server_ip, client_ip="0.0.0.0", your_ip="0.0.0.0", gateway_ip="0.0.0.0",
        options=None, lease_time=60, subnet_mask="255.255.255.0", dns_servers=None, domain_name="example.com",
        broadcast_address=None, t1_time=0, t2_time=0, option_overload=None, time_offset=0, time_servers=None, name_servers=None,
        log_servers=None, cookie_servers=None, lpr_servers=None, impress_servers=None, rlp_servers=None, max_message_size=1500,
        error_message=None
    ):
        """
        Constructs a DHCP message based on the provided parameters.
        Args:
            xid (int): Transaction ID.
            client_mac (str): Client MAC address in the format "XX:XX:XX:XX:XX:XX".
            msg_type (int): DHCP message type (e.g., 1 for DHCPDISCOVER, 2 for DHCPOFFER).
            server_ip (str): Server IP address.
            client_ip (str, optional): Client IP address. Defaults to "0.0.0.0".
            your_ip (str, optional): 'Your' IP address. Defaults to "0.0.0.0".
            gateway_ip (str, optional): Gateway IP address. Defaults to "0.0.0.0".
            options (bytes, optional): Additional DHCP options. Defaults to None.
            lease_time (int, optional): Lease time in seconds. Defaults to 60.
            subnet_mask (str, optional): Subnet mask. Defaults to "255.255.255.0".
            dns_servers (list, optional): List of DNS server IP addresses. Defaults to None.
            domain_name (str, optional): Domain name. Defaults to "example.com".
            broadcast_address (str, optional): Broadcast address. Defaults to None.
            t1_time (int, optional): Renewal (T1) time in seconds. Defaults to 0.
            t2_time (int, optional): Rebinding (T2) time in seconds. Defaults to 0.
            option_overload (int, optional): Option overload value. Defaults to None.
            time_offset (int, optional): Time offset in seconds. Defaults to 0.
            time_servers (list, optional): List of time server IP addresses. Defaults to None.
            name_servers (list, optional): List of name server IP addresses. Defaults to None.
            log_servers (list, optional): List of log server IP addresses. Defaults to None.
            cookie_servers (list, optional): List of cookie server IP addresses. Defaults to None.
            lpr_servers (list, optional): List of LPR server IP addresses. Defaults to None.
            impress_servers (list, optional): List of impress server IP addresses. Defaults to None.
            rlp_servers (list, optional): List of RLP server IP addresses. Defaults to None.
            max_message_size (int, optional): Maximum DHCP message size. Defaults to 1500.
            error_message (str, optional): Error message to include in the DHCP options. Defaults to None.
        Returns:
            bytes: The constructed DHCP message.
        """
        # Fixed-length fields
        op = 2 if msg_type in (2, 5, 6) else 1  # BOOTREPLY for OFFER, ACK, NAK
        htype = 1  # Hardware type: 1 = Ethernet
        hlen = 6  # Hardware address length: 6 bytes for MAC
        hops = 0  # Hops: 0
        secs = 0  # Seconds elapsed: 0
        flags = 0x8000  # Broadcast flag
        chaddr = bytes.fromhex(client_mac.replace(
            ":", "")) + b'\x00' * 10  # Pad to 16 bytes
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
        max_message_size_option = b'\x39\x02' + \
            struct.pack('!H', max_message_size)

        # Add Option Overload (Option 52)
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
            cookie_list = b"".join(socket.inet_aton(ip)
                                   for ip in cookie_servers)
            cookie_server_option = b'\x08' + \
                len(cookie_list).to_bytes(1, 'big') + cookie_list
        lpr_server_option = b""
        if lpr_servers:
            lpr_list = b"".join(socket.inet_aton(ip) for ip in lpr_servers)
            lpr_server_option = b'\x09' + \
                len(lpr_list).to_bytes(1, 'big') + lpr_list
        impress_server_option = b""
        if impress_servers:
            impress_list = b"".join(socket.inet_aton(ip)
                                    for ip in impress_servers)
            impress_server_option = b'\x0a' + \
                len(impress_list).to_bytes(1, 'big') + impress_list
        rlp_server_option = b""
        if rlp_servers:
            rlp_list = b"".join(socket.inet_aton(ip) for ip in rlp_servers)
            rlp_server_option = b'\x0b' + \
                len(rlp_list).to_bytes(1, 'big') + rlp_list

        # Option 56: Error Message
        error_message_option = b""
        if error_message:
            error_message_option = b'\x38' + \
                len(error_message).to_bytes(1, 'big') + error_message.encode()

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
            max_message_size_option +
            error_message_option
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
            int.from_bytes(socket.inet_aton(your_ip),
                           byteorder='big'),  # Your IP
            int.from_bytes(socket.inet_aton(server_ip),
                           byteorder='big'),  # Server IP
            int.from_bytes(socket.inet_aton(gateway_ip),
                           byteorder='big'),  # Gateway IP
            chaddr, sname, file
        ) + magic_cookie + options_data

        return dhcp_message

    # ====================================================================================================
    # ========================= Parse the Incoming DHCP Message Format ===================================
    # ====================================================================================================
    @staticmethod
    def parse_dhcp_message(message):
        """
        Parse a DHCP message and extract its components.
        Args:
            message (bytes): The raw DHCP message to be parsed.
        Returns:
            dict: A dictionary containing the parsed DHCP message fields:
                - op (int): Message op code / message type.
                - htype (int): Hardware address type.
                - hlen (int): Hardware address length.
                - hops (int): Hops.
                - xid (int): Transaction ID.
                - secs (int): Seconds elapsed since client began address acquisition or renewal process.
                - flags (int): Flags.
                - ciaddr (int): Client IP address (if already in use).
                - yiaddr (int): 'Your' (client) IP address.
                - siaddr (int): IP address of next server to use in bootstrap.
                - giaddr (int): Relay agent IP address.
                - chaddr (bytes): Client hardware address (first 6 bytes).
                - sname (str): Optional server host name.
                - file (str): Boot file name.
                - magic_cookie (bytes): Magic cookie.
                - options (dict): Parsed DHCP options.
        """
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
        dhcp_data["options"] = Server.parse_dhcp_options(options)

        return dhcp_data

    # ====================================================================================================
    # ================= Parse the Options from the Incoming DHCP Message Format ==========================
    # ====================================================================================================
    @staticmethod
    def parse_dhcp_options(options):
        """
        Parses DHCP options from a given byte sequence.
        Args:
            options (bytes): A byte sequence containing DHCP options.
        Returns:
            dict: A dictionary where the keys are option types (int) and the values are the corresponding option values (bytes).
        Notes:
            - Option type 255 indicates the end of options and stops parsing.
            - Option type 0 is padding and is skipped.
        """
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

    # ====================================================================================================
    # ========================= Checking for the lease Duration Expiration ===============================
    # ====================================================================================================
    @staticmethod
    def lease_expiry_checker():
        """
        Continuously checks for expired leases and handles their expiration.
        This function runs an infinite loop that periodically checks the lease table
        for expired leases. When a lease is found to be expired, it performs the following actions:
        1. Removes the expired lease from the lease table.
        2. Returns the associated IP address back to the IP pool.
        3. Logs the expiration event.
        4. Removes the client from the discover cache if present.
        The function ensures thread safety by using locks when accessing shared resources
        such as the lease table, IP pool, and discover cache.
        Note:
            This function is intended to be run in a separate thread.
        Sleep Duration:
            The function sleeps for 1 second between each check to avoid excessive CPU usage.
        """
        while True:
            current_time = time.time()
            expired_clients = []

            with Server.lease_table_lock:
                for ip in Server.IP_GUI:
                    if isinstance(Server.IP_GUI[ip], list) and len(Server.IP_GUI[ip]) > 1:
                        if Server.IP_GUI[ip][1] > 0:
                            Server.IP_GUI[ip][1] -= 1
                    else:
                        print(f"Skipping {ip}, unexpected value: {Server.IP_GUI[ip]}")


                for key in list(discover_table.keys()):
                    mac_ip_pairs = [(mac, value[0])
                                    for mac, value in lease_table.items()]
                    if (key, discover_table[key][0]) not in mac_ip_pairs:
                        discover_table.pop(key)

                for mac_address, (ip, lease_expiry, xid) in lease_table.items():
                    if lease_expiry < current_time:
                        expired_clients.append((mac_address, xid, mac_address))

                for mac_address, xid, mac_address in expired_clients:
                    ip, _, _ = lease_table.pop(mac_address)
                    discover_table.pop(mac_address)
                    Server.IP_GUI[ip] = ["Not Assigned",0]

                    # Return the IP to the pool
                    with Server.ip_pool_lock:
                        Server.ip_pool.append(ip)
                        Server.write_ip_pool(
                            Server.ip_pool_file_path, list(Server.ip_pool))

                    log_message(f"Lease expired: Released IP { ip} for client(MAC: {mac_address})(XID: {xid})", "info")

                    # Remove the client from discover_cache
                    with Server.discover_cache_lock:  # Ensure thread safety if discover_cache is shared across threads
                        for key in list(discover_cache.keys()):
                            log_message(f"Checking {mac_address} with { discover_cache[key].get('mac_address')}", "debug")
                            if key == mac_address:
                                del discover_cache[key]
                                log_message(f"Removed client(MAC: { mac_address}) from discover_cache", "info")
                                break  # Exit loop once the entry is found and removed
            time.sleep(1)  # Check every 5 seconds

    # ====================================================================================================
    # =============================== Sending ACK Message ================================================
    # ====================================================================================================
    @staticmethod
    def dhcp_send_ack(xid, mac_address, server_socket, client_tuple, requested_ip, requested_lease):
        ack_message = Server.construct_dhcp_message(
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
        with Server.ip_pool_lock:
            Server.write_ip_pool(Server.ip_pool_file_path,
                                 list(Server.ip_pool))

    # ====================================================================================================
    # =============================== Sending NACK Message ===============================================
    # ====================================================================================================
    @staticmethod
    def dhcp_send_nack(xid, mac_address, server_socket, client_tuple):
        nak_message = Server.construct_dhcp_message(
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
            rlp_servers=["192.168.1.70"],  # Example RLP Server
            error_message="Requested IP is not available."
        )
        server_socket.sendto(nak_message, client_tuple)
        # print()

    # ====================================================================================================
    # =============================== Sending OFFER Message ==============================================
    # ====================================================================================================
    @staticmethod
    def dhcp_send_offer(requested_ip, requested_lease, xid, client_address, mac_address, server_socket, client_tuple):
        with Server.ip_pool_lock:
            if requested_ip and requested_ip in Server.ip_pool:
                with Server.lease_table_lock:
                    discover_table[mac_address] = (
                        requested_ip, requested_lease, xid)
                log_message(f"Offering Requested IP {requested_ip} to {client_address}(MAC: { mac_address}) with lease duration {requested_lease} seconds", "info")

                offer_message = Server.construct_dhcp_message(
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

                server_socket.sendto(offer_message, client_tuple)
            else:
                if mac_address not in lease_table.keys():
                    log_message(
                        f"Requested IP {requested_ip} is not available.", "warning")
                    # DHCP NAK (Not Acknowledged)
                    # Server Identifier Option
                    nak_options = b'\x36\x04' + socket.inet_aton(server_ip)
                    nak_message = Server.construct_dhcp_message(
                        xid=xid,
                        client_mac=mac_address,
                        msg_type=6,  # DHCP NAK message type
                        server_ip=server_ip,
                        options=nak_options
                    )
                    server_socket.sendto(nak_message, client_tuple)

    # ====================================================================================================
    # ======================== Handling DISCOVER Message Type (1) ========================================
    # ====================================================================================================
    @staticmethod
    def handle_dhcp_discover(parsed_message, client_address, mac_address, xid, server_socket, client_tuple):

        options = parsed_message['options']
        requested_ip = None
        requested_lease = lease_duration

        if mac_address in Server.blocked_mac_addresses:
            Server.dhcp_send_block_nack(
                xid, mac_address, server_socket, client_tuple)
            return

        if not Server.ip_pool and (mac_address not in discover_table.keys()):
            log_message(
                "IP pool is empty. Cannot assign IP to client.", "warning")
            Server.dhcp_send_nack(
                xid, mac_address, server_socket, client_tuple)
            return

        i = 0
        for i in options.keys():
            option_value = options[i]
            if i == 50:  # Requested IP (Option 50)
                requested_ip = socket.inet_ntoa(option_value)
                log_message(f"Requested IP: {requested_ip}", "info")
            elif i == 51:  # Lease Duration (Option 51)
                requested_lease = int.from_bytes(
                    option_value, byteorder='big')
                log_message(f"Requested Lease Duration: { requested_lease} seconds", "info")

        if requested_ip and requested_ip not in Server.ip_pool:
            log_message(
                f"Requested IP {requested_ip} is not available.", "warning")
            requested_ip = Server.ip_pool[0]

        if not requested_ip:
            requested_ip = Server.ip_pool[0]
        # Save the Discover message options for later use in Request
        with Server.discover_cache_lock:
            discover_cache[mac_address] = {
                'requested_ip': requested_ip,
                'requested_lease': lease_duration if requested_lease == 0 else requested_lease
            }

        # Send DHCP Offer
        Server.dhcp_send_offer(requested_ip, requested_lease, xid,
                               client_address, mac_address, server_socket, client_tuple)

    # ====================================================================================================
    # ======================== Handling REQUEST Message Type (3) =========================================
    # ====================================================================================================
    @staticmethod
    def handle_dhcp_request(parsed_message, client_address, mac_address, xid, server_socket, client_tuple):
        requested_lease = lease_duration

        if mac_address in Server.blocked_mac_addresses:
            Server.dhcp_send_block_nack(
                xid, mac_address, server_socket, client_tuple)
            return

        if 50 in parsed_message['options']:
            requested_ip = parsed_message['options'][50]
        else:
            requested_ip = client_address
        # print("requested_ip", requested_ip)
        mac_address = Server.get_mac_address(parsed_message)  # MAC is 6 bytes

        # Retrieve saved Discover data from cache
        with Server.discover_cache_lock:
            discover_data = discover_cache.get(mac_address)
            if discover_data:
                requested_ip = discover_data['requested_ip'] or requested_ip
                requested_lease = discover_data['requested_lease'] or requested_lease
                log_message(f"Received DHCP Request from {client_address} for IP { requested_ip} with lease duration {requested_lease} seconds", "info")

        with Server.lease_table_lock:
            if mac_address in discover_table and discover_table[mac_address][0] == requested_ip:
                lease_table[mac_address] = (
                    requested_ip, time.time() +
                    requested_lease, discover_table[mac_address][2]
                )
                Server.IP_GUI[requested_ip] = [mac_address,requested_lease]
                with Server.ip_pool_lock:
                    if requested_ip in Server.ip_pool:
                        Server.ip_pool.remove(requested_ip)

                Server.dhcp_send_ack(
                    xid, mac_address, server_socket, client_tuple, requested_ip, requested_lease)
                log_message(f"Assigned IP {requested_ip} to(MAC: { mac_address}) with lease duration {requested_lease} seconds", "info")
            else:
                Server.dhcp_send_nack(
                    xid, mac_address, server_socket, client_tuple)

                log_message(f"Rejected IP request {requested_ip} from { client_tuple}(MAC: {mac_address})", "warning")

    # ====================================================================================================
    # ======================== Handling DECLINE Message Type (4) =========================================
    # ====================================================================================================
    @staticmethod
    def handle_dhcp_decline(mac_address, declined_ip):
        if mac_address in discover_table:
            discover_table.pop(mac_address)
        else:
            log_message(f"Client with MAC address { mac_address} didn't send a discover message", "warning")

    # ====================================================================================================
    # ======================== Handling RELEASE Message Type (7) =========================================
    # ====================================================================================================
    @staticmethod
    def handle_dhcp_release(mac_address):
        if mac_address in lease_table:
            lease_record = lease_table[mac_address]
            lease_record = list(lease_record)
            released_ip = lease_record[0]
            log_message(f"Received DHCP Release for IP { released_ip} from {mac_address}", "info")
            lease_record[1] = time.time()
            lease_record = tuple(lease_record)
            # Update the record in the table
            lease_table[mac_address] = lease_record
            log_message(f"Updated lease expiry for / IP { released_ip} to current time", "info")

    # ====================================================================================================
    # ======================== Handling INFORM Message Type (8) ==========================================
    # ====================================================================================================
    @staticmethod
    def handle_dhcp_inform(parsed_message, client_address, mac_address, xid, server_socket, client_tuple):
        """
        Handles DHCP INFORM messages from clients.
        Args:
            parsed_message (dict): The parsed DHCP message.
            client_address (str): The IP address of the client.
            mac_address (str): The MAC address of the client.
            xid (int): The transaction ID.
            server_socket (socket.socket): The server's socket used to send responses.
            client_tuple (tuple): The address of the client in the form (IP, port).
        """
        log_message(f"Received DHCP INFORM from {mac_address}", "info")

        # Construct DHCP ACK message with additional configuration parameters
        ack_message = Server.construct_dhcp_message(
            xid=xid,
            client_mac=mac_address,
            msg_type=5,  # DHCP ACK
            server_ip=server_ip,
            client_ip=client_address,
            your_ip=client_address,
            gateway_ip="192.168.1.2",
            lease_time=0,  # No lease time for INFORM
            subnet_mask="255.255.255.0",
            dns_servers=["208.67.222.222", "208.67.220.220"],
            domain_name="example.com",
            broadcast_address="192.168.1.255",
            t1_time=0,
            t2_time=0,
            option_overload=0,  # No option overload
            max_message_size=1500  # Maximum DHCP message size
        )

        server_socket.sendto(ack_message, client_tuple)

    # ====================================================================================================
    # ========================= Handling the incoming client =============================================
    # ====================================================================================================
    @staticmethod
    # Handles incoming DHCP messages from clients
    def handle_client(message, client_address, server_socket, ip_pool_file_path, blocked_mac_addresses_file_path):
        """
        Handles incoming DHCP messages from clients and responds accordingly.
        Parameters:
        message (bytes): The DHCP message received from the client.
        client_address (tuple): The address of the client in the form (IP, port).
        server_socket (socket.socket): The server's socket used to send responses.
        The function processes different types of DHCP messages:
        - DHCP Discover: Logs the discovery, checks IP pool, and sends a DHCP Offer or NAK.
        - DHCP Request: Logs the request, checks lease table, and sends a DHCP ACK or NAK.
        - DHCP Decline: Logs the decline and updates the lease expiry time.
        - DHCP Release: Logs the release and updates the lease expiry time.
        - Other message types: Logs a warning for invalid message types.
        The function uses several locks to ensure thread-safe access to shared resources like
        the IP pool, lease table, and discover cache.
        """
        with Server.ip_pool_lock:
            Server.ip_pool = Server.load_ip_pool(ip_pool_file_path)
        Server.blocked_mac_addresses = Server.load_blocked_mac_addresses(
            blocked_mac_addresses_file_path)
        # print(Server.ip_pool)
        parsed_message = Server.parse_dhcp_message(message)
        client_tuple = Server.get_client_tuple(client_address)
        mac_address = Server.get_mac_address(parsed_message)
        msg_type = Server.get_msg_type(parsed_message)
        xid = Server.get_xid(parsed_message)
        match msg_type:
            case 1:  # DHCP Discover
                log_message(f"Received DHCP Discover from { mac_address}", "info")
                log_message(f"Client MAC Address: {mac_address}", "info")
                # print("in the discover branch", Server.ip_pool)
                Server.handle_dhcp_discover(
                    parsed_message, client_address, mac_address, xid, server_socket, client_tuple)

            case 3:  # DHCP Request
                Server.handle_dhcp_request(
                    parsed_message, client_address, mac_address, xid, server_socket, client_tuple)
                # print("in the request branch", Server.ip_pool)

                # print("ip pool after request", Server.ip_pool)
            case 4:  # DHCP Decline
                declined_ip = discover_table[mac_address][0]
                log_message(f"Received DHCP Decline for IP { declined_ip} from {mac_address}", "info")
                Server.handle_dhcp_decline(mac_address, declined_ip)
                # print("in the decline branch", Server.ip_pool)
            case 7:  # DHCP Release
                Server.handle_dhcp_release(mac_address)
                # print("in the release branch", Server.ip_pool)
            case 8:
                Server.handle_dhcp_inform()
                # print("in the inform branch", Server.ip_pool)
            case _:
                log_message(f"invalid message type from { client_tuple} (MAC: {mac_address}", "warning")

        # print("ip pool before write", Server.ip_pool)
        with Server.ip_pool_lock:
            Server.write_ip_pool(ip_pool_file_path, list(Server.ip_pool))
        # print("ip pool after write", Server.ip_pool)

    # ====================================================================================================
    # ============================== Starting the DHCP Agent =============================================
    # ====================================================================================================
    def start_dhcp_server(self, ip_pool_file_path, blocked_mac_addresses_file_path):
        """
        Starts the DHCP server.
        This method sets up a UDP socket for the DHCP server, logs the server start,
        and waits for client messages. It also starts a separate thread to check for
        lease expiries and handles incoming DHCP messages in separate threads.
        The server listens for DHCP messages on the configured IP address and port,
        and processes each message in a new thread to handle multiple clients concurrently.
        Note:
            This method runs indefinitely, handling incoming DHCP messages and checking
            for lease expiries.
        Raises:
            Exception: If there is an error setting up the socket or handling client messages.
        """
        Server.ip_pool_file_path = ip_pool_file_path
        Server.ip_pool = Server.load_ip_pool(ip_pool_file_path)
        Server.IP_GUI = {ip: ["Not Assigned", 0] for ip in Server.ip_pool}

        server_socket = Server.setup_socket()
        log_message(f"DHCP Server started on { server_ip}, waiting for clients...", "info")

        # Start the lease expiry checker in a separate thread
        threading.Thread(target=Server.lease_expiry_checker,
                         daemon=True).start()
        while True:

            message, client_address = server_socket.recvfrom(1024)
            client_address = Server.get_client_address(client_address)
            # print("seif")
            threading.Thread(target=Server.handle_client, args=(
                message, client_address, server_socket, ip_pool_file_path, blocked_mac_addresses_file_path)).start()
            # try:
            # Server.handle_client(
            #     message, client_address, server_socket, ip_pool_file_path, blocked_mac_addresses_file_path)
            # except KeyboardInterrupt:
            #     log_message(
            #         "\033[91mKEYBOARD INTERRUPT DHCP Server stopped\033[0m", "info")

    @staticmethod
    def main():
        ip_pool_file_path = os.path.join(os.getcwd(), "src/server/ip_pool.txt")
        # ip_pool = [
        #     # "192.168.1.100",
        #     # "192.168.1.101",
        #     # "192.168.1.102",
        #     # "192.168.1.103",
        #     # "192.168.1.104",
        # ]
        server = Server()
        # Server.write_ip_pool(ip_pool_file_path, ip_pool)
        blocked_mac_addresses_file_path = os.path.join(
            os.getcwd(), "src/server/blocked_mac.txt")
        # Seif: a0:b3:cc:49:fc:d7
        try:
            server.start_dhcp_server(ip_pool_file_path=ip_pool_file_path,
                                     blocked_mac_addresses_file_path=blocked_mac_addresses_file_path)
        except KeyboardInterrupt:
            log_message(
                "\033[91mKEYBOARD INTERRUPT DHCP Server stopped\033[0m", "info")


# ====================================================================================================
# ========================================= MAIN =====================================================
# ====================================================================================================
if __name__ == "__main__":
    ip_pool_file_path = os.path.join(os.getcwd(), "src/server/ip_pool.txt")
    # ip_pool = [
    # "192.168.1.100",
    # "192.168.1.101",
    # "192.168.1.102",
    # "192.168.1.103",
    # "192.168.1.104",
    # ]
    server = Server()
    # Server.write_ip_pool(ip_pool_file_path, ip_pool)
    blocked_mac_addresses_file_path = os.path.join(
        os.getcwd(), "src/server/blocked_mac.txt")
    # Seif: a0:b3:cc:49:fc:d7
    try:
        server.start_dhcp_server(ip_pool_file_path=ip_pool_file_path,
                                 blocked_mac_addresses_file_path=blocked_mac_addresses_file_path)
    except KeyboardInterrupt:
        log_message(
            "\033[91mKEYBOARD INTERRUPT DHCP Server stopped\033[0m", "info")
