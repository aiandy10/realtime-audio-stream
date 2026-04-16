import asyncio
import websockets
import struct
import numpy as np
import sounddevice as sd
import io
import base64
import requests
import soundfile as sf

WS_URL = "ws://127.0.0.1:8765"


API_URL = "http://internal-k8s-devinternal-e5d13f2ce1-164374216.ap-south-1.elb.amazonaws.com/llm-core/transcribe/endpoints/whisper-turbo-1773222895/invocations"

HEADERS = {
    "Content-Type": "application/json",
    "X-Amzn-SageMaker-Custom-Attributes": "sk-S6vc4Y8cl4lzZRzH8-Re_7_5bKvPWq1FwEnzzSVVBqk"
}


def numpy_to_wav_bytes(audio, sr):
    buffer = io.BytesIO()
    sf.write(buffer, audio, sr, format='WAV')
    return buffer.getvalue()


def wav_to_base64(wav_bytes):
    return base64.b64encode(wav_bytes).decode("utf-8")


async def receiver():
    async with websockets.connect(WS_URL) as ws:
        print("[Receiver] Connected")

        tested = False  # ensure only one API call

        while True:
            data = await ws.recv()

            if not isinstance(data, (bytes, bytearray)):
                continue

            sample_rate = struct.unpack("I", data[:4])[0]
            audio = np.frombuffer(data[4:], dtype=np.int16)

            audio = audio.flatten()
            audio = audio.astype(np.float32) / 32768.0

            print(f"[Receiver] Playing chunk: {len(audio)} samples")

            #  play audio (keep for debugging)
            sd.play(audio, samplerate=sample_rate)
            sd.wait()

            #  SEND TO WHISPER API (ONLY ONCE)
            if not tested:
                print("[TEST] Sending chunk to Whisper API...")

                wav_bytes = numpy_to_wav_bytes(audio, sample_rate)
                base64_audio = wav_to_base64(wav_bytes)

                payload = {
                    "audio": base64_audio
                }

                try:
                    response = requests.post(API_URL, headers=HEADERS, json=payload)
                    print("[API STATUS]", response.status_code)
                    print("[API RESPONSE]", response.text)
                except Exception as e:
                    print("[API ERROR]", e)

                tested = True


asyncio.run(receiver())