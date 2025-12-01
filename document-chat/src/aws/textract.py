import asyncio
import logging
import time
from concurrent.futures import Executor
from typing import TYPE_CHECKING, Final, Optional

import boto3

from src.utils import asyncfy, timer

if TYPE_CHECKING:
    from mypy_boto3_textract import TextractClient
    from mypy_boto3_textract.type_defs import GetDocumentTextDetectionResponseTypeDef

logger = logging.getLogger("aws.textract")

DEFAULT_JOB_STATUS_DELAY: Final[int] = 20


class Textract:
    client: "TextractClient"

    def __init__(self, client: Optional["TextractClient"] = None) -> None:
        self.client = client or boto3.client("textract")

    def start_document_text_detection(self, bucket: str, key: str) -> str:
        response = self.client.start_document_text_detection(
            DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}}
        )
        return response["JobId"]

    async def astart_document_text_detection(
        self, bucket: str, key: str, executor: Executor | None = None
    ) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            executor, self.start_document_text_detection, bucket, key
        )

    def get_document_text_detection(
        self, job_id: str, next_token: str | None = None
    ) -> "GetDocumentTextDetectionResponseTypeDef":
        if next_token:
            return self.client.get_document_text_detection(
                JobId=job_id, NextToken=next_token
            )
        return self.client.get_document_text_detection(JobId=job_id)

    async def aget_document_text_detection(
        self,
        job_id: str,
        next_token: str | None = None,
        executor: Executor | None = None,
    ) -> "GetDocumentTextDetectionResponseTypeDef":
        return await asyncfy(
            self.get_document_text_detection, job_id, next_token, executor=executor
        )

    def _parse_document_text_detection(
        self, response: "GetDocumentTextDetectionResponseTypeDef"
    ) -> str:
        return "\n".join(
            b["Text"]
            for b in response.get("Blocks", [])
            if "BlockType" in b and b["BlockType"] == "LINE" and "Text" in b
        )

    def detect_document_text(
        self,
        bucket: str,
        key: str,
        delay: int = DEFAULT_JOB_STATUS_DELAY,
        timeout: int | None = None,
        verbose: bool = False,
    ) -> str:
        job_id = self.start_document_text_detection(bucket, key)
        if verbose:
            logger.info("Job created: %s", job_id)
        next_token: str | None = None
        text = ""
        has_timeout = timer(timeout) if timeout else None
        while True:
            response = self.get_document_text_detection(job_id, next_token)

            if response["JobStatus"] == "IN_PROGRESS":
                if verbose:
                    logger.info("Job %s status: %s", job_id, response["JobStatus"])
                if has_timeout and has_timeout():
                    raise TimeoutError(f"Job {job_id} timed out!")
                time.sleep(delay)
                continue

            if response["JobStatus"] == "SUCCEEDED":
                text = text and text + "\n"
                text += self._parse_document_text_detection(response)
                next_token = response.get("NextToken", None)
                if next_token:
                    if verbose:
                        logger.info("Job %s completed but has more blocks", job_id)
                    continue
                break

            raise ValueError(
                f"Job {job_id} return status error: {response['JobStatus']}", response
            )
        return text.strip()

    async def adetect_document_text(
        self,
        bucket: str,
        key: str,
        delay: int = DEFAULT_JOB_STATUS_DELAY,
        timeout: int | None = None,
        verbose: bool = False,
    ) -> str:
        job_id = await self.astart_document_text_detection(bucket, key)
        if verbose:
            logger.info("Job created: %s", job_id)
        next_token: str | None = None
        text = ""
        has_timeout = timer(timeout) if timeout else None
        while True:
            response = await self.aget_document_text_detection(job_id, next_token)

            if response["JobStatus"] == "IN_PROGRESS":
                if verbose:
                    logger.info("Job %s status: %s", job_id, response["JobStatus"])
                if has_timeout and has_timeout():
                    raise TimeoutError(f"Job {job_id} timed out!")
                await asyncio.sleep(delay)
                continue

            if response["JobStatus"] == "SUCCEEDED":
                text = text and text + "\n"
                text += self._parse_document_text_detection(response)
                next_token = response.get("NextToken", None)
                if next_token:
                    if verbose:
                        logger.info("Job %s completed but has more blocks", job_id)
                    continue
                break

            raise ValueError(
                f"Job {job_id} return status error: {response['JobStatus']}", response
            )
        return text.strip()
