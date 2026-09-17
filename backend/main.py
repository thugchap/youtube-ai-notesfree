import os, re, io, base64
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

load_dotenv()
app = FastAPI(title="YouTube AI Notes")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class Req(BaseModel):
    youtube_url: HttpUrl
    language: str = "Hindi"
    exam_style: str = "Detailed exam notes"

def get_id(url):
    m = re.search(r"(?:v=|youtu\.be/|youtube\.com/shorts/)([A-Za-z0-9_-]{11})", str(url))
    if not m: raise ValueError("Valid YouTube URL नहीं मिली।")
    return m.group(1)

def transcript(vid):
    try:
        data = YouTubeTranscriptApi().fetch(vid)
        return "\n".join(x.text for x in data)
    except Exception:
        try:
            data = YouTubeTranscriptApi.get_transcript(vid, languages=["hi","en"])
            return "\n".join(x["text"] for x in data)
        except Exception as e:
            raise RuntimeError("Accessible transcript/captions नहीं मिले।") from e

def ai_notes(text, language, style):
    key = os.getenv("OPENAI_API_KEY")
    if not key: raise RuntimeError("OPENAI_API_KEY .env में सेट करें।")
    prompt = f"""Create {style} from this YouTube transcript in {language}.
Do not invent facts. Structure:
# Title
## 1. Topic overview
## 2. Detailed theory
## 3. Important definitions
## 4. Important facts, dates and names
## 5. Examples
## 6. Exceptions/special points if supported
## 7. Quick revision
## 8. 10 MCQs, each with 4 options, answer and short explanation.
Transcript:
{text[:120000]}"""
    r = OpenAI(api_key=key).responses.create(
        model=os.getenv("OPENAI_MODEL","gpt-5.6"), input=prompt)
    return r.output_text

def pdf(notes):
    b = io.BytesIO()
    fp="/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
    bp="/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
    if os.path.exists(fp):
        pdfmetrics.registerFont(TTFont("NotoDeva",fp))
        if os.path.exists(bp): pdfmetrics.registerFont(TTFont("NotoDevaBold",bp))
        body, bold="NotoDeva","NotoDevaBold" if os.path.exists(bp) else "NotoDeva"
    else: body=bold="Helvetica"
    s=getSampleStyleSheet()
    title=ParagraphStyle("t",parent=s["Title"],fontName=bold,fontSize=18,leading=24)
    h=ParagraphStyle("h",parent=s["Heading2"],fontName=bold,fontSize=13,leading=18,spaceBefore=10)
    p=ParagraphStyle("p",parent=s["BodyText"],fontName=body,fontSize=10.5,leading=16,spaceAfter=7)
    story=[]
    for line in notes.splitlines():
        line=line.strip()
        if not line: story.append(Spacer(1,5))
        elif line.startswith("# "): story.append(Paragraph(line[2:],title))
        elif line.startswith("## "): story.append(Paragraph(line[3:],h))
        else:
            line=line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            story.append(Paragraph(line,p))
    SimpleDocTemplate(b,pagesize=A4,rightMargin=40,leftMargin=40,topMargin=40,bottomMargin=40).build(story)
    return b.getvalue()

@app.post("/generate")
def generate(req: Req):
    try:
        vid=get_id(req.youtube_url)
        text=transcript(vid)
        notes=ai_notes(text,req.language,req.exam_style)
        return {"video_id":vid,"notes":notes,
                "pdf_base64":base64.b64encode(pdf(notes)).decode()}
    except Exception as e:
        raise HTTPException(400,str(e))
