from gtts import gTTS
from pydub import AudioSegment
import os
import sys
import subprocess

# Define the file paths
text_file_path = sys.argv[1]
audio_file_path = r"D:\Coding\Python\VideoEditing\output.mp3"

# Read the content of the text file
with open(text_file_path, 'r', encoding='utf-8') as file:
    text = file.read()

# Convert text to speech with British female accent
tts = gTTS(text, lang='en')

# Save the audio file temporarily
temp_audio_path = r"D:\Coding\Python\VideoEditing\temp_output.mp3"
tts.save(temp_audio_path)

# Load the temporary audio file using pydub
audio = AudioSegment.from_file(temp_audio_path)

# Slow down the speed by 0.2x (0.8x playback speed)
audio_slowed = audio.speedup(playback_speed=0.5)

# Export the modified audio to the desired file path
audio_slowed.export(audio_file_path, format='mp3')

# Remove the temporary file
os.remove(temp_audio_path)

print(f"Audio file saved at: {audio_file_path}")

# Automatically run the editing script
try:
    subprocess.run(['python', r'D:\Coding\Python\VideoEditing\editing.py'], check=True)
    print("Video editing completed successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error in editing.py: {e}")
