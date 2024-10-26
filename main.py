from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pydub import AudioSegment
from PIL import Image
import nltk
import os
import string

# Download required NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

app = FastAPI()

# Set up templates and static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Ensure the "static" directory exists for saving images
if not os.path.exists("static"):
    os.makedirs("static")

# Input text model
class TextData(BaseModel):
    text: str
    summary_ratio: float = 0.3  # Optional, default to summarizing 30% of the text

# Summarization function
def extractive_summarizer(text, summary_ratio=0.3):
    sentences = nltk.sent_tokenize(text)
    words = nltk.word_tokenize(text.lower())
    stop_words = set(nltk.corpus.stopwords.words('english'))
    words = [word for word in words if word not in stop_words and word not in string.punctuation]

    word_frequencies = {}
    for word in words:
        word_frequencies[word] = word_frequencies.get(word, 0) + 1
    
    sentence_scores = {}
    for sentence in sentences:
        for word in nltk.word_tokenize(sentence.lower()):
            if word in word_frequencies:
                sentence_scores[sentence] = sentence_scores.get(sentence, 0) + word_frequencies[word]

    summary_length = int(len(sentences) * summary_ratio)
    sorted_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)
    summary = ' '.join(sorted_sentences[:summary_length])
    
    return summary

# HTML Content for the combined interface
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Utility App</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: auto;
            padding: 20px;
            background-color: #f4f4f4;
        }
        textarea, input[type="number"] {
            width: 100%;
        }
        button {
            margin-top: 10px;
        }
        .summary, .audio-player, .image-display {
            margin-top: 20px;
            padding: 10px;
            background: #fff;
            border: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <h1>Utility App</h1>

    <h2>Text Summarizer</h2>
    <form id="summarize-form">
        <textarea id="text" placeholder="Enter text to summarize..."></textarea>
        <input type="number" id="summary_ratio" placeholder="Summary Ratio (e.g., 0.3)" step="0.1" min="0" max="1" value="0.3" required>
        <button type="submit">Summarize</button>
    </form>
    <div class="summary" id="summary"></div>

    <h2>Audio Trimming</h2>
    <form id="trim-form" enctype="multipart/form-data">
        <input type="file" name="audio_file" accept=".wav" required>
        <br>
        <label for="start">Start Time (seconds):</label>
        <input type="number" name="start" id="start" value="0" step="0.1" required>
        <br>
        <label for="end">End Time (seconds):</label>
        <input type="number" name="end" id="end" value="0" step="0.1" required>
        <br>
        <button type="submit">Trim Audio</button>
    </form>
    <div id="audio-player" class="audio-player"></div>

    <h2>Image Resizing</h2>
    <form id="resize-form" enctype="multipart/form-data">
        <input type="file" name="image_file" accept="image/*" required>
        <br>
        <label for="width">New Width (pixels):</label>
        <input type="number" name="width" id="width" required>
        <br>
        <label for="height">New Height (pixels):</label>
        <input type="number" name="height" id="height" required>
        <br>
        <button type="submit">Resize Image</button>
    </form>
    <div id="image-display" class="image-display"></div>

    <script>
        document.getElementById('summarize-form').addEventListener('submit', async (event) => {
            event.preventDefault();
            const text = document.getElementById('text').value;
            const summaryRatio = document.getElementById('summary_ratio').value;

            const response = await fetch('/summarize/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text, summary_ratio: parseFloat(summaryRatio) })
            });

            if (response.ok) {
                const result = await response.json();
                document.getElementById('summary').innerText = result.summary;
            } else {
                const error = await response.json();
                document.getElementById('summary').innerText = error.detail;
            }
        });

        document.getElementById('trim-form').addEventListener('submit', async (event) => {
            event.preventDefault();
            const formData = new FormData(event.target);
            const response = await fetch('/trim-audio/', {
                method: 'POST',
                body: formData,
            });
            const result = await response.json();
            if (result.success) {
                document.getElementById('audio-player').innerHTML = 
                    `<h2>Trimmed Audio:</h2>
                    <audio controls>
                        <source src="${result.file_path}" type="audio/wav">
                        Your browser does not support the audio element.
                    </audio>`;
            } else {
                alert(result.message);
            }
        });

        document.getElementById('resize-form').addEventListener('submit', async (event) => {
            event.preventDefault();
            const formData = new FormData(event.target);
            const response = await fetch('/resize-image/', {
                method: 'POST',
                body: formData,
            });
            const result = await response.json();
            if (result.success) {
                document.getElementById('image-display').innerHTML = 
                    `<h2>Original Image:</h2>
                    <img src="${result.original_file_path}" alt="Original Image" style="max-width: 100%; height: auto;">
                    <h2>Resized Image:</h2>
                    <img src="${result.resized_file_path}" alt="Resized Image" style="max-width: 100%; height: auto;">`;
            } else {
                alert(result.message);
            }
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_form():
    return HTML_CONTENT

@app.post("/summarize/")
async def summarize(text_data: TextData):
    if not text_data.text:
        raise HTTPException(status_code=400, detail="Text content cannot be empty")
    
    summary = extractive_summarizer(text_data.text, summary_ratio=text_data.summary_ratio)
    return {"summary": summary}

@app.post("/trim-audio")
async def trim_audio(
    audio_file: UploadFile = File(...),
    start: float = Form(0),
    end: float = Form(0)
):
    # Check if the uploaded file is a WAV file
    if audio_file.content_type != 'audio/wav':
        return JSONResponse(content={"success": False, "message": "Unsupported audio format. Please upload a WAV file."}, status_code=400)

    try:
        # Load the audio file
        audio = AudioSegment.from_wav(audio_file.file)

        # Trim the audio if start and end times are provided
        if start < 0 or end < 0 or start >= len(audio) / 1000 or end <= start:
            return JSONResponse(content={"success": False, "message": "Invalid start or end time."}, status_code=400)

        # Trim the audio
        trimmed_audio = audio[start * 1000:end * 1000]  # Convert to milliseconds

        # Save the trimmed audio
        output_path = f"static/trimmed_{audio_file.filename}"
        trimmed_audio.export(output_path, format="wav")

        return JSONResponse(content={"success": True, "file_path": output_path})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)})

@app.post("/resize-image")
async def resize_image(
    image_file: UploadFile = File(...),
    width: int = Form(...),
    height: int = Form(...)
):
    # Ensure the uploaded file is an image
    if image_file.content_type.startswith('image/'):

        try:
            # Load the image
            image = Image.open(image_file.file)
            original_file_path = f"static/original_{image_file.filename}"
            image.save(original_file_path)

            # Resize the image
            resized_image = image.resize((width, height))
            resized_file_path = f"static/resized_{image_file.filename}"
            resized_image.save(resized_file_path)

            return JSONResponse(content={"success": True, "original_file_path": original_file_path, "resized_file_path": resized_file_path})
        except Exception as e:
            return JSONResponse(content={"success": False, "message": str(e)}, status_code=400)
    else:
        return JSONResponse(content={"success": False, "message": "Unsupported image format."}, status_code=400)

# Run the app with the command: uvicorn main:app --reload
