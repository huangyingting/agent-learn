import argparse
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from phoenix.otel import register

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run an agent with a specified model.")
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

def instrument(project_name: str = "default") -> None:
    register(
        project_name=project_name,
    )
    SmolagentsInstrumentor().instrument(skip_dep_check=True)