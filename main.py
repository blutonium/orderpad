import sys
import json
import argparse
import os
from collections import namedtuple
import mido
from thekensql import ThekenSQL
import time

configfile = 'config.json'
sqlconfigfile = 'sql.json'

def led_off(note):
    return mido.Message('note_on', note=note, velocity=0)


def led_green(note):
    return mido.Message('note_on', note=note, velocity=1)


def led_green_blink(note):
    return mido.Message('note_on', note=note, velocity=2)


def led_red(note):
    return mido.Message('note_on', note=note, velocity=3)


def led_red_blink(note):
    return mido.Message('note_on', note=note, velocity=4)


def led_yellow(note):
    return mido.Message('note_on', note=note, velocity=5)


def led_yellow_blink(note):
    return mido.Message('note_on', note=note, velocity=6)

class APCMini:
    def __init__(self, sqldb):
        self.opened = False
        self.config = None
        self.sqldb = sqldb

    def send(self, msg):
        self.midoOut.send(msg)

    def playAnimation(self):
        t = 0.15

        for note in range(0, 99):
            self.send(led_off(note))

        for note in range(63, 0, -1):
            self.send(led_red(note))

            if note + 1 <= 63:
                self.send(led_yellow(note + 1))

            if note + 2 <= 63:
                self.send(led_green(note + 2))

            time.sleep(t)

    def __searchfordevice(self, devicepart):
        print('Scanning for devices...')
        availableports = mido.get_input_names()
        for port in availableports:
            if devicepart in port:                
                print('Found device:', port)
                return port
        return None           

    def open(self, devicepart):
        if not self.opened:
            self.device = self.__searchfordevice(devicepart)
            if self.device:
                self.midoIn = mido.open_input(self.device)
                self.midoOut = mido.open_output(self.device)
                if self.midoIn and self.midoOut:                    
                    self.opened = True

        return self.opened                

    def readFromDevice(self):
        if self.opened:
            while True:
                msg = self.midoIn.receive()
                if (msg.type == 'note_off'):
                    return msg

    def load(self):
        if os.path.isfile(configfile):
            with open(configfile) as json_file:
                print('Loaded')
                config = json.load(json_file)
                self.config = {}
                for k, v in config.items():
                    self.config[int(k)] = v

                return True 

        return False


    def save(self):
        yn = input('Save? [Y/N]')    
        if yn.lower() == 'y':
            with open(configfile, "w") as json_file:
                json_file.write(json.dumps(self.config, indent=2))
            print('Saved to', configfile)

    def setButtonColor(self, note, default):
        if self.config and note in self.config:
            d = self.config[note]
            min_age = d['min_age']
            if min_age >= 18:
                self.send(led_red(note))
            elif min_age >= 16:
                self.send(led_green(note))
            else:
                self.send(led_yellow(note))
        else:
            self.send(default)    

    def colorButtons(self):
        for note in range(63, 0, -1):
            self.setButtonColor(note, led_off(note))

    def configure(self, products):
        if not self.config: 
            self.config = dict()
        changed = False

        # delete old crap from the configuration in case a product got deleted
        # also update stuff
        keys_to_delete = []
        for k, d in self.config.items():
           product_id = d['product_id']
           if product_id in products:
               if not 'min_age' in d or products[product_id]['min_age'] != d['min_age']:
                   d['min_age'] = products[product_id]['min_age']
                   changed = True
           else:
               keys_to_delete.append(k)

        if len(keys_to_delete) > 0:
           changed = True
           for k in keys_to_delete:
               del self.config[k]

        self.colorButtons()
        if self.opened:
            for product in products.values():
                skip = False
                for d in self.config.values():
                    # ugly
                    if product['product_id'] == d['product_id']:
                        skip = True
                        break

                if not skip:
                    print('Press Button for "{} ({}l)"'.format(product['name'], product['liter']))
                    msg = self.readFromDevice()
                    if msg:
                        print('Mapping {} (ID:{}) -> {}'.format(product['name'], product['product_id'], msg.note))
                        changed = True
                        d = {
                            'name': product['name'],
                            'product_id': product['product_id'],
                            'id': msg.note,
                            'min_age': product['min_age']  
                        }
                        self.config[msg.note] = d             
                        self.setButtonColor(msg.note, led_off(msg.note))
        if changed:
            self.save()

    def run(self):
        while True:
            msg = self.readFromDevice()
            if msg:
                print('Pressed', msg.note)
                if msg.note in self.config:
                    print('Button', self.config[msg.note]['name'], 'pressed')
                    self.sqldb.addOrder(self.config[msg.note]['product_id'])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parses stuff from the APC Mini')
    parser.add_argument('device', action='store', nargs='?', type=str, help='device to open')
    parser.add_argument('clientid', action='store', nargs='?', type=int, help='clientid to use')
    parser.add_argument('--list-devices', dest='listdevices', action='store_true',
                        help='Print MIDI devices')

    args = parser.parse_args()

    if args.listdevices:
        devices = mido.get_input_names()
        if len(devices) > 0:
            print('Devices:')
            for device in devices:
                print(device)
        exit(0)

    if not args.clientid or not args.device:
        parser.print_help()
        exit(1)

    device = args.device
    midiid = args.clientid

    sql = ThekenSQL(midiid)
    if not sql.load(sqlconfigfile):
        sql.host = input('SQL Hostname: ')
        sql.user = input('SQL Username: ')
        sql.passwd = input('SQL Password: ')
        sql.database = input('SQL Database: ')
        sql.save(sqlconfigfile)        

    if sql.connect():
        products = sql.fetchProducts()
            
        apcmini = APCMini(sql)
        if apcmini.open(device):

            # play some shitty animation
            apcmini.playAnimation()

            # load config
            apcmini.load()

            # checks for changes of products.
            apcmini.configure(products)
            
            # Set color of all buttons accordingly
            apcmini.colorButtons()

            print('Running...')
            apcmini.run()
        else:
            print('Device not found')
