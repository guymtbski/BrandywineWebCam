import os
import requests
import schedule
import time
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask, render_template, send_from_directory, jsonify
import cv2
import subprocess  # Import for FFmpeg

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
    if not images:
        print("No images to create a video.")
        return

    video_path = os.path.join(image_folder, 'timelapse.mp4')

    # Use FFmpeg to create the video with debugging and absolute path
    ffmpeg_cmd = [
        'ffmpeg', '-loglevel', 'debug', 
        '-framerate', '1',
        '-pattern_type', 'glob',
        '-i', f'{os.getcwd()}/{image_folder}/*.jpg',  # Use absolute path
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        video_path
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print("Timelapse video created successfully at", video_path)
    except subprocess.CalledProcessError as e:
        print(f"Error creating video: {e}")

def scrape_initial_images():
    print("Scraping initial 24 images...")
    for _ in range(max_images):
        download_image()

def schedule_downloads():
    schedule.every().hour.at(":01").do(download_image)
    schedule.every().hour.at(":31").do(download_image)

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
    scrape_initial_images()
    schedule_downloads()

    import threading
    threading.Thread(target=schedule.run_pending, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
