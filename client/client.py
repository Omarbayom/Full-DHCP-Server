import socket
from config import SERVER_PORT, CLIENT_PORT, BUFFER_SIZE

SERVER_IP = "127.0.0.1"


def dhcp_client():
    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(("", CLIENT_PORT))

    try:
        # Send DHCPDISCOVER
        discover_message = b"DHCPDISCOVER"
        client_socket.sendto(discover_message, (SERVER_IP, SERVER_PORT))
        print("Sent DHCPDISCOVER")

        # Wait for DHCPOFFER
        data, server = client_socket.recvfrom(BUFFER_SIZE)
        print(f"Received from server: {data}")

        if data.startswith(b"DHCPOFFER:"):
            offered_ip = data.split(b":")[1].decode()
            print(f"Offered IP: {offered_ip}")

            # Send DHCPREQUEST
            request_message = b"DHCPREQUEST"
            client_socket.sendto(request_message, (SERVER_IP, SERVER_PORT))
            print("Sent DHCPREQUEST")

            # Wait for DHCPACK
            data, server = client_socket.recvfrom(BUFFER_SIZE)
            print(f"Received from server: {data}")

            if data.startswith(b"DHCPACK:"):
                assigned_ip = data.split(b":")[1].decode()
                print(f"Assigned IP: {assigned_ip}")
    finally:
        client_socket.close()


if __name__ == "__main__":
    dhcp_client()
