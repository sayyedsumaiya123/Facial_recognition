
# import requests

# url = "http://127.0.0.1:5000/new_user"

# # Send POST request with form data
# # response = requests.post(url, data={'name': 'sumsss'})

# # print(response.json())  



# # Example to send the request to the Flask server
# response = requests.post(url, data={'name': 'sumsss', 'age': '18', 'gender': 'male'})

# print(response.json())
import requests

# Define the API endpoint
url = "http://192.168.1.45:5000/sign_up_new_admin"

# Define the test payload (form data)
data = {
    "name": "Urusa Shaikh",
    "age": "18",
    "gender": "Female",
    "phone_no" : "9326397622",
    "address" : "N/A"

}

# Send the request
response = requests.post(url, data=data)

# Print the response
print("Status Code:", response.status_code)
try:
    print("Response:", response.json())
except Exception:
    print("Response Text:", response.text)
