
# # import requests

# # url = "http://127.0.0.1:5000/new_user"

# # # Send POST request with form data
# # # response = requests.post(url, data={'name': 'sumsss'})

# # # print(response.json())  



# # # Example to send the request to the Flask server
# # response = requests.post(url, data={'name': 'sumsss', 'age': '18', 'gender': 'male'})

# # print(response.json())
# import requests

# # # Define the API endpoint
# url = "http://192.168.1.45:5000/detect"

# # Define the test payload (form data)
# data = {}

# response = requests.post(url, data=data)

# # Print the response
# print("Status Code:", response.status_code)
# try:
#     print("Response:", response.json())
# except Exception:
#     print("Response Text:", response.text)
# import requests

# url = "http://192.168.1.45:5000/detect"  # Ensure Flask is running here

# try:
#     response = requests.post(url)  # Add necessary parameters if required

#     print("Status Code:", response.status_code)
#     print("Response:", response.json())  # JSON response handling
# except requests.exceptions.ConnectionError:
#     print("Error: Could not connect to the server. Is Flask running?")
# except requests.exceptions.RequestException as e:
#     print(f"Request failed: {e}")
import requests

url = "http://127.0.0.1:5000/sign_up_new_admin"
data = {
    "name": "Sayyed Sumaiya",
    "age": "18",
    "gender": "Female",
    "phone_no": "9167367967",
    "address": "Garib Nawaz"
}
response = requests.post(url, data=data)
print(response.json())
