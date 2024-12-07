import threading
import socket

HEADER = 16  # constant first msg from client size in bytes, tells us whats the size of the 	    #msg that the client wants to send
# define a port
PORT = 5050  # port that is not used most prolyl
# use ipconfig to get your local ipv4 address
SERVER = "insert your ip address here"
# another way to initialize server without needing to manually get your ip
SERVER = socket.gethostbyname(socket.gethostname())  # better option
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MSG = "!DISCONNECT"

# making socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # making socket
# AF_INET means we use ipv4
# bind socket to the address so that anything connect to that address 		  #will connect to that socket
server.bind(ADDR)


def handle_client(conn, addr):  # runs for each client in separate thread
    print("New connecion-> {addr} connected.")
    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)  # this is blocking code
        # we receive firt msg, of size HEADER that specifies length of the real msg

        if msg_length:
            # from string to int as it comes in 			#byte format, we decode it using uf-8 to string then typecast to 			#int
            msg_length = int(msg_length)
            # get the msg with the 			#specified length by client
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MSG:
                connected = False

        print(f"[{addr}] {msg}")
        conn.send("Msg receied".encode(FORMAT))


def start():  # allow server to start listening or connections and pass them to handle client
    server.listen()  # listening for new connections
    print("[LISTENING] server is listening on {SERVER}")
    while True:
        # this is a blocking code					#conn is a socket object stands for connection
        conn, addr = server.accept()
        # wait for a new connetion to the serer, when new connection occurs, store 		#ip addr and port of that connection and store an object to allow us to
        # send informaion back to that connection
        # when new 		#connection occurs, pass it to handle_client with the arguments conn and 		#addr
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()  # start the thread
        # how many 			#connections we got
        print(f"Active connections-> {threading.activeCount()-1}")


print("Server starting....")
start()
