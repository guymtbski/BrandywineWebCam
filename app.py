from flask import Flask, render_template, jsonify
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
import os
import datetime
import logging
from urllib.parse import urljoin  # Import urljoin

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Image directory
IMG_DIR = 'static/images'
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

def scrape_and_replace_image():
    try:
        logging.info("Starting image scraping and replacement process")

        # Scrape the image
        url = "https://pmsccams.com/?SearchDeviceID=4"
        response = requests.get(url)
        response.raise_for_status()

        logging.info("Successfully fetched webpage content")

        soup = BeautifulSoup(response.content, "html.parser")
        img_tag = soup.find('img')  # Find the <img> tag
        if img_tag is None:
            logging.error("Image tag not found on the page")
            return

        relative_img_url = img_tag['src']

        # Construct the full image URL
        base_url = response.url
        full_img_url = urljoin(base_url, relative_img_url)
        logging.info(f"Full image URL: {full_img_url}")

        # Download the image using full_img_url
        img_data = requests.get(full_img_url).content

        logging.info("Successfully downloaded image")

        # Determine the filename for replacement
        img_files = [f for f in os.listdir(IMG_DIR) if f.endswith(('.jpg', '.jpeg', '.png'))]
        if img_files:
            img_to_replace = os.path.join(IMG_DIR, img_files[0])  # Replace the first image
            with open(img_to_replace, 'wb') as f:
                f.write(img_data)
            logging.info(f"Replaced image: {img_to_replace}")
        else:
            # If no images exist yet, save as a new image
            with open(os.path.join(IMG_DIR, 'image1.jpg'), 'wb') as f:
                f.write(img_data)
            logging.info("Saved initial image")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching image: {e}")
    except Exception as e:
        logging.exception(f"An error occurred: {e}")

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
