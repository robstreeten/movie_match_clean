from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import requests
import openai
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/titles")
def get_titles():
    url = "https://dds-apife.filmbankconnect.com/arts/catalogue/v1/all-contents"
    try:
        response = requests.get(url)
        data = response.json()
        titles = [hit.get("title", "") for hit in data.get("hits", []) if "title" in hit]
        return {
            "count": len(titles),
            "sample": titles[:100]
        }
    except Exception as e:
        return {
            "error": str(e),
            "count": 0,
            "sample": []
        }

@app.post("/match-movies")
async def match_movies(request: Request):
    body = await request.json()
    search_term = body.get("searchTerm", "")
    print("Search Term:", search_term)

    # Get movie titles
    api_response = get_titles()
    titles = api_response.get("sample", [])
    print("Titles being sent to GPT:", titles)

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

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=0.7
        )
        gpt_content = response.choices[0].message.content.strip()
        print("GPT Raw Response:\n", gpt_content)

        try:
            matches = json.loads(gpt_content)
        except json.JSONDecodeError as e:
            print("JSON parsing failed:", str(e))
            matches = []

        return JSONResponse(content={"matches": matches})

    except Exception as e:
        print("OpenAI Error:", str(e))
        return JSONResponse(content={"matches": [], "error": str(e)}, status_code=500)

@app.get("/")
def serve_index():
    return FileResponse(os.path.join("frontend", "index.html"))

