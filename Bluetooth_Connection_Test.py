import bluetooth
from time import sleep

# Pair HC-05 with PC first
# TODO add try catch statement for OSError when board is powered off to auto-reconnect
# TODO investigate multithreading/REST interfaces to allow streaming commands to multiple machines
# TODO see if we can connect to HC-05's without passwords disabled, not vital
target_name = "HC-05"
target_address = None

nearby_devices = bluetooth.discover_devices()
print(nearby_devices)

for bdaddr in nearby_devices:
    print(bluetooth.lookup_name(bdaddr))
    if target_name == bluetooth.lookup_name(bdaddr):
        target_address = bdaddr
        break

if target_address is not None:
    print("found target bluetooth device with address ", target_address)
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

    print("Trying connection")

    i = 0  # Your port range starts here
    maxPort = 3  # Your port range ends here
    err = True
    while err and i <= maxPort:
        print("Checking Port ", i)
        port = i
        try:
            sock.connect((target_address, port))
            err = False
        except Exception as e:
            # Print the exception if you like
            i += 1
    if i > maxPort:
        print("Port detection Failed.")
        exit(0)

    print("Trying sending")
    while True:
        sock.send("Challenge\n")
        sleep(4)
    print("Finished sending")
    print(sock.recv(1024))
    print("Finished receiving")
    sock.close()
else:
    print("could not find target bluetooth device nearby")
