from tkinter import Tk, Label, Button, Frame, Toplevel, Text
from tkinter import ttk, messagebox
from tkinter.simpledialog import askstring
from PIL import Image, ImageTk
import re

class DHCPServerGUI:
    def __init__(self, root):
        self.ip_list = []  # Stores the IP addresses in the table
        self.root = root
        self.root.title("DHCP Server GUI")
        self.root.geometry("600x600")  # Set the window size to 600x600 for Phase 2 size

        # Initial Frame (Phase 1)
        self.main_frame = Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # Create a frame to center both the image and the button vertically and horizontally
        center_frame = Frame(self.main_frame)
        center_frame.pack(expand=True)  # This will expand and center the content vertically and horizontally

        # Server Image using PIL to load jpg
        try:
            self.server_image = Image.open("D:\\Semester 7\\Networks\\server_img.jpg")
            self.server_image = self.server_image.resize((215, 215))  # Resize for better fitting
            self.server_image = ImageTk.PhotoImage(self.server_image)
            self.image_label = Label(center_frame, image=self.server_image)
            self.image_label.pack(pady=10)  # Center image vertically and horizontally within the frame
        except Exception as e:
            print(f"Error loading image: {e}")

        # Modify Server Button (Phase 1)
        self.modify_button = Button(
            center_frame, text="Modify Server", font=("Helvetica", 18, "bold"), bg="#4CAF50", fg="white",
            padx=20, pady=10, command=self.show_modify_window
        )
        self.modify_button.pack(pady=10)  # Center button vertically below the image within the same frame

        # Frame for Modify Server (Phase 2 - Initially Hidden)
        self.modify_frame = Frame(self.root)

        # Table variable, initialized to None
        self.table = None

        # Buttons for Add/Delete (Initialized to None)
        self.add_button = None
        self.delete_button = None
        self.back_button = None
        self.start_button = None  # Start Server button will be added in Phase 2

    def show_modify_window(self):
        # Hide the main frame and show modify frame (Phase 2)
        self.main_frame.pack_forget()
        self.modify_frame.pack(fill="both", expand=True)

        # No need to change window size here, it's already set to 600x600 globally

        # Create the table only if it does not already exist
        if self.table is None:
            self.table = ttk.Treeview(self.modify_frame, columns=("#", "IP Address"), show="headings")
            self.table.heading("#", text="#")
            self.table.heading("IP Address", text="IP Address")

            # Add line separation by setting column width and alignment
            self.table.column("#", width=40, anchor="center")
            self.table.column("IP Address", width=150, anchor="w")

            # Pre-populate the table with default IPs
            default_ips = ["192.168.1.001", "192.168.1.002", "192.168.1.003"]
            for idx, ip in enumerate(default_ips, start=1):
                self.table.insert("", "end", values=(idx, ip))
                self.ip_list.append(ip)  # Add default IPs to the list

            self.table.pack(fill="both", expand=True, padx=10, pady=10)

        # Create the buttons for Add/Delete, Back, and Start Server (Phase 2)
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

    # def add_ip(self):
    #     ip = askstring("Add IP", "Enter IP Address:")
    #     if ip:
    #         # Get the current number of rows in the table and add a new row with the IP
    #         current_row_count = len(self.table.get_children())
    #         self.table.insert("", "end", values=(current_row_count + 1, ip))

    def delete_ip(self):
        selected_item = self.table.selection()  # Get the selected item in the table
        if selected_item:
            # Retrieve the IP from the selected row
            ip_to_remove = self.table.item(selected_item, "values")[1]

            # Remove the item from the table
            self.table.delete(selected_item)

            # Remove the IP from the list
            if ip_to_remove in self.ip_list:
                self.ip_list.remove(ip_to_remove)

            # Update the row indexes
            self.update_indexes()

            print("IP List Updated:", self.ip_list)  # Debug
        else:
            # If no item is selected, show an alert message
            messagebox.showwarning("No Selection", "Please select an IP to delete.")

    def update_indexes(self):
        """Updates the row indexes in the table after an item is deleted."""
        for idx, item in enumerate(self.table.get_children(), start=1):
            # Update only the index column (the first column)
            values = self.table.item(item, "values")
            self.table.item(item, values=(idx, values[1]))

    def show_main_window(self):
        # Hide modify frame and show main frame again
        self.modify_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)

    def start_server(self):
        # Check if the table is empty before starting the server
        if self.table is None or len(self.table.get_children()) == 0:
            messagebox.showerror("Error", "Cannot start server. No IPs are present.")
            return

        # Create a new window to show logs
        self.log_window = Toplevel(self.root)
        self.log_window.title("DHCP Server Logs")
        self.log_window.geometry("600x400")

        # White background for log window
        self.log_window.configure(bg="white")

        # Create a text widget to show logs
        self.log_text = Text(self.log_window, wrap="word", height=20, width=70, bg="white", fg="black")
        self.log_text.pack(padx=10, pady=10)

        # Read log messages from the file and display in the log_text widget
        try:
            with open("server_logs.txt", "r") as log_file: #n2ra men hena el log file
                log_content = log_file.read()
                self.log_text.insert("end", log_content)
        except FileNotFoundError:
            # If the log file is not found, inform the user
            messagebox.showerror("Error", "Log file not found.")
        except Exception as e:
            # Handle any other exceptions (like permission errors, etc.)
            messagebox.showerror("Error", f"Error reading log file: {e}")

        # Disable the text widget to make it read-only
        self.log_text.config(state="disabled")


    def add_ip(self):
        ip = askstring("Add IP", "Enter IP Address:")
        if ip:
            # Validate IP format and avoid reserved IPs
            if not self.is_valid_ip(ip):
                return

            # Check if the IP already exists in the table (more validation)
            existing_ips = [self.table.item(item)["values"][1] for item in self.table.get_children()]

            if ip in existing_ips:
                messagebox.showwarning("Duplicate IP", f"The IP address {ip} already exists.")
                return

            # Get the current number of rows in the table and add a new row with the IP
            current_row_count = len(self.table.get_children())
            self.table.insert("", "end", values=(current_row_count + 1, ip))
            self.ip_list.append(ip)  # Add the new IP to the list
            print("IP List Updated:", self.ip_list) #debug

    def is_valid_ip(self, ip):
        """Validates the IP address format and checks for reserved IPs."""
        # Check if the IP format is valid
        parts = ip.split(".")
        if len(parts) != 4:
            messagebox.showerror("Invalid Entry", "Invalid IP format! IP should be in the format: xxx.xxx.xxx.xxx")
            return False

        # Ensure each part of the IP is a number between 0 and 255
        for part in parts:
            if not part.isdigit() or not 0 <= int(part) <= 255:
                messagebox.showerror("Invalid Entry",
                                     "Invalid IP format! Each octet should be a number between 0 and 255.")
                return False

        # Reserved IPs check
        reserved_ips = ["0.0.0.0", "255.255.255.255", "00.00.00.00", "000.000.000.000"]
        if ip in reserved_ips:
            messagebox.showerror("Reserved IP", "Can't use reserved IP addresses like 0.0.0.0 or 255.255.255.255.")
            return False

        return True


if __name__ == "__main__":
    root = Tk()
    app = DHCPServerGUI(root)
    root.mainloop()
