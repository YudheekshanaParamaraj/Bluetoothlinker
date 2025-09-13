import asyncio
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from bleak import BleakScanner, BleakClient

devices = []
client = None
loop = asyncio.new_event_loop()

# Example UUIDs (replace with your phone's GATT characteristic)
SERVICE_UUID = "0000181c-0000-1000-8000-00805f9b34fb"   # User Data Service
CHAR_UUID = "00002ab4-0000-1000-8000-00805f9b34fb"     # Uncertainty characteristic


# ----------------------------
# Async Functions
# ----------------------------
async def scan_devices_async():
    global devices
    devices = await BleakScanner.discover()
    return devices


async def connect_device_async(address):
    global client
    client = BleakClient(address)
    await client.connect()
    if client.is_connected:
        # Start notifications for two-way communication
        await client.start_notify(CHAR_UUID, notification_handler)
        return client.services  # services already discovered


async def send_message_async(message):
    global client
    if not client or not client.is_connected:
        raise Exception("Not connected to any device")

    # Write message
    await client.write_gatt_char(CHAR_UUID, message.encode())

    # Optional: try reading back (not always supported by phone)
    try:
        response = await client.read_gatt_char(CHAR_UUID)
        return response.decode(errors="ignore")
    except Exception:
        return "(No response received)"


# ----------------------------
# Notification Handler
# ----------------------------
def notification_handler(sender, data: bytearray):
    """Callback when phone sends a notification"""
    msg = data.decode(errors="ignore")
    root.after(0, lambda: text_area.insert(tk.END, f"📩 From phone: {msg}\n"))
    root.after(0, text_area.see, tk.END)


# ----------------------------
# Thread Wrappers (for Tkinter)
# ----------------------------
def run_async_task(coro, callback=None):
    def worker():
        try:
            result = loop.run_until_complete(coro)
            if callback:
                root.after(0, callback, result)
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Error", str(e)))
    threading.Thread(target=worker, daemon=True).start()


def scan_devices():
    run_async_task(scan_devices_async(), update_device_list)


def update_device_list(found_devices):
    listbox.delete(0, tk.END)
    for d in found_devices:
        name = d.name or "Unknown"
        listbox.insert(tk.END, f"{name} [{d.address}]")


def connect_device():
    selection = listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "No device selected")
        return

    device = devices[selection[0]]
    run_async_task(connect_device_async(device.address), show_services)


def show_services(services):
    if not services:
        messagebox.showerror("Error", "No services found")
        return

    text_area.insert(tk.END, "Discovered Services:\n")
    for service in services:
        text_area.insert(tk.END, f"Service {service.uuid}\n")
        for char in service.characteristics:
            text_area.insert(tk.END, f"  Characteristic {char.uuid} ({char.properties})\n")
    text_area.insert(tk.END, "\n")
    text_area.see(tk.END)
    messagebox.showinfo("Connected", "Device connected and services discovered!")


def send_message():
    msg = entry.get()
    if not msg:
        messagebox.showerror("Error", "Message cannot be empty")
        return
    run_async_task(send_message_async(msg), show_response)


def show_response(response):
    text_area.insert(tk.END, f"PC wrote → Device replied: {response}\n")
    text_area.see(tk.END)


# ----------------------------
# Tkinter GUI
# ----------------------------
root = tk.Tk()
root.title("Bluetooth Communication")

tk.Button(root, text="Scan Devices", command=scan_devices).pack(pady=5)

listbox = tk.Listbox(root, width=50)
listbox.pack(pady=5)

tk.Button(root, text="Connect", command=connect_device).pack(pady=5)

entry = tk.Entry(root, width=40)
entry.pack(pady=5)

tk.Button(root, text="Send Message", command=send_message).pack(pady=5)

text_area = scrolledtext.ScrolledText(root, width=60, height=15)
text_area.pack(pady=5)

# Run asyncio loop in background thread
def start_loop():
    asyncio.set_event_loop(loop)
loop_thread = threading.Thread(target=start_loop, daemon=True)
loop_thread.start()

root.mainloop()
