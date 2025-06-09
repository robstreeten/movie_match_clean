from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import openai
import httpx
import os
import json

app = FastAPI()

# CORS for frontend/backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse("frontend/build/index.html")


@app.get("/titles")
async def get_titles():
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://dds-apife.filmbankconnect.com/arts/catalogue/v1/all-contents")
            response.raise_for_status()
            data = response.json()
            titles = [item["title"] for item in data if "title" in item]
            return {
                "count": len(titles),
                "sample": titles[:10]  # Show first 10 titles
            }
    except Exception as e:
        return {"error": str(e)}


@app.get("/test")
async def test():
    return {"status": "Backend is working"}


@app.post("/match-movies")
async def match_movies(request: Request):
    data = await request.json()
    search_term = data.get("searchTerm")

    # Step 1: Fetch the movie list
    dds_api_url = "https://dds-apife.filmbankconnect.com/arts/catalogue/v1/all-contents"
    async with httpx.AsyncClient() as client:
        response = await client.get(dds_api_url)
        all_movies = response.json()

    # Step 2: Extract titles
    titles = [item["title"] for item in all_movies if "title" in item][:150]
    print("First 5 titles:", titles[:5])
    print("Search term:", search_term)
    if not titles:
        return {"matches": []}

    # Step 3: Build prompt
    prompt = f"""
You are a helpful assistant. A user is searching for movies related to: "{search_term}".

From the list below, identify only the movies that strongly relate to the topic. For each match, give a one-sentence reason.

Movies:
{chr(10).join(titles)}

Respond ONLY in this JSON format:
[
  {{ "title": "...", "reason": "..." }},
  ...
]
"""

    # Step 4: OpenAI call
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You classify movie titles based on search topics."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        parsed = json.loads(completion.choices[0].message.content.strip())
        return {"matches": parsed}
    except Exception as e:
        print("OpenAI error:", e)
        return {"matches": []}
