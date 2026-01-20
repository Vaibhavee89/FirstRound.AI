import os
import subprocess
import aiohttp
import openai
import json
import base64
import tempfile
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import Response, JSONResponse, FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import VoiceResponse, Gather
from loguru import logger

load_dotenv()

DAILY_API_KEY = os.getenv("DAILY_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "http://localhost:7860")

# Store interview context for phone calls
interview_contexts = {}

# Directory for conversation logs and audio files
LOGS_DIR = Path("/app/logs")
LOGS_DIR.mkdir(exist_ok=True)
AUDIO_DIR = Path("/app/audio")
AUDIO_DIR.mkdir(exist_ok=True)

# OpenAI TTS voice options: alloy, echo, fable, onyx, nova, shimmer
OPENAI_TTS_VOICE = "nova"  # Professional, clear female voice

# Set to False to use Twilio's Polly voices (faster) or True for OpenAI TTS (better quality but slower)
USE_OPENAI_TTS = False  # Disabled for faster response times

def generate_openai_tts(text: str, filename: str) -> str:
    """Generate speech using OpenAI TTS API and save to file"""
    if not USE_OPENAI_TTS:
        return None  # Skip TTS generation for faster responses
    
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.audio.speech.create(
            model="tts-1",  # tts-1 is faster than tts-1-hd
            voice=OPENAI_TTS_VOICE,
            input=text,
            response_format="mp3"
        )
        
        audio_path = AUDIO_DIR / filename
        response.stream_to_file(str(audio_path))
        logger.info(f"Generated TTS audio: {audio_path}")
        return str(audio_path)
    except Exception as e:
        logger.error(f"OpenAI TTS error: {e}")
        return None

def save_conversation_log(call_sid: str, context: dict, status: str = "in_progress"):
    """Save conversation log to JSON file"""
    log_data = {
        "call_sid": call_sid,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "job_description": context.get("jd", "")[:500],  # Truncate for readability
        "resume_summary": context.get("resume", "")[:500],
        "conversation": context.get("conversation", []),
        "exchange_count": len(context.get("conversation", [])) // 2,
        "evaluation": context.get("evaluation", None)
    }
    
    log_file = LOGS_DIR / f"interview_{call_sid}.json"
    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Saved conversation log to {log_file}")
    return log_file

async def evaluate_interview(call_sid: str, context: dict) -> dict:
    """Evaluate the interview and return scores and decision"""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        conversation_text = "\n".join([
            f"{'Candidate' if msg['role'] == 'user' else 'Interviewer'}: {msg['content']}"
            for msg in context.get("conversation", [])
        ])
        
        evaluation_prompt = f"""You are an expert HR evaluator. Analyze this phone screening interview and provide a detailed evaluation.

JOB DESCRIPTION:
{context.get('jd', 'Not provided')}

CANDIDATE RESUME:
{context.get('resume', 'Not provided')}

INTERVIEW TRANSCRIPT:
{conversation_text}

Evaluate the candidate on the following criteria (score 1-10 for each):

1. **Technical Fit**: How well do the candidate's skills match the job requirements?
2. **Experience Relevance**: How relevant is their past experience to this role?
3. **Communication Skills**: How clearly and effectively did they communicate?
4. **Problem-Solving**: Did they demonstrate analytical thinking and problem-solving ability?
5. **Culture Fit**: Based on their responses, would they fit well in a professional environment?

Provide your response in the following JSON format ONLY (no other text):
{{
    "technical_fit": <score 1-10>,
    "experience_relevance": <score 1-10>,
    "communication": <score 1-10>,
    "problem_solving": <score 1-10>,
    "culture_fit": <score 1-10>,
    "overall_score": <average of all scores>,
    "decision": "<ACCEPT or REJECT>",
    "summary": "<2-3 sentence summary of the candidate>",
    "strengths": ["<strength 1>", "<strength 2>"],
    "areas_of_concern": ["<concern 1>", "<concern 2>"]
}}

Decision criteria:
- ACCEPT if overall_score >= 6 AND no individual score below 4
- REJECT otherwise"""

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": evaluation_prompt}],
            max_tokens=500
        )
        
        response_text = completion.choices[0].message.content.strip()
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        evaluation = json.loads(response_text)
        logger.info(f"Evaluation for {call_sid}: {evaluation}")
        return evaluation
        
    except Exception as e:
        logger.error(f"Evaluation error for {call_sid}: {e}")
        return {
            "technical_fit": 5,
            "experience_relevance": 5,
            "communication": 5,
            "problem_solving": 5,
            "culture_fit": 5,
            "overall_score": 5,
            "decision": "PENDING",
            "summary": "Evaluation could not be completed automatically.",
            "strengths": [],
            "areas_of_concern": ["Automatic evaluation failed"]
        }

