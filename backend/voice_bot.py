
import os
import aiohttp

from dotenv import load_dotenv
from loguru import logger
from backend.app.appointment_service import (
    check_doctor_availability,
    book_appointment,
    cancel_appointment,
)
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.pipeline.runner import PipelineRunner
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.services.google.llm import GoogleLLMService
from pipecat.services.elevenlabs.stt import ElevenLabsSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

from backend.app.database import SessionLocal

load_dotenv()


async def check_availability_handler(params: FunctionCallParams):
    """Fetch actual doctors and available slots from SQLite."""

    arguments = params.arguments
    specialty = arguments.get("specialty")
    appointment_date = arguments.get("appointment_date")

    db = SessionLocal()

    try:
        results = check_doctor_availability(
            db=db,
            specialty=specialty,
            appointment_date=appointment_date,
        )

        available = [
            doctor for doctor in results
            if doctor["available_slots"]
        ]

        if available:
            result = {
                "success": True,
                "doctors": available,
            }
        else:
            result = {
                "success": True,
                "doctors": [],
                "message": (
                    "No available doctors or slots found. "
                    "Ask the patient whether they would like "
                    "another date or specialty."
                ),
            }

        await params.result_callback(result)

    except Exception:
        logger.exception("Availability lookup failed")
        await params.result_callback({
            "success": False,
            "message": "Unable to check availability right now.",
        })

    finally:
        db.close()


def has_explicit_phone_confirmation(params: FunctionCallParams) -> bool:
    """Validate confirmation of the exact phone number."""

    messages = params.context.get_messages()

    def get_field(message, field):
        if isinstance(message, dict):
            return message.get(field, "")
        return getattr(message, field, "")

    patient_phone = "".join(
        ch for ch in str(params.arguments.get("patient_phone", ""))
        if ch.isdigit()
    )

    if not patient_phone:
        return False

    # Find the latest user message, ignoring later tool-call messages.
    user_message = None
    user_index = -1

    for index in range(len(messages) - 1, -1, -1):
        if get_field(messages[index], "role") == "user":
            user_message = messages[index]
            user_index = index
            break

    if user_message is None:
        return False

    user_reply = str(
        get_field(user_message, "content")
    ).strip().lower()

    confirmations = {
        "yes",
        "yes i confirm",
        "i confirm",
        "correct",
        "that's correct",
        "that is correct",
        "yeah",
        "yep",
        "confirmed",
        "yes that is my correct phone number",
        "yes that is my correct number",
        "yes please book the appointment",
    }

    if user_reply not in confirmations:
        return False

    # Find the assistant's latest message before the user's confirmation.
    for index in range(user_index - 1, -1, -1):
        message = messages[index]

        if get_field(message, "role") == "assistant":
            assistant_text = str(
                get_field(message, "content")
            )

            assistant_phone = "".join(
                ch for ch in assistant_text if ch.isdigit()
            )

            return patient_phone in assistant_phone

    return False


async def book_appointment_handler(params: FunctionCallParams):
    """Book only after checking explicit phone confirmation."""

    arguments = params.arguments

    if arguments.get("phone_confirmed") is not True:
        await params.result_callback({
            "success": False,
            "message": (
                "Booking is not authorized yet. Ask the patient "
                "for their phone number, repeat it digit by digit, "
                "and obtain explicit confirmation."
            ),
        })
        return

    if not has_explicit_phone_confirmation(params):
        await params.result_callback({
            "success": False,
            "message": (
                "The patient's latest response does not confirm "
                "the phone number. Do not book."
            ),
        })
        return

    slot_id = arguments.get("slot_id")
    patient_phone = arguments.get("patient_phone")

    if not slot_id or not patient_phone:
        await params.result_callback({
            "success": False,
            "message": "A slot ID and phone number are required.",
        })
        return

    db = SessionLocal()

    try:
        result = book_appointment(
            db=db,
            slot_id=int(slot_id),
            patient_phone=patient_phone,
            phone_confirmed=True,
        )

        await params.result_callback(result)

    except Exception:
        logger.exception("Appointment booking failed")
        await params.result_callback({
            "success": False,
            "message": "Unable to book the appointment right now.",
        })

    finally:
        db.close()
