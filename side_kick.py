import os
import shutil
import cv2
from firebase_admin import storage
import datetime
from flask import jsonify
import numpy as np


def append_history(name):
    filename = 'Urusa Shaikh/timestamps/access_history.txt'
    local_path = 'data/access_history.txt'

    if not download_file_from_firebase(filename, local_path):
        return jsonify({'error': 'Cannot download access_history.txt'}), 400
    
    # Append the new data to the history file
    with open(local_path, 'a') as file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"\nName : {name}\t Time : {timestamp}")

    # Check if the file was updated correctly
    print(f"File content after update:\n{open(local_path, 'r').read()}")

    # Ensure that the file exists locally and is ready to be uploaded
    if os.path.exists(local_path):
        print(f"File exists locally: {local_path}")

        # Upload the file to Firebase Storage
        upload_paths = [f"{filename}"]  # Firebase path to upload the file
        if upload_file([local_path], upload_paths):
            print(f"✅ File uploaded to Firebase Storage: {filename}")
            return jsonify({"status": "success", "message": "History updated and uploaded successfully!"}), 200
        else:
            print(f"Error uploading file to Firebase.")
            return jsonify({"status": "failure", "message": "Failed to upload the file"}), 500
    else:
        print(f"File does not exist at {local_path}")
        return jsonify({"status": "failure", "message": "Local file not found"}), 400
        


def download_file_from_firebase(file_name,local_destination):
    # File name in Firebase Storage
    # file_name = f'{name}/{name}_classifier.xml'  # Example: 'files/example.xml'

    # # Local destination to save the downloaded file with the given name
    # local_destination = f"data/classifiers/{name}_classifier.xml"

    try:
        # Access the storage bucket
        bucket = storage.bucket()

        # Get the file object
        blob = bucket.blob(file_name)

        # Download the file
        blob.download_to_filename(local_destination)
        print(f"File downloaded successfully to: {local_destination}")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

# Upload file to Firebase Storage
def upload_file(file_paths, upload_paths):
    try:
        for file_path, upload_path in zip(file_paths, upload_paths):
            bucket = storage.bucket()
            blob = bucket.blob(upload_path)
            blob.upload_from_filename(file_path)
            print(f"✅ File uploaded to {upload_path}")
    except Exception as e:
        print(f"Error uploading file: {e}")
        return False
    return True

# Capture images using the webcam
def start_capture(name):
    # Check if person is already registered
    with open('nameslist.txt', 'r') as file:
        if name in file.read():
            print(f'{name} already exists')
            return -1
        else:
            with open('nameslist.txt', 'a') as file:
                file.write(f'{name} ')
    
    path = "./data/" + name
    num_of_images = 0
    detector = cv2.CascadeClassifier("./data/haarcascade_frontalface_default.xml")

    try:
        os.makedirs(path)
    except:
        print('Directory Already Created')

    vid = cv2.VideoCapture(0)
    while True:
        ret, img = vid.read()
        new_img = None
        grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face = detector.detectMultiScale(image=grayimg, scaleFactor=1.1, minNeighbors=5)

        for x, y, w, h in face:
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 0), 2)
            cv2.putText(img, "Face Detected", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255))
            cv2.putText(img, str(str(num_of_images) + " images captured"), (x, y+h+20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255))
            new_img = img[y:y+h, x:x+w]
        
        cv2.imshow("Face Detection", img)
        key = cv2.waitKey(1) & 0xFF

        try:
            if new_img is not None:
                cv2.imwrite(str(path + "/" + str(num_of_images) + name + ".jpg"), new_img)
                num_of_images += 1
        except Exception as e:
            print(f"Error saving image: {e}")
            pass

        if key == ord("q") or key == 27 or num_of_images >= 300:  # Capture up to 10 images
            break

    cv2.destroyAllWindows()
    return num_of_images

def make_details(user_details):
    name, age, gender = user_details
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"name: {name}\nage: {age}\ngender: {gender}\ntime of register: {timestamp}"
    
    filename = f"data/details/{name}_info.txt"
    with open(filename, "w") as file:
        file.write(content)
    print(f"✅ File '{filename}' created successfully.")
    return filename

