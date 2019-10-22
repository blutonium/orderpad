# orderpad
Python written program to use a mididevice as an orderpad, e.g. for a bar

# How does it work?
Program has to run on a system directly connected to the midi device. We use a raspberrypi.
You need a SQL server with two tables, products(product_id | name | min_age | liter | description | created_at) and orders(order_id | product_id | midi_client | created_at).

To show all connected midi devices, use "python main.py --list-devices". To run the program you have to start main.py with the argument "device name", like in run.sh.

On the first launch, the program will pull all products from sql products table and ask you to press a button for every product. On this way you do the mapping of the products to the buttons of your midi device.
After every product is configured, the program will start and write an entry in the "orders" table when you press a button.
To use multiple midi devices you have to start multiple instances of the program, for example in the run.sh.
Please be sure that every device will use the same config file.

To reconfigure the mapping, simply delete the config.json file.

Credits to Luca.
