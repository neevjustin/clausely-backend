from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found in environment.")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("models/gemini-2.5-flash")

# FastAPI app setup
app = FastAPI(
    title="T&C Analyzer API",
    description="Analyzes Terms & Conditions for red/green flags.",
    version="1.0.0"
)

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://clauselyai.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class AnalyzeRequest(BaseModel):
    text: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def home():
    return {"message": "T&C Analyzer API is running."}

@app.post("/analyze")
async def analyze_tc(data: AnalyzeRequest):
    if not data.text.strip():
        raise HTTPException(status_code=400, detail="No T&C text provided.")

    prompt = f"""
        You're powering a website that explains Terms & Conditions to regular users.

        Analyze the text below and return a **valid JSON object** with these keys:

        - green_flags: List 3–5 GOOD clauses. Max 10 words per bullet. Only those which are worth mentioning.
        - red_flags: List 3–5 RISKY clauses. Max 10 words per bullet. Only those which are worth mentioning.
        - warnings: List 3–5 CAUTIONARY points. Keep it simple. Only those which are worth mentioning.
        - summary: List 3–5 high-level takeaways. Avoid repeating above. Only those which are worth mentioning.

        Requirements:
        - Reword legal language into clear, plain English.
        - Avoid jargon, legal terms, and long phrases.
        - Do NOT use markdown, formatting, or explanations.
        - Do NOT include "you", "your", "we", etc.
        - Only return clean, raw JSON. No intro or code blocks.

        T&C:
        '''{data.text}'''
        """

    try:
        response = model.generate_content(prompt)
        result = response.text.strip()

        # Try parsing JSON to validate output
        import json
        parsed = json.loads(result)

        return {"result": parsed}

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=502,
            detail="Model response was not valid JSON."
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



    
