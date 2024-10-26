import os
import pyttsx3
import subprocess
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# File paths
audio_file_path = r"D:\Coding\Python\VisioGen\output.mp3"
editing_script_path = r"D:\Coding\Python\VisioGen\editing.py"
main_script_path = r"D:\Coding\Python\VisioGen\main.py"
output_video_path = r"D:\Coding\Python\VisioGen\random_subclip_with_audio(captioned).mp4"

# Function to synthesize text to audio
def synthesize_text(text, voice_type):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    selected_voice = None
    for voice in voices:
        if voice_type.lower() == 'female' and 'zira' in voice.name.lower():
            selected_voice = voice.id
            break
        elif voice_type.lower() == 'male' and 'david' in voice.name.lower():
            selected_voice = voice.id
            break

    if selected_voice:
        engine.setProperty('voice', selected_voice)
        print(f"Using voice: {voice.name}")
    else:
        engine.setProperty('voice', voices[0].id)
        print("No matching voice found, using default voice.")

    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate * 0.85)
    engine.save_to_file(text, audio_file_path)
    engine.runAndWait()
    print(f'Audio content written to file "{audio_file_path}"')

# Function to run editing script with a timeout
def run_editing_script(timeout=300):
    try:
        subprocess.run(["python", editing_script_path], check=True, timeout=timeout)
        print(f'Successfully ran editing script: {editing_script_path}')
        
        subprocess.run(["python", main_script_path], check=True, timeout=timeout)
        print(f'Successfully ran main script: {main_script_path}')
        
    except subprocess.TimeoutExpired:
        print(f'Script timed out after {timeout} seconds')
    except subprocess.CalledProcessError as e:
        print(f'Error occurred while running script: {e}')

# Streaming response for large files
def generate_large_file(file_path, chunk_size=8192):
    with open(file_path, 'rb') as file:
        while chunk := file.read(chunk_size):
            yield chunk

# Set environment variables
def set_environment_variables(font, video_type, text):
    os.environ['SELECTED_FONT'] = font
    os.environ['VIDEO_TYPE'] = video_type
    os.environ['RECEIVED_TEXT'] = text

# Main route for processing text and generating video
@app.route('/endpoint', methods=['POST', 'GET'])
def process_text():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            text = data.get('text', '')
            font = data.get('font', 'Arvo-Bold')
            video_type = data.get('videoType', 'Minecraft')
            voice_type = data.get('voiceType', 'Male')

            synthesize_text(text, voice_type)
            set_environment_variables(font, video_type, text)
            run_editing_script()

            if os.path.exists(output_video_path):
                return jsonify({'status': 'success', 'video_url': f'http://192.168.1.8:5000/endpoint/video'})
            else:
                return jsonify({'status': 'error', 'message': 'Video file not found'}), 404
        else:
            return jsonify({'status': 'error', 'message': 'Invalid JSON'}), 400

    elif request.method == 'GET':
        return jsonify({'status': 'error', 'message': 'Use POST to generate video.'}), 400

@app.route('/endpoint/video', methods=['GET'])
def send_video():
    if os.path.exists(output_video_path):
        return Response(
            stream_with_context(generate_large_file(output_video_path)),
            mimetype='video/mp4',
            headers={
                "Content-Disposition": "inline; filename=generated_video.mp4",  # Set to inline
                "Cache-Control": "no-cache",
                "Access-Control-Expose-Headers": "Content-Disposition",
            }
        )
    else:
        return jsonify({'status': 'error', 'message': 'Video file not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
