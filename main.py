import numpy as np
from time import time
import cv2
import os
import firebase_admin
# from tkinter import messagebox
from firebase_admin import credentials, storage
from flask import Flask, request, jsonify
from side_kick import *

# Initialize Firebase Admin SDK
cred = credentials.Certificate("home-security-dce26-firebase-adminsdk-bp0es-739f819549.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'home-security-dce26.firebasestorage.app'
})



app = Flask(__name__)

# To check if Admin is Signed in or not
@app.route('/is_signed_in', methods=['POST'])
def is_signed_in():
    with open('log.txt', 'r') as file:
        return jsonify({'isLogged': file.read().strip() == 'True'})
    
# Sign Out 
@app.route('/sign_out', methods=['POST'])
def sign_out():
    with open('log.txt', 'w') as file:
        file.write("False")
    return jsonify({'status': 'success', 'msg': 'Signed Out'})

# Edit Admin Profile Details
@app.route('/edit_admin_details', methods=['POST'])
def edit_admin_details():
    name = request.form.get('admin_name', 'Urusa Shaikh')
    email = request.form.get('email', '')
    age = request.form.get('age', '')
    gender = request.form.get('gender', '')
    address = request.form.get('address', '')
    
    data = {}
    updates = {'email': email, 'age': age, 'gender': gender, 'address': address}
    
    file_path = f'{name}/admin_details.txt'
    local_path = 'data/details/admin_details.txt'
    
    if not download_file_from_firebase(file_path, local_path):
        return jsonify({'status': 'error', 'msg': 'Unable to access Admin details'})
    
    # Read the downloaded file
    with open(local_path, 'r') as file:
        for line in file:
            key, value = line.strip().split(':')
            data[key.strip()] = value.strip()
    
    data.update(updates) # update the required updates
    
    # write those updates in the file
    with open(local_path, 'w') as file:
        new_data = ''
        for key, value in data.items():
            new_data += f'{key}: {value}\n'
        file.write(new_data)
    
    if not upload_file([local_path], [file_path]):
        return jsonify({'status': 'error', 'msg': 'Unable to update the changes'})
    
    os.remove(local_path)
    return jsonify({'status': 'success', 'msg': 'Updated Successfully'})

# Register new user or face for unlocking
@app.route('/new_user', methods=['POST'])
def add_new_user():
    name = request.form.get('name', '').strip()
    age = request.form.get('age', '').strip()
    gender = request.form.get('gender', '').strip()

    # Extract uploaded images
    image_files = list(request.files.values())

    if not name or not age or not gender or not image_files:
        return jsonify({'status': 'error', 'msg': 'Name, age, gender, and images are required'}), 400

    print(f"Name: {name}, Age: {age}, Gender: {gender}, Images: {len(image_files)}")

    # Use /tmp for storage in Cloud Run
    image_folder = os.path.join("/tmp", "uploads", name)  # Using /tmp directory
    os.makedirs(image_folder, exist_ok=True)

    existing_images = set(os.listdir(image_folder))  # Get existing image names

    saved_images_count = 0
    for index, image_file in enumerate(image_files):
        image_path = os.path.join(image_folder, f"{name}_{index}.jpg")
        
        # Check if the image already exists before saving
        if f"{name}_{index}.jpg" not in existing_images:
            image_file.save(image_path)
            saved_images_count += 1  # Count only new images

    # Train the classifier
    classifier_path = train_classifier(name)
    
    # Upload the classifier to Firebase
    upload_file(classifier_path, f"Urusa Shaikh/{name}/{name}_classifier.xml")

    # Remove the temporary classifier file
    os.remove(classifier_path)

    # Optionally remove the temporary image folder if needed (this is a clean-up step)
    # os.rmdir(image_folder)

    return jsonify({
        "status": "success",
        "message": f"Images received! New saved images: {saved_images_count}"
    }), 200

