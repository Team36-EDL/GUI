# GUI Code (sender_gui.py)
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import serial
import os
import time
import serial.tools.list_ports

# Initialize serial port as None
ser = None
parsed_lines = []  # Store parsed HEX lines
loaded_file_name = ""  # Track loaded HEX file name

# Dictionary of board signatures
BOARD_SIGNATURES = {
    "Arduino UNO": "ARDUINO_UNO_R3",
    "Arduino Nano": "ARDUINO_NANO",
    "Arduino Mega": "ARDUINO_MEGA",
    "STM32F103": "STM32F103"
}

selected_board = None  # Track selected board

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
    global loaded_file_name
    file_path = filedialog.askopenfilename(filetypes=[("HEX Files", ".hex"), ("All Files", ".*")])

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
                parsed_lines.append(line.strip())
                tree.insert("", "end", values=(
                    parsed_data["Byte Count"],
                    parsed_data["Address"],
                    parsed_data["Record Type"],
                    parsed_data["Data"],
                    parsed_data["Checksum"]
                ))

        loaded_file_name = os.path.basename(file_path)
        label_loaded_file.config(text=f"Loaded File: {loaded_file_name}")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to read file:\n{e}")

def select_board():
    """Handle board selection"""
    global selected_board
    selected = board_var.get()
    if selected in BOARD_SIGNATURES:
        selected_board = selected
        messagebox.showinfo("Success", f"Selected board: {selected}")
    else:
        messagebox.showerror("Error", "Please select a valid board!")

def detect_ports():
    """Detects USB-to-UART modules and auto-selects the correct port."""
    ports = list(serial.tools.list_ports.comports())
    usb_ports = []

    for port in ports:
        port_name = port.device
        description = port.description

        if "USB" in description or "UART" in description or "CP210" in description or "CH340" in description:
            usb_ports.append(f"{port_name} - {description}")

    com_dropdown['values'] = usb_ports

    if usb_ports:
        com_var.set(usb_ports[0])
    else:
        com_var.set("")

def connect_uart():
    """Establish UART connection to USB-to-UART module."""
    global ser
    port_info = com_var.get()

    if not port_info:
        messagebox.showerror("Error", "No COM port selected!")
        return

    port = port_info.split(" - ")[0]
    baud = int(baud_var.get())

    disconnect_uart()

    try:
        ser = serial.Serial(
            port=port,
            baudrate=baud,
            timeout=1,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
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

def send_signature():
    """Send device signature based on selected board."""
    global ser, selected_board
    
    if not selected_board:
        messagebox.showerror("Error", "Please select a board first!")
        return
        
    if ser is None or not ser.is_open:
        messagebox.showerror("Error", "UART connection not established!")
        return

    try:
        # Simply send the signature
        signature = BOARD_SIGNATURES[selected_board] + "\n"
        ser.write(signature.encode())
        messagebox.showinfo("Success", "Signature sent successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to send signature:\n{e}")

def send_hex_data():
    """Send HEX file content."""
    global ser
    if ser is None or not ser.is_open:
        messagebox.showerror("Error", "UART connection not established!")
        return

    if not parsed_lines:
        messagebox.showerror("Error", "No HEX file loaded!")
        return

    try:
        for line in parsed_lines:
            ser.write((line + "\n").encode())
            time.sleep(0.05)
        ser.write(b"END\n")
        messagebox.showinfo("Success", "HEX file transmitted successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send data:\n{e}")

# Create main application window
root = tk.Tk()
root.title("Board Programmer")
root.geometry("800x600")

# Board Selection Frame
board_frame = ttk.LabelFrame(root, text="Board Selection")
board_frame.pack(fill="x", padx=10, pady=5)

board_var = tk.StringVar()
board_dropdown = ttk.Combobox(board_frame, textvariable=board_var, values=list(BOARD_SIGNATURES.keys()))
board_dropdown.grid(row=0, column=0, padx=5, pady=2)

btn_select_board = tk.Button(board_frame, text="Select Board", command=select_board)
btn_select_board.grid(row=0, column=1, padx=5, pady=2)

# Load HEX File Button
btn_load = tk.Button(root, text="Load HEX File", command=load_hex_file)
btn_load.pack(pady=5)

# Display the loaded file name
label_loaded_file = tk.Label(root, text="Loaded File: None")
label_loaded_file.pack(pady=5)

# Create a Treeview widget to display parsed HEX data
columns = ("Byte Count", "Address", "Record Type", "Data", "Checksum")
tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center", width=120)

tree.pack(expand=True, fill="both", pady=5)

# UART Settings Frame
uart_frame = ttk.LabelFrame(root, text="UART Settings")
uart_frame.pack(fill="x", padx=10, pady=5)

com_var = tk.StringVar()
com_dropdown = ttk.Combobox(uart_frame, textvariable=com_var, width=30)
com_dropdown.grid(row=0, column=1, padx=5, pady=2)
detect_ports()

baud_var = tk.StringVar(value="38400")  # Default baud rate
baud_dropdown = ttk.Combobox(uart_frame, textvariable=baud_var, values=["9600", "38400", "57600", "115200"], width=15)
baud_dropdown.grid(row=0, column=2, padx=5, pady=2)

btn_refresh = tk.Button(uart_frame, text="Refresh", command=detect_ports)
btn_refresh.grid(row=0, column=3, padx=5, pady=2)

btn_connect = tk.Button(uart_frame, text="Connect", command=connect_uart)
btn_connect.grid(row=1, column=2, padx=5, pady=2)

btn_disconnect = tk.Button(uart_frame, text="Disconnect", command=disconnect_uart)
btn_disconnect.grid(row=1, column=3, padx=5, pady=2)

btn_check_signature = tk.Button(root, text="Check Signature", command=send_signature)
btn_check_signature.pack(pady=5)

btn_send = tk.Button(root, text="Program Device", command=send_hex_data)
btn_send.pack(pady=10)

root.mainloop()