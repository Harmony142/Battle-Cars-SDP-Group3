
import bluetooth

device_name = 'HC-06'

# Scan for nearby devices
print('Scanning for nearby devices named', device_name)
nearby_devices = bluetooth.discover_devices()

# Try and find our bluetooth module
print('Searching for our bluetooth module...')
for bluetooth_device_address in nearby_devices:
    print(bluetooth.lookup_name(bluetooth_device_address))
    if bluetooth.lookup_name(bluetooth_device_address) == device_name:
        print(bluetooth_device_address)
        break
