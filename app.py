from flask import Flask, render_template, jsonify
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
import os

app = Flask(__name__)

# Image directory
IMG_DIR = 'static/images'
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

def scrape_and_replace_image():
    try:
        # Scrape the image
        url = "https://pmsccams.com/?SearchDeviceID=4"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.content, "html.parser")
        img_tag = soup.find('img', id='camSnapshot')  # Replace with actual tag and attribute
        img_url = img_tag['src']

        # Download the image
        img_data = requests.get(img_url).content
        
        # Determine the filename for replacement
        img_files = [f for f in os.listdir(IMG_DIR) if f.endswith(('.jpg', '.jpeg', '.png'))]
        if img_files:
            img_to_replace = os.path.join(IMG_DIR, img_files[0])  # Replace the first image
            with open(img_to_replace, 'wb') as f:
                f.write(img_data)
        else:
            # If no images exist yet, save as a new image
            with open(os.path.join(IMG_DIR, 'image1.jpg'), 'wb') as f:
                f.write(img_data)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching image: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Schedule the task
scheduler = BackgroundScheduler()
scheduler.add_job(scrape_and_replace_image, 'interval', minutes=30, next_run_time=datetime.datetime.now() + datetime.timedelta(minutes=1))
scheduler.start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/images")
def get_images():
    img_files = [f for f in os.listdir(IMG_DIR) if f.endswith(('.jpg', '.jpeg', '.png'))]
    return jsonify(img_files)

if __name__ == "__main__":
    app.run(debug=True)
