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
            titles = [item["title"] for item in data if "title" in item]
            return {
                "count": len(titles),
                "sample": titles[:10]
            }
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

