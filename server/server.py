import socket
from threading import Thread
from config import SERVER_PORT, CLIENT_PORT, BUFFER_SIZE

# IP pool for the server to assign
ip_pool = ["192.168.1.2", "192.168.1.3", "192.168.1.4"]
leased_ips = {}


def handle_client(data, addr, server_socket):
    global ip_pool, leased_ips
    print(f"Received data from {addr}: {data}")

    if data.startswith(b"DHCPDISCOVER"):
        if ip_pool:
            offered_ip = ip_pool.pop(0)
            leased_ips[addr] = offered_ip
            offer_message = f"DHCPOFFER:{offered_ip}".encode()
            server_socket.sendto(offer_message, (addr[0], CLIENT_PORT))
            print(f"Offered IP {offered_ip} to {addr}")
        else:
            print("No available IPs to offer.")
    elif data.startswith(b"DHCPREQUEST"):
        client_ip = leased_ips.get(addr)
        if client_ip:
            ack_message = f"DHCPACK:{client_ip}".encode()
            server_socket.sendto(ack_message, (addr[0], CLIENT_PORT))
            print(f"Assigned IP {client_ip} to {addr}")
        else:
            print(f"No lease found for {addr}.")
    else:
        print("Unknown message type.")


def start_server():
    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("", SERVER_PORT))
    print(f"DHCP Server is running on port {SERVER_PORT}...")

    # Handle multiple clients
    while True:
        data, addr = server_socket.recvfrom(BUFFER_SIZE)
        Thread(target=handle_client, args=(data, addr, server_socket)).start()


if __name__ == "__main__":
    start_server()
