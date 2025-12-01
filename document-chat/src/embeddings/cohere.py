import asyncio
import json
import logging
from concurrent.futures import Executor
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Literal,
    NotRequired,
    Optional,
    Required,
    TypedDict,
)

import boto3

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient

logger = logging.getLogger("embeddings.cohere")


class CohereInputContentText(TypedDict):
    type: Literal["text"]
    text: str


class CohereInputContentImage(TypedDict):
    type: Literal["image_url"]
    image_url: str


class CohereInputContent(TypedDict):
    content: list[CohereInputContentText | CohereInputContentImage]


type CohereInputType = Literal[
    "search_document", "search_query", "classification", "clustering"
]
type CohereEmbeddingType = Literal["float", "int8", "uint8", "binary", "ubinary"]
type CohereOutputDimension = Literal[256, 512, 1024, 1536]


class CohereRequestBody(TypedDict, total=False):
    input_type: Required[CohereInputType]
    texts: list[str]
    images: list[str]
    inputs: list[CohereInputContent]
    embedding_types: list[CohereEmbeddingType]
    output_dimension: CohereOutputDimension
    max_tokens: int
    truncate: Literal["NONE", "LEFT", "RIGHT"]


class CohereResponseBodyFloats(TypedDict):
    id: str
    embeddings: list[list[float]]
    response_type: Literal["embeddings_floats"]
    texts: NotRequired[list[str]]
    inputs: NotRequired[list[CohereInputContent]]


class CohereResponseBodyMulti(TypedDict):
    id: str
    embeddings: dict[CohereEmbeddingType, list[list[float]]]
    response_type: Literal["embeddings_by_type"]
    texts: NotRequired[list[str]]
    inputs: NotRequired[list[CohereInputContent]]


type CohereResponseBody = CohereResponseBodyFloats | CohereResponseBodyMulti


class BedrockCohereEmbeddings:
    MODEL_ID: ClassVar[str] = "cohere.embed-v4:0"
    DEFAULT_OUTPUT_DIMENSION: ClassVar[CohereOutputDimension] = 1536

    client: "BedrockRuntimeClient"
    output_dimension: CohereOutputDimension
    verbose: bool

    def __init__(
        self,
        output_dimension: CohereOutputDimension | None = None,
        client: Optional["BedrockRuntimeClient"] = None,
        verbose: bool = False,
    ) -> None:
        self.output_dimension = output_dimension or self.DEFAULT_OUTPUT_DIMENSION
        self.client = client or boto3.client("bedrock-runtime")
        self.verbose = verbose

    def _invoke_bedrock_cohere_model(
        self, body: CohereRequestBody
    ) -> CohereResponseBody:
        _body = json.dumps(body, indent=2)
        if self.verbose:
            logger.info("Calling Bedrock Cohere model with input: %s", _body)
        response = self.client.invoke_model(
            modelId=self.MODEL_ID,
            body=_body,
            accept="*/*",
            contentType="application/json",
        )
        response_body = json.loads(response["body"].read())
        if self.verbose:
            logger.info(
                "Response from Bedrock Cohere model: %s",
                json.dumps(response_body, indent=2),
            )
        return response_body

    async def _ainvoke_bedrock_cohere_model(
        self, body: CohereRequestBody, executor: Executor | None = None
    ) -> CohereResponseBody:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            executor, self._invoke_bedrock_cohere_model, body
        )

    def _get_query_body(self, query: str) -> CohereRequestBody:
        return {
            "input_type": "search_query",
            "embedding_types": ["float"],
            "texts": [query],
            "output_dimension": self.output_dimension,
            "truncate": "NONE",
        }

    def embed_query(self, query: str) -> list[float]:
        body = self._get_query_body(query)
        response = self._invoke_bedrock_cohere_model(body)
        if response["response_type"] == "embeddings_floats":
            return response["embeddings"][0]
        return response["embeddings"]["float"][0]

    async def aembed_query(self, query: str) -> list[float]:
        body = self._get_query_body(query)
        response = await self._ainvoke_bedrock_cohere_model(body)
        if response["response_type"] == "embeddings_floats":
            return response["embeddings"][0]
        return response["embeddings"]["float"][0]

    def _get_documents_body(self, documents: list[str]) -> CohereRequestBody:
        return {
            "input_type": "search_document",
            "embedding_types": ["float"],
            "texts": documents,
            "output_dimension": self.output_dimension,
            "truncate": "NONE",
        }

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        body = self._get_documents_body(documents)
        response = self._invoke_bedrock_cohere_model(body)
        if response["response_type"] == "embeddings_floats":
            return response["embeddings"]
        return response["embeddings"]["float"]

    async def aembed_documents(self, documents: list[str]) -> list[list[float]]:
        body = self._get_documents_body(documents)
        response = await self._ainvoke_bedrock_cohere_model(body)
        if response["response_type"] == "embeddings_floats":
            return response["embeddings"]
        return response["embeddings"]["float"]
