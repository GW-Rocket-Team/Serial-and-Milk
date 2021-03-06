from ast import literal_eval # For interpreting module data
from time import sleep       # For delays

import serial                # For reading in a serial device
import pynmea2               # For reading NMEA 0183 sentences
import multiprocessing       # For multiprocessing in Python
import logging

from Tkinter import *
import tkMessageBox

com_queue = multiprocessing.Queue()

def do_nothing():
    pass

def print_nmea(telemetry):
    print "Latitude: {}".format(telemetry.latitude)
    print "Longitude: {}".format(telemetry.longitude)
    print "Altitude: {}\n".format(telemetry.altitude)

logging.basicConfig(filename='telemetry.log', format='%(asctime)s %(message)s', level=logging.DEBUG)
logging.debug("-------------- Start of Log -----------------------")

def read_com_port(com_port, com_queue):
    if (com_port == "---"):
        with serial.Serial(com_port, baudrate = 9600, timeout = 0.5) as ser:
            
            # Flushing any prior content within serial buffers
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            # Getting rid of weird looking data
            for i in range(10):
                ser.readline()
                
            while True:
                try:
                    if (ser.isOpen() == False):
                        ser.open()
                        
                        raw_sentence = ser.readline().decode('ascii', errors = 'replace') # Reads serial data
                        
                        telemetry = pynmea2.parse(raw_sentence) # Parses data
                        
                        while not com_queue.empty():
                            com_queue.get_nowait()
                            
                        com_queue.put(telemetry)
                        
                        logging.info("%s\n", telemetry)
                except Exception as e:
                    print e
                    ser.close()                # Closes the serial port

def read_from_queue():
    passes = 0
    
    while com_queue.empty() and (passes < 1000):
        passes = passes + 1

    if passes == 1000:
        return None
    
    return com_queue.get()

def update_labels(nmea_var, time_var, lat_var, long_var, alt_var):
    telemetry = read_from_queue()

    if not telemetry == None:
        data_time = telemetry.timestamp
        
        nmea_var.set(telemetry)
        time_var.set(data_time.strftime("%X"))
        lat_var.set(telemetry.latitude)
        long_var.set(telemetry.longitude)
        alt_var.set(telemetry.altitude)

def load_nmea_gui(master, menubar):
    Label(master, text='Raw NMEA').pack(pady=5,padx=50)
    nmea_val = StringVar()
    Label(master, textvariable=nmea_val).pack(pady=5, padx=50)

    Label(master, text='Time Stamp').pack(pady=5,padx=50)
    time_val = StringVar()
    Label(master, textvariable=time_val).pack(pady=5, padx=50)

    Label(master, text='Latitude').pack(pady=5,padx=50)
    latitude_val = StringVar()
    Label(master, textvariable=latitude_val).pack(pady=5, padx=50)
    
    Label(master, text='Longitude').pack(pady=5,padx=50)
    longitude_val = StringVar()
    Label(master, textvariable=longitude_val).pack(pady=5, padx=50)
    
    Label(master, text='Altitude').pack(pady=5,padx=50)
    altitude_val = StringVar()
    Label(master, textvariable=altitude_val).pack(pady=5, padx=50)

    telemetry_menu = Menu(menubar, tearoff = 0)
    telemetry_menu.add_command(label = "Save Telemetry Log", command = do_nothing)
    menubar.add_cascade(label = "Telemetry", menu = telemetry_menu)

    master.after(100, update_labels, nmea_val, time_val, latitude_val, longitude_val, altitude_val)

if __name__ == '__main__':
    
    #com_port = raw_input("Enter a COM port to listen to: ")
    port_file = open("port.txt", "r")
    com_port = port_file.read()
    
    p = multiprocessing.Process(target=read_com_port, args=(com_port,com_queue,))
    p.start()
    
    master = Tk()
    master.title("Serial and Milk - Telemetry Mode")
    master.geometry("720x320")

    menubar = Menu(master)
    
    file_menu = Menu(menubar, tearoff = 0)
    file_menu.add_command(label = "New", command = do_nothing)
    file_menu.add_command(label = "Open", command = do_nothing)
    file_menu.add_command(label = "Save", command = do_nothing)
    file_menu.add_separator()
    file_menu.add_command(label = "Change Port", command = do_nothing)
    file_menu.add_separator()
    file_menu.add_command(label = "Exit", command = master.quit)

    help_menu = Menu(menubar, tearoff = 0)
    help_menu.add_command(label = "About", command = do_nothing)
    help_menu.add_command(label = "GitHub", command = do_nothing)
    
    menubar.add_cascade(label = "File", menu = file_menu)
    

    load_nmea_gui(master, menubar)

    menubar.add_cascade(label = "Help", menu = help_menu)
    master.config(menu = menubar)
   
    master.mainloop()

    # Handling closing multiprocessing stuff
    com_queue.close()
    com_queue.join_thread()
    p.terminate()
