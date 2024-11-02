import os
import requests
import schedule
import time
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask, render_template, send_from_directory, jsonify
import cv2
from timelapse import create_timelapse  # Import the timelapse library

# Configure storage
image_folder = "images"
os.makedirs(image_folder, exist_ok=True)
max_images = 24  # Keeps only the last 24 images

# Base URL and page URL
base_url = 'https://pmsccams.com'
page_url = 'https://pmsccams.com/?SearchDeviceID=4'

# Flask app setup
app = Flask(__name__)

def download_image():
    print("Fetching new image...")
    try:
        response = requests.get(page_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        img_tag = soup.find('img')

        if img_tag:
            img_url = base_url + img_tag['src'].replace("\\", "/")
            img_response = requests.get(img_url)
            img_response.raise_for_status()

            if 'image' in img_response.headers['Content-Type']:
                current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                image_name = f'WebCamImage_{current_time}.jpg'
                image_path = os.path.join(image_folder, image_name)

                with open(image_path, 'wb') as f:
                    f.write(img_response.content)
                print(f"Image saved successfully as {image_name}")

                # Manage images and create timelapse
                manage_images()
                create_timelapse_video()
            else:
                print("Downloaded content is not an image.")
        else:
            print("No image found on the page.")

    except Exception as e:
        print(f"Error occurred: {e}")

def manage_images():
    images = sorted(os.listdir(image_folder), reverse=True)
    if len(images) > max_images:
        for image in images[max_images:]:
            os.remove(os.path.join(image_folder, image))
            print(f"Deleted old image: {image}")

def create_timelapse_video():
    images = sorted(os.listdir(image_folder))[-max_images:]
    if len(images) < 10:  # Check for minimum number of images
        print("Not enough images to create a video yet.")
        return

    video_path = os.path.join(image_folder, 'timelapse.mp4')

    # Check if the video already exists and is less than 30 minutes old
    if os.path.exists(video_path):
        creation_time = os.path.getmtime(video_path)
        now = time.time()
        time_diff = now - creation_time  # Time difference in seconds
        if time_diff < (30 * 60):  # 30 minutes in seconds
            print("Video is less than 30 minutes old. Skipping creation.")
            return

    try:
        # Use the timelapse library to create the video
        create_timelapse(
            image_folder,            # Input folder containing images
            video_path,              # Output video file path
            fps=1,                   # Frames per second
            image_extensions=['jpg'],  # Image file extensions to include
            overwrite=True           # Overwrite existing video file
        )
        print("Timelapse video created successfully at", video_path)

    except Exception as e:
        print(f"Error creating video: {e}")

def scrape_initial_images():
    print("Scraping initial 24 images...")
    for _ in range(max_images):
        download_image()
        time.sleep(60)  # Wait 60 seconds between downloads

def schedule_downloads():
    # Schedule downloads to start AFTER the initial scrape
    schedule.every().hour.at(":01").do(download_image)
    schedule.every().hour.at(":31").do(download_image)

    # IMPORTANT: Wait for the initial scraping to finish
    while len(os.listdir(image_folder)) < max_images:
        time.sleep(10)  # Check every 10 seconds

    # Now start the scheduler in the background
    import threading
    threading.Thread(target=schedule.run_pending, daemon=True).start()

# Route to display the timelapse as an HTML slideshow
@app.route("/")
def index():
    images = sorted(os.listdir(image_folder))[-max_images:]
    return render_template("index.html", images=images, video_path="images/timelapse.mp4")

# Route to serve images
@app.route("/images/<filename>")
def serve_image(filename):
    if filename == "timelapse.mp4":
        return send_from_directory(image_folder, filename, mimetype="video/mp4")
    else:
        return send_from_directory(image_folder, filename)

@app.route("/list-files")
def list_files():
    files = os.listdir(image_folder)
    return jsonify(files)

if __name__ == "__main__":
    scrape_initial_images()  # Scrape initial images first
    schedule_downloads()     # Then start the scheduler

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
