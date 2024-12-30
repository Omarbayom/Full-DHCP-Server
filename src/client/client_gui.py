from threading import Thread
import time
from tkinter import Tk, Label, Button, Frame, Text, Entry
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import os
from client import start_dhcp_client


class DHCPServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DHCP Client GUI")
        self.root.geometry("600x600")

        self.log_file_path = os.path.join(
            os.getcwd(), "output/client_requests.log")

        # Frames
        self.main_frame = Frame(self.root)
        self.modify_frame = Frame(self.root)
        self.client_request_frame = Frame(self.root)
        self.log_viewer_frame = Frame(self.root)

        # Setup the main frame and show it
        self.setup_main_frame()
        self.show_main_window()

        # Start log monitoring
        Thread(target=self.monitor_log_file, daemon=True).start()

    def setup_main_frame(self):
        """Setup the main frame UI."""
        center_frame = Frame(self.main_frame)
        center_frame.pack(expand=True)

        try:
            server_image = Image.open(os.path.join(
                os.path.curdir, "utils/client.png"))
            server_image = server_image.resize((215, 215))
            self.server_image = ImageTk.PhotoImage(server_image)
            Label(center_frame, image=self.server_image).pack(pady=10)
        except Exception as e:
            print(f"Error loading image: {e}")

        Button(
            center_frame,
            text="Modify Server",
            font=("Helvetica", 18, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10,
            command=self.show_modify_window,
        ).pack(pady=10)

    def show_main_window(self):
        """Show the main window and hide all other frames."""
        self.hide_all_frames()
        self.main_frame.pack(fill="both", expand=True)

    def show_modify_window(self):
        """Show the modify window and hide all other frames."""
        self.hide_all_frames()

        # Clear existing widgets in the frame
        for widget in self.modify_frame.winfo_children():
            widget.destroy()

        self.modify_frame.pack(fill="both", expand=True)

        Button(
            self.modify_frame,
            text="Add Client Request",
            font=("Helvetica", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self.show_client_request_window,
        ).pack(pady=20)

        Button(
            self.modify_frame,
            text="View Log",
            font=("Helvetica", 14, "bold"),
            bg="#2196F3",
            fg="white",
            command=self.show_log_viewer,
        ).pack(pady=20)

        Button(
            self.modify_frame,
            text="Back",
            font=("Helvetica", 14),
            bg="red",
            fg="white",
            command=self.show_main_window,
        ).pack(pady=10)

    def show_client_request_window(self):
        """Show the client request window and hide all other frames."""
        self.hide_all_frames()
        for widget in self.client_request_frame.winfo_children():
            widget.destroy()
        self.client_request_frame.pack(fill="both", expand=True)

        Label(self.client_request_frame, text="Enter Requested IP:",
              font=("Helvetica", 12)).pack(pady=5)
        self.requested_ip_entry = Entry(
            self.client_request_frame, font=("Helvetica", 12))
        self.requested_ip_entry.pack(pady=5)

        Label(self.client_request_frame, text="Enter Requested Lease Time:",
              font=("Helvetica", 12)).pack(pady=5)
        self.requested_lease_entry = Entry(
            self.client_request_frame, font=("Helvetica", 12))
        self.requested_lease_entry.pack(pady=5)

        Label(self.client_request_frame, text="Enter MAC Address:",
              font=("Helvetica", 12)).pack(pady=5)
        self.mac_address_entry = Entry(
            self.client_request_frame, font=("Helvetica", 12))
        self.mac_address_entry.pack(pady=5)

        # Add dynamic labels for status
        self.status_label = Label(
            self.client_request_frame, text="Status: ", font=("Helvetica", 12, "bold"))
        self.status_label.pack(pady=5)
        self.ip_label = Label(self.client_request_frame,
                              text="Current IP: 0.0.0.0", font=("Helvetica", 12))
        self.ip_label.pack(pady=5)
        self.timer_label = Label(
            self.client_request_frame, text="Lease Time: 0", font=("Helvetica", 12))
        self.timer_label.pack(pady=5)

        Button(
            self.client_request_frame,
            text="Submit",
            font=("Helvetica", 14),
            bg="#4CAF50",
            fg="white",
            command=self.submit_client_request,
        ).pack(pady=10)

        Button(
            self.client_request_frame,
            text="Back",
            font=("Helvetica", 14),
            bg="red",
            fg="white",
            command=self.show_modify_window,
        ).pack(pady=10)

    def submit_client_request(self):
        """Submit client request and update the GUI based on the response."""
        requested_ip = self.requested_ip_entry.get() or None
        requested_lease = self.requested_lease_entry.get() or None
        mac_address = self.mac_address_entry.get() or None

        if not self.is_valid_ip(requested_ip):
            return

        try:
            requested_lease = int(requested_lease)
            response = start_dhcp_client(
                requested_ip=requested_ip, lease_duration=requested_lease, mac_address=mac_address)

            leased_ip, status, lease_time = response

            if status == "ACK":
                self.status_label.config(text="Status: ACK", fg="green")
                self.ip_label.config(text=f"Current IP: {leased_ip}")
                self.start_lease_countdown(lease_time)
            else:
                self.status_label.config(text="Status: NACK", fg="red")
                self.ip_label.config(text="Current IP: 0.0.0.0")
                self.timer_label.config(text="Lease Time: 0")

        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to send client request: {e}")

    def start_lease_countdown(self, lease_time):
        """Start countdown for lease duration."""
        def countdown():
            nonlocal lease_time
            while lease_time > 0:
                self.timer_label.config(text=f"Lease Time: {lease_time}")
                self.root.update()
                time.sleep(1)
                lease_time -= 1
            # Reset to default once the timer ends
            self.ip_label.config(text="Current IP: 0.0.0.0")
            self.timer_label.config(text="Lease Time: 0")

        Thread(target=countdown, daemon=True).start()

    def is_valid_ip(self, ip):
        """Validate IP address format."""
        if not ip:
            return True  # Allow None for default IP
        parts = ip.split(".")
        if len(parts) != 4 or not all(part.isdigit() and 0 <= int(part) <= 255 for part in parts):
            messagebox.showerror(
                "Invalid Entry", "IP should be in the format: xxx.xxx.xxx.xxx")
            return False
        return True

    def show_log_viewer(self):
        """Show the log viewer window and hide all other frames."""
        self.hide_all_frames()
        self.log_viewer_frame.pack(fill="both", expand=True)

        Label(self.log_viewer_frame, text="Log Viewer",
              font=("Helvetica", 16, "bold")).pack(pady=10)

        self.log_text = ScrolledText(self.log_viewer_frame, font=(
            "Helvetica", 12), wrap="word", height=20, width=70)
        self.log_text.pack(pady=10)

        self.load_log_file()

        Button(
            self.log_viewer_frame,
            text="Back",
            font=("Helvetica", 14),
            bg="red",
            fg="white",
            command=self.show_modify_window,
        ).pack(pady=10)

    def load_log_file(self):
        """Load existing log file content into the text widget."""
        if os.path.exists(self.log_file_path):
            with open(self.log_file_path, "r") as log_file:
                self.log_text.delete("1.0", "end")
                self.log_text.insert("1.0", log_file.read())

    def monitor_log_file(self):
        """Monitor the log file for updates and display changes in the text widget."""
        last_size = 0
        while True:
            if os.path.exists(self.log_file_path):
                current_size = os.path.getsize(self.log_file_path)
                if current_size > last_size:
                    with open(self.log_file_path, "r") as log_file:
                        log_file.seek(last_size)
                        new_content = log_file.read()
                        self.log_text.insert("end", new_content)
                        self.log_text.yview("end")
                    last_size = current_size
            time.sleep(1)

    def hide_all_frames(self):
        """Hide all frames."""
        for frame in [self.main_frame, self.modify_frame, self.client_request_frame, self.log_viewer_frame]:
            frame.pack_forget()


if __name__ == "__main__":
    root = Tk()
    app = DHCPServerGUI(root)
    root.mainloop()
