
# 🗣️ ConvoAi

ConvoAi is a web application built using Flask that allows users to upload audio files, transcribe them, and analyze the sentiment of the transcription using Google's Generative AI and Cloud Storage.

## ✨ Features

- **Upload Audio Files**: Users can upload audio files which are then saved to Google Cloud Storage.
- **Transcription and Sentiment Analysis**: The uploaded audio files are transcribed, and the sentiment of the transcription is analyzed and saved.
- **List and Serve Files**: Users can list all the saved audio and transcription files and download them.

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/akshayk122/ConvoAi.git
   cd ConvoAi
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up Google Cloud Storage:
   - Ensure you have a Google Cloud project set up.
   - Create a bucket named `convoaiproject`.
   - Save your Google Cloud credentials JSON file and set the environment variable:
     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
     ```

4. Configure the API key:
   - Create a file named `config.json` in the `static` folder.
   - Add your API key in the following format:
     ```json
     {
       "API_KEY": "your_google_api_key"
     }
     ```

## 🚀 Usage

1. Run the Flask application:
   ```bash
   python main.py
   ```

2. Access the application at `http://localhost:8080`.
