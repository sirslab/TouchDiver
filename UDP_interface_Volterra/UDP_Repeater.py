import socket

import numpy
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import time
import pyformulas as pf

import matplotlib.pyplot as plt


from weartsdk import *
from weartsdk.WeArtCommon import HandSide, ActuationPoint, TextureType
import time
import logging

def cleanString(message):
    values_string = message.split('F')
    values_string = [item.replace(',', '.') for item in values_string]

    matrixOfValues_string = [s.split() for s in values_string]
    cleanedList = [lst for lst in matrixOfValues_string if lst]
    values = np.array(cleanedList)
    # remove_chars = ["\r", "\n", ";"]
    # cleaned_list = []
    # for s in values_string:
    #     for char in remove_chars:
    #         s = s.replace(char, "")
    #     cleaned_list.append(s)
    #     values_string = cleaned_list

    # values_string = [float(item.replace(',', '.')) for item in values_string]
    #print(values)

    values = values.astype(float)
    return values

if __name__ == '__main__':

    #### WEART INIT

    # Istantiate TCP/IP client to communicate with the Middleware
    client = WeArtClient(WeArtCommon.DEFAULT_IP_ADDRESS, WeArtCommon.DEFAULT_TCP_PORT, log_level=logging.INFO)
    client.Run()
    client.Start()

    # Listener to receive data status from Middleware
    mwListener = MiddlewareStatusListener()
    client.AddMessageListener(mwListener)

    # Calibration manager
    calibration = WeArtTrackingCalibration()
    client.AddMessageListener(calibration)
    # Start Calibration Finger tracking algorithm
    client.StartCalibration()

    # Wait for the result
    while (not calibration.getResult()):
        time.sleep(1)

    # Stop calibration
    client.StopCalibration()

    # Instantiate a HapticObject to provide actuations
    hapticObject_index = WeArtHapticObject(client)
    hapticObject_index.handSideFlag = HandSide.Right.value
    hapticObject_index.actuationPointFlag = ActuationPoint.Index# | ActuationPoint.Middle

    hapticObject_thumb = WeArtHapticObject(client)
    hapticObject_thumb.handSideFlag = HandSide.Right.value
    hapticObject_thumb.actuationPointFlag = ActuationPoint.Thumb  # | ActuationPoint.Middle

    # Create an effect with Temperatures, Force and Textures
    touchEffect_index = TouchEffect(WeArtTemperature(), WeArtForce(), WeArtTexture())
    touchEffect_thumb = TouchEffect(WeArtTemperature(), WeArtForce(), WeArtTexture())

    # Temperature properties
    temperature = WeArtTemperature()
    temperature.active = False
    temperature.value = 0.5
    # Force properties
    force = WeArtForce()
    force.active = False
    force.value = 0.0
    # Textures properties
    tex = WeArtTexture()
    tex.active = False
    tex.textureType = TextureType.TextileMeshMedium
    tex.textureVelocity = 0.5  # maximum value

    touchEffect_index.Set(temperature, force, tex)
    if (len(hapticObject_index.activeEffects) <= 0):
        hapticObject_index.AddEffect(touchEffect_index)  # Add effect if there is not any
    else:
        # Update the effect over time
        hapticObject_index.UpdateEffects()

    touchEffect_thumb.Set(temperature, force, tex)
    if (len(hapticObject_thumb.activeEffects) <= 0):
        hapticObject_thumb.AddEffect(touchEffect_thumb)  # Add effect if there is not any
    else:
        # Update the effect over time
        hapticObject_thumb.UpdateEffects()




    # Define the parameters
    local_ip = '0.0.0.0'  # Listen on all available network interfaces
    local_port = 8000  # The local port to listen on
    buffer_size = 2048  # Maximum buffer size for incoming data

    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the local IP and port
    udp_socket.bind((local_ip, local_port))

    print(f"Listening for UDP data on {local_ip}:{local_port}...")

    input("Press Enter to Start acquisition of 10 samples...")
    i = 0
    baseline = []
    while i < 10:
        #print(".")
        data, addr = udp_socket.recvfrom(buffer_size)
        received_message = data.decode('utf-8')
        values = cleanString(received_message)
        valuesAVG = np.mean(values, axis=1)
        if len(baseline):
            baseline = np.vstack([baseline, valuesAVG])
        else:
            baseline = valuesAVG
        i = i + 1
    #print(baseline)
    baselineAVG = np.mean(baseline, axis=0)
    input("Press Enter to Start ...")


    while True:
        # Receive data from the remote UDP server (returns data and the sender's address)
        data, addr = udp_socket.recvfrom(buffer_size)

        # Decode the data to a string (assuming UTF-8 encoding)
        received_message = data.decode('utf-8')

        # Print the received string and the sender's address
        # print("Received message: {received_message} from {addr}")

        values_ = cleanString(received_message)
        #valuesAVG = np.mean(values_, axis=1)

        normalizedCommand_ = abs(values_)*10
        #print(normalizedCommand_)

        normalizedCommand_index = normalizedCommand_[0][0]
        print("Index: ",  normalizedCommand_index)

        if len(normalizedCommand_)>1:
            normalizedCommand_thumb = normalizedCommand_[1][0]
            numberOfFingers = 2
            #print("2 FIngers")
            print("Thumb: ", normalizedCommand_thumb)

        else:
            numberOfFingers = 1
            #print("1 Finger")



        ##WEART

        force_index = WeArtForce()
        force_thumb = WeArtForce()
        force_index.active = True
        force_index.value = normalizedCommand_index

        touchEffect_index.Set(temperature, force_index, tex)
        if (len(hapticObject_index.activeEffects) <= 0):
            hapticObject_index.AddEffect(touchEffect_index)  # Add effect if there is not any
        else:
            hapticObject_index.UpdateEffects()



        if numberOfFingers == 2:
            force_thumb.active = True
            force_thumb.value = normalizedCommand_thumb

            touchEffect_thumb.Set(temperature, force_thumb, tex)
            if (len(hapticObject_thumb.activeEffects) <= 0):
                hapticObject_thumb.AddEffect(touchEffect_thumb)  # Add effect if there is not any
            else:
                hapticObject_thumb.UpdateEffects()

        #print(f"forza{force.value}")






    client.StopRawData()

    '''
    # Instantiate Analog Sensor raw data
    # This feature work just enabling the functionality from the Middleware
    # during this condition streaming the WeArtTrackingRawData doesn't work
    analogSensorData = WeArtAnalogSensorData(HandSide.Right, ActuationPoint.Index)
    client.AddMessageListener(analogSensorData)

    # Read sample analog sensor data
    ts = analogSensorData.GetLastSample().timestamp
    while ts == 0:
        time.sleep(1)
        ts = analogSensorData.GetLastSample().timestamp
    sample = analogSensorData.GetLastSample()
    print(sample)
    '''

    # Stop client and close the commnunication with the Middleware
    client.Stop()
    client.Close()
