import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from app.core.config import settings
from ..exceptions.travel_exceptions import StorageError


class StorageService:
    """
    Encapsula toda la interacción con Cloudflare R2 (S3-compatible).
    El resto del módulo no sabe nada del proveedor — cambiar a S3 u otro
    requiere modificar solo este archivo.
    """

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
        self.bucket     = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL.rstrip("/")

    # ── Presigned URL ──────────────────────────────────────────────────────────

    def generate_upload_url(self, key: str, content_type: str, expires: int = 600) -> str:
        """Genera una presigned PUT URL para subir directamente desde el frontend."""
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

    # ── Object operations ──────────────────────────────────────────────────────

    def delete_object(self, key: str) -> None:
        """Elimina un objeto. Idempotente: no lanza error si no existe."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except ClientError as e:
            raise StorageError(str(e))

    def delete_objects_by_prefix(self, prefix: str) -> None:
        """
        Elimina en batch todos los objetos bajo un prefix.
        Usado para borrar un viaje completo: users/{uid}/trips/{tid}/
        """
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
        """Verifica que el objeto existe en R2 (usado en confirm_photo_upload)."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    # ── URL helpers ────────────────────────────────────────────────────────────

    def build_public_url(self, key: str) -> str:
        """Construye la URL pública permanente de un objeto."""
        return f"{self.public_url}/{key}"

    # ── Key helpers (static) ───────────────────────────────────────────────────

    @staticmethod
    def build_photo_key(
        user_id: int, trip_id: int, album_id: int, photo_id: int, extension: str
    ) -> str:
        """
        Jerarquía: users/{uid}/trips/{tid}/albums/{aid}/{photo_id}.{ext}
        Permite borrado eficiente por prefijo de viaje o álbum.
        """
        return f"users/{user_id}/trips/{trip_id}/albums/{album_id}/{photo_id}.{extension}"

    @staticmethod
    def build_trip_prefix(user_id: int, trip_id: int) -> str:
        return f"users/{user_id}/trips/{trip_id}/"

    @staticmethod
    def build_album_prefix(user_id: int, trip_id: int, album_id: int) -> str:
        return f"users/{user_id}/trips/{trip_id}/albums/{album_id}/"


# Singleton — importado directamente por los services
storage_service = StorageService()