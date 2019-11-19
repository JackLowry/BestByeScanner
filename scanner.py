
import wiringpi as wipi
import time
import requests
import os
import glob
from bluetooth import *
import time
import json
import thread

def bluetooth_server():
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
        
def api_call(upc):
    call_str = "https://api.barcodelookup.com/v2/products?barcode={}&formatted=y&key={}"
    api_key = ""
    with open('api_key.txt', 'r') as f:
        api_key = f.read().strip()
    call_str = call_str.format(upc,api_key)
    response = requests.get(call_str, ).json()
    response["scan_date"] =  time.time()
    response["quant"] = 1
    with open('products/{}'.format(upc), 'w+b') as f:
        json.dump(response,f)
        
def parse_json(upc):
    with open('products/' + upc) as f:
        return json.load(f)

        
def remove_item(upc_code):
    curr_items.remove(upc_code)
    if os.path.exists('products/' + upc_code):
        item = parse_json(upc_code)
        if(item["quant"] > 1):
            item["quant"] -= 1
            os.remove("products/" + upc_code)
            with open('products/{}'.format(upc_code), 'w+b') as f:
                json.dump(item,f)
        else:
            os.remove("products/" + upc_code)
    print(upc_code + " removed!")

def add_item(upc_code):
    print("Adding " + upc_code)
    if os.path.exists('products/' + upc_code):
        item = parse_json(upc_code)
        item["quant"] += 1
        os.remove("products/" + upc_code)
        with open('products/{}'.format(upc_code), 'w+b') as f:
                json.dump(item,f)
    else:
        api_call(upc_code)
    curr_items.append(upc_code)

thread.start_new_thread(bluetooth_server, ())

serial = wipi.serialOpen('/dev/serial0', 9600)

newLine = False

curr_items = []

upc_code = ""

for filename in os.listdir('products/'):
    item = parse_json(filename)
    for i in range(0, item["quant"]):
        curr_items.append(filename)

print(curr_items)

remove_cd = 3
remove_upc = None
while True:
    if(remove_cd > 0):
        remove_cd -= 1
    elif(remove_upc is not None and remove_cd == 0):
        add_item(remove_upc)
        remove_upc = None
    while wipi.serialDataAvail(serial) != 0:
        data = chr(wipi.serialGetchar(serial)) 
        upc_code += data.strip()
        if(wipi.serialDataAvail(serial) == 0):
            if(upc_code in curr_items):
                if(remove_upc is not None):
                    remove_item(remove_upc)
                    remove_upc = None
                    remove_cd = 0
                else:
                    remove_cd = 5
                    remove_upc = upc_code
            else:
                add_item(upc_code)
                
            upc_code = ""           
    time.sleep(1)
    print curr_items

