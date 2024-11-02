import os
import requests
import schedule
import time
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask, render_template, send_from_directory
import cv2

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
                create_timelapse_video()  # Create or update the timelapse video
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
    images = sorted(os.listdir(image_folder))[-max_images:]  # Get the last images
    if not images:
        print("No images to create a video.")
        return

    # Define the video file path
    video_path = os.path.join(image_folder, 'timelapse.mp4')
    
    # Get the size of the first image to set the video size
    first_image = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = first_image.shape
    
    # Create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for mp4
    video = cv2.VideoWriter(video_path, fourcc, 1, (width, height))  # 1 fps for timelapse

    # Write each image to the video
    for image in images:
        image_path = os.path.join(image_folder, image)
        img = cv2.imread(image_path)
        video.write(img)
    
    video.release()
    print("Timelapse video created successfully at", video_path)

# Schedule image download at 1 minute past the hour and 1 minute past the half-hour
def schedule_downloads():
    schedule.every().hour.at(":01").do(download_image)  # Every hour at minute 1
    schedule.every().hour.at(":31").do(download_image)  # Every half hour at minute 1

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Route to display the timelapse as an HTML slideshow
@app.route("/")
def index():
    images = sorted(os.listdir(image_folder))[-max_images:]
    return render_template("index.html", images=images)

# Route to serve images
@app.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory(image_folder, filename)

# Route to serve the timelapse video
@app.route("/timelapse")
def serve_timelapse():
    return send_from_directory(image_folder, 'timelapse.mp4')

if __name__ == "__main__":
    # Run the scheduler in a background thread
    import threading
    threading.Thread(target=run_scheduler).start()
    
    # Run Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
