import os

from dotenv import load_dotenv
from enum import Enum
from typing import List, Literal, Optional
from openai import OpenAI
from pydantic import BaseModel, Field, json

from engine.strategy.base import Strategy
from engine.strategy.strategy_schema import StrategySchema

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class IndicatorName(str, Enum):
    PRICE = "PRICE"
    SMA = "SMA"
    EMA = "EMA"
    RSI = "RSI"
    MACD = "MACD"
    BOLLINGER_UPPER = "BOLLINGER_UPPER"
    BOLLINGER_MIDDLE = "BOLLINGER_MIDDLE"
    BOLLINGER_LOWER = "BOLLINGER_LOWER"

class OperatorType(str, Enum):
    LESS_THAN = "<"
    GREATER_THAN = ">"
    EQUAL_TO = "=="
    LESS_THAN_OR_EQUAL_TO = "<="
    GREATER_THAN_OR_EQUAL_TO = ">="

def generate_strategy(prompt: str, max_tokens: int = 500) -> StrategySchema:
    """
    Generate a trading strategy based on the provided prompt using OpenAI's GPT model.

    Args:
        prompt (str): The prompt describing the desired trading strategy.
        max_tokens (int): The maximum number of tokens to generate in the response.

    Returns:
        StrategySchema: A parsed strategy schema object.
    """

    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a trading strategy generator. Generate a JSON representation of a trading strategy based on the user's prompt."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_completion_tokens=max_tokens,
        temperature=0.7,
        response_format=StrategySchema  # Ensure the response is in the format of StrategySchema
    )

    parsed_strategy = response.choices[0].message.parsed
    return parsed_strategy