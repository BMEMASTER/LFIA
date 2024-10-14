#!/usr/bin/python3
import os
import time
device_file ='/sys/bus/w1/devices/28-00000e2413fc/w1_slave'

def read_temp_raw():
    #try:
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    #except:
        #print("ds18b20 is None")
        #return None
    return lines

def read_temp():
    lines = read_temp_raw()
    #print(lines[0].strip()[-3:] != 'YES')
    pre_lines = ['09 02 4b 46 7f ff 07 10 f8 : crc=f8 YES\n', '09 02 4b 46 7f ff 07 10 f8 t=38.6\n']
    #lines =['09 02 4b 46 7f ff 07 10 f8 11 22 : crc=f7 YErS\n', '09 02 4b 46 7f ff 07 10 f8 t=11222\n']
    #if lines == None:
        #return None
    if lines[0].strip()[-3:] == 'YES':
        pre_lines = lines
    #while lines[0].strip()[-3:] != 'YES':
        #print(lines[0].strip()[-3:] != 'YES')
        #time.sleep(0.1)
        #lines = read_temp_raw()
    lines = pre_lines
    equals_pos = lines[1].find('t=')
    #print(equals_pos)
    temp_c = 80
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        #print(lines[1][-5:])
        #temp_string = lines[1].strip()[-5:]
        #print(temp_string.find('='))
        if temp_string.find('=')!=-1:
            pass
        else:
            temp_c = float(temp_string)/1000.0
            
    return temp_c

if __name__ == '__main__':
    temp = read_temp()
    if temp == None:
        print("sensor not connected!")
    else:
        while True:
            print('温度:%2.2f'%read_temp())
            time.sleep(1)
