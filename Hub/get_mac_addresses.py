
import bluetooth

# Scan for nearby devices
print('Scanning for nearby devices')
nearby_devices = bluetooth.discover_devices()

# Printout all found devices
for bluetooth_device_address in nearby_devices:
    print(bluetooth.lookup_name(bluetooth_device_address), bluetooth_device_address)

