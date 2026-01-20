import asyncio
import os
import sys
import argparse

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.frames.frames import LLMMessagesFrame, EndFrame
from pipecat.processors.aggregators.llm_response import LLMUserResponseAggregator
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.openai import OpenAILLMService
from pipecat.transports.services.daily import DailyParams, DailyTransport
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

async def main():
    parser = argparse.ArgumentParser(description="Pipecat Job Interview Bot")
    parser.add_argument("-u", "--url", type=str, required=True, help="Daily.co Room URL")
    parser.add_argument("-t", "--token", type=str, required=True, help="Daily.co Meeting Token")
    parser.add_argument("--jd", type=str, default="", help="Job Description")
    parser.add_argument("--resume", type=str, default="", help="Candidate Resume")
    args = parser.parse_args()

    logger.info(f"Starting bot in room: {args.url}")

    transport = DailyTransport(
        room_url=args.url,
        token=args.token,
        bot_name="Interviewer",
        params=DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            camera_out_enabled=False,
            vad_enabled=True,
            vad_analyzer_profile="daily-pty",
            vad_audio_passthrough=True,
        ),
    )

    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="79a125e8-cd45-4c13-8a67-188112f4dd22", # Example voice
    )
    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
    )

    messages = [
        {
            "role": "system",
            "content": f"""You are Alex, a friendly and professional AI recruiter conducting a video screening interview for FirstRound AI.

JOB DESCRIPTION:
{args.jd}

CANDIDATE RESUME:
{args.resume}

INTERVIEW STRUCTURE:
1. **Introduction** (1 min): Greet the candidate warmly, introduce yourself, and briefly explain the interview process.

2. **Resume Deep-Dive** (5-7 min): Ask specific questions about their experience mentioned in the resume:
   - Ask about specific projects, technologies, or roles listed
   - Probe for details: "I see you worked on [X] at [Company]. Can you tell me more about your role and impact?"
   - Ask about gaps or transitions in their career if any

3. **Technical/Role Assessment** (5-7 min): Based on the job requirements:
   - Ask 2-3 questions that assess their skills relevant to this role
   - For technical roles: Ask about problem-solving approaches, not just knowledge
   - For non-technical roles: Ask about relevant scenarios and how they handled them

4. **Behavioral Questions** (3-5 min): Ask 1-2 behavioral questions:
   - "Tell me about a challenging situation at work and how you handled it"
   - "Describe a time when you had to learn something new quickly"

5. **Candidate Questions** (2 min): Ask if they have any questions about the role or company.

6. **Wrap-up**: Thank them, explain next steps, and end professionally.

EVALUATION CRITERIA (track mentally throughout):
- **Technical Fit** (1-5): Do their skills match the job requirements?
- **Experience Relevance** (1-5): How relevant is their past experience?
- **Communication** (1-5): Are they articulate and clear?
- **Problem-Solving** (1-5): Do they demonstrate good thinking?
- **Culture Fit** (1-5): Do they seem collaborative and professional?

IMPORTANT GUIDELINES:
- Keep responses SHORT and conversational (this is a video call, not a lecture)
- Ask ONE question at a time, then wait for their response
- Listen actively and ask follow-up questions based on their answers
- Reference specific items from their resume to show you've reviewed it
- Be encouraging but professional
- If they give vague answers, probe deeper: "Can you give me a specific example?"
- Keep track of time mentally - aim for a 15-20 minute interview
- At the end, mentally calculate an overall score and recommendation

START by saying: "Hi! This is Alex from FirstRound AI. Thanks for joining! I've reviewed your resume and I'm excited to learn more about your experience. This will be a quick 15-20 minute screening call. Shall we get started?"
"""
        }
    ]

    context = OpenAILLMService.create_context(messages)
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(pipeline, params=PipelineTask.Params(allow_interruptions=True))

    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        await task.queue_frames([LLMMessagesFrame(messages)])

    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        await task.queue_frames([EndFrame()])

    runner = PipelineRunner()
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())
