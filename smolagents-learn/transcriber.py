import magic
from openai import AzureOpenAI
from pydub import AudioSegment
import io
from dotenv import load_dotenv
import os
import requests
from urllib.parse import urlparse
from smolagents import CodeAgent, tool
import argparse
from smolagents.cli import load_model

load_dotenv()

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run a web browser automation script with a specified model.")
    parser.add_argument(
        "--model-type",
        type=str,
        default="LiteLLMModel",
        help="The model type to use (e.g., OpenAIServerModel, LiteLLMModel, TransformersModel, HfApiModel)",
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default="azure/gpt-4.1-mini",
        help="The model ID to use for the specified model type",
    )
    return parser.parse_args()

@tool
def transcribe(filepath_or_url: str, end_seconds: int = -1) -> str:
  """
  Transcribe audio from a file or URL.
  Args:
      filepath_or_url: The file path or URL of the audio to transcribe, supported formats .mpeg, .mp4, .mp3, .wav, .webm, .m4a, .mpga
      end_seconds: The end time in seconds to trim the audio (default: -1 for no trim)
  """
  ALLOWED_MIME_TYPES = {
      "audio/mpeg", "audio/mp4", "audio/mp3",
      "audio/wav", "audio/webm", "audio/m4a",
      "audio/mpga"
  }

  parsed_url = urlparse(filepath_or_url)
  is_remote = parsed_url.scheme in ['http', 'https']

  if is_remote:
    response = requests.get(filepath_or_url, stream=True)
    response.raise_for_status()  # Raise exception for HTTP errors

    content = io.BytesIO(response.content)

    content_type = response.headers.get('Content-Type')
    if not content_type or content_type not in ALLOWED_MIME_TYPES:
      content.seek(0)
      mime = magic.from_buffer(content.read(2048), mime=True)
      content.seek(0)
      if mime not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported file format: {mime}")

    audio = AudioSegment.from_file(content)

  else:
    file_path = filepath_or_url

    mime = magic.from_file(file_path, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
      raise ValueError(f"Unsupported file format: {mime}")

    audio = AudioSegment.from_file(file_path)

  if end_seconds > 0 and end_seconds < len(audio) / 1000:
    trimed_audio = audio[:end_seconds * 1000]
  else:
    trimed_audio = audio

  buffer = io.BytesIO()
  trimed_audio.export(buffer, format="mp3")
  buffer.seek(0)
  buffer.name = "trimed_audio.mp3"

  client = AzureOpenAI(
      azure_deployment=os.getenv("AZURE_OPEN_TRANSCRIBE_DEPLOYMENT"),
      api_version=os.getenv("OPENAI_API_VERSION"),
      azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
      api_key=os.getenv("AZURE_OPENAI_API_KEY"),
  )

  transcript = client.audio.transcriptions.create(
      model=os.getenv("AZURE_OPEN_TRANSCRIBE_DEPLOYMENT"),
      file=buffer,
  )
  return transcript.text


def main():
    args = parse_arguments()
    model = load_model(args.model_type, args.model_id)
    agent = CodeAgent(tools=[transcribe], model=model, additional_authorized_imports= "*", add_base_tools=True, verbosity_level=2)
    agent.run(
        "Listen to the first two minutes of U.S. President Trump's speech on his first 100 days from '../data/trump_100days_abc_interview.mp3' and extract the key points.",
    )

if __name__ == "__main__":
    main()