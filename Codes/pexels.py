import requests
import os
import subprocess  # Import the subprocess module

# Your Pexels API key
API_KEY = 'HEgYKYK4oCKA1AUTvuWARzfPPulyQMYKDggEgjGnbTscud01lf8xxXxx'
headers = {
    'Authorization': API_KEY
}

# Get the prompt from the environment variable
prompt_text = os.environ.get('VIDEO_PROMPT', 'nature')  # Default to 'nature' if no prompt provided

# Define the download folder
download_folder = r"D:\Coding\Python\VisioGen\DownloadedVideos"

def clear_download_folder(folder):
    """Delete all files in the specified folder."""
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)  # Remove file
                print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

# Clear the download folder
os.makedirs(download_folder, exist_ok=True)  # Create download folder if it doesn't exist
clear_download_folder(download_folder)  # Clear existing files

# Define the search parameters
url = f'https://api.pexels.com/videos/search?query={prompt_text}&per_page=5'  # Fetch top 5 results

# Send the request
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    video_links = []
    
    downloaded_count = 0  # Counter for downloaded videos
    max_downloads = 4  # Maximum number of videos to download

    for video in data['videos']:
        # Iterate over each available video file for this video
        for video_file in video['video_files']:
            # Check if the resolution is 1920x1080
            if video_file['width'] == 1920 and video_file['height'] == 1080:
                print(f"Downloading video: {video_file['link']}")
                video_url = video_file['link']
                video_name = os.path.join(download_folder, f"{video['id']}.mp4")
                
                # Download the video
                video_response = requests.get(video_url)
                with open(video_name, 'wb') as f:
                    f.write(video_response.content)
                video_links.append(video_name)  # Store the path of downloaded video
                print(f"Downloaded: {video_name}")

                downloaded_count += 1  # Increment the download count
                if downloaded_count >= max_downloads:  # Stop if the limit is reached
                    break  # Exit the inner loop
        if downloaded_count >= max_downloads:  # Check after inner loop
            break  # Exit the outer loop

    # Return list of downloaded video paths
    print(f"Downloaded videos: {video_links}")
    print("Downloads are done!")  # Indicate that the download process is complete

    # Run the editing2.py script
    editing_script_path = r"D:\Coding\Python\VisioGen\editing2.py"  # Path to your editing2.py script
    try:
        subprocess.run(['python', editing_script_path], check=True)  # Run the script
        print("Editing script has been executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error while running editing2.py: {e}")

else:
    print(f"Failed to retrieve videos: {response.status_code}")
