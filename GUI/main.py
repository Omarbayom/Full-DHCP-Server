from tkinter import Tk, Label, Button, Frame, Toplevel, Text
from tkinter import ttk, messagebox
from tkinter.simpledialog import askstring
from PIL import Image, ImageTk
import threading
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LogFileHandler(FileSystemEventHandler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith("server_logs.txt"):
            self.callback()

class DHCPServerGUI:
    def __init__(self, root):
        self.ip_list = []  # Stores the IP addresses in the table
        self.root = root
        self.root.title("DHCP Server GUI")
        self.root.geometry("600x600")  # Set the window size to 600x600 for Phase 2 size

        self.server_started = False  # Flag to track if the server is running
        self.observer = None  # File system observer

        # Initial Frame (Phase 1)
        self.main_frame = Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # Create a frame to center both the image and the button vertically and horizontally
        center_frame = Frame(self.main_frame)
        center_frame.pack(expand=True)

        # Server Image using PIL to load jpg
        try:
            self.server_image = Image.open("D:\\Semester 7\\Networks\\server_img.jpg")
            self.server_image = self.server_image.resize((215, 215))  # Resize for better fitting
            self.server_image = ImageTk.PhotoImage(self.server_image)
            self.image_label = Label(center_frame, image=self.server_image)
            self.image_label.pack(pady=10)
        except Exception as e:
            print(f"Error loading image: {e}")

        # Modify Server Button (Phase 1)
        self.modify_button = Button(
            center_frame, text="Modify Server", font=("Helvetica", 18, "bold"), bg="#4CAF50", fg="white",
            padx=20, pady=10, command=self.show_modify_window
        )
        self.modify_button.pack(pady=10)

        # Frame for Modify Server (Phase 2 - Initially Hidden)
        self.modify_frame = Frame(self.root)
        self.table = None
        self.add_button = None
        self.delete_button = None
        self.back_button = None
        self.start_button = None

    def show_modify_window(self):
        self.main_frame.pack_forget()
        self.modify_frame.pack(fill="both", expand=True)

        # Create table only if it doesn't exist
        if self.table is None:
            self.table = ttk.Treeview(self.modify_frame, columns=("#", "IP Address"), show="headings")
            self.table.heading("#", text="#")
            self.table.heading("IP Address", text="IP Address")
            self.table.column("#", width=40, anchor="center")
            self.table.column("IP Address", width=150, anchor="w")
            default_ips = ["192.168.1.001", "192.168.1.002", "192.168.1.003"]
            for idx, ip in enumerate(default_ips, start=1):
                self.table.insert("", "end", values=(idx, ip))
                self.ip_list.append(ip)
            self.table.pack(fill="both", expand=True, padx=10, pady=10)

        # Create Add/Delete/Back buttons
        if self.add_button is None:
            button_frame = Frame(self.modify_frame)
            button_frame.pack(pady=10)

            self.add_button = Button(button_frame, text="+", font=("Helvetica", 14), command=self.add_ip, width=4)
            self.add_button.pack(side="left", padx=5)

            self.delete_button = Button(button_frame, text="-", font=("Helvetica", 14), command=self.delete_ip, width=4)
            self.delete_button.pack(side="left", padx=5)

            self.back_button = Button(button_frame, text="Back", font=("Helvetica", 15), command=self.show_main_window, width=5)
            self.back_button.pack(side="left", padx=5)

            # Add the Start Server Button
            self.start_button = Button(
                self.modify_frame, text="Start Server", font=("Helvetica", 14, "bold"), bg="#008CBA", fg="white",
                padx=20, pady=10, command=self.start_server, width=20
            )
            self.start_button.pack(pady=10)

    def update_log_display(self):
        """Update the log display when file changes are detected"""
        try:
            if hasattr(self, 'log_text') and os.path.exists("server_logs.txt"):
                with open("server_logs.txt", "r") as log_file:
                    content = log_file.read()
                    self.log_text.config(state="normal")
                    self.log_text.delete(1.0, "end")
                    self.log_text.insert("end", content)
                    self.log_text.see("end")
                    self.log_text.config(state="disabled")
        except Exception as e:
            print(f"Error updating log display: {e}")

    def start_server(self):
        if self.table is None or len(self.table.get_children()) == 0:
            messagebox.showerror("Error", "Cannot start server. No IPs are present.")
            return

        self.server_started = True
        print(f"Server started: {self.server_started}")

        # Replace Start Server button with Terminate Server button
        self.start_button.config(text="Terminate Server", bg="red", command=self.terminate_server)

        # Create a new window to show logs
        self.log_window = Toplevel(self.root)
        self.log_window.title("DHCP Server Logs")
        self.log_window.geometry("600x400")

        # Create a text widget to show logs
        self.log_text = Text(self.log_window, wrap="word", height=20, width=70, bg="white", fg="black")
        self.log_text.pack(padx=10, pady=10)

        # Make the log window close behave like the "Terminate" button
        self.log_window.protocol("WM_DELETE_WINDOW", self.terminate_server)

        # Disable the text widget to make it read-only
        self.log_text.config(state="disabled")

        # Set up the file system observer
        self.observer = Observer()
        event_handler = LogFileHandler(self.update_log_display)
        self.observer.schedule(event_handler, path=os.path.dirname(os.path.abspath("server_logs.txt")) or ".",
                             recursive=False)
        self.observer.start()

        # Initial log display
        self.update_log_display()

    def terminate_server(self):
        self.server_started = False
        print(f"Server terminated: {self.server_started}")

        # Stop the file system observer
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

        self.start_button.config(text="Start Server", bg="#008CBA", command=self.start_server)

        # Close the log window if it's open
        if hasattr(self, 'log_window') and self.log_window.winfo_exists():
            self.log_window.destroy()

    def delete_ip(self):
        selected_item = self.table.selection()
        if selected_item:
            ip_to_remove = self.table.item(selected_item, "values")[1]
            self.table.delete(selected_item)
            if ip_to_remove in self.ip_list:
                self.ip_list.remove(ip_to_remove)
            self.update_indexes()
            print("IP List Updated:", self.ip_list)
        else:
            messagebox.showwarning("No Selection", "Please select an IP to delete.")

    def update_indexes(self):
        for idx, item in enumerate(self.table.get_children(), start=1):
            values = self.table.item(item, "values")
            self.table.item(item, values=(idx, values[1]))

    def show_main_window(self):
        self.modify_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)

    def add_ip(self):
        ip = askstring("Add IP", "Enter IP Address:")
        if ip and self.is_valid_ip(ip):
            existing_ips = [self.table.item(item)["values"][1] for item in self.table.get_children()]
            if ip in existing_ips:
                messagebox.showwarning("Duplicate IP", f"The IP address {ip} already exists.")
                return

            current_row_count = len(self.table.get_children())
            self.table.insert("", "end", values=(current_row_count + 1, ip))
            self.ip_list.append(ip)
            print("IP List Updated:", self.ip_list)

    def is_valid_ip(self, ip):
        parts = ip.split(".")
        if len(parts) != 4:
            messagebox.showerror("Invalid Entry", "Invalid IP format! IP should be in the format: xxx.xxx.xxx.xxx")
            return False

        for part in parts:
            if not part.isdigit() or not 0 <= int(part) <= 255:
                messagebox.showerror("Invalid Entry", "Invalid IP format! Each octet should be a number between 0 and 255.")
                return False

        if sum(int(part) for part in parts) == 0:
            messagebox.showerror("Reserved IP", "Can't use reserved IP addresses like 0.0.0.0 or 255.255.255.255.")
            return False

        reserved_ips = ["0.0.0.0", "255.255.255.255", "00.00.00.00", "000.000.000.000"]
        if ip in reserved_ips:
            messagebox.showerror("Reserved IP", "Can't use reserved IP addresses like 0.0.0.0 or 255.255.255.255.")
            return False

        return True

if __name__ == "__main__":
    root = Tk()
    app = DHCPServerGUI(root)
    root.mainloop()