import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
)


class S3Storage:
    def __init__(self):
        self.bucket_name = os.getenv(
            "FLOODLENS_S3_BUCKET"
        )

        self.region = os.getenv(
            "AWS_REGION",
            "us-east-1"
        )

        self.enabled = bool(
            self.bucket_name
        )

        if self.enabled:
            self.client = boto3.client(
                "s3",
                region_name=self.region,
            )
        else:
            self.client = None

    @staticmethod
    def sanitize_filename(filename):
        if not filename:
            return "upload"

        filename = Path(
            filename
        ).name

        return re.sub(
            r"[^A-Za-z0-9._-]",
            "_",
            filename,
        )

    def create_analysis_id(self):
        return str(
            uuid.uuid4()
        )

    def build_key(
        self,
        category,
        analysis_id,
        filename,
    ):
        now = datetime.now(
            timezone.utc
        )

        safe_filename = (
            self.sanitize_filename(
                filename
            )
        )

        return (
            f"{category}/"
            f"{now.year}/"
            f"{now.month:02d}/"
            f"{now.day:02d}/"
            f"{analysis_id}-"
            f"{safe_filename}"
        )

    def upload_bytes(
        self,
        data,
        key,
        content_type,
    ):
        if not self.enabled:
            return None

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type,
            )

            return key

        except (
            ClientError,
            BotoCoreError,
        ) as error:
            raise RuntimeError(
                "Failed to upload file "
                f"to S3: {error}"
            ) from error

    def upload_file(
        self,
        file_path,
        key,
        content_type,
    ):
        if not self.enabled:
            return None

        try:
            self.client.upload_file(
                Filename=str(file_path),
                Bucket=self.bucket_name,
                Key=key,
                ExtraArgs={
                    "ContentType": content_type
                },
            )

            return key

        except (
            ClientError,
            BotoCoreError,
        ) as error:
            raise RuntimeError(
                "Failed to upload file "
                f"to S3: {error}"
            ) from error

    def upload_json(
        self,
        data,
        key,
    ):
        if not self.enabled:
            return None

        body = json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ).encode(
            "utf-8"
        )

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=body,
                ContentType="application/json",
            )

            return key

        except (
            ClientError,
            BotoCoreError,
        ) as error:
            raise RuntimeError(
                "Failed to upload JSON "
                f"to S3: {error}"
            ) from error

    def list_analysis_results(
        self,
        limit=20,
    ):
        if not self.enabled:
            return []

        prefixes = {
            "image": "results/images/",
            "video": "results/videos/",
        }

        objects = []

        try:
            paginator = (
                self.client
                .get_paginator(
                    "list_objects_v2"
                )
            )

            for (
                analysis_type,
                prefix
            ) in prefixes.items():

                pages = paginator.paginate(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                )

                for page in pages:
                    for item in page.get(
                        "Contents",
                        [],
                    ):
                        if not item[
                            "Key"
                        ].endswith(
                            ".json"
                        ):
                            continue

                        objects.append(
                            {
                                "analysis_type":
                                    analysis_type,
                                "key":
                                    item["Key"],
                                "last_modified":
                                    item[
                                        "LastModified"
                                    ],
                            }
                        )

            objects.sort(
                key=lambda item:
                    item["last_modified"],
                reverse=True,
            )

            objects = objects[:limit]

            analyses = []

            for item in objects:
                response = (
                    self.client.get_object(
                        Bucket=
                            self.bucket_name,
                        Key=item["key"],
                    )
                )

                content = (
                    response["Body"]
                    .read()
                    .decode("utf-8")
                )

                data = json.loads(
                    content
                )

                data["history"] = {
                    "analysis_type":
                        item[
                            "analysis_type"
                        ],
                    "result_key":
                        item["key"],
                    "created_at":
                        item[
                            "last_modified"
                        ].isoformat(),
                }

                analyses.append(
                    data
                )

            return analyses

        except (
            ClientError,
            BotoCoreError,
            json.JSONDecodeError,
        ) as error:
            raise RuntimeError(
                "Failed to retrieve "
                f"analysis history: {error}"
            ) from error