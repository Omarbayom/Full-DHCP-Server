import socket
import struct
import time
import random
from client.config import SERVER_PORT, CLIENT_PORT, BUFFER_SIZE


def send_dhcp_discover(client_socket, xid, mac_address):
    msg_type = 1  # DHCP Discover
    mac_bytes = bytes.fromhex(mac_address.replace(":", ""))
    mac_bytes = mac_bytes.ljust(16, b'\x00')

    discover_message = struct.pack("!I B 16s", xid, msg_type, mac_bytes)
    discover_message += struct.pack("!B", 255)

    client_socket.sendto(discover_message, ("255.255.255.255", SERVER_PORT))
    print(f"Sent DHCP Discover from MAC {mac_address}")


def send_dhcp_request(client_socket, xid, mac_address, server_identifier, offered_ip, server_address):
    msg_type = 3  # DHCP Request
    mac_bytes = bytes.fromhex(mac_address.replace(":", ""))
    mac_bytes = mac_bytes.ljust(16, b'\x00')

    message = struct.pack("!I B 16s 4s 4s", xid, msg_type, mac_bytes,
                          socket.inet_aton(server_identifier),
                          socket.inet_aton(offered_ip))
    message += struct.pack("!B", 255)

    client_socket.sendto(message, (server_address[0], SERVER_PORT))
    print(f"Sent DHCP Request for IP {offered_ip}")


def send_dhcp_release(client_socket, xid, mac_address, server_identifier, leased_ip, server_address):
    msg_type = 7  # DHCP Release
    mac_bytes = bytes.fromhex(mac_address.replace(":", ""))
    mac_bytes = mac_bytes.ljust(16, b'\x00')

    release_message = struct.pack("!I B 16s 4s 4s", xid, msg_type, mac_bytes,
                                  socket.inet_aton(server_identifier),
                                  socket.inet_aton(leased_ip))
    release_message += struct.pack("!B", 255)

    client_socket.sendto(release_message, (server_address[0], SERVER_PORT))
    print(f"Sent DHCP Release for IP {leased_ip}")


def start_dhcp_client():
    xid = generate_transaction_id()
    mac_address = generate_unique_mac()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_socket.bind(("", random.randint(10000, 65000)))
    client_socket.settimeout(10)

    print(f"Starting DHCP client with MAC {mac_address} and XID {xid}...")

    try:
        send_dhcp_discover(client_socket, xid, mac_address)

        while True:
            try:
                message, server_address = client_socket.recvfrom(BUFFER_SIZE)
                xid_received, msg_type = struct.unpack("!I B", message[:5])

                if xid_received != xid:
                    continue

                if msg_type == 2:  # DHCP Offer
                    offered_ip = socket.inet_ntoa(message[5:9])
                    server_identifier = socket.inet_ntoa(message[9:13])
                    print(f"Received DHCP Offer: {offered_ip}")

                    send_dhcp_request(client_socket, xid, mac_address,
                                      server_identifier, offered_ip, server_address)

                elif msg_type == 5:  # DHCP ACK
                    leased_ip = socket.inet_ntoa(message[5:9])
                    print(f"Received DHCP ACK: IP {
                          leased_ip} successfully leased")
                    print("Waiting 5 seconds before releasing IP...")
                    time.sleep(5)

                    send_dhcp_release(client_socket, xid, mac_address,
                                      server_identifier, leased_ip, server_address)
                    break

                elif msg_type == 6:  # DHCP NAK
                    print("Received DHCP NAK: Request rejected")
                    break

            except socket.timeout:
                print("Timeout: No response from DHCP server")
                break

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        client_socket.close()


if __name__ == "__main__":
    try:
        start_dhcp_client()
    except KeyboardInterrupt:
        print("\nClient terminated by user")
