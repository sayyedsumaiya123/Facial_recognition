import cv2
from time import time
from PIL import Image
from tkinter import messagebox
import os
import firebase_admin
from firebase_admin import credentials, storage

# Initialize Firebase with your service account key
cred = credentials.Certificate("home-security-dce26-firebase-adminsdk-bp0es-ab0f47e5cd.json")  # Replace with the path to your JSON key
firebase_admin.initialize_app(cred, {
    'storageBucket': 'home-security-dce26.firebasestorage.app'  # Replace with your Firebase storage bucket
})

def download_xml(name):
    """
    Downloads an XML file from Firebase Storage and saves it as {name}_classifier.xml.

    Args:
        name (str): The prefix for the downloaded file's name.
    """
    # File name in Firebase Storage
    file_name = f'{name}/{name}_classifier.xml'  # Example: 'files/example.xml'

    # Local destination to save the downloaded file with the given name
    local_destination = f"data/classifiers/{name}_classifier.xml"

    try:
        # Access the storage bucket
        bucket = storage.bucket()

        # Get the file object   
        blob = bucket.blob(file_name)

        # Download the file
        blob.download_to_filename(local_destination)
        print(f"File downloaded successfully to: {local_destination}")
    except Exception as e:
        print(f"An error occurred: {e}")



def main_app(name, timeout = 5):
    
        download_xml(name)
        
        face_cascade = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(f"data/classifiers/{name}_classifier.xml")
        cap = cv2.VideoCapture(0)
        pred = False
        start_time = time()
        while True:
            ret, frame = cap.read()
            #default_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray,1.3,5)

            for (x,y,w,h) in faces:


                roi_gray = gray[y:y+h,x:x+w]

                id,confidence = recognizer.predict(roi_gray)
                confidence = 100 - int(confidence)
                if confidence > 50:
                    #if u want to print confidence level
                            #confidence = 100 - int(confidence)
                        pred = True
                        text = 'Recognized: '+ name.upper()
                        font = cv2.FONT_HERSHEY_PLAIN
                        frame = cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        frame = cv2.putText(frame, text, (x, y-4), font, 1, (0, 255, 0), 1, cv2.LINE_AA)
                       
                       
                else:   
                        pred = False
                        text = "Unknown Face"
                        font = cv2.FONT_HERSHEY_PLAIN
                        frame = cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                        frame = cv2.putText(frame, text, (x, y-4), font, 1, (0, 0,255), 1, cv2.LINE_AA)
                       
                        
            cv2.imshow("image", frame)

        
            elapsed_time = time() - start_time
            if elapsed_time >= timeout:
                print(pred)
                if pred:
                    messagebox.showinfo('Congrat', 'You have been recognized, ' + name)
                else:
                    messagebox.showerror('Alert', f'Not Recognized as {name}')
                break

            if cv2.waitKey(20) & 0xFF == ord('q'):
                break
        
        os.remove(f'data/classifiers/{name}_classifier.xml')
        
        cap.release()
        cv2.destroyAllWindows()
        
name = 'sums'
main_app(name)