async def update_application_status(call_sid: str, evaluation: dict):
    """Update the application status in the frontend database"""
    try:
        frontend_url = os.getenv("FRONTEND_URL", "http://frontend:3000")
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{frontend_url}/api/applications/{call_sid}",
                json={
                    "status": "accepted" if evaluation.get("decision") == "ACCEPT" else "rejected",
                    "evaluation": evaluation,
                    "interviewedAt": datetime.now().isoformat()
                }
            ) as resp:
                if resp.status == 200:
                    logger.info(f"Updated application status for {call_sid}")
                else:
                    logger.error(f"Failed to update application: {await resp.text()}")
    except Exception as e:
        logger.error(f"Error updating application status: {e}")

class InterviewRequest(BaseModel):
    jd: str
    resume: str

class PhoneInterviewRequest(BaseModel):
    jd: str
    resume: str
    phone_number: str  # Candidate's phone number to call

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown (cleanup subprocesses if needed, though they might outlive)

app = FastAPI(lifespan=lifespan)

@app.post("/start-interview")
async def start_interview(request: InterviewRequest):
    """Start a web-based interview using Daily.co"""
    if not DAILY_API_KEY:
        raise HTTPException(status_code=500, detail="DAILY_API_KEY not configured")

    # 1. Create a Daily room
    headers = {
        "Authorization": f"Bearer {DAILY_API_KEY}",
        "Content-Type": "application/json"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.daily.co/v1/rooms", headers=headers, json={"properties": {"exp": 3600}}) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=500, detail=f"Failed to create room: {await resp.text()}")
            room_data = await resp.json()
            room_url = room_data["url"]
            room_name = room_data["name"]

        # 2. Create a meeting token for the bot (owner)
        async with session.post("https://api.daily.co/v1/meeting-tokens", headers=headers, json={"properties": {"room_name": room_name, "is_owner": True}}) as resp:
             if resp.status != 200:
                raise HTTPException(status_code=500, detail=f"Failed to create token: {await resp.text()}")
             token_data = await resp.json()
             bot_token = token_data["token"]

    # 3. Spawn the bot process
    cmd = [
        "python", "bot_runner.py",
        "-u", room_url,
        "-t", bot_token,
        "--jd", request.jd,
        "--resume", request.resume
    ]
    
    subprocess.Popen(cmd)
    return {"room_url": room_url}

@app.post("/start-phone-interview")
async def start_phone_interview(request: PhoneInterviewRequest):
    """Start a phone-based interview by calling the candidate"""
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        raise HTTPException(status_code=500, detail="Twilio credentials not configured")

    try:
        client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Store context with a temporary key, will be moved when we get the call SID
        # We use the phone number as temp key since it's unique per call attempt
        temp_key = f"pending_{request.phone_number}"
        interview_contexts[temp_key] = {
            "jd": request.jd,
            "resume": request.resume,
        }
        
        # Use webhook URL - Twilio will call this when answered
        call = client.calls.create(
            to=request.phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{WEBHOOK_BASE_URL}/twilio/voice-webhook",
            status_callback=f"{WEBHOOK_BASE_URL}/twilio/status-callback",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
        )
        
        # Move context to actual call SID
        interview_contexts[call.sid] = interview_contexts.pop(temp_key)
        
        logger.info(f"Initiated call {call.sid} to {request.phone_number}")
        return {"call_sid": call.sid, "status": "calling"}
        
    except Exception as e:
        logger.error(f"Failed to initiate call: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")

@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve generated audio files for Twilio to play"""
    audio_path = AUDIO_DIR / filename
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(str(audio_path), media_type="audio/mpeg")

@app.post("/twilio/voice-webhook")
async def twilio_voice_webhook(request: Request):
    """Twilio webhook called when call is answered - returns TwiML with interview questions"""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    
    logger.info(f"Voice webhook called for {call_sid}")
    
    context = interview_contexts.get(call_sid, {"jd": "", "resume": ""})
    
    response = VoiceResponse()
    
    # Generate greeting with OpenAI TTS
    greeting_text = (
        "Hi! This is Alex from FirstRound AI. Thanks for taking my call! "
        "I've reviewed your resume and I'm excited to learn more about your experience. "
        "This will be a quick screening call. Let's get started."
    )
    greeting_audio = generate_openai_tts(greeting_text, f"greeting_{call_sid}.mp3")
    
    if greeting_audio:
        response.play(f"{WEBHOOK_BASE_URL}/audio/greeting_{call_sid}.mp3")
    else:
        response.say(greeting_text, voice="Polly.Joanna")  # Fallback to AWS Polly
    
    # Generate first question with OpenAI TTS
    first_question = "First, could you please introduce yourself and tell me a bit about your background?"
    question_audio = generate_openai_tts(first_question, f"q1_{call_sid}.mp3")
    
    # Use Gather to collect speech input - move to next question after 10 sec pause
    gather = response.gather(
        input="speech",
        action=f"{WEBHOOK_BASE_URL}/twilio/process-response/{call_sid}",
        method="POST",
        speech_timeout="10",  # Move on after 10 seconds of silence
        timeout=30,  # Wait up to 30 seconds for speech to start
        language="en-US"
    )
    
    if question_audio:
        gather.play(f"{WEBHOOK_BASE_URL}/audio/q1_{call_sid}.mp3")
    else:
        gather.say(first_question, voice="Polly.Joanna")
    
    # If no input, prompt again
    response.say("I didn't catch that. Let me try again.", voice="Polly.Joanna")
    response.redirect(f"{WEBHOOK_BASE_URL}/twilio/voice-webhook")
    
    return Response(content=str(response), media_type="application/xml")

@app.post("/twilio/process-response/{call_sid}")
async def process_response(request: Request, call_sid: str):
    """Process candidate's speech response and generate next question"""
    form_data = await request.form()
    speech_result = form_data.get("SpeechResult", "")
    
    logger.info(f"Received speech from {call_sid}: {speech_result[:100]}...")
    
    context = interview_contexts.get(call_sid, {"jd": "", "resume": "", "conversation": []})
    
    # Initialize conversation history if not exists
    if "conversation" not in context:
        context["conversation"] = []
    
    # Add user response to conversation
    context["conversation"].append({"role": "user", "content": speech_result})
    
    # Generate AI response using OpenAI
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        system_prompt = f"""You are Alex, a friendly AI recruiter conducting a thorough phone screening interview.

JOB DESCRIPTION:
{context.get('jd', 'Not provided')}

CANDIDATE RESUME:
{context.get('resume', 'Not provided')}

INTERVIEW STRUCTURE (5 questions total):
1. Introduction & Background - Ask about their overall experience and career journey
2. Technical Skills - Deep dive into their technical expertise relevant to the role
3. Project Experience - Ask about a specific project they worked on and their contributions
4. Problem Solving - Present a scenario or ask how they handled a challenging situation
5. Culture & Goals - Ask about their career goals and what they're looking for

GUIDELINES:
- Ask ONE question at a time and let the candidate speak fully
- Encourage detailed responses - say things like "Tell me more" or "Can you elaborate?"
- Reference specific items from their resume
- Ask follow-up questions to get deeper insights
- Be patient and give candidates time to think and respond thoroughly
- Be encouraging but professional
- After question 5, wrap up the interview professionally

Current question number: {(len(context['conversation']) // 2) + 1}
If this is question 6 or more, wrap up the interview."""

        messages = [{"role": "system", "content": system_prompt}] + context["conversation"]
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # Faster model for real-time conversation
            messages=messages,
            max_tokens=100  # Shorter responses for phone
        )
        
        ai_response = completion.choices[0].message.content
        context["conversation"].append({"role": "assistant", "content": ai_response})
        
        # Update context
        interview_contexts[call_sid] = context
        
        # Save conversation log
        save_conversation_log(call_sid, context, "in_progress")
        
        logger.info(f"AI response for {call_sid}: {ai_response[:100]}...")
        
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        ai_response = "I apologize, I'm having some technical difficulties. Could you please repeat that?"
    
    response = VoiceResponse()
    
    # Generate unique audio filename based on exchange count
    exchange_num = len(context.get("conversation", [])) // 2
    audio_filename = f"response_{call_sid}_{exchange_num}.mp3"
    
    # Check if we should end the interview (after 5 questions = 10 messages)
    if len(context["conversation"]) >= 10:
        # Generate closing audio with OpenAI TTS
        closing_text = ai_response + " Thank you so much for your time today. We'll be in touch soon with next steps. Have a great day!"
        closing_audio = generate_openai_tts(closing_text, f"closing_{call_sid}.mp3")
        
        if closing_audio:
            response.play(f"{WEBHOOK_BASE_URL}/audio/closing_{call_sid}.mp3")
        else:
            response.say(closing_text, voice="Polly.Joanna")
        response.hangup()
    else:
        # Generate response audio with OpenAI TTS
        response_audio = generate_openai_tts(ai_response, audio_filename)
        
        # Continue the conversation - move to next question after 10 sec pause
        gather = response.gather(
            input="speech",
            action=f"{WEBHOOK_BASE_URL}/twilio/process-response/{call_sid}",
            method="POST",
            speech_timeout="10",  # Move on after 10 seconds of silence
            timeout=30,  # Wait up to 30 seconds for speech to start
            language="en-US"
        )
        if response_audio:
            gather.play(f"{WEBHOOK_BASE_URL}/audio/{audio_filename}")
        else:
            gather.say(ai_response, voice="Polly.Joanna")
        
        # Fallback if no speech detected
        response.say("Are you still there?", voice="Polly.Joanna")
        response.redirect(f"{WEBHOOK_BASE_URL}/twilio/process-response/{call_sid}")
    
    return Response(content=str(response), media_type="application/xml")

