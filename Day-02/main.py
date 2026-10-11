import os
import uuid
import asyncio
import edge_tts
from deep_translator import GoogleTranslator
from flask import Flask, Response, jsonify, render_template, request, url_for

app = Flask(__name__)

AUDIO_FOLDER = os.path.join(app.static_folder, "audio")
os.makedirs(AUDIO_FOLDER, exist_ok=True)

PREVIEW_TEXT = "Hello, this is a preview of this voice."


# build the voice list and generate audio

def load_voice_map():
    voices = asyncio.run(edge_tts.list_voices())
    voice_map = {}
    for voice in voices:
        locale = voice["Locale"]
        language_name = voice["FriendlyName"].split(" - ")[-1]
        persona_name = voice["FriendlyName"].split(" Online")[0].replace("Microsoft ", "")
        voice_map.setdefault(locale, {"language_name": language_name})
        voice_map[locale].setdefault(voice["Gender"], {"short_name": voice["ShortName"], "name": persona_name})
    return dict(sorted(voice_map.items(), key=lambda item: item[1]["language_name"]))


# loaded once at startup so every request reuses the same catalog
VOICE_MAP = load_voice_map()


# runs edge-tts and collects the streamed audio into raw bytes (no file needed)
async def synthesize_to_bytes(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    audio_bytes = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes.extend(chunk["data"])
    return bytes(audio_bytes)


@app.route("/")
def home():
    return render_template("index.html", voice_map=VOICE_MAP)


# generates a short live sample so you can hear a voice before converting
@app.route("/preview")
def preview():
    voice = request.args.get("voice")
    target_language = voice.split("-")[0]

    try:
        text = GoogleTranslator(source="auto", target=target_language).translate(PREVIEW_TEXT)
    except Exception:
        text = PREVIEW_TEXT

    audio_bytes = asyncio.run(synthesize_to_bytes(text, voice))
    return Response(audio_bytes, mimetype="audio/mpeg")


# translates the submitted text into the voice's language, then speaks it
@app.route("/convert", methods=["POST"])
def convert():
    text = request.form.get("text")
    voice = request.form.get("voice")

    target_language = voice.split("-")[0]
    translated_text = GoogleTranslator(source="auto", target=target_language).translate(text)

    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(AUDIO_FOLDER, filename)

    asyncio.run(edge_tts.Communicate(translated_text, voice).save(filepath))

    audio_url = url_for("static", filename=f"audio/{filename}")
    return jsonify(audio_url=audio_url, translated_text=translated_text)



if __name__ == "__main__":
    app.run(debug=True, port=5001)
