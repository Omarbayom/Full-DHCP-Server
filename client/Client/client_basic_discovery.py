import socket
import struct
import time
import random
from client_config import SERVER_PORT, CLIENT_PORT, BUFFER_SIZE


def generate_unique_mac():
    mac = [0x00, 0x1A, 0x2B, random.randint(0x00, 0xFF),
           random.randint(0x00, 0xFF), random.randint(0x00, 0xFF)]
    return ":".join(f"{octet:02X}" for octet in mac)


def generate_transaction_id():
    return random.randint(1, 0xFFFFFFFF)


def send_dhcp_discover(client_socket, xid, mac_address):
    msg_type = 1  # DHCP Discover
    mac_bytes = bytes.fromhex(mac_address.replace(":", ""))
    mac_bytes = mac_bytes.ljust(16, b'\x00')

    discover_message = struct.pack("!I B 16s", xid, msg_type, mac_bytes)
    discover_message += struct.pack("!B", 255)  # End option

    client_socket.sendto(discover_message, ("255.255.255.255", SERVER_PORT))
    print(f"Sent DHCP Discover from MAC {mac_address}")


def send_dhcp_request(client_socket, xid, mac_address, server_identifier, offered_ip, server_address):
    msg_type = 3  # DHCP Request
    mac_bytes = bytes.fromhex(mac_address.replace(":", ""))
    mac_bytes = mac_bytes.ljust(16, b'\x00')

    message = struct.pack("!I B 16s 4s 4s", xid, msg_type, mac_bytes,
                          socket.inet_aton(server_identifier),
                          socket.inet_aton(offered_ip))
    message += struct.pack("!B", 255)  # End option

    client_socket.sendto(message, (server_address[0], SERVER_PORT))
    print(f"Sent DHCP Request for IP {offered_ip} to server {server_address}")


def start_dhcp_client():
    xid = generate_transaction_id()
    mac_address = generate_unique_mac()
    port = random.randint(10000, 65000)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_socket.bind(("", port))
    client_socket.settimeout(10)

    print(f"Starting DHCP client on port {port} with MAC {mac_address} and XID {xid}")

    send_dhcp_discover(client_socket, xid, mac_address)

    try:
        while True:
            message, server_address = client_socket.recvfrom(BUFFER_SIZE)
            xid_received, msg_type = struct.unpack("!I B", message[:5])

            if xid_received != xid:
                continue

            if msg_type == 2:  # DHCP Offer
                offered_ip = socket.inet_ntoa(message[5:9])
                server_identifier = socket.inet_ntoa(message[9:13])
                print(f"Received DHCP Offer: {offered_ip} from {server_address}")
                send_dhcp_request(client_socket, xid, mac_address,
                                  server_identifier, offered_ip, server_address)

            elif msg_type == 5:  # DHCP Ack
                lease_duration = struct.unpack("!I", message[9:13])[0]
                leased_ip = socket.inet_ntoa(message[5:9])
                print(f"Received DHCP Ack: Lease successful! Duration: {lease_duration} seconds for IP {leased_ip}")
                return True

            elif msg_type == 6:  # DHCP Nak
                print("Received DHCP Nak: Request rejected.")
                return False

    except socket.timeout:
        print("Timeout: No response from DHCP server.")
        return False
    except KeyboardInterrupt:
        print("Client terminated by user.")
        return False
    finally:
        client_socket.close()


if __name__ == "__main__":
    start_dhcp_client()