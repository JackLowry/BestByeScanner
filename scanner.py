
import wiringpi as wipi
import time
import requests
import os
import glob
from bluetooth import *
import time
import json

serial = wipi.serialOpen('/dev/serial0', 9600)

newLine = False

curr_items = []

upc_code = ""

def api_call(upc):
	call_str = "https://api.barcodelookup.com/v2/products?barcode={}&formatted=y&key={}"
	api_key = ""
	with open('api_key.txt', 'r') as f:
		api_key = f.read().strip()
	call_str = call_str.format(upc,api_key)
	response = requests.get(call_str, ).json()
	response["scan_date"] =  time.time()
	with open('products/{}.pdf'.format(upc), 'w+b') as f:
		json.dump(response,f)
		

for filename in os.listdir('products/'):
    curr_items.append(filename[:len(filename)-4])

print(curr_items)

server_sock=BluetoothSocket( RFCOMM )
server_sock.bind(("",PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]

uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

advertise_service( server_sock, "AquaPiServer",
                   service_id = uuid,
                   service_classes = [ uuid, SERIAL_PORT_CLASS ],
                   profiles = [ SERIAL_PORT_PROFILE ] 
#                   protocols = [ OBEX_UUID ] 
                    )
while True:

	print "Waiting for connection on RFCOMM channel %d" % port

	client_sock, client_info = server_sock.accept()
	print "Accepted connection from ", client_info

	try:
	        data = client_sock.recv(1024)
        	if len(data) == 0: break
	        print "received [%s]" % data

		if data == 'temp':
			data = str(read_temp())+'!'
		elif data == 'lightOn':
			GPIO.output(17,False)
			data = 'light on!'
		elif data == 'lightOff':
			GPIO.output(17,True)
			data = 'light off!'
		else:
			data = 'WTF!' 
	        client_sock.send(data)
		print "sending [%s]" % data

	except IOError:
		pass

	except KeyboardInterrupt:

		print "disconnected"

		client_sock.close()
		server_sock.close()
		print "all done"

		break
	while wipi.serialDataAvail(serial) != 0:
		data = chr(wipi.serialGetchar(serial)) 
		upc_code += data.strip()
		if(wipi.serialDataAvail(serial) == 0):
			if(upc_code in curr_items):
				curr_items.remove(upc_code)
				os.remove("products/" + upc_code + ".pdf")
				print(upc_code + " removed!")
			else:
				print("Adding " + upc_code)
				curr_items.append(upc_code)
				api_call(upc_code)
			upc_code = ""
	time.sleep(1)

