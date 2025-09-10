import asyncio
import threading
import tkinter as tk
from tkinter import messagebox
from bleak import BleakScanner, BleakClient

devices = []
client = None
CHAR_UUID = CHAR_UUID = "00002ab4-0000-1000-8000-00805f9b34fb"

def scan_devices():
    def worker():
        async def run_scan():
            global devices
            devices = await BleakScanner.discover()
            listbox.delete(0, tk.END)
            for i, d in enumerate(devices):
                listbox.insert(tk.END, f"{d.name} [{d.address}]")
        asyncio.run(run_scan())
    threading.Thread(target=worker).start()

def connect_device():
    selection = listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "No device selected")
        return
    
    device = devices[selection[0]]
    def worker():
        async def run_connect():
            global client
            client = BleakClient(device.address)
            await client.connect()
            if client.is_connected:
                messagebox.showinfo("Connected", f"Connected to {device.name}")
        asyncio.run(run_connect())
    threading.Thread(target=worker).start()

def send_message():
    if not client:
        messagebox.showerror("Error", "Not connected")
        return
    
    def worker():
        async def run_send():
            try:
                await client.write_gatt_char(CHAR_UUID, b"Hello from PC!")
                response = await client.read_gatt_char(CHAR_UUID)
                messagebox.showinfo("Received", f"Phone says: {response.decode()}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        asyncio.run(run_send())
    threading.Thread(target=worker).start()

# GUI
root = tk.Tk()
root.title("Bluetooth Communication")

tk.Button(root, text="Scan Devices", command=scan_devices).pack(pady=5)
listbox = tk.Listbox(root, width=50)
listbox.pack(pady=5)
tk.Button(root, text="Connect", command=connect_device).pack(pady=5)
tk.Button(root, text="Send Message", command=send_message).pack(pady=5)

root.mainloop()
