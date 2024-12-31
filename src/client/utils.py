import random
import struct
import time
import socket


class Client:
    def __init__(self, requested_ip=None, lease_duration=None):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.client_socket.settimeout(10)
        self.requested_ip = requested_ip
        self.lease_duration = lease_duration

    @staticmethod
    def generate_unique_mac():
        mac = [0x00, 0x1A, 0x2B, random.randint(0x00, 0xFF),
               random.randint(0x00, 0xFF), random.randint(0x00, 0xFF)]
        return ":".join(f"{octet:02X}" for octet in mac)

    @staticmethod
    def generate_transaction_id():
        return random.randint(1, 0xFFFFFFFF)

    @staticmethod
    def create_dhcp_message(op, htype, hlen, hops, xid, flags, ciaddr, yiaddr, siaddr, giaddr, mac_bytes):
        """Create the fixed part of a DHCP message."""
        return struct.pack(
            "!BBBBIHHIIII16s64s128s4s",
            op,  # op (Message type: Boot Request or Reply)
            htype,  # htype (Hardware type: Ethernet)
            hlen,  # hlen (Hardware address length)
            hops,  # hops (Number of relay agent hops)
            xid,  # xid (Transaction ID)
            0,  # secs (Seconds elapsed)
            flags,  # flags (Broadcast flag)
            ciaddr,  # ciaddr (Client IP address)
            yiaddr,  # yiaddr (Your IP address)
            siaddr,  # siaddr (Server IP address)
            giaddr,  # giaddr (Gateway IP address)
            # chaddr (Client hardware address, padded to 16 bytes)
            mac_bytes.ljust(16, b'\x00'),
            b"",  # sname (Server host name, 64 bytes)
            b"",  # file (Boot file name, 128 bytes)
            b"\x63\x82\x53\x63"  # Magic cookie (DHCP)
        )

    @staticmethod
    def append_dhcp_options(base_message, options_dict):
        """Append DHCP options to the message."""
        options = b''
        for option, value in options_dict.items():
            if isinstance(value, bytes):
                options += struct.pack(f"BB{len(value)}s",
                                       option, len(value), value)
            elif isinstance(value, int):
                options += struct.pack("BBI", option, 4, value)
        options += struct.pack("B", 255)  # End Option
        return base_message + options.ljust(300 - len(base_message), b'\x00')

    @staticmethod
    def send_dhcp_discover(client_socket, xid, mac_address, requested_ip=None, lease_duration=None):
        """Send a DHCP Discover message."""
        mac_bytes = bytes.fromhex(mac_address.replace(":", ""))

        message = Client.create_dhcp_message(
            op=1,
            htype=1,
            hlen=6,
            hops=0,
            xid=xid,
            flags=0x8000,
            ciaddr=0,
            yiaddr=0,
            siaddr=0,
            giaddr=0,
            mac_bytes=mac_bytes
        )

        options_dict = {
            53: b"\x01",  # DHCP Discover
        }
        if requested_ip:
            options_dict[50] = socket.inet_aton(requested_ip)  # Requested IP
        if lease_duration:
            options_dict[51] = lease_duration.to_bytes(
                4, byteorder='big')  # Lease Time
        # print(f"\033[92m{lease_duration}\033[0m")
        final_message = Client.append_dhcp_options(message, options_dict)
        client_socket.sendto(final_message, ("255.255.255.255", 67))
        print(f"Sent DHCP Discover from MAC {mac_address} with requested IP { requested_ip}, Lease {lease_duration}")
        return final_message

    @staticmethod
    def send_dhcp_request(client_socket, xid, mac_address, server_identifier, offered_ip):
        """Send a DHCP Request message."""
        mac_bytes = bytes.fromhex(mac_address.replace(":", ""))

        message = Client.create_dhcp_message(
            op=1,
            htype=1,
            hlen=6,
            hops=0,
            xid=xid,
            flags=0x8000,
            ciaddr=0,
            yiaddr=0,
            siaddr=0,
            giaddr=0,
            mac_bytes=mac_bytes
        )

        options_dict = {
            53: b"\x03",  # DHCP Request
            54: socket.inet_aton(server_identifier),  # Server Identifier
            50: socket.inet_aton(offered_ip)  # Requested IP
        }

        final_message = Client.append_dhcp_options(message, options_dict)
        client_socket.sendto(final_message, ("255.255.255.255", 67))
        # print(final_message)
        print(f"Sent DHCP Request for IP { offered_ip} to Server {server_identifier}")

    @staticmethod
    def send_dhcp_release(client_socket, xid, mac_address, server_identifier, leased_ip):
        """Send a DHCP Release message."""
        mac_bytes = bytes.fromhex(mac_address.replace(":", ""))

        message = Client.create_dhcp_message(
            op=1,
            htype=1,
            hlen=6,
            hops=0,
            xid=xid,
            flags=0x8000,
            ciaddr=0,
            yiaddr=socket.inet_aton(leased_ip),
            siaddr=0,
            giaddr=0,
            mac_bytes=mac_bytes
        )

        options_dict = {
            53: b"\x07",  # DHCP Release
            54: socket.inet_aton(server_identifier),  # Server Identifier
        }

        final_message = Client.append_dhcp_options(message, options_dict)
        client_socket.sendto(final_message, ("255.255.255.255", 67))
        print(f"Sent DHCP Release for IP { leased_ip} to Server {server_identifier}")

    @staticmethod
    def send_dhcp_decline(client_socket, xid, mac_address, server_identifier, declined_ip):
        """Send a DHCP Decline message."""
        mac_bytes = bytes.fromhex(mac_address.replace(":", ""))

        message = Client.create_dhcp_message(
            op=1,
            htype=1,
            hlen=6,
            hops=0,
            xid=xid,
            flags=0x8000,
            ciaddr=0,
            yiaddr=0,
            siaddr=0,
            giaddr=0,
            mac_bytes=mac_bytes
        )

        options_dict = {
            53: b"\x04",  # DHCP Decline
            54: socket.inet_aton(server_identifier),  # Server Identifier
            50: socket.inet_aton(declined_ip)  # Declined IP Address
        }

        final_message = Client.append_dhcp_options(message, options_dict)
        client_socket.sendto(final_message, ("255.255.255.255", 67))
        print(f"Sent DHCP Decline for IP { declined_ip} to Server {server_identifier}")

    @staticmethod
    def send_dhcp_inform(client_socket, xid, mac_address, client_ip):
        """Send a DHCP Inform message."""
        mac_bytes = bytes.fromhex(mac_address.replace(":", ""))

        message = Client.create_dhcp_message(
            op=1,
            htype=1,
            hlen=6,
            hops=0,
            xid=xid,
            flags=0x0000,  # No broadcast flag
            ciaddr=socket.inet_aton(client_ip),  # Client's configured IP
            yiaddr=0,
            siaddr=0,
            giaddr=0,
            mac_bytes=mac_bytes
        )

        options_dict = {
            53: b"\x08",  # DHCP Inform
        }

        final_message = Client.append_dhcp_options(message, options_dict)
        client_socket.sendto(final_message, ("255.255.255.255", 67))
        print(f"Sent DHCP Inform from IP {client_ip} and MAC {mac_address}")
