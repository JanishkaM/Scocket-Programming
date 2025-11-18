import socket

HEADER = 64
RES = 8
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

PORT = 6050
SERVER = "192.168.8.121"

ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b" " * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)

def main():
    print("Type your messages below. Type '!DISCONNECT' to exit.")
    while True:
        msg = input("Enter message: ")
        send(msg)
        if msg == DISCONNECT_MESSAGE:
            break
        response = client.recv(8).decode(FORMAT)
        print(f"Server response: {response}")
        
main()