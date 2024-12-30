from threading import Thread
import time
from PIL import Image, ImageTk
import os
from customtkinter import CTk, CTkLabel, CTkButton, CTkFrame, CTkEntry, CTkTextbox, CTkScrollbar
from tkinter import messagebox

import customtkinter

from client import start_dhcp_client
from utils import Client


class DHCPServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DHCP Client GUI")
        self.root.geometry("800x600")
        self.log_opened = False
        self.log_file_path = os.path.join(
            os.getcwd(), "output/client_requests.log")
        self.force_ip_var = customtkinter.StringVar(value="false")
        # Frames
        self.main_frame = CTkFrame(self.root)
        self.modify_frame = CTkFrame(self.root)
        self.client_request_frame = CTkFrame(self.root)
        self.log_viewer_frame = CTkFrame(self.root)

        # Setup the main frame and show it
        self.setup_main_frame()
        self.show_main_window()

        # Initialize log_text
        self.log_text = ""

        # Start log monitoring
        Thread(target=self.monitor_log_file, daemon=True).start()

    def setup_main_frame(self):
        """Setup the main frame UI."""
        center_frame = CTkFrame(self.main_frame)
        center_frame.pack(expand=True)

        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(script_dir, "client.png")
            self.server_image = Image.open(image_path)
            # Resize the image for better fitting
            self.server_image = self.server_image.resize((215, 215))
            self.server_image = ImageTk.PhotoImage(self.server_image)
            CTkLabel(center_frame, image=self.server_image,
                     text="").pack(pady=10)
        except Exception as e:
            print(f"Error loading image: {e}")

        CTkButton(
            center_frame,
            text="Modify Client",
            font=("Helvetica", 18, "bold"),
            fg_color="#4CAF50",
            text_color="white",
            command=self.show_modify_window,
        ).pack(pady=10)

    def show_main_window(self):
        """Show the main window and hide all other frames."""
        self.hide_all_frames()
        self.main_frame.pack(fill="both", expand=True)

    def show_modify_window(self):
        self.log_opened = False
        """Show the modify window and hide all other frames."""
        self.hide_all_frames()

        # Clear existing widgets in the frame
        for widget in self.modify_frame.winfo_children():
            widget.destroy()

        self.modify_frame.pack(fill="both", expand=True)

        CTkButton(
            self.modify_frame,
            text="Add Client Request",
            font=("Helvetica", 14, "bold"),
            fg_color="#4CAF50",
            text_color="white",
            command=self.show_client_request_window,
        ).pack(pady=20)

        CTkButton(
            self.modify_frame,
            text="View Log",
            font=("Helvetica", 14, "bold"),
            fg_color="#2196F3",
            text_color="white",
            command=self.show_log_viewer,
        ).pack(pady=20)

        CTkButton(
            self.modify_frame,
            text="Back",
            font=("Helvetica", 14),
            fg_color="red",
            text_color="white",
            command=self.show_main_window,
        ).pack(pady=10)

    def show_client_request_window(self):
        """Show the client request window and hide all other frames."""
        self.hide_all_frames()
        for widget in self.client_request_frame.winfo_children():
            widget.destroy()
        self.client_request_frame.pack(fill="both", expand=True)

        CTkLabel(self.client_request_frame, text="Enter Requested IP:",
                 font=("Helvetica", 12)).pack(pady=5)
        self.requested_ip_entry = CTkEntry(
            self.client_request_frame, font=("Helvetica", 12))
        self.requested_ip_entry.pack(pady=5)

        CTkLabel(self.client_request_frame, text="Enter Requested Lease Time:", font=(
            "Helvetica", 12)).pack(pady=5)
        self.requested_lease_entry = CTkEntry(
            self.client_request_frame, font=("Helvetica", 12))
        self.requested_lease_entry.pack(pady=5)

        CTkLabel(self.client_request_frame, text="Enter MAC Address:",
                 font=("Helvetica", 12)).pack(pady=5)
        self.mac_address_entry = CTkEntry(
            self.client_request_frame, font=("Helvetica", 12))
        self.mac_address_entry.pack(pady=5)
        self.checkbox = customtkinter.CTkCheckBox(
            master=self.client_request_frame,
            text="Force IP Assignment",
            variable=self.force_ip_var,
            onvalue="true",
            offvalue="false",
            command=self.on_checkbox_toggle
        )
        self.checkbox.pack(pady=5)
        # Add dynamic labels for status
        self.status_label = CTkLabel(
            self.client_request_frame, text="Status: ", font=("Helvetica", 12, "bold"))
        self.status_label.pack(pady=5)
        self.ip_label = CTkLabel(
            self.client_request_frame, text="Current IP: 0.0.0.0", font=("Helvetica", 12))
        self.ip_label.pack(pady=5)
        self.timer_label = CTkLabel(
            self.client_request_frame, text="Lease Time: 0", font=("Helvetica", 12))
        self.timer_label.pack(pady=5)

        CTkButton(
            self.client_request_frame,
            text="Submit",
            font=("Helvetica", 14),
            fg_color="#4CAF50",
            text_color="white",
            command=self.submit_client_request,
        ).pack(pady=10)

        CTkButton(
            self.client_request_frame,
            text="Back",
            font=("Helvetica", 14),
            fg_color="red",
            text_color="white",
            command=self.show_modify_window,
        ).pack(pady=10)

    def on_checkbox_toggle(self):
        # Print current value when toggled
        pass
        # print(f"Force IP Assignment is set to: {self.force_ip_var.get()}")

    def submit_client_request(self):
        """Submit client request and update the GUI based on the response."""
        requested_ip = self.requested_ip_entry.get() or None
        requested_lease = self.requested_lease_entry.get() or None
        mac_address = self.mac_address_entry.get() or Client.generate_unique_mac()

        if not self.is_valid_ip(requested_ip):
            return

        try:
            requested_lease = int(requested_lease)
            action = 'REQUEST' if self.force_ip_var.get() == 'false' else 'DECLINE'
            response = start_dhcp_client(
                requested_ip=requested_ip, lease_duration=requested_lease, mac_address=mac_address, action=action)

            leased_ip, status, lease_time = response
            with open(self.log_file_path, "a") as log_file:
                log_file.write(
                    f"Requested IP: {leased_ip}, Lease Time: {
                        lease_time}, MAC Address: {mac_address}, Response: {status}\n"
                )

            if status == "ACK":
                self.status_label.configure(
                    text="Status: ACK", text_color="green")
                self.ip_label.configure(text=f"Current IP: {leased_ip}")
                self.start_lease_countdown(lease_time)
            else:
                self.status_label.configure(
                    text="Status: NACK", text_color="red")
                self.ip_label.configure(text="Current IP: 0.0.0.0")
                self.timer_label.configure(text="Lease Time: 0")

        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to send client request: {e}")

    def start_lease_countdown(self, lease_time):
        """Start countdown for lease duration."""
        def countdown():
            nonlocal lease_time
            while lease_time > 0:
                self.timer_label.configure(text=f"Lease Time: {lease_time}")
                self.root.update()
                time.sleep(1)
                lease_time -= 1
            # Reset to default once the timer ends
            self.ip_label.configure(text="Current IP: 0.0.0.0")
            self.timer_label.configure(text="Lease Time: 0")

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

    def update_log_display(self):
        """Update the log display when file changes are detected."""
        try:
            log_file_path = os.path.join(
                os.getcwd(), "output/client_requests.log")
            if not os.path.exists(log_file_path):
                print("Log file does not exist yet.")
                return

            # Read log file content
            with open(log_file_path, "r") as log_file:
                content = log_file.read()

            # Update log text widget
            if hasattr(self, 'log_text'):
                self.log_text.configure(state="normal")
                self.log_text.delete("1.0", "end")
                self.log_text.insert("end", content)
                self.log_text.see("end")
                self.log_text.configure(state="disabled")

        except Exception as e:
            print(f"Error updating log display: {e}")

    def show_log_viewer(self):
        """Show the log viewer window and hide all other frames."""
        self.log_opened = True
        self.hide_all_frames()
        for widget in self.log_viewer_frame.winfo_children():
            widget.destroy()
        self.log_viewer_frame.pack(fill="both", expand=True)
        CTkLabel(self.log_viewer_frame, text="Log Viewer",
                 font=("Helvetica", 16, "bold")).pack(pady=10)

        self.log_text = CTkTextbox(self.log_viewer_frame, font=(
            "Helvetica", 12), wrap="word", height=450, width=750)
        self.log_text.pack(pady=10)

        # Initial log display
        self.update_log_display()

        def continuous_log_update():
            while self.log_opened:
                self.update_log_display()
                time.sleep(1)  # Update every second

        Thread(target=continuous_log_update, daemon=True).start()

        CTkButton(
            self.log_viewer_frame,
            text="Back",
            font=("Helvetica", 14),
            fg_color="red",
            text_color="white",
            command=self.show_modify_window,
        ).pack(pady=10)

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
    root = CTk()
    app = DHCPServerGUI(root)
    root.mainloop()
