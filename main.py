from fastapi import FastAPI

import routers.audio_file as audio
import routers.text_input as text

tags_metadata = [
    {
        "name": "audio-file-upload",
        "description": "Operations where the audio input is uploaded as an .wav file"
    },
    {
        "name": "text-input",
        "descruption": "Operations where the text is given as input."
    }
]

app = FastAPI(
    title="Fri der man",
    description="API for fri der man",
    version="1.0.0",
    openapi_tags=tags_metadata
)
app.include_router(audio.router)
app.include_router(text.router)
