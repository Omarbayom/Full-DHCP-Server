import socket
import struct
import time
import random
from utils import Client
# from src.server.config import ip_pool
from config import test_cases
import subprocess


def start_dhcp_client(mac_address=None, requested_ip=None, lease_duration=None):
    """Start the DHCP client."""
    xid = Client.generate_transaction_id()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_socket.bind(("", 68))
    client_socket.settimeout(10)  # Timeout for receiving responses

    mac_address = mac_address or Client.generate_unique_mac()
    print(f"Starting DHCP client with MAC {mac_address} and XID {xid}")

    Client.send_dhcp_discover(client_socket, xid, mac_address,
                              requested_ip, lease_duration)

    try:
        while True:
            message, _ = client_socket.recvfrom(1024)
            xid_received, = struct.unpack("!I", message[4:8])

            if xid_received != xid:
                continue

            msg_type = message[242]
            if msg_type == 2:  # DHCP Offer
                offered_ip = socket.inet_ntoa(message[16:20])
                server_identifier = socket.inet_ntoa(message[20:24])
                print(f"Received DHCP Offer: IP {
                      offered_ip} from Server {server_identifier}")
                Client.send_dhcp_request(client_socket, xid, mac_address,
                                         server_identifier, offered_ip)

            elif msg_type == 5:  # DHCP Ack
                leased_ip = socket.inet_ntoa(message[16:20])
                # lease_duration = struct.unpack("!I", message[244:248])[0]
                print(f"Received DHCP Ack: IP {
                      leased_ip} assigned successfully!")
                return [leased_ip, "ACK", lease_duration]
            elif msg_type == 6:  # DHCP Nack
                print("Received DHCP Nack: IP not assigned!")
                return ["", "NACK", lease_duration]
    except socket.timeout:
        print("DHCP client timed out waiting for responses.")
        return None

    finally:
        client_socket.close()


if __name__ == "__main__":
    for i, test_case in enumerate(test_cases):
        print("\033[93mtest case", i+1, test_case, "\033[0m")
        try:
            if test_case == "Wait_For_Lease":
                time.sleep(31)
            requested_ip, lease_duration = test_cases[test_case]['inputs']
            output = start_dhcp_client(requested_ip=requested_ip,
                                       lease_duration=lease_duration)

            if test_case == "Wait_For_Lease" or test_case == "Non_Existant_IP":
                if test_cases[test_case]['expected_output'][1:] == output[1:]:
                    test_cases[test_case]['pass'] = True
                    print("\033[92mtest case passed\033[0m")
                else:
                    print("EXPECTED OUTPUT",
                          test_cases[test_case]['expected_output'])
                    print("OUTPUT", output)
            else:
                if test_cases[test_case]['expected_output'] == output:
                    test_cases[test_case]['pass'] = True
                    print("\033[92mtest case passed\033[0m")
                else:
                    print("EXPECTED OUTPUT",
                          test_cases[test_case]['expected_output'])
                    print("OUTPUT", output)
        except Exception as e:
            print(e)
            print("\033[91mtest case failed\033[0m")
