import socket
import threading

HEADER = 64
FORMAT = "utf-8"

DISCONNECT_MESSAGE = "!DISCONNECT"
ALL_USERS = "!ALLUSERS"

PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

print(f"Server IP Address: {SERVER}")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            
            if msg == DISCONNECT_MESSAGE:
                connected = False
                
            if msg == ALL_USERS:
                conn.send("User1, User2, User3".encode(FORMAT))
                continue

            print(f"[{addr}] {msg}")
            conn.send("Received".encode(FORMAT))
    conn.close()

def start():
    server.listen()
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

print("[STARTING] server is starting...")
start()