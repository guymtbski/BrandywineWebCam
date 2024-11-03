import os
import requests
import schedule
import time
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask, render_template, send_from_directory, jsonify
import cv2
from moviepy.editor import ImageSequenceClip

# Configure storage
image_folder = "images"
os.makedirs(image_folder, exist_ok=True)
max_images = 24  # Keep only the last 24 images

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
                create_timelapse_video()  # Create video on each image download
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
    elif len(images) < max_images and len(images) > 0:
        # Replicate the first image if there are less than 24 images
        first_image = images[0]
        for i in range(len(images), max_images):
            new_image_name = f"WebCamImage_replicated_{i}.jpg"
            new_image_path = os.path.join(image_folder, new_image_name)
            os.system(f"cp {os.path.join(image_folder, first_image)} {new_image_path}")
            print(f"Replicated image {first_image} as {new_image_name}")


def create_timelapse_video():
    # Get the last 24 images, or the replicated ones if there are fewer
    images = sorted(os.listdir(image_folder))[-max_images:]

    video_path = os.path.join(image_folder, 'timelapse.mp4')

    try:
        # Use moviepy to create the video
        image_files = [os.path.join(image_folder, img) for img in images]
        clip = ImageSequenceClip(image_files, fps=1)
        clip.write_videofile(video_path, codec="libx264", ffmpeg_params=['-pix_fmt', 'yuv420p'])  # Explicit codec and pixel format
        print("Timelapse video created successfully at", video_path)
    except Exception as e:
        print(f"Error creating video: {e}")


def schedule_downloads():
    schedule.every().hour.at(":01").do(download_image)
    schedule.every().hour.at(":31").do(download_image)

    # Run the scheduler in a background thread
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
        return send_from_directory(image_folder, filename, mimetype="video/mp4")  # Explicit MIME type for video
    else:
        return send_from_directory(image_folder, filename)

if __name__ == "__main__":
    # Schedule downloads
    schedule_downloads()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