@app.post("/twilio/status-callback")
async def twilio_status_callback(request: Request):
    """Twilio status callback for call events"""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")
    
    logger.info(f"Call {call_sid} status: {call_status}")
    
    if call_status == "completed":
        if call_sid in interview_contexts:
            context = interview_contexts[call_sid]
            
            # Only evaluate if there was actual conversation
            if len(context.get("conversation", [])) >= 2:
                logger.info(f"Evaluating interview for {call_sid}...")
                evaluation = await evaluate_interview(call_sid, context)
                context["evaluation"] = evaluation
                
                # Update application status in frontend
                await update_application_status(call_sid, evaluation)
            
            # Save final conversation log with evaluation
            save_conversation_log(call_sid, context, call_status)
            del interview_contexts[call_sid]
            
    elif call_status in ["failed", "busy", "no-answer"]:
        if call_sid in interview_contexts:
            save_conversation_log(call_sid, interview_contexts[call_sid], call_status)
            del interview_contexts[call_sid]
    
    return {"status": "ok"}

@app.get("/logs")
async def list_logs():
    """List all conversation logs"""
    logs = []
    for log_file in LOGS_DIR.glob("interview_*.json"):
        with open(log_file) as f:
            log_data = json.load(f)
            logs.append({
                "call_sid": log_data.get("call_sid"),
                "timestamp": log_data.get("timestamp"),
                "status": log_data.get("status"),
                "exchange_count": log_data.get("exchange_count", 0)
            })
    return sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)

@app.get("/logs/{call_sid}")
async def get_log(call_sid: str):
    """Get a specific conversation log"""
    log_file = LOGS_DIR / f"interview_{call_sid}.json"
    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Log not found")
    
    with open(log_file) as f:
        return json.load(f)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
