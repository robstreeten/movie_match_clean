from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import openai
import httpx
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse("frontend/build/index.html")


@app.get("/test")
async def test():
    return {"status": "Backend is working"}

@app.post("/match-movies")
async def match_movies(request: Request):
    data = await request.json()
    search_term = data.get("searchTerm")

    dds_api_url = "https://dds-apife.filmbankconnect.com/arts/catalogue/v1/all-contents"
    openai.api_key = os.getenv("OPENAI_API_KEY")

    async with httpx.AsyncClient() as client:
        response = await client.get(dds_api_url)
        all_movies = response.json()

    titles = [item["title"] for item in all_movies if "title" in item]

    prompt = f"""
You are a movie classification assistant. A user has entered the term: "{search_term}".

Here is a list of movie titles:
{chr(10).join(titles)}

From this list, return only the titles that clearly relate to the term, with a 1-sentence reason per match. Be strict—only return strong matches.

Respond in this format:
[
  {{"title": "...", "reason": "..."}},
  ...
]
"""

    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
    )

    try:
        result = json.loads(completion.choices[0].message.content.strip())
    except:
        result = []

    return {"matches": result}
