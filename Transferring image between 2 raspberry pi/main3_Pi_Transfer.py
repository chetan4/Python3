import numpy as np
import cv2
import sys
import os
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

sub_topic = "<your registered email id with www.maqiatto.com>/RX" 
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


####################################################

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

###################################################### 




# Format photo will be saved as e.g. jpeg
PHOTOFORMAT = 'jpeg'


global_image_path = 'Images/'
global_my_ip_camera_url = "http://192.168.1.103:8080/shot.jpg" 
global_width = 800
global_height = 600
global_video_device = 0
global_frame_from_ip_camera = False

LOCAL_PATH = ""

if platform == 'Windows':
    LOCAL_PATH = os.getcwd() + "\\Download\\" 
    global_image_path = os.getcwd() + '\\Images\\'
else:
    LOCAL_PATH = os.getcwd() + "/Download/"    
    global_image_path = os.getcwd() + '/Images/'
    pass


clients = mqtt.Client()


# The callback for when the client receives a CONNACK response from the server.
def on_connect(clients, userdata, flags, rc):
    #print("Connected with result code "+str(rc))
    clients.subscribe(sub_topic)  #topic   = "TX"

# The callback for when a PUBLISH message is received from the server.
def on_message(clients, userdata, msg):
    #print(msg.topic+" "+str(msg.payload))    
    str_rec = str(msg.payload, 'UTF-8')
    print("Message From Receiver: = " + str_rec)    
    pass

def subscribeThread(i_info):    
    clients.on_connect = on_connect
    clients.on_message = on_message
    clients.username_pw_set(user, passwd)
    clients.connect(broker, port)    
    clients.loop_forever()
    

def notifyDestinationPi2(i_image_name):
    #i_image_name = "grape_rot.jpg" 
    try: 
        clientp = mqtt.Client()
        clientp.username_pw_set(user, passwd)
        clientp.connect(broker, port)
        clientp.publish(pub_topic, i_image_name )  
        clientp.disconnect() 
    except Exception as e:
        print("Error sending image name to DestinationPi2!\n" + "Actual error = " + str(e))
        return  False
    return True


# Create two threads as follows
try:
    _thread.start_new_thread( subscribeThread, ("subscribeThread",) ) 
except Exception as e:
    print ("Error: unable to start thread")
    print ("\nError = " + str(e))


# Upload localfile to Dropbox
def uploadFileToDropbox(i_img_name_with_path, i_image_name):

    err_flag = False

    # Check that access tocken added
    if (len(TOKEN) == 0):
        sys.exit("ERROR: Missing access token. "
                 "try re-generating an access token from the app console at dropbox.com.")
        err_flag = True    

    # Create instance of a Dropbox class, which can make requests to API
    #print("Creating a Dropbox object...")
    dbx = dropbox.Dropbox(TOKEN)

    # Check that the access token is valid
    try:
        dbx.users_get_current_account()
    except AuthError as err:
        sys.exit("ERROR: Invalid access token; try re-generating an "
                 "access token from the app console at dropbox.com.")
        err_flag = True

    # Specify upload path
    uploadPath = DROPBOX_PATH + i_image_name    

    # Read in file and upload
    with open(i_img_name_with_path, 'rb') as f:
        #print("Uploading " + i_image_name + " to Dropbox as " + uploadPath + "...")

        try:
            dbx.files_upload(f.read(), uploadPath)
        except ApiError as err:
            # Check user has enough Dropbox space quota
            if (err.error.is_path() and
                    err.error.get_path().error.is_insufficient_space()):
                sys.exit("ERROR: Cannot upload; insufficient space.")
                err_flag = True
            elif err.user_message_text:
                print(err.user_message_text)
                sys.exit()
                err_flag = True
            else:
                print(err)
                sys.exit()
                err_flag = True
    if err_flag == True:
        return    False
    else:
        return    True


def sendToDestinationPi2(i_img_nme_wit_path, i_image_path, i_image_name):
    
    if uploadFileToDropbox(i_img_nme_wit_path, i_image_name) == True:
        print("Image has been uploaded...")
        
        if notifyDestinationPi2(i_image_name) == True:
            return  True
        else:
            return  False
        
    else:
        return  False
    
# Delete file
def deleteLocal(file): 
    os.remove(file)
    #print("File: " + file + " deleted ...")

##############User  function##################

def getImageFrameFromIPCamera(your_ip_camera_url):
    # Use urllib to get the image from the IP camera
    #imgResp = urllib.urlopen(your_ip_camera_url)
    imgResp = urllib.request.urlopen(your_ip_camera_url)
    
    # Numpy to convert into a array
    imgNp = np.array(bytearray(imgResp.read()), dtype=np.uint8)
    
    # Finally decode the array to OpenCV usable format ;) 
    img = cv2.imdecode(imgNp,-1)    

    return True, img


##############################################


WINDOW_NAME  = 'Transfer Image using IOT between Pi'

cap = None

if global_frame_from_ip_camera == False:
    cap = cv2.VideoCapture(global_video_device)
    pass

    
def main():    

    global global_frame_from_ip_camera
    global global_image_path
        
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    cv2.setWindowTitle(WINDOW_NAME, 'Click "C" to take photo...')

    i = 0
    ret_val = None
    frame = None
    
    while True:

        if global_frame_from_ip_camera == False:
            ret_val, frame = cap.read()
        else:
            ret_val, frame = getImageFrameFromIPCamera(global_my_ip_camera_url)
            pass
          
        frame = cv2.resize(frame, (global_width, global_height))        
        
        if not ret_val:
            print('Camera capturing fails...exiting')
            break
        
        cv2.imshow(WINDOW_NAME, frame)

        buttonPressed = cv2.waitKey(1)
        
        if  buttonPressed == 27:
            ## Terminate the Program
            break
        
        if buttonPressed == ord('c') or buttonPressed == ord('C'):
             
            
            ts = calendar.timegm(time.gmtime())
            
            nameOfImage = "image_capture_" + str(ts) + "_" + str(i) + ".jpeg"
            
            image_name_with_path = global_image_path + nameOfImage
            cv2.imwrite(image_name_with_path, frame)
            
            #print(" Image save with name " + nameOfImage + "in folder " + global_image_path)
            
            if sendToDestinationPi2(image_name_with_path, global_image_path, nameOfImage) == True:
                print("Image sent successfully to Receiver Pi...")
            else:
                print("Error sending Image to Receiver Pi!")
                pass
            
            i = i + 1
            
            deleteLocal(image_name_with_path)

    cv2.destroyAllWindows()
    if global_frame_from_ip_camera == False: 
        cap.release()
        pass
    pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally: 
        cv2.destroyAllWindows() 
        print ("\n\nProgram terminated...")
        pass

    
