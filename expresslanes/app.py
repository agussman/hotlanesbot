from chalice import Chalice, Rate

import requests
import json

import time
from multiprocessing import Process, Pipe

app = Chalice(app_name='expresslanes')

URL = "https://www.expresslanes.com/maps-api/get-ramps-price"

ENTRY_EXIT_JSON = "./data/entry_exit.json"

def load_entry_exits(json_file):
    with open(json_file) as f:
        return json.load(f)


# Automatically runs every 5 minutes
# The function you decorate must accept a single argument, which will be of type CloudWatchEvent.
@app.schedule(Rate(1, unit=Rate.MINUTES))
def periodic_task(event):
    print("Periodic Running...")
    return {"hello": "world"}


def get_ramps_price(ramp_entry, ramp_exit, conn):
    print("get_ramps_price()...")
    payload = {
        "ramp_entry": ramp_entry,
        "ramp_exit": ramp_exit
    }
    resp = requests.get(url=URL, params=payload)

    print("{} {}".format(resp.status_code, resp.url))

    conn.send(resp.content)
    conn.close()

    #data = json.loads(resp.content)
    
    #print("Got response: {}".format(data))
    

#fetch("https://www.expresslanes.com/maps-api/get-ramps-price?ramp_entry=217&ramp_exit=191", {"credentials":"include","headers":{"accept":"application/json, text/javascript, */*; q=0.01","accept-language":"en-US,en;q=0.9","cache-control":"no-cache","pragma":"no-cache","x-requested-with":"XMLHttpRequest"},"referrer":"https://www.expresslanes.com/map-your-trip","referrerPolicy":"no-referrer-when-downgrade","body":null,"method":"GET","mode":"cors"});


entry_exits = load_entry_exits(ENTRY_EXIT_JSON)

#print(entry_exits)

# create a list to keep all processes
processes = []

# create a list to keep connections
parent_connections = []


# Timing
_start = time.time()

for entry, exits in entry_exits.items():
    print(entry)
    for outpoint in exits:
        # create a pipe for communication
        parent_conn, child_conn = Pipe()
        parent_connections.append(parent_conn)

        #get_ramps_price(entry, outpoint)
        # create the process, pass instance and connection
        process = Process(target=get_ramps_price, args=(entry, outpoint, child_conn,))
        processes.append(process)


# start all processes
for process in processes:
    process.start()

# make sure that all processes have finished
for process in processes:
    process.join()

for parent_connection in parent_connections:
    data = json.loads(parent_connection.recv())    
    print("Got response: {}".format(data))

_end = time.time()

print("Execution time: {}".format(time.time() - _start))

# @app.route('/')
# def index():
#     return {'hello': 'world'}


# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#