# delete registered user
@app.route('/delete', methods=['POST'])
def delete_person():
    admin_name = request.form.get('admin_name', 'Urusa Shaikh')
    name = request.form.get('name', '')
    if not name:
        return jsonify({'error': 'Name is required'}), 400

    try:
  
        with open('nameslist.txt', 'r') as file:
            if name not in file.read():
                print('No Person to delete')
                return jsonify({'failure' : f'{name} not found' }),400
        
        bucket = storage.bucket()
        blob_classifier = bucket.blob(f"{admin_name}/{name}/{name}_classifier.xml")
        blob_info = bucket.blob(f"{admin_name}/{name}/{name}_info.txt")
        blob_classifier.delete()
        blob_info.delete()
        print(f"✅ Deleted {name} from Firebase Storage")
        
        with open('nameslist.txt', 'r') as file:
            data = file.read()  # Read the entire file content

        # Replace the specific name
        data = data.replace(f'{name}', '')

    # Overwrite the file with the modified content
        with open('nameslist.txt', 'w') as file:
            file.write(data)

    except Exception as e:
        return jsonify({'error': f'Failed to delete: {e}'}), 500

    # local_path = os.path.join("data", name)
    # if os.path.exists(local_path):
    #     shutil.rmtree(local_path)

    return jsonify({'success': f'{name} deleted successfully'}), 200

# Update User details
@app.route('/update_user', methods=['POST'])
def update_user():
    admin_name = request.form.get('admin_name', 'Urusa Shaikh')
    name = request.form.get('name', '')
    age = request.form.get('age', '')
    gender = request.form.get('gender', '')
    
    if not name or not age or not gender:
        return jsonify({'error': 'Name, age, and gender are required'}), 400
    
    # Download the file from Firebase
    if not download_file_from_firebase( f'{admin_name}/{name}/{name}_info.txt', f'data/details/{name}_info.txt'):
        return jsonify({'error': f'Cannot download {name}_info.txt'}), 400

    # Update the details in the file
    updated_file = update_details((name, age, gender))
    
    if updated_file:
        # Upload the updated file to Firebase
        if upload_file([updated_file], [f'{admin_name}/{name}/{name}_info.txt']):
            os.remove(updated_file)
            return jsonify({'status': 'success', 'message': 'User details updated successfully'}), 200
        else:
            os.remove(updated_file)
            return jsonify({'error': 'Failed to upload updated details to Firebase'}), 500
    else:
        os.remove(updated_file)
        return jsonify({'error': 'Failed to update user details'}), 500
    
# display all users
@app.route('/all_user', methods=['POST'])
def show_all_user():
    admin_name = request.form.get('admin_name', 'Urusa Shaikh')
    local_path =''
    with open('nameslist.txt', 'r') as file:
        names = file.read().split()

    json_file = {}  # Dictionary to store user details

    for name in names:
        cloud_path = f'{admin_name}/{name}/{name}_info.txt'
        local_path = f'data/details/{name}_info.txt'
        
        if not download_file_from_firebase(cloud_path, local_path):
            return jsonify({'failure': f'Unable to download {name}_info.txt'}), 500
        
        with open(local_path, 'r') as file:
            arr = file.read().strip().split('\n')

        user_data = []
        for line in arr:
            if line:
                key, value = line.split(':', 1)
                user_data.append(value.strip())  # Store values in array

        json_file[name] = user_data  # Store as an array inside dictionary

    os.remove(local_path)
    return jsonify(json_file)

@app.route('/sign_up_new_admin', methods=['POST'])
def sign_new_admin():
    name = request.form.get('admin_name', '')
    age = request.form.get('age', '')
    gender = request.form.get('gender', '')
    phone_no = request.form.get('phone_no', '')
    address = request.form.get('address', '')
    
    file_paths = ['data/admin_details.txt', 'data/access_history.txt']
    upload_paths = [f'{name}/admin_details.txt', f'{name}/timestamps/access_history.txt']
    file_content = f'admin_name: {name}\nage: {age}\ngender: {gender}\nphone_no: {phone_no}\naddress: {address}'
    
    with open(file_paths[0], 'w') as file:
        file.write(file_content)
    
    with open(file_paths[1], 'w') as file:
        file.write("")
    
    if not upload_file(file_paths, upload_paths):
        for file_path in file_paths:
            os.remove(file_path)
        return jsonify({'error': f'Unable to create {name}'})
    for file_path in file_paths:
        os.remove(file_path)
    return jsonify({'success': f'New admin, {name}, created.'})

