# Socket Programming Chat App

This project demonstrates a basic multi-user chat application written entirely with Python sockets. It contains:

- `server.py`: a threaded TCP server that accepts multiple clients, tracks usernames, and broadcasts messages.
- `client.py`: a Tkinter-based desktop client with a simple chat UI, active user list, and message log.

Together they illustrate how to design a simple application-layer protocol on top of TCP by explicitly framing every message with a fixed-size header.

## Features

- Username handshake that registers each client with the server.
- Live chat broadcast: every message is relayed to all connected peers (except the sender, who renders locally).
- Active user list pushed from the server using a JSON payload.
- Tkinter UI with chat history, system notifications, and Shift+Enter multi-line input support.
- Graceful shutdown path triggered when `!DISCONNECT` is sent or the window closes.

## Architecture Overview

### Client (`client.py`)
- Builds a Tkinter window with a scrolling chat view, entry box, and sidebar showing currently connected users.
- Prompts for a username, opens a TCP socket to the server, and immediately sends `USERNAME:<name>` so the server can label future messages.
- Runs a background receive thread that continuously reads framed messages. Messages starting with `!USERLIST:` are parsed as JSON, while all other payloads are rendered in the chat pane.
- Wraps outgoing messages using the same framing scheme and shows the sender's own text instantly for responsiveness.

### Server (`server.py`)
- Listens on `0.0.0.0:5050`, accepting each client in its own thread.
- Stores client metadata (address and username) in a shared dictionary guarded by a lock.
- On each message, it decides whether to broadcast a chat payload or to process the `!DISCONNECT` control message.
- Periodically sends the user list by prepending `!USERLIST:` to a JSON array so clients can keep their sidebars in sync.

## Why the `HEADER` Constant Matters

TCP is a stream, so there is no concept of "message" boundaries. Both client and server therefore preface every payload with a fixed-length header (`HEADER = 64`). The header encodes the length of the upcoming message and is padded with spaces to fill 64 bytes. The receiver always:

1. Reads exactly 64 bytes.
2. Converts the stripped value into an integer length.
3. Calls `recv(length)` to obtain the full message body.

Without this manual framing, reads could split or merge payloads unpredictably, leading to truncated JSON, interleaved chat lines, or blocked sockets waiting for bytes that never arrive. The 64-byte header ensures each logical message is reconstructed exactly as the sender intended.

> You can experiment with different header sizes, but **both client and server must agree** on the value or every read will desynchronize.

## Requirements

- Python 3.8+
- Tkinter (bundled with standard CPython installers on most platforms)
- Network connectivity between the machines running the server and clients

## Running the Project

1. **Start the server** (on a reachable host/IP):

```sh
python server.py
```

2. **Update the client target** if necessary by editing `SERVER` in `client.py` to the server's public or LAN IP.

3. **Launch each client**:

```sh
python client.py
```

4. Enter a username when prompted and begin chatting.

## Customization Tips

- Change `PORT` in both files to move the service to another TCP port.
- Customize UI fonts/colors or add sound notifications in `BasicChatUI`.
- Extend the protocol with more control messages (e.g., private chats) by reserving additional prefixes like `!WHISPER:` similar to the user list command.

## Troubleshooting

- **Cannot connect**: verify the server is running, reachable on the network, and that firewalls allow inbound TCP on the selected port.
- **User list not updating**: make sure both sides agree on `USER_LIST_MESSAGE` and that the JSON payload is well-formed.
- **Random disconnects**: check for exceptions in the server log; malformed headers or mismatched `HEADER` sizes are common culprits.