async def cancel_appointment_handler(params: FunctionCallParams):
    """Cancel only after explicit phone confirmation."""

    arguments = params.arguments

    if arguments.get("phone_confirmed") is not True:
        await params.result_callback({
            "success": False,
            "message": (
                "Cancellation is not authorized. Ask the patient "
                "for their phone number, repeat it digit by digit, "
                "and obtain explicit confirmation."
            ),
        })
        return

    if not has_explicit_phone_confirmation(params):
        await params.result_callback({
            "success": False,
            "message": (
                "The patient's latest response does not confirm "
                "the phone number. Do not cancel."
            ),
        })
        return

    patient_phone = arguments.get("patient_phone")
    appointment_id = arguments.get("appointment_id")

    if not patient_phone:
        await params.result_callback({
            "success": False,
            "message": "The patient's phone number is required.",
        })
        return

    db = SessionLocal()

    try:
        result = cancel_appointment(
            db=db,
            patient_phone=patient_phone,
            appointment_id=appointment_id,
            phone_confirmed=True,
        )

        await params.result_callback(result)

    except Exception:
        logger.exception("Appointment cancellation failed")
        await params.result_callback({
            "success": False,
            "message": "Unable to cancel the appointment right now.",
        })

    finally:
        db.close()

async def bot(runner_args: RunnerArguments):
    logger.info("Starting Doctor Appointment Assistant")

    transport = SmallWebRTCTransport(
        webrtc_connection=runner_args.webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        ),
    )

    aiohttp_session = aiohttp.ClientSession()

    stt = ElevenLabsSTTService(
        api_key=os.environ["ELEVENLABS_API_KEY"],
        aiohttp_session=aiohttp_session,
    )

    tts = ElevenLabsTTSService(
        api_key=os.environ["ELEVENLABS_API_KEY"],
        aiohttp_session=aiohttp_session,
        settings=ElevenLabsTTSService.Settings(
            voice=os.environ["ELEVENLABS_VOICE_ID"]
        ),
    )

    
    llm = GoogleLLMService(
    api_key=os.environ["GEMINI_API_KEY"],
    settings=GoogleLLMService.Settings(
        model="gemini-3.5-flash-lite",
        system_instruction=(
            "You are a friendly AI Doctor Appointment Assistant. "
            "Use check_doctor_availability for all availability questions. "
            "Never invent doctors, dates, or slots. "
            "Ask one question at a time. "
            "Before booking or cancelling, collect the phone number, "
            "repeat it digit by digit, and obtain explicit verbal confirmation. "
            "Never claim an action succeeded unless the tool confirms success."
        )
    ),
    tools=[
        {
            "function_declarations": [
                {
                    "name": "check_doctor_availability",
                    "description": "Check real doctors and available slots from the database.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "specialty": {"type": "STRING"},
                            "appointment_date": {"type": "STRING"}
                        },
                        "required": []
                    }
                },
                {
                    "name": "book_appointment",
                    "description": "Book a selected appointment after phone confirmation.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "slot_id": {"type": "INTEGER"},
                            "patient_phone": {"type": "STRING"},
                            "phone_confirmed": {"type": "BOOLEAN"}
                        },
                        "required": [
                            "slot_id",
                            "patient_phone",
                            "phone_confirmed"
                        ]
                    }
                },
                {
                    "name": "cancel_appointment",
                    "description": "Cancel an existing appointment after phone confirmation.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "appointment_id": {"type": "INTEGER"},
                            "patient_phone": {"type": "STRING"},
                            "phone_confirmed": {"type": "BOOLEAN"}
                        },
                        "required": [
                            "patient_phone",
                            "phone_confirmed"
                        ]
                    }
                }
            ]
        }
    ],
)


    llm.register_function(
        "check_doctor_availability",
        check_availability_handler,
    )

    llm.register_function(
        "book_appointment",
        book_appointment_handler,
    )

    llm.register_function(
    "cancel_appointment",
    cancel_appointment_handler,
    )

    context = LLMContext()

    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer()
        ),
    )

    pipeline = Pipeline([
        transport.input(),
        stt,
        user_aggregator,
        llm,
        tts,
        transport.output(),
        assistant_aggregator,
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    runner = PipelineRunner(
        handle_sigint=runner_args.handle_sigint
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Browser connected")

        context.add_message({
            "role": "developer",
            "content": (
                "Introduce yourself as the Doctor Appointment "
                "Assistant and ask how you can help."
            ),
        })

        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Browser disconnected")
        await task.cancel()

    await runner.run(task)


if __name__ == "__main__":
    import http
    from enum import Enum

    class HTTPMethod(str, Enum):
        CONNECT = "CONNECT"
        DELETE = "DELETE"
        GET = "GET"
        HEAD = "HEAD"
        OPTIONS = "OPTIONS"
        PATCH = "PATCH"
        POST = "POST"
        PUT = "PUT"
        TRACE = "TRACE"

    http.HTTPMethod = HTTPMethod

    from pipecat.runner.run import main
    main()
