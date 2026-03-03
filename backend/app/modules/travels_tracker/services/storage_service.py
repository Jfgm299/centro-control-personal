import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from ..exceptions.travel_exceptions import StorageError


class StorageService:

    def __init__(self):
        from app.modules.travels_tracker.manifest import get_settings
        s = get_settings()

        self.client = boto3.client(
            "s3",
            endpoint_url=f"https://{s['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
            aws_access_key_id=s["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=s["R2_SECRET_ACCESS_KEY"],
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
        self.bucket     = s["R2_BUCKET_NAME"]
        self.public_url = s["R2_PUBLIC_URL"].rstrip("/")

    def generate_upload_url(self, key: str, content_type: str, expires: int = 600) -> str:
        try:
            return self.client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket":      self.bucket,
                    "Key":         key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires,
            )
        except ClientError as e:
            raise StorageError(str(e))

    def delete_object(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except ClientError as e:
            raise StorageError(str(e))

    def delete_objects_by_prefix(self, prefix: str) -> None:
        try:
            paginator = self.client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                objects = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
                if objects:
                    self.client.delete_objects(
                        Bucket=self.bucket,
                        Delete={"Objects": objects, "Quiet": True},
                    )
        except ClientError as e:
            raise StorageError(str(e))

    def object_exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def build_public_url(self, key: str) -> str:
        return f"{self.public_url}/{key}"

    @staticmethod
    def build_photo_key(
        user_id: int, trip_id: int, album_id: int, photo_id: int, extension: str
    ) -> str:
        return f"users/{user_id}/trips/{trip_id}/albums/{album_id}/{photo_id}.{extension}"

    @staticmethod
    def build_trip_prefix(user_id: int, trip_id: int) -> str:
        return f"users/{user_id}/trips/{trip_id}/"

    @staticmethod
    def build_album_prefix(user_id: int, trip_id: int, album_id: int) -> str:
        return f"users/{user_id}/trips/{trip_id}/albums/{album_id}/"



# Por esto:
_storage_service = None

def get_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
