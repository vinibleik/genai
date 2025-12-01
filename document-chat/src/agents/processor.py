import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from pydantic_ai import (
    BuiltinToolCallPart,
    BuiltinToolReturnPart,
    FilePart,
    ModelMessage,
    ModelRequest,
    ModelRequestPart,
    ModelResponse,
    ModelResponsePart,
    RetryPromptPart,
    SystemPromptPart,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from src.models.message import (
    Message,
    MessageContent,
    MessageRole,
    TextContent,
    ToolCallContent,
    ToolResponseContent,
)


class ModelRequestProcessor:
    def process_user_prompt_part(
        self, part: UserPromptPart
    ) -> list[TextContent]:
        if isinstance(part.content, str):
            return [TextContent(type="text", text=part.content)]
        return [
            TextContent(type="text", text=c)
            for c in part.content
            if isinstance(c, str)
        ]

    def process_system_prompt_part(self, part: SystemPromptPart) -> list[Any]:
        raise NotImplementedError(
            "ModelRequest SystemPromptPart not supported yet"
        )

    def process_tool_return_part(
        self, part: ToolReturnPart
    ) -> list[ToolResponseContent]:
        return [
            ToolResponseContent(
                type="tool_response",
                tool_call_id=part.tool_call_id,
                tool_name=part.tool_name,
                content=part.model_response_str(),
            )
        ]

    def process_retry_prompt_part(self, part: RetryPromptPart) -> list[Any]:
        raise NotImplementedError(
            "ModelRequest RetryPromptPart not supported yet"
        )

    def process_model_request_part(
        self, part: ModelRequestPart
    ) -> Sequence[MessageContent]:
        match part.part_kind:
            case "system-prompt":
                return self.process_system_prompt_part(part)
            case "user-prompt":
                return self.process_user_prompt_part(part)
            case "tool-return":
                return self.process_tool_return_part(part)
            case "retry-prompt":
                return self.process_retry_prompt_part(part)
            case _:
                raise ValueError(f"Invalid part: {part.part_kind}")

    def process_message_request(self, message: ModelRequest) -> str:
        text = "ModelRequest"
        text += "\nRun: " + str(message.run_id)
        text += "\nInstructions: " + str(message.instructions)
        text += "\nMetadata: " + str(message.metadata)
        text += "\nParts:\n" + "\n".join(
            str(self.process_model_request_part(p)) for p in message.parts
        )
        return text

    def from_message_db(self, message: Message) -> ModelRequest:
        parts: list[ModelRequestPart] = []
        for c in message.content:
            if c["type"] == "text":
                parts.append(UserPromptPart(c["text"]))
            if c["type"] == "tool_response":
                parts.append(
                    ToolReturnPart(
                        c["tool_name"], c["content"], c["tool_call_id"]
                    )
                )
        return ModelRequest(parts=parts)

    def _get_message_content(
        self, message: ModelRequest
    ) -> list[MessageContent]:
        content: list[MessageContent] = []
        for part in message.parts:
            content.extend(self.process_model_request_part(part))
        return content

    def _get_message_timestampt(self, message: ModelRequest) -> datetime:
        return message.parts[0].timestamp

    def to_message_db(
        self, chat_id: uuid.UUID, message: ModelRequest
    ) -> Message:
        content = self._get_message_content(message)
        created_at = self._get_message_timestampt(message)
        return Message(
            chat_id=chat_id,
            role=MessageRole.USER,
            content=content,
            system=message.instructions,
            created_at=created_at,
        )


class ModelResponseProcessor:
    def process_text_part(self, part: TextPart) -> list[TextContent]:
        return [TextContent(type="text", text=part.content)]

    def process_tool_call_part(
        self, part: ToolCallPart
    ) -> list[ToolCallContent]:
        return [
            ToolCallContent(
                type="tool_call",
                tool_call_id=part.tool_call_id,
                tool_name=part.tool_name,
                args=part.args_as_dict(),
            )
        ]

    def process_thinking_part(self, part: ThinkingPart) -> list[Any]:
        raise NotImplementedError(
            "ModelResponse ThinkingPart not supported yet"
        )

    def process_file_part(self, part: FilePart) -> list[Any]:
        raise NotImplementedError("ModelResponse FilePart not supported yet")

    def process_builtin_tool_call_part(
        self, part: BuiltinToolCallPart
    ) -> list[Any]:
        raise NotImplementedError(
            "ModelResponse BuiltinToolCallPart not supported yet"
        )

    def process_builtin_tool_return_part(
        self, part: BuiltinToolReturnPart
    ) -> list[Any]:
        raise NotImplementedError(
            "ModelResponse BuiltinToolReturnPart not supported yet"
        )

    def process_model_response_part(
        self, part: ModelResponsePart
    ) -> Sequence[MessageContent]:
        match part.part_kind:
            case "text":
                return self.process_text_part(part)
            case "tool-call":
                return self.process_tool_call_part(part)
            case "thinking":
                return self.process_thinking_part(part)
            case "file":
                return self.process_file_part(part)
            case "builtin-tool-call":
                return self.process_builtin_tool_call_part(part)
            case "builtin-tool-return":
                return self.process_builtin_tool_return_part(part)
            case _:
                raise ValueError(f"Invalid part: {part.part_kind}")

    def process_message_response(self, message: ModelResponse) -> str:
        text = "ModelResponse"
        # text += "\nTime: " + format_datetime(message.timestamp)
        text += "\nRun: " + str(message.run_id)
        text += "\nProvider: " + str(message.provider_name)
        text += "\nModel: " + str(message.model_name)
        text += "\nUsage: " + repr(message.usage)
        text += "\nProvider Details: " + str(message.provider_details)
        text += "\nFinish Reason: " + str(message.finish_reason)
        text += "\nMetadata: " + str(message.metadata)
        text += "\nParts:\n" + "\n".join(
            str(self.process_model_response_part(p)) for p in message.parts
        )
        return text

    def from_message_db(self, message: Message) -> ModelResponse:
        parts: list[ModelResponsePart] = []
        for c in message.content:
            if c["type"] == "text":
                parts.append(TextPart(c["text"]))
            if c["type"] == "tool_call":
                parts.append(
                    ToolCallPart(c["tool_name"], c["args"], c["tool_call_id"])
                )
        return ModelResponse(parts=parts)

    def _get_message_content(
        self, message: ModelResponse
    ) -> list[MessageContent]:
        content: list[MessageContent] = []
        for part in message.parts:
            content.extend(self.process_model_response_part(part))
        return content

    def to_message_db(
        self, chat_id: uuid.UUID, message: ModelResponse
    ) -> Message:
        content = self._get_message_content(message)
        return Message(
            chat_id=chat_id,
            role=MessageRole.AI,
            content=content,
            created_at=message.timestamp,
            usage={
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
            },
            model=message.model_name,
        )


class MessagesProcessor:
    request_processor: ModelRequestProcessor
    response_processor: ModelResponseProcessor

    def __init__(self) -> None:
        self.response_processor = ModelResponseProcessor()
        self.request_processor = ModelRequestProcessor()

    def process_messages_from_db(
        self, messages: list[Message]
    ) -> list[ModelMessage]:
        return [
            self.request_processor.from_message_db(m)
            if m.role == MessageRole.USER
            else self.response_processor.from_message_db(m)
            for m in messages
        ]

    def process_messages_to_db(
        self, chat_id: uuid.UUID, messages: list[ModelMessage]
    ) -> list[Message]:
        return [
            self.request_processor.to_message_db(chat_id, m)
            if m.kind == "request"
            else self.response_processor.to_message_db(chat_id, m)
            for m in messages
        ]


processor = MessagesProcessor()
