from agents import AsyncOpenAI, OpenAIChatCompletionsModel
from anthropic import AsyncAnthropic

from project.core.settings import settings

anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

gpt_4o_model_openai = OpenAIChatCompletionsModel(
    model="gpt-4o",
    openai_client=AsyncOpenAI(api_key=settings.OPENAI_API_KEY),
)

gpt_4o_mini_model_openai = OpenAIChatCompletionsModel(
    model="gpt-4o",
    openai_client=AsyncOpenAI(api_key=settings.OPENAI_API_KEY),
)
