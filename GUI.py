import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import serial
import time
import serial.tools.list_ports

# Initialize serial port as None
ser = None
parsed_lines = []  # Store parsed HEX lines
device_matched = False  # Track if the correct device is detected
loaded_file_name = ""  # Track loaded HEX file name
bt_com_port = None  # The COM port of the Bluetooth module

def parse_hex_line(line):
    """Parses a HEX file line into components."""
    if not line.startswith(":"):
        return None

    line = line.strip()
    byte_count = int(line[1:3], 16)
    address = line[3:7]
    record_type = line[7:9]
    data = line[9:-2]
    checksum = line[-2:]

    return {
        "Byte Count": byte_count,
        "Address": address,
        "Record Type": record_type,
        "Data": data,
        "Checksum": checksum
    }

def load_hex_file():
    """Loads HEX file and parses it."""
    global loaded_file_name  # Track file name
    file_path = filedialog.askopenfilename(filetypes=[("HEX Files", "*.hex"), ("All Files", "*.*")])

    if not file_path:
        return  

    try:
        with open(file_path, "r") as file:
            lines = file.readlines()

        # Clear existing data
        for row in tree.get_children():
            tree.delete(row)

        global parsed_lines
        parsed_lines = []  # Reset HEX data list

        for line in lines:
            parsed_data = parse_hex_line(line)
            if parsed_data:
                parsed_lines.append(line.strip())  # Store raw HEX line
                tree.insert("", "end", values=(
                    parsed_data["Byte Count"],
                    parsed_data["Address"],
                    parsed_data["Record Type"],
                    parsed_data["Data"],
                    parsed_data["Checksum"]
                ))

        loaded_file_name = os.path.basename(file_path)  # Save the name of the loaded file
        label_loaded_file.config(text=f"Loaded File: {loaded_file_name}")  # Display the file name

    except Exception as e:
        messagebox.showerror("Error", f"Failed to read file:\n{e}")

def reload_hex_file():
    """Reloads the previously loaded HEX file."""
    global loaded_file_name
    if loaded_file_name:
        # Ask the user if they want to reload the same file
        reload = messagebox.askyesno("Reload", f"Do you want to reload the file: {loaded_file_name}?")
        if reload:
            # Reload the file by calling load_hex_file again
            load_hex_file()
    else:
        messagebox.showerror("Error", "No HEX file loaded previously!")

def detect_ports():
    """Detects USB-to-UART modules and auto-selects the correct port."""
    ports = list(serial.tools.list_ports.comports())
    usb_ports = []
    selected_port = None

    for port in ports:
        port_name = port.device
        description = port.description

        # Only add USB Serial devices (ignore Bluetooth)
        if "USB" in description or "UART" in description or "CP210" in description or "CH340" in description:
            usb_ports.append(f"{port_name} - {description}")

    # Update dropdown with filtered USB-UART ports
    com_dropdown['values'] = usb_ports

    if usb_ports:
        com_var.set(usb_ports[0])  # Auto-select first USB-UART device
        selected_port = usb_ports[0]
    else:
        com_var.set("")  # No USB-UART device found

    messagebox.showinfo("Port Detection", f"Detected USB-to-UART: {selected_port or 'None'}")

def connect_uart():
    """Establish UART connection to USB-to-UART module."""
    global ser
    port_info = com_var.get()

    if not port_info:
        messagebox.showerror("Error", "No COM port selected!")
        return

    # Extract COM port name and baud rate
    port = port_info.split(" - ")[0]
    baud = int(baud_var.get())

    # Close existing connection (if any)
    disconnect_uart()

    try:
        ser = serial.Serial(port, baudrate=baud, timeout=1)
        messagebox.showinfo("Success", f"Connected to {port} at {baud} baud.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open serial port:\n{e}")

def disconnect_uart():
    """Disconnect the serial port."""
    global ser
    if ser and ser.is_open:
        ser.close()
        messagebox.showinfo("Disconnected", "UART connection closed.")
    ser = None

def connect_bluetooth():
    """Search for nearby Bluetooth devices and allow user to select and connect."""
    global ser, bt_com_port

    # Check if serial connection is established
    if ser is None or not ser.is_open:
        messagebox.showerror("Error", "Bluetooth connection is not established!")
        return

    try:
        # Send AT command to initiate device search (scan for devices)
        ser.write(b'AT+INQ\r\n')  # AT command to start the inquiry process
        time.sleep(3)  # Wait for devices to be discovered

        # Read the response from the HC-05
        response = ser.readline().decode().strip()

        if "OK" in response:
            # Successfully started inquiry
            messagebox.showinfo("Searching", "Searching for nearby Bluetooth devices...")

            # Here, you could use AT commands or code to parse the list of discovered devices
            # For now, we mock a list of discovered devices for the example
            devices = ["Device 1 (HC-05)", "Device 2 (Smartphone)", "Device 3 (HC-06)"]

            # Display device list in a new window for user to select from
            device_window = tk.Toplevel(root)
            device_window.title("Select Bluetooth Device")
            listbox = tk.Listbox(device_window)
            for device in devices:
                listbox.insert(tk.END, device)
            listbox.pack(pady=10)

            # Ask for PIN and connect to selected device
            def connect_to_device():
                selected_device = listbox.get(tk.ACTIVE)
                if selected_device:
                    # Prompt for PIN (password)
                    pin = simpledialog.askstring("PIN", f"Enter PIN for {selected_device} (default 1234):", parent=device_window)
                    if pin:
                        # Send PIN command to HC-05 (if needed)
                        ser.write(f'AT+PAIR={selected_device}, {pin}\r\n'.encode())
                        messagebox.showinfo("Success", f"Connecting to {selected_device}...")
                    device_window.destroy()

            connect_button = tk.Button(device_window, text="Connect", command=connect_to_device)
            connect_button.pack(pady=10)

        else:
            messagebox.showerror("Error", "Failed to start Bluetooth inquiry!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to search for Bluetooth devices: {e}")
        return

def disconnect_bluetooth():
    """Disconnect Bluetooth connection."""
    global ser
    if ser and ser.is_open:
        ser.close()
        messagebox.showinfo("Disconnected", "Bluetooth connection closed.")
        ser = None
    else:
        messagebox.showwarning("Warning", "No Bluetooth connection to disconnect.")

# The rest of the application code for creating the GUI and handling buttons would follow here...

root.mainloop()
