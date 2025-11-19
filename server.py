# Server.py

import socket
import threading
import json
import time

HEADER = 64
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
USER_LIST_MESSAGE = "!USERLIST:"

PORT = 5050
SERVER = '0.0.0.0' 
ADDR = (SERVER, PORT)

print(f"Server IP Address: {socket.gethostbyname(socket.gethostname())}")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

# clients dictionary maps conn object to a dict containing 'username' and 'addr'
clients = {} 
clients_lock = threading.Lock() 

def send_message_to_client(client_conn, message):
    """Encodes and sends a message to a single client connection."""
    try:
        msg_encoded = message.encode(FORMAT)
        msg_length = len(msg_encoded)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b" " * (HEADER - len(send_length))
        
        client_conn.send(send_length)
        client_conn.send(msg_encoded)
        return True
    except:
        # Failed to send, connection is likely broken
        return False

def get_active_users():
    """Returns a list of active usernames."""
    with clients_lock:
        # Use a list comprehension to get just the usernames
        return [data['username'] for data in clients.values()]

def broadcast_user_list():
    """Sends the current list of active users to ALL clients."""
    user_list = get_active_users()
    # Serialize the list into a JSON string and prefix with the special tag
    list_msg = USER_LIST_MESSAGE + json.dumps(user_list)
    
    with clients_lock:
        for client_conn in clients:
            send_message_to_client(client_conn, list_msg)

def broadcast_chat_message(message, sender_conn):
    """Broadcasts a chat message to all clients except the sender."""
    with clients_lock:
        sender_username = clients.get(sender_conn, {}).get('username', 'Unknown User')
        # Prepend sender's username to the message
        full_message = f"[{sender_username}] {message}"
        
        for client_conn in clients:
            if client_conn != sender_conn:
                send_message_to_client(client_conn, full_message)

def handle_client(conn, addr):
    client_info = {'addr': addr, 'username': str(addr)} # Default info
    print(f"[NEW CONNECTION] {addr} connected.")
    
    connected = True
    # First message loop to get the username
    try:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            
            if msg.startswith("USERNAME:"):
                username = msg.split(":")[1].strip()
                if username:
                    client_info['username'] = username
                
    except:
        print(f"[ERROR] Failed to receive initial username from {addr}")
        conn.close()
        return

    # Add client to the global list with its information
    with clients_lock:
        clients[conn] = client_info

    # Notify all clients about the new user and update their user lists
    print(f"[JOIN] {client_info['username']} joined.")
    broadcast_chat_message(f"User {client_info['username']} joined the chat.", conn)
    broadcast_user_list()

    # Main message loop
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

    # Disconnect logic
    username = client_info['username']
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