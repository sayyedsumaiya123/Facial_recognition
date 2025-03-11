import numpy as np
from time import time
import cv2
import os
import firebase_admin
# from tkinter import messagebox
from firebase_admin import credentials, storage
from flask import Flask, request, jsonify
from side_kick import *
from werkzeug.utils import secure_filename

# Initialize Firebase Admin SDK
cred = credentials.Certificate("home-security-dce26-firebase-adminsdk-bp0es-ab0f47e5cd.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'home-security-dce26.firebasestorage.app'
})

app = Flask(__name__)

@app.route('/new_user', methods=['POST'])
def add_new_user():
    name = request.form.get('name', '').strip()
    age = request.form.get('age', '').strip()
    gender = request.form.get('gender', '').strip()

    image_files = list(request.files.values())

    if not name or not age or not gender or not image_files:
        return jsonify({'error': 'Name, age, gender, and images are required'}), 400

    print(f"Name: {name}, Age: {age}, Gender: {gender}, Images: {len(image_files)}")

    namelist_path = "nameslist.txt" 

    if not os.path.exists(namelist_path):
        open(namelist_path, "w").close()  # Create an empty file if it doesn't exist

    # Read existing names
    with open(namelist_path, "r") as f:
        existing_names = {line.strip() for line in f}  # Store names in a set for fast lookup

    # Add name only if it's not already present
    if name not in existing_names:
        with open(namelist_path, "a") as f:
            f.write(name + "\n")
        print(f"Added {name} to namelist.txt")
    else:
        print(f"{name} already exists in namelist.txt")


    image_folder = os.path.join("data", name)
    os.makedirs(image_folder, exist_ok=True)
    image_number = 0  # Start numbering from 1

    for image_file in image_files:
        image_data = image_file.read()  # Read file data once
        
        # Save original image
        image_path = os.path.join(image_folder, f"{name}_{image_number}.jpg")
        with open(image_path, "wb") as f:
            f.write(image_data)
        image_number += 1  # Increment counter

        # Duplicate each image 20 times
        for i in range(1, 21):
            duplicate_image_path = os.path.join(image_folder, f"    {name}_{image_number}.jpg")
            with open(duplicate_image_path, "wb") as f:
                f.write(image_data)
            image_number += 1  # Increment counter

    local_path = os.path.join("data","classifiers", f"{name}_classifier.xml")
    file_name = f"Urusa Shaikh/{name}/{name}_classifier.xml"

    # Train classifier and upload it
    classifier_path = train_classifier(name)

    detail_path = make_details([name,age,gender])
    files_to_delete = [classifier_path,detail_path]

    print(f"Uploading file from {local_path} to {file_name}")

    upload_to = [f"Urusa Shaikh/{name}/{name}_classifier.xml", f"Urusa Shaikh/{name}/{name}_info.txt"]

    if upload_file(files_to_delete, upload_to): 
            # Clean up local files after uploading
            delete_local_files(name, files_to_delete)
            return jsonify({"status": "success", "message": "Face training completed and uploaded!"}), 200
    else:
            delete_local_files(name, files_to_delete)
            return jsonify({"error": "Failed to upload the classifier to Firebase"}), 500


# delete registered user
@app.route('/delete', methods=['POST'])
def delete_person():
    name = request.form.get('name', '')
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    try:
        with open('nameslist.txt', 'r') as file:
            if name not in file.read():
                print('No Person to delete')
                return jsonify({'failure' : f'{name} not found' }),400
        
        bucket = storage.bucket()
        blob_classifier = bucket.blob(f"Urusa Shaikh/{name}/{name}_classifier.xml")
        blob_info = bucket.blob(f"Urusa Shaikh/{name}/{name}_info.txt")
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


#modify details of user
@app.route('/modify', methods=['GET', 'POST'])
def modify_info():  
    print("Received Data:", request.form)

    name = request.form.get('name', '').strip()
    age = request.form.get('age', '').strip()
    gender = request.form.get('gender', '').strip()

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    details_path = f'data/details/{name}_info.txt'

    # Fetch existing user details if age and gender are not provided
    if not age and not gender:
        if not download_file_from_firebase(f'Urusa Shaikh/{name}/{name}_info.txt', details_path):
            return jsonify({'error': f'Cannot download {name}_info.txt'}), 400

        with open(details_path, "r") as f:
            lines = f.readlines()

        print("File Contents:", lines)  # Debugging

        # Extract values from key-value format
        details = {}
        for line in lines:
            parts = line.strip().split(": ", 1)
            if len(parts) == 2:
                key, value = parts
                details[key.lower()] = value  # Store in lowercase for easy lookup

        age = details.get("age", "")  # Default to empty string if missing
        gender = details.get("gender", "")

        print("Extracted Age:", age)
        print("Extracted Gender:", gender)

        return jsonify({'name': name, 'age': age, 'gender': gender}), 200

    # Update the details in the file
    if update_details((name, age, gender)):
        if upload_file([details_path], [f'Urusa Shaikh/{name}/{name}_info.txt']):
            return jsonify({'status': 'success', 'message': 'User details updated'}), 200
        return jsonify({'error': 'Failed to upload updated details'}), 500

    return jsonify({'error': 'Failed to update user details'}), 500

#display all users
@app.route('/all_user', methods=['POST'])
def show_all_user():
    with open('nameslist.txt', 'r') as file:
        names = file.read().split()

    json_file = {}  # Dictionary to store user details

    for name in names:
        cloud_path = f'Urusa Shaikh/{name}/{name}_info.txt'
        local_path = f'data/details/{name}_info.txt'
        
        if not download_file_from_firebase(cloud_path, local_path):
            return jsonify({'failure': f'Unable to download {name}_info.txt'}), 500
        
        with open(local_path, 'r') as file:
            arr = file.read().strip().split('\n')

        user_info = {}  # Dictionary to store user details correctly
        for line in arr:
            if line:
                key, value = line.split(':', 1)
                user_info[key.strip().lower()] = value.strip()  # Store as key-value

        # Store in JSON with correct structure
        json_file[name] = {
            "name": name,
            "age": user_info.get("age", "N/A"),
            "gender": user_info.get("gender", "N/A")
        }

    os.remove(local_path)
    return jsonify(json_file)



