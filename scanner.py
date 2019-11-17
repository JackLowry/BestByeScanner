
import wiringpi as wipi
import time
import requests
import os
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

while True:
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

