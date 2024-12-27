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
    discover_message += struct.pack("!B", 255)  # End of options

    client_socket.sendto(discover_message, ("255.255.255.255", SERVER_PORT))
    print(f"Sent DHCP Discover from MAC {mac_address}")


def start_dhcp_client():
    max_retries = 3
    retry_count = 0
    retry_delay = 5  # seconds between retries

    while retry_count < max_retries:
        xid = generate_transaction_id()
        mac_address = generate_unique_mac()

        # Create new socket for each attempt
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.bind(("", random.randint(10000, 65000)))
        client_socket.settimeout(5)

        print(f"\nAttempt {retry_count + 1} of {max_retries}")
        print(f"Starting DHCP client with MAC {mac_address} and XID {xid}...")

        try:
            send_dhcp_discover(client_socket, xid, mac_address)

            # Wait for any response
            while True:
                try:
                    message, _ = client_socket.recvfrom(BUFFER_SIZE)
                    xid_received, msg_type = struct.unpack("!I B", message[:5])

                    if xid_received != xid:
                        continue

                    if msg_type == 2:  # DHCP Offer
                        print("Received DHCP Offer - unexpected response when no IPs should be available")
                        return

                except socket.timeout:
                    print("No response from server - no IPs available in pool")
                    break  # Break inner while loop on timeout

            retry_count += 1
            if retry_count < max_retries:
                print(f"Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)

        except Exception as e:
            print(f"Error occurred: {e}")
            retry_count += 1
        finally:
            client_socket.close()

    print("\nMax retries reached. No IP addresses available in pool.")
    print("Please contact network administrator to resolve IP pool exhaustion.")


if __name__ == "__main__":
    try:
        start_dhcp_client()
    except KeyboardInterrupt:
        print("\nClient terminated by user")