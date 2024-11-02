import cv2
import os
import glob

def create_timelapse(image_folder, output_video_path, fps=4):
    # Get list of image files sorted by creation time
    image_files = sorted(glob.glob(os.path.join(image_folder, '*.jpg')), key=os.path.getctime, reverse=True)

    # Take the 10 most recent images
    recent_images = image_files[:10]
    
    if not recent_images:
        print("No images found in the directory.")
        return

    # Read the first image to get the dimensions
    first_image = cv2.imread(recent_images[0])
    height, width, layers = first_image.shape

    # Create a video writer object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Specify codec
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # Loop through the images and write them to the video
    for image_path in recent_images:
        image = cv2.imread(image_path)
        video_writer.write(image)

    # Release the video writer
    video_writer.release()
    print(f"Timelapse video created at: {output_video_path}")

# Usage
image_folder = 'C:/Users/Admin/Desktop/brandywine_images'  # Change this to your image folder path
output_video_path = 'timelapse_video.mp4'  # Desired output video file name
create_timelapse(image_folder, output_video_path)