@app.route('/sign_admin', methods=['POST'])
def sign_admin():
    name = request.form.get('name', '')
    age = request.form.get('age', '')
    gender = request.form.get('gender', '')
    phone_no = request.form.get('phone_no', '')
    
    file_paths = ['data/admin_details.txt', 'data/access_history.txt']
    upload_paths = [f'{name}/admin_details.txt', f'{name}/timestamps/access_history.txt']
    file_content = f'admin_name: {name}\nage: {age}\ngender: {gender}\nphone_no: {phone_no}'
    
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

@app.route('/show_admin_info', methods=['POST'])
def show_admin_info():
    
    admin_name = request.form.get('name', 'Urusa Shaikh')
    
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

# Edit Admin Profile Details
@app.route('/edit_admin_details', methods=['POST'])
def edit_admin_details():
    email = request.form.get('email', '')
    age = request.form.get('age', '')
    gender = request.form.get('gender', '')
    address = request.form.get('address', '')
    
    data = {}
    updates = {'email': email, 'age': age, 'gender': gender, 'address': address}
    
    file_path = 'Urusa Shaikh/admin_details.txt'
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

#sign up new admin
@app.route('/sign_up_new_admin', methods=['POST'])
def sign_new_admin():
    name = request.form.get('name', '')
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


# To check if Admin is Signed in or not
@app.route('/is_signed_in', methods=['POST'])
def is_signed_in():
    with open('log.txt', 'r') as file:
        content = file.read().strip()
        print(content)
        return jsonify({'isLogged': str(content).lower() == "true"})

# Sign Out 
@app.route('/sign_out', methods=['POST'])
def sign_out():
    with open('log.txt', 'w') as file:
        file.write("False")
    return jsonify({'status': 'success', 'msg': 'Signed Out'})

@app.route('/sign_in', methods=['POST'])
def sign_in():
    name = request.form.get('name', '')
    phno = request.form.get('phone_no', '')
    file_name = f'{name}/admin_details.txt'
    local_file = 'data/admin_details.txt'
    
    if folder_exists(name):
        if not download_file_from_firebase(file_name, local_file):
            return {'status': 'error', 'message': f'Unable to fetch data of {name}'}
        else:
            with open(local_file, 'r') as file:
                for line in file:
                    if 'phone_no' in line:
                        if phno == line.split(':')[1].strip():
                            # Authentication successful - return data needed for OTP
                            with open('log.txt', 'w') as file:
                                file.write("True")
                            
                            # Format phone number for Firebase (adding +91 if not present)
                            formatted_phone = phno
                            if not phno.startswith('+'):
                                formatted_phone = f"+91{phno}"
                            
                            return {
                                'status': 'success', 
                                'message': 'Sign in Success',
                                'phone_number': formatted_phone,
                                'send_otp': True
                            }
                        else:
                            return {'status': 'error', 'message': 'Invalid Phone Number'}
            os.remove(local_file)
                     
    else:
        return {'status': 'error', 'message': f'{name} does not exists'}


def detect_face(timeout=5):
    try:
        name = request.form.get('name', '')
        file_path = f'Urusa Shaikh/{name}/{name}_classifier.xml'
        local_path = f'data/classifiers/{name}_classifier.xml'

        # Download classifier file from Firebase
        if not download_file_from_firebase(file_path, local_path):
            return jsonify({"status": "failure", 'message': f'Unable to download {file_path}'})
        
        # Initialize face detection and recognition components
        face_cascade = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(local_path)
        cap = cv2.VideoCapture(0)
        pred = False
        start_time = time()

        # Start the face detection loop
        while True:
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                roi_gray = gray[y:y+h, x:x+w]
                id, confidence = recognizer.predict(roi_gray)
                confidence = 100 - int(confidence)

                if confidence > 50:
                    pred = True
                    text = 'Recognized: ' + name.upper()
                    frame = cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    frame = cv2.putText(frame, text, (x, y-4), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1, cv2.LINE_AA)
                else:
                    pred = False
                    text = "Unknown Face"
                    frame = cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    frame = cv2.putText(frame, text, (x, y-4), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 1, cv2.LINE_AA)

            cv2.imshow("image", frame)

            elapsed_time = time() - start_time
            if elapsed_time >= timeout:
                # Return response after timeout
                new_name = ""
                if pred:
                    new_name = name
                    append_history(new_name) 
                    


                    # Send a successful response
                    return jsonify({"status": "success", "message": "Face detected successfully!", "name": new_name})
                    
                else:
                    new_name = "Unknown"
                    append_history(new_name)

                    # Send an error response
                    return jsonify({"status": "failure", "message": f'Not recognized as {name}', "name": new_name})

            if cv2.waitKey(20) & 0xFF == ord('q'):
                break

        # Cleanup after the loop ends
        os.remove(f'data/classifiers/{name}_classifier.xml')
        cap.release()
        cv2.destroyAllWindows()

        # Return a default failure response
        return jsonify({"status": "failure", "message": "Unknown Face!"})

    except Exception as e:
        # Handle exceptions and return error response
        return jsonify({"status": "error", "message": str(e)}), 500

#show history of last accessed users 
@app.route('/show_history', methods=['POST'])
def show_history():
    file_path = 'Urusa Shaikh/timestamps/access_history.txt'
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

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