def update_details(user_details):
    name, age, gender = user_details
    try:
        with open(f'data/details/{name}_info.txt', 'r') as file:
            data = file.read()  # Read the entire file content

        # Replace the age and gender in the file content
        data = data.replace(f'age: {data.split("age: ")[1].split()[0]}', f'age: {age}')
        data = data.replace(f'gender: {data.split("gender: ")[1].split()[0]}', f'gender: {gender}')

        updated_file_path = f'data/details/{name}_info.txt'
        with open(updated_file_path, 'w') as file:
            file.write(data)  # Write the updated data back to the file
        
        print(f"✅ Details updated successfully for {name}")
        return updated_file_path  # Return the updated file path
    
    except Exception as e:
        print(f"Error updating details for {name}: {e}")
        return None
    
def delete_local_files(name, files):
    for file in files:
        os.remove(file)
    shutil.rmtree(os.path.join("data", name))
    

# def train_classifier(name):
#     # Define a local directory to store data and classifier
#     save_directory = os.path.join("uploads", name)  # Using 'uploads' for images
    
#     # Create necessary directories if they don't exist
#     os.makedirs(save_directory, exist_ok=True)
    
#     faces = []
#     ids = []
    
#     # Load the pre-trained Haar Cascade for face detection
#     detector_path = "data/haarcascade_frontalface_default.xml"  # Ensure this file exists in your project directory
#     detector = cv2.CascadeClassifier(detector_path)

#     if detector.empty():
#         print(f"Error: Haarcascade not found at {detector_path}")
#         return None

#     # Read images from the directory
#     for pic in os.listdir(save_directory):
#         imgpath = os.path.join(save_directory, pic)
#         try:
#             img = cv2.imread(imgpath)
#             gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#             face = detector.detectMultiScale(gray, 1.1, 4)
#             for (x, y, w, h) in face:
#                 faces.append(gray[y:y+h, x:x+w])
#                 ids.append(int(pic.split('_')[1].split('.')[0]))  # Extract number from filename (name_1.jpg → 1)
#         except Exception as e:
#             print(f"Error reading image {pic}: {e}")
    
#     if len(faces) == 0 or len(ids) == 0:
#         print("Error: No faces detected. Training aborted.")
#         return None

#     # Train the face recognizer
#     clf = cv2.face.LBPHFaceRecognizer_create()
#     clf.train(faces, np.array(ids))

#     # Define the classifier save path inside 'uploads'
#     classifier_directory = os.path.join("uploads", name)
#     os.makedirs(classifier_directory, exist_ok=True)
#     classifier_path = os.path.join(classifier_directory, f"{name}_classifier.xml")
    
#     # Save the trained model
#     clf.write(classifier_path)
#     print(f"Classifier saved at {classifier_path}")

#     return classifier_path
def train_classifier(name):
    
    save_directory = os.path.join("data", name)
    os.makedirs(save_directory, exist_ok=True)

    faces = []
    ids = []

    detector = cv2.CascadeClassifier("./data/haarcascade_frontalface_default.xml")
    
    if detector.empty():
        print("Error: Haarcascade file not found!")
        return None

    for pic in os.listdir(save_directory):
        imgpath = os.path.join(save_directory, pic)
        try:
            img = cv2.imread(imgpath)
            cv2.imshow("Captured Image", img)  # Show the image being processed

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            face = detector.detectMultiScale(gray, 1.1, 4)

            for (x, y, w, h) in face:
                faces.append(gray[y:y+h, x:x+w])
                
                file_id = ''.join(filter(str.isdigit, pic))  # Extract numeric ID
                ids.append(int(file_id))
        
        except Exception as e:
            print(f"Error reading image {pic}: {e}")

    if not faces or not ids:
        print(": No faces detected. Training aborted.")
        return NameError

    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.train(faces, np.array(ids))

    classifier_directory = os.path.join("data","classifiers")
    os.makedirs(classifier_directory, exist_ok=True)
    classifier_path = os.path.join(classifier_directory, f"{name}_classifier.xml")

    clf.write(classifier_path)
    print(f"✅ Classifier saved at {classifier_path}")

    return classifier_path

def folder_exists(folder_path):
    bucket = storage.bucket()
    blobs = list(bucket.list_blobs(prefix=folder_path))  # List all files in folder
    return bool(blobs)  # Returns True if there are files, False otherwise