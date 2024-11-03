from flask import Flask, render_template, jsonify, send_from_directory
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
import os
import datetime
import logging
from urllib.parse import urljoin

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

        url = "https://pmsccams.com/?SearchDeviceID=4"
        response = requests.get(url)
        response.raise_for_status()

        logging.info("Successfully fetched webpage content")

        soup = BeautifulSoup(response.content, "html.parser")
        img_tag = soup.find('img')
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

        img_files = [f for f in os.listdir(IMG_DIR) if f.endswith(('.jpg', '.jpeg', '.png'))]
        if img_files:
            # Generate a timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_filename = f"image_{timestamp}.jpg"
            img_to_replace = os.path.join(IMG_DIR, new_filename)

            with open(img_to_replace, 'wb') as f:
                f.write(img_data)
            logging.info(f"Replaced image: {img_to_replace}")
        else:
            # Generate a timestamped filename for the initial image
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            initial_filename = f"image_{timestamp}.jpg"
            with open(os.path.join(IMG_DIR, initial_filename), 'wb') as f:
                f.write(img_data)
            logging.info(f"Saved initial image to: {os.path.join(IMG_DIR, initial_filename)}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching image: {e}")
    except Exception as e:
        logging.exception(f"An error occurred: {e}")

# Schedule the task (consider using Render's built-in scheduler)
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

@app.route('/view/<filename>')
def view_image(filename):
    return send_from_directory(IMG_DIR, filename)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=10000)
