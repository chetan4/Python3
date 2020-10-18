import numpy as np
import cv2
import sys 
import os
import platform
import urllib.request
import time
import calendar
import dropbox
from   dropbox.exceptions import ApiError, AuthError
import _thread 
import paho.mqtt.client as mqtt
import datetime

####################################################

# MQTT - credentials (just edit your "user" and "passwd")
'''
I am using "www.maqiatto.com" online MQTT broker for my project.
Please add the Topic for your require project in following manner
as shown.
'''

sub_topic = "<your registered email id with www.maqiatto.com>/TX" 
pub_topic = "<your registered email id with www.maqiatto.com>/RX" 
 
broker  = "maqiatto.com"	# Keep as it is
port    = 1883				# Keep as it is 

user    = "<your registered email id with www.maqiatto.com>"
passwd  = "<your registered email id Password with www.maqiatto.com>"

# Dropbox Authorisation token
TOKEN = '<your DROPBOX authentication key>'

# Dropbox Path 
DROPBOX_PATH = '/ImageTransferBetweenPi/'  #Edit this for your dropbox app folder
####################################################  

nameOfImage = ""

global_my_ip_camera_url = "http://192.168.1.103:8080/shot.jpg" 
global_width = 800
global_height = 600
global_video_device = 0
global_frame_from_ip_camera = True

platform = ""
platforms = {
            'linux1' : 'Linux',
            'linux2' : 'Linux',
            'darwin' : 'OS X',
            'win32'  : 'Windows'
            }

if sys.platform not in platforms:
    platform = sys.platform
else:
    platform = platforms[sys.platform]
    pass

if platform == 'Windows':
    nameOfImage = os.getcwd() + "\\Download\\welcome.jpeg"
else:
    nameOfImage = os.getcwd() + "/Download/welcome.jpeg"
    pass

# Format photo will be saved as e.g. jpeg
PHOTOFORMAT = 'jpeg' 

LOCAL_PATH = ""

if platform == 'Windows':
    LOCAL_PATH = os.getcwd() + "\\Download\\" 
    global_image_path = '\\Images\\'
else:
    LOCAL_PATH = os.getcwd() + "/Download/"    
    global_image_path = os.getcwd() + 'Images/'
    pass


clients = mqtt.Client()


# The callback for when the client receives a CONNACK response from the server.
def on_connect(clients, userdata, flags, rc):
    #print("Connected with result code "+str(rc))
    clients.subscribe(sub_topic)  #topic   = "TX"

# The callback for when a PUBLISH message is received from the server.
def on_message(clients, userdata, msg):
    global nameOfImage
    
    #print(msg.topic+" "+str(msg.payload))    
    str_rec = str(msg.payload, 'UTF-8') 
    if downloadDropboxFile(str_rec, LOCAL_PATH) == True:        
        nameOfImage = LOCAL_PATH + str_rec    
        print("New Image Recevied = " + str_rec)
        notifySenderOfImage("Following " + str_rec + " Image was Revceived." )
        pass
    pass

def subscribeThread(i_info):    
    clients.on_connect = on_connect
    clients.on_message = on_message
    clients.username_pw_set(user, passwd)
    clients.connect(broker, port)    
    clients.loop_forever()
    

def notifySenderOfImage(i_message): 
    try: 
        clientp = mqtt.Client()
        clientp.username_pw_set(user, passwd)
        clientp.connect(broker, port)
        clientp.publish(pub_topic, i_message)  
        clientp.disconnect() 
    except Exception as e:
        print("Error sending message:\n" + "Actual error = " + str(e))
        return  False
    return True


# Create two threads as follows
try:
    _thread.start_new_thread( subscribeThread, ("subscribeThread",) ) 
except Exception as e:
    print ("Error: unable to start thread")
    print ("\nError = " + str(e))

#Dropbox function    ========== Start ===========

 

##############User  function################## 
def downloadDropboxFile(i_dropbox_file, i_local_path):
    try:
        dbx = dropbox.Dropbox(TOKEN)
        new_file_name = i_local_path + i_dropbox_file
        print("New file name = " + new_file_name )
        with open(new_file_name , "wb") as f:
            metadata, res = dbx.files_download(path= DROPBOX_PATH + i_dropbox_file)
            f.write(res.content)
        print("File was downloaded")
    except Exception as e:
        print("Error Downloading file:\n" + str(e))
        return  False
    return  True

def getTime():    
    return  '{:%m/%d/%y %I:%M %S %p}'.format(datetime.datetime.today())


##############################################
#Dropbox function   ========== Ends ===========


####################################################

WINDOW_NAME  = 'Image Received From Source Pi'  
    
def main():
    global nameOfImage
    
    oldNameOfImage = ""
    # font 
    font = cv2.FONT_HERSHEY_SIMPLEX  
    # org 
    org = (50, 50)   
    # fontScale 
    fontScale = 1   
    # Blue color in BGR 
    color = (0, 150, 0)   
    # Line thickness of 2 px 
    thickness = 2
    
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    cv2.setWindowTitle(WINDOW_NAME, 'Click "Q or Esc" to Quit.') 
    
    while True:
        try:
            img = cv2.imread(nameOfImage, cv2.IMREAD_COLOR)
            img = cv2.putText(img,"Today : " + getTime(), org, font,  
                              fontScale, color, thickness, cv2.LINE_AA)       
            cv2.imshow(WINDOW_NAME, img)
        except:
            pass        

        buttonPressed = cv2.waitKey(1)        
        if  buttonPressed == 27:
            ## Terminate the Program
            break 
    cv2.destroyAllWindows() 


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally: 
        print ("\n\nProgram terminated...")
        pass

    
