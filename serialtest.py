
import wiringpi as wipi
import time
import requests

serial = wipi.serialOpen('/dev/serial0', 9600)

newLine = False

upc_code = ""

def api_call(upc):
	call_str = "https://api.barcodelookup.com/v2/products?barcode={}&formatted=y&key={}"
	api_key = ""
	with open('api_key.txt', 'r') as f:
		api_key = f.read().strip()
	call_str = call_str.format(upc,api_key)
	response = requests.get(call_str, )
	with open('serialOutput.pdf', 'wb') as f:
		f.write(response.content)
		


while True:
	while wipi.serialDataAvail(serial) != 0:
		data = chr(wipi.serialGetchar(serial)) 
		upc_code += data.strip()
		if(wipi.serialDataAvail(serial) == 0):
			print(upc_code)
			api_call(upc_code)	

	time.sleep(1)	

