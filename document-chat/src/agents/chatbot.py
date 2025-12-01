import logging
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent, ModelMessage, RunContext
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def create_panel(
    console: Console, data: object, title: str | Text | None = None
) -> str:
    with console.capture() as cap:
        console.print(data)
    text = Text.from_ansi(cap.get())
    if isinstance(title, str):
        title = Text.assemble((title, "bright_blue"))
    panel = Panel(text, title=title, border_style="bright_yellow")
    with console.capture() as cap:
        console.print(panel)
    return cap.get()


class FilterNonAnthropicRequests(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return (
            record.name == "anthropic._base_client"
            and "Request options" in record.msg
        )


class AnthropicRequestFormatter(logging.Formatter):
    def __init__(
        self,
        console: Console | None = None,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: str = "%",
        validate: bool = True,
        *,
        defaults: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)  # type: ignore
        self.console = console or Console()

    def format(self, record: logging.LogRecord) -> str:
        return create_panel(
            self.console,
            record.args,
            "Anthropic Request",
        )


def init_logging(console: Console | None = None, level: int = logging.DEBUG):
    logger_filter = FilterNonAnthropicRequests()
    logger_formatter = AnthropicRequestFormatter(console)
    logger_handler = logging.StreamHandler(sys.stdout)
    logger_handler.setFormatter(logger_formatter)
    logger_handler.addFilter(logger_filter)
    logging.basicConfig(level=level, handlers=[logger_handler])
    logger = logging.getLogger()
    return logger


init_logging()


@dataclass
class ChatbotDeps:
    n: int


async def roulette_wheel(ctx: RunContext[ChatbotDeps], square: int) -> str:
    """check if the square is a winner"""
    return "winner" if square == ctx.deps.n else "loser"


def init_agent():
    model = AnthropicModel(
        "claude-haiku-4-5-20251001",
        settings=AnthropicModelSettings(temperature=0, max_tokens=1 << 12),
    )
    agent = Agent(
        model,
        instructions="""You are a chatbot. Converse with the user friendly.""",
        deps_type=ChatbotDeps,
        tools=[roulette_wheel],
    )
    return agent


async def run_agent(
    user_input: str,
    deps: ChatbotDeps,
    history: Sequence[ModelMessage] | None = None,
) -> list[ModelMessage]:
    agent = init_agent()
    response = await agent.run(user_input, deps=deps, message_history=history)
    return response.new_messages()
