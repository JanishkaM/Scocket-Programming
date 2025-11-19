import socket
import threading
import json
import time

HEADER = 64
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
USER_LIST_MESSAGE = "!USERLIST:"

PORT = 5050
SERVER = "94.237.67.44"
ADDR = (SERVER, PORT)

print(f"Server IP Address: {socket.gethostbyname(socket.gethostname())}")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


clients = {}
clients_lock = threading.Lock()


def send_message_to_client(client_conn, message):
    try:
        msg_encoded = message.encode(FORMAT)
        msg_length = len(msg_encoded)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b" " * (HEADER - len(send_length))

        client_conn.send(send_length)
        client_conn.send(msg_encoded)
        return True
    except:

        return False


def get_active_users():
    with clients_lock:

        return [data["username"] for data in clients.values()]


def broadcast_user_list():
    user_list = get_active_users()

    list_msg = USER_LIST_MESSAGE + json.dumps(user_list)

    with clients_lock:
        for client_conn in clients:
            send_message_to_client(client_conn, list_msg)


def broadcast_chat_message(message, sender_conn):
    with clients_lock:
        sender_username = clients.get(sender_conn, {}).get("username", "Unknown User")

        full_message = f"[{sender_username}] {message}"

        for client_conn in clients:
            if client_conn != sender_conn:
                send_message_to_client(client_conn, full_message)


def handle_client(conn, addr):
    client_info = {"addr": addr, "username": str(addr)}
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True

    try:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)

            if msg.startswith("USERNAME:"):
                username = msg.split(":")[1].strip()
                if username:
                    client_info["username"] = username

    except:
        print(f"[ERROR] Failed to receive initial username from {addr}")
        conn.close()
        return

    with clients_lock:
        clients[conn] = client_info

    print(f"[JOIN] {client_info['username']} joined.")
    broadcast_chat_message(f"User {client_info['username']} joined the chat.", conn)
    broadcast_user_list()

    while connected:
        try:
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(FORMAT)

                if msg == DISCONNECT_MESSAGE:
                    connected = False
                else:
                    print(f"[{client_info['username']}] {msg}")
                    broadcast_chat_message(msg, conn)
        except:
            connected = False
            break

    username = client_info["username"]
    print(f"[DISCONNECT] {username} disconnected from {addr}.")
    broadcast_chat_message(f"User {username} left the chat.", conn)

    with clients_lock:
        if conn in clients:
            del clients[conn]

    broadcast_user_list()
    conn.close()


def start():
    server.listen()
    print("[LISTENING] Server is listening for connections...")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


print("[STARTING] Server is starting...")
start()