@app.route('/sign_in', methods=['POST'])
def sign_in():
    name = request.form.get('admin_name', '')
    phno = request.form.get('phone_no', '')
    file_name = f'{name}/admin_details.txt'
    local_file = 'data/admin_details.txt'
    jfile = {'status': 'NA'}
    
    if folder_exists(name):
        if not download_file_from_firebase(file_name, local_file):
            jfile = {'status': 'error', 'message': f'Unable to fetch data of {name}'}
        else:
            with open(local_file, 'r') as file:
                for line in file:
                    if 'phone_no' in line:
                        if phno == line.split(':')[1].strip():
                            with open('log.txt', 'w') as file:
                                file.write("True")
                            jfile = {'status': 'success', 'message': 'Sign in Success'}
                        else:
                            jfile = {'status': 'error', 'message': 'Invalid Phone Number'}
            os.remove(local_file)
                     
    else:
        jfile = {'status': 'error', 'message': f'{name} does not exists'}
        
    return jfile

@app.route('/show_admin_info', methods=['POST'])
def show_admin_info():
    try:    
        admin_name = request.form.get('admin_name', 'Urusa Shaikh')
        
        json_file = {}
        file_name = f'{admin_name}/admin_details.txt'
        local_path = 'data/details/admin_details.txt'
        
        if not download_file_from_firebase(file_name, local_path):
            return jsonify({'error': 'Unable to fetch Admin information'})
        
        with open(local_path, 'r') as file:
            lines = file.readlines()
        
        for line in lines:
            line = line.strip()
            if not line or ':' not in line:
                continue
            key, value = line.split(':', 1)
            json_file[key.strip()] = value.strip()
            
        os.remove(local_path)
        return json_file
    except Exception as e:
        return jsonify({'status': 'error', 'msg': e})
    
@app.route('/show_history', methods=['POST'])
def show_history():
    try:
        admin_name = request.form.get('admin_name', 'Urusa Shaikh')
        file_path = f'{admin_name}/timestamps/access_history.txt'
        local_path = 'data/details/access_history.txt'
        hist_dict = {"name": [], "time": []}  # Dictionary with separate lists
        
        if not download_file_from_firebase(file_path, local_path):
            return jsonify({'status': 'failure', 'message': 'Unable to fetch Data from Firebase'})
        
        with open(local_path, "r") as file:
            for line in file:
                parts = line.strip().split("\t")  # Splitting by tab
                if len(parts) == 2:
                    name = parts[0].split(" : ")[1]
                    time = parts[1].split(" : ")[1]
                    
                    hist_dict["name"].insert(0, name)  # Append name
                    hist_dict["time"].insert(0, time)  # Append time
        
        return jsonify({'status': 'success', 'data': hist_dict})
    except Exception as e:
        return jsonify({'status': 'error', 'msg': e})

@app.route('/detect', methods=['POST'])
def detect_face(timeout=5):
    try:
        admin_name = request.form.get('admin_name', 'Urusa Shaikh')
        cap = cv2.VideoCapture(0)
        face_cascade = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')
        recognized_name = "Unknown"
        start_time = time()

        # Read names from file
        with open('nameslist.txt', 'r') as file:
            names = file.read().split()

        classifiers = {}

        # Load all classifiers
        for name in names:
            file_path = f'{admin_name}/{name}/{name}_classifier.xml'
            local_path = f'data/classifiers/{name}_classifier.xml'

            if download_file_from_firebase(file_path, local_path):
                recognizer = cv2.face.LBPHFaceRecognizer_create()
                recognizer.read(local_path)
                classifiers[name] = recognizer

        # Start the face detection loop
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                roi_gray = gray[y:y+h, x:x+w]
                
                # Check the face against all classifiers
                for name, recognizer in classifiers.items():
                    id, confidence = recognizer.predict(roi_gray)
                    confidence = 100 - int(confidence)

                    if confidence > 50:
                        recognized_name = name
                        frame = cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        frame = cv2.putText(frame, f"Recognized: {name.upper()}", (x, y-4), 
                                            cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1, cv2.LINE_AA)
                        break  # Stop checking other classifiers if a match is found
                else:
                    frame = cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    frame = cv2.putText(frame, "Unknown Face", (x, y-4), 
                                        cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 1, cv2.LINE_AA)

            cv2.imshow("image", frame)

            if time() - start_time >= timeout:
                append_history(recognized_name)
                return jsonify({"status": "success" if recognized_name != "Unknown" else "failure",
                                "message": "Face detection complete.",
                                "name": recognized_name})

            if cv2.waitKey(20) & 0xFF == ord('q'):
                break

        # Cleanup
        cap.release()
        cv2.destroyAllWindows()

        # Remove classifier files
        for name in classifiers.keys():
            os.remove(f'data/classifiers/{name}_classifier.xml')

        return jsonify({"status": "failure", "message": "Unknown Face!"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
