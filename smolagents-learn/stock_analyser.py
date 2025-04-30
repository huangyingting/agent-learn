from smolagents import CodeAgent
from smolagents.cli import load_model
import argparse
from dotenv import load_dotenv

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

def main():
    args = parse_arguments()
    model = load_model(args.model_type, args.model_id)
    agent = CodeAgent(tools=[], model=model, additional_authorized_imports= "*", add_base_tools=True, verbosity_level=2)
    agent.run(
        "Please analyze Microsoft's stock trend over the last 30 days, create a chart to visualize the data, and save the chart to disk.",
    )

if __name__ == "__main__":
    main()