from flask import Flask, render_template, request, jsonify,send_file
from google.cloud import storage
import google.generativeai as genai
import json 
import io
import os
import datetime

app = Flask(__name__,static_folder='static')

storage_client = storage.Client()
bucket_name = 'convoaiproject'  
bucket = storage_client.bucket(bucket_name)
TRANSCRIPTS_FOLDER = 'static/rtranscripts/'
AUDIOS_FOLDER = 'static/recordings/'

#read api key
configfile="static/config.json"
with open(configfile, 'r') as file:
    data = json.load(file)
    key=data.get("API_KEY")

genai.configure(api_key=key)

@app.route('/')
def index():
    return render_template('index.html')


def upload_audio_text(file_content,filename,content_type):
    blob = bucket.blob(filename)
    blob.upload_from_string(
    file_content,
    content_type=content_type
    )      

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    try:
        if 'audio_file' not in request.files:
            return "No audio file provided.", 400

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_file = request.files['audio_file']
        audio_content = audio_file.read()
        audio_filename = f'static/audio/audio_{timestamp}.wav'
        upload_audio_text(audio_content,audio_filename,audio_file.content_type)
        text_filename = f'static/atranscripts/audio_transcript_{timestamp}.txt'
        response_text=analyze_audio(audio_filename)
        json_response=response_text.strip().removeprefix('```json').removesuffix('```')
        data = json.loads(json_response)
        print(data)
        transcript = data.get("transcription")
        score=data.get("sentiment_analysis")
        content = f"Transcript:\n{transcript}\n\nSentiment: {score}"
        upload_audio_text(content,text_filename,'text/plain')
        return content

    except Exception as e:
        return str(e), 500


@app.route('/upload_recording', methods=['POST'])
def upload_recording():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']

        if audio_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        audio_content = audio_file.read()
        if len(audio_content) == 0:
            return jsonify({'error': 'File is empty'}), 400

        # Save audio file to Google Cloud Storage
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f'static/recordings/recording_{timestamp}.wav'
        upload_audio_text(audio_content,audio_filename,audio_file.content_type)
        text_filename = f'static/rtranscripts/transcript_{timestamp}.txt'
        # Save the transcript to Google Cloud Storage
        audio_file_uri=f"static/recordings/recording_{timestamp}.wav"
        response_text=analyze_audio(audio_file_uri)
        json_response=response_text.strip().removeprefix('```json').removesuffix('```')
        data = json.loads(json_response)
        transcript = data.get("transcription")
        score=data.get("sentiment_analysis")
        content = f"Transcript:\n{transcript}\n\nSentiment : {score}"
        upload_audio_text(content,text_filename,'text/plain')
        return jsonify({'message': 'Success', 'audio_url': audio_filename, 'transcript_url': text_filename}), 200

    except speech.exceptions.GoogleAPICallError as api_error:
        print(f"Google Speech API Error: {str(api_error)}")
        return jsonify({'error': 'Speech-to-Text processing failed'}), 500

    except Exception as e:
        print(f"Error in upload_recording: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
@app.route('/list_files')
def list_files():
    transcripts = []
    audios = []
    u_trans=[]
    u_audios=[]

    # List  transcript files
    blobs = bucket.list_blobs(prefix='static/rtranscripts/')
    for blob in blobs:
        if blob.name.endswith(".txt"):
            transcripts.append({
                'name': blob.name.split("/")[-1],
                'url': f'/serve_text/{blob.name}'
            })

    # List recording  files
    ablobs = bucket.list_blobs(prefix='static/recordings/')
    for blob in ablobs:
        if blob.name.endswith(".wav"):
            audios.append({
                'name': blob.name.split("/")[-1],
                'url': f'/serve_audio/{blob.name}' 
            })
    
    # List uploaded text files
    ublobs = bucket.list_blobs(prefix='static/atranscripts/')
    for blob in ublobs:
        if blob.name.endswith(".txt"):
            u_trans.append({
                'name': blob.name.split("/")[-1],
                'url': f'/serve_text/{blob.name}'
            })
    
    # List uploaded audio files
    ua_blobs = bucket.list_blobs(prefix='static/audio/')
    for blob in ua_blobs:
        if blob.name.endswith(".wav"):
            u_audios.append({
                'name': blob.name.split("/")[-1],
                'url': f'/serve_audio/{blob.name}' 
            })

    return jsonify({
        'transcripts': transcripts,
        'audios': audios,
        'u_trans' : u_trans,
        'u_audios' : u_audios
    })

@app.route('/serve_text/<path:filename>')
def serve_txt(filename):
    try:
        blob = bucket.blob(filename)
        content = blob.download_as_text()
        return content, 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        return jsonify({'error': 'An error occurred while serving the transcript file'}), 500

# Add this new route to serve audio files
@app.route('/serve_audio/<path:filename>')
def serve_audio(filename):
    blob = bucket.blob(filename)
    
    file_bytes = blob.download_as_bytes()
    return send_file(
        io.BytesIO(file_bytes),
        mimetype='audio/wav',
        as_attachment=True,
        download_name=filename.split('/')[-1]
    )

##audio to transcript

def analyze_audio(audio_file_uri):
    try:
        blob_path = audio_file_uri
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(audio_file_uri)
        
        # Download the audio file content
        audio_data = blob.download_as_bytes()
        
        # Configure Gemini
        generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
        }
        
        # Initialize Gemini model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config
        )
        contents = {
            "parts": [
                {
                    "text":"""transcribe this WAV format audio and provide the transcript and sentiment analysis score in JSON format. If no transcript is available,
                            - return 0 for the sentiment analysis score,if transcript was available return the esntiment like Possitive,Negative,Nuetral. The JSON response format should be as follows
                            -json reponse:{
                                            "transcription": "full transcribed text here",
                                            "sentiment_analysis": score
                                        }

                        - output should just json

                    """

                },
                {
                    "inline_data": {
                        "mime_type": "audio/wav",
                        "data": audio_data
                    }
                }
            ]
        }
        
        response = model.generate_content(contents)
        print(response)
        return response.text

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "location": "Error accessing file in GCS bucket"
        })


# Example usage
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)