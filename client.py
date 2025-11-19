import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
from datetime import datetime
import json

HEADER = 64
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
USER_LIST_MESSAGE = "!USERLIST:"

PORT = 5050
SERVER = "20.205.17.205"

class BasicChatUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Basic Chat Client")
        self.root.geometry("900x650")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.client = None
        self.connected = False
        self.username = ""

        self.setup_username()

        main_container = tk.Frame(root)
        main_container.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(main_container, pady=5, relief=tk.RAISED, borderwidth=1)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="Chat Room",
            font=("Arial", 10, "bold"),
        ).pack(side=tk.LEFT, padx=10)

        self.user_label = tk.Label(
            header,
            text=f"User: {self.username}",
            font=("Arial", 10),
        )
        self.user_label.pack(side=tk.RIGHT, padx=10)

        content_frame = tk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        sidebar = tk.Frame(content_frame, width=150, relief=tk.GROOVE, borderwidth=1)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Active Users", font=("Arial", 10, "bold"), pady=5).pack(
            fill=tk.X
        )

        self.users_listbox = tk.Listbox(
            sidebar,
            font=("Arial", 10),
            selectmode=tk.SINGLE,
            height=1,
            exportselection=0,
        )
        self.users_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        chat_container = tk.Frame(content_frame)
        chat_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(
            chat_container,
            wrap=tk.WORD,
            font=("Arial", 10),
            state="disabled",
            borderwidth=1,
            relief=tk.SUNKEN,
            padx=5,
            pady=5,
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        self.chat_display.tag_config(
            "system", foreground="gray", font=("Arial", 9, "italic")
        )
        self.chat_display.tag_config("timestamp", foreground="gray", font=("Arial", 8))
        self.chat_display.tag_config("sender", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("message", foreground="black")

        input_container = tk.Frame(chat_container, pady=5)
        input_container.pack(fill=tk.X)

        self.message_entry = tk.Text(
            input_container,
            height=3,
            font=("Arial", 10),
            borderwidth=1,
            relief=tk.SUNKEN,
            padx=5,
            pady=5,
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry.bind("<Return>", self.send_message_enter)
        self.message_entry.bind("<Shift-Return>", lambda e: None)

        tk.Button(
            input_container,
            text="Send",
            command=self.send_message,
            font=("Arial", 10, "bold"),
            height=3,
            padx=10,
        ).pack(side=tk.RIGHT)

        self.status_label = tk.Label(
            root,
            text="Not Connected",
            anchor=tk.W,
            relief=tk.SUNKEN,
            font=("Arial", 9),
            padx=5,
        )
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

        self.connect_to_server()

    def setup_username(self):
        """Get username from user"""
        while True:
            username = simpledialog.askstring(
                "Username", "Enter your username:", parent=self.root
            )
            if username and username.strip():
                self.username = username.strip()
                break
            elif username is None:
                self.root.quit()
                return
            else:
                messagebox.showwarning("Invalid Username", "Username cannot be empty")

    def connect_to_server(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((SERVER, PORT))
            self.connected = True
            self.update_status("Connected to server", "black")
            self.display_system_message("Connected to chat server")

            self.send_raw_message(f"USERNAME:{self.username}")

            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()

        except Exception as e:
            self.update_status("Connection failed", "red")
            messagebox.showerror(
                "Connection Error",
                f"Could not connect to server at {SERVER}:{PORT}\n{e}",
            )
            self.root.quit()

    def receive_messages(self):
        """Thread to continuously receive messages"""
        while self.connected:
            try:
                msg_length = self.client.recv(HEADER).decode(FORMAT)
                if msg_length:
                    msg_length = int(msg_length)
                    msg = self.client.recv(msg_length).decode(FORMAT)

                    if msg.startswith(USER_LIST_MESSAGE):
                        self.update_user_list(msg)
                    else:
                        self.display_received_message(msg)

            except:
                if self.connected:
                    self.display_system_message("Connection to server lost")
                    self.update_status("Disconnected", "red")
                    self.connected = False
                break

    def send_raw_message(self, msg):
        """Send raw message to server"""
        if not self.connected:
            return
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b" " * (HEADER - len(send_length))
        self.client.send(send_length)
        self.client.send(message)

    def send_message(self):
        msg = self.message_entry.get("1.0", tk.END).strip()
        self.message_entry.delete("1.0", tk.END)
        if not msg:
            return

        if not self.connected:
            messagebox.showwarning(
                "Not Connected", "You are not connected to the server"
            )
            return

        try:
            self.send_raw_message(msg)

            self.display_own_message(msg)

            if msg == DISCONNECT_MESSAGE:
                self.disconnect()

        except Exception as e:
            self.display_system_message(f"Failed to send message: {e}")
            self.disconnect()

    def send_message_enter(self, event):
        """Handle Enter key press"""
        if not (event.state & 0x1):
            self.send_message()
            return "break"

    def display_own_message(self, message):
        """Display user's own message for immediate feedback"""
        timestamp = datetime.now().strftime("[%H:%M]")

        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, f"{timestamp} ", "timestamp")
        self.chat_display.insert(
            tk.END, f"{self.username} (You): ", ("sender", "self_sender")
        )
        self.chat_display.insert(tk.END, f"{message}\n", "message")
        self.chat_display.see(tk.END)
        self.chat_display.config(state="disabled")

    def display_received_message(self, full_message):
        """Display received message from other users or server"""
        timestamp = datetime.now().strftime("[%H:%M]")

        sender_tag = "sender"
        message_tag = "message"
        sender_part = "Server"
        message_part = full_message

        if full_message.startswith("[") and "]" in full_message:
            parts = full_message.split("]", 1)
            sender_part = parts[0].replace("[", "").strip()
            message_part = parts[1].strip()

            if sender_part == "Server":
                sender_tag = "system"
                message_tag = "system"

        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, f"{timestamp} ", "timestamp")

        if sender_tag != "system":
            self.chat_display.insert(tk.END, f"{sender_part}: ", sender_tag)

        self.chat_display.insert(tk.END, f"{message_part}\n", message_tag)
        self.chat_display.see(tk.END)
        self.chat_display.config(state="disabled")

    def display_system_message(self, message):
        """Display system message"""
        timestamp = datetime.now().strftime("[%H:%M]")

        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, f"{timestamp} ", "timestamp")
        self.chat_display.insert(tk.END, f"[SYSTEM] {message}\n", "system")
        self.chat_display.see(tk.END)
        self.chat_display.config(state="disabled")

    def update_user_list(self, full_message):
        """Update the online users list from the server's special message"""
        try:
            user_list_json = full_message.replace(USER_LIST_MESSAGE, "", 1)
            user_list = json.loads(user_list_json)

            self.users_listbox.delete(0, tk.END)
            for user in user_list:
                display_name = f"{user} (you)" if user == self.username else user
                self.users_listbox.insert(tk.END, display_name)

            self.display_system_message(f"Active users updated: {len(user_list)}")

        except json.JSONDecodeError:
            self.display_system_message("Error parsing user list from server.")
        except Exception as e:
            self.display_system_message(f"Failed to update user list: {e}")

    def update_status(self, status, color):
        """Update status bar"""
        self.status_label.config(text=status, foreground=color)

    def disconnect(self):
        """Disconnect from server"""
        if self.connected:
            try:
                self.send_raw_message(DISCONNECT_MESSAGE)
            except:
                pass

            self.connected = False
            self.client.close()
            self.update_status("Disconnected from server", "red")
            self.display_system_message(
                "Disconnected from server. Close window to exit."
            )

    def on_closing(self):
        """Handle window close"""
        self.disconnect()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = BasicChatUI(root)
    root.mainloop()
