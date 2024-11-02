import os
import requests
import schedule
import time
from datetime import datetime
from bs4 import BeautifulSoup

# Folder where the images will be saved
save_folder = os.path.dirname(os.path.abspath(__file__))

# Base URL and page URL
base_url = 'https://pmsccams.com'
page_url = 'https://pmsccams.com/?SearchDeviceID=4'

def download_image():
    print("getting image")
    try:
        # Fetch the webpage content
        response = requests.get(page_url)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the image tag
        img_tag = soup.find('img')
        if img_tag:
            # Extract the relative image URL from the 'src' attribute
            img_url = img_tag['src']
            
            # Build the full image URL by combining it with the base URL
            full_img_url = base_url + img_url.replace("\\", "/")
            
            # Download the image from the full URL
            img_response = requests.get(full_img_url)
            img_response.raise_for_status()

            # Verify the content type
            if 'image' in img_response.headers['Content-Type']:
                # Format the timestamp for the image filename
                current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                image_name = f'WebCamImage_{current_time}.jpg'  # Name example: WebCamImage_2024-10-19_14-30-00.jpg
                image_path = os.path.join(save_folder, image_name)

                # Save the image
                with open(image_path, 'wb') as f:
                    f.write(img_response.content)
                print(f"Image saved successfully as {image_name}")
            else:
                print("The downloaded content is not an image.")
        else:
            print("No image found on the page.")
    
    except Exception as e:
        print(f"An error occurred: {e}")

# Schedule the job to run every 30 minutes
schedule.every(30).minutes.do(download_image)

# Run the scheduler indefinitely
while True:
    schedule.run_pending()
    time.sleep(1)  # Sleep for 30 minutes (30 * 60 seconds)
