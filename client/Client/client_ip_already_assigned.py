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


def send_dhcp_discover(client_socket, xid, mac_address, requested_ip):
    msg_type = 1  # DHCP Discover
    mac_bytes = bytes.fromhex(mac_address.replace(":", ""))
    mac_bytes = mac_bytes.ljust(16, b'\x00')

    # Basic message
    discover_message = struct.pack("!I B 16s", xid, msg_type, mac_bytes)

    # Add requested IP option
    requested_ip_bytes = socket.inet_aton(requested_ip)
    discover_message += struct.pack("!BB4s", 50, 4, requested_ip_bytes)

    # End of options
    discover_message += struct.pack("!B", 255)

    client_socket.sendto(discover_message, ("255.255.255.255", SERVER_PORT))
    print(f"Sent DHCP Discover from MAC {mac_address} requesting IP {requested_ip}")


def send_dhcp_decline(client_socket, xid, mac_address, server_identifier, offered_ip, server_address):
    msg_type = 4  # DHCP Decline
    mac_bytes = bytes.fromhex(mac_address.replace(":", ""))
    mac_bytes = mac_bytes.ljust(16, b'\x00')

    message = struct.pack("!I B 16s 4s 4s", xid, msg_type, mac_bytes,
                          socket.inet_aton(server_identifier),
                          socket.inet_aton(offered_ip))
    message += struct.pack("!B", 255)

    client_socket.sendto(message, (server_address[0], SERVER_PORT))
    print(f"Sent DHCP Decline for IP {offered_ip} - IP already assigned")


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


def start_dhcp_client(requested_ip):
    xid = generate_transaction_id()
    mac_address = generate_unique_mac()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_socket.bind(("", random.randint(10000, 65000)))
    client_socket.settimeout(10)

    print(f"Starting DHCP client with MAC {mac_address} and XID {xid}")
    print(f"Requesting specific IP: {requested_ip}")

    try:
        send_dhcp_discover(client_socket, xid, mac_address, requested_ip)

        while True:
            try:
                message, server_address = client_socket.recvfrom(BUFFER_SIZE)
                xid_received, msg_type = struct.unpack("!I B", message[:5])

                if xid_received != xid:
                    continue

                if msg_type == 2:  # DHCP Offer
                    offered_ip = socket.inet_ntoa(message[5:9])
                    server_identifier = socket.inet_ntoa(message[9:13])

                    if offered_ip != requested_ip:
                        print(f"Requested IP {requested_ip} is unavailable (already assigned)")
                        print(f"Server offered alternative IP: {offered_ip}")

                        actions = input("Enter Action (R for Request new IP, D for Decline): ")
                        if actions.upper() == 'R':
                            print("Accepting alternative IP...")
                            send_dhcp_request(client_socket, xid, mac_address,
                                              server_identifier, offered_ip, server_address)
                        else:
                            print("Declining alternative IP...")
                            send_dhcp_decline(client_socket, xid, mac_address,
                                              server_identifier, offered_ip, server_address)
                            return False
                    else:
                        print("Warning: Server offered the requested IP even though it should be assigned!")
                        print("This might indicate a problem with the DHCP server's lease database.")
                        return False

                elif msg_type == 5:  # DHCP ACK
                    leased_ip = socket.inet_ntoa(message[5:9])
                    print(f"Received DHCP ACK: Successfully leased IP {leased_ip}")
                    return True

                elif msg_type == 6:  # DHCP NAK
                    print("Received DHCP NAK: Request rejected")
                    return False

            except socket.timeout:
                print("Timeout: No response from DHCP server")
                print("The requested IP might be already assigned and no other IPs are available")
                return False

    except Exception as e:
        print(f"Error occurred: {e}")
        return False
    finally:
        client_socket.close()


if __name__ == "__main__":
    requested_ip = "192.168.1.100"  # Example specific IP that should be already assigned
    try:
        start_dhcp_client(requested_ip)
    except KeyboardInterrupt:
        print("\nClient terminated by user")