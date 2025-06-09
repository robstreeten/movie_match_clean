from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

# Allow local dev + production access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API is up"}

@app.get("/raw")
async def get_raw():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://dds-apife.filmbankconnect.com/arts/catalogue/v1/all-contents")
            response.raise_for_status()
            data = response.json()

            # Show keys at the top level and 3 items from any list inside
            return {
                "top_level_keys": list(data.keys()),
                "example_value": data.get("content", [])[:3] if isinstance(data.get("content", []), list) else "No list under 'content'"
            }
    except Exception as e:
        return {"error": str(e)}


@app.get("/titles")
async def get_titles():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://dds-apife.filmbankconnect.com/arts/catalogue/v1/all-contents")
            response.raise_for_status()
            data = response.json()

            hits = data.get("hits", [])
            titles = [item.get("title") for item in hits if "title" in item]

            return {
                "count": len(titles),
                "sample": titles[:10]
            }
    except Exception as e:
        return {"error": str(e)}

from fastapi import Request
import openai
import os
import json

@app.post("/match-movies")
async def match_movies(request: Request):
    try:
        body = await request.json()
        search_term = body.get("searchTerm", "")

        # Fetch movie titles
        async with httpx.AsyncClient() as client:
            response = await client.get("https://dds-apife.filmbankconnect.com/arts/catalogue/v1/all-contents")
            response.raise_for_status()
            data = response.json()
            hits = data.get("hits", [])
            titles = [item.get("title") for item in hits if "title" in item][:100]

        # Build GPT prompt
        prompt = f"""
You're a helpful assistant. A user is looking for movies related to: "{search_term}".

From this list, choose any strong matches and explain in one sentence why they relate.

Movies:
{chr(10).join(titles)}

Return your answer ONLY in this JSON format:
[
  {{ "title": "...", "reason": "..." }},
  ...
]
"""

        openai.api_key = os.getenv("OPENAI_API_KEY")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a movie classification assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )

        gpt_content = response.choices[0].message.content.strip()
        matches = json.loads(gpt_content)

        return {"matches": matches}

    except Exception as e:
        return {"error": str(e)}

