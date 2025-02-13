# Receiver Code (receiver.py)
import serial

def setup_serial():
    """Setup serial connection for receiver."""
    try:
        ser = serial.Serial(
            port='COM12',  # Change this to your receiver's COM port
            baudrate=38400,
            timeout=1,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        print("Serial port opened successfully")
        return ser
    except Exception as e:
        print(f"Error opening serial port: {e}")
        return None

def main():
    ser = setup_serial()
    if not ser:
        return

    print("Waiting for signature...")
    try:
        while True:
            if ser.in_waiting > 0:
                # Read and display received signature
                received_data = ser.readline().decode().strip()
                print(f"Received signature: {received_data}")

    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed")

if __name__ == "__main__":
    main()