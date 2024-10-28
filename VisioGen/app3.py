import os
import boto3
import subprocess
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# File paths
audio_file_path = r"/home/ubuntu/VisioGen/output.mp3"
editing_script_path = r"/home/ubuntu/VisioGen/editing.py"
main_script_path = r"/home/ubuntu/VisioGen/main.py"
output_video_path = r"/home/ubuntu/VisioGen/random_subclip_with_audio(captioned).mp4"

# EC2 instance DNS address
EC2_DNS = "ec2-15-206-80-220.ap-south-1.compute.amazonaws.com"

# Function to synthesize text to audio with adjustable speed and voice type using Amazon Polly
def synthesize_text(text, voice_gender, speech_speed):
    try:
        # Initialize a Boto3 client for Polly with specified region
        polly_client = boto3.client('polly', region_name='ap-south-1')  # Specify your desired AWS region

        # Select the appropriate voice based on the gender
        if voice_gender.lower() == 'female':
            voice_id = 'Joanna'  # Female voice for English
        else:
            voice_id = 'Matthew'  # Male voice for English

        # Adjust text to include SSML for speed control
        ssml_text = f"<speak><prosody rate='{int(speech_speed * 100)}%'>{text}</prosody></speak>"

        # Request Amazon Polly to synthesize the speech
        response = polly_client.synthesize_speech(
            Text=ssml_text,
            VoiceId=voice_id,
            OutputFormat='mp3',
            Engine='neural',
            LanguageCode='en-US',
            TextType='ssml'
        )

        # Save audio content to a file
        with open(audio_file_path, "wb") as out:
            out.write(response['AudioStream'].read())
            print(f'Audio content written to file "{audio_file_path}"')

    except Exception as e:
        print(f"Error synthesizing text with Amazon Polly: {e}")

# Function to run editing script with a timeout
def run_editing_script(timeout=300):
    try:
        subprocess.run(["python3", editing_script_path], check=True, timeout=timeout)
        print(f'Successfully ran editing script: {editing_script_path}')
        
        subprocess.run(["python3", main_script_path], check=True, timeout=timeout)
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
            print(f"Received data: {data}")  # Debugging statement

            text = data.get('text', '')
            font = data.get('font', 'Arvo-Bold')
            video_type = data.get('videoType', 'Minecraft')
            voice_gender = data.get('voiceType', 'Male')  # Now supports Male/Female
            speech_speed = float(data.get('speechSpeed', 1.0))  # Speech speed, default is 1.0

            # Check if any of the critical parameters are missing
            if not text:
                return jsonify({'status': 'error', 'message': 'Text for synthesis is required.'}), 400
            
            print(f"Text: {text}, Font: {font}, Video Type: {video_type}, Voice Gender: {voice_gender}, Speech Speed: {speech_speed}")

            synthesize_text(text, voice_gender, speech_speed)
            set_environment_variables(font, video_type, text)
            run_editing_script()

            if os.path.exists(output_video_path):
                return jsonify({'status': 'success', 'video_url': f'http://{EC2_DNS}/endpoint/video'})
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
                "Content-Disposition": "inline; filename=generated_video.mp4",
                "Cache-Control": "no-cache",
                "Access-Control-Expose-Headers": "Content-Disposition",
            }
        )
    else:
        return jsonify({'status': 'error', 'message': 'Video file not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
