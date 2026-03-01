import enum


class PhotoStatus(str, enum.Enum):
    pending  = "pending"
    uploaded = "uploaded"
    deleted  = "deleted"