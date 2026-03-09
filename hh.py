import http.client
import requests
import time

def generate_cartoon(image_path):
    
    api_key = "a7e715f2eamshc4ba76896b7f9f1p1ccccdjsn55f1d728fccb"
    host = "ai-cartoon-generator.p.rapidapi.com"

    # STEP 1: Upload image
    url = "https://ai-cartoon-generator.p.rapidapi.com/image/effects/generate_cartoonized_image"

    files = {
        'image': open(image_path, 'rb')
    }

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": host
    }

    response = requests.post(url, files=files, headers=headers)
    result = response.json()

    print("Upload Response:", result)

    task_id = result.get("task_id")

    if not task_id:
        print("Task ID not received")
        return

    # STEP 2: Wait for processing
    time.sleep(20)

    # STEP 3: Fetch result
    conn = http.client.HTTPSConnection(host)

    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': host
    }

    endpoint = f"/api/rapidapi/query-async-task-result?task_id={task_id}"

    conn.request("GET", endpoint, headers=headers)

    res = conn.getresponse()
    data = res.read()

    print("Cartoon Result:")
    print(data.decode("utf-8"))


# CALL FUNCTION
generate_cartoon(r"C:\Users\Priya\OneDrive\Desktop\U01MI23S0005\cartoon_project\image.png")