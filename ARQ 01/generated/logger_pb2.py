# -*- coding: utf-8 -*-
import json

class HitRequest:
    def __init__(self, timestamp: str = "", url: str = ""):
        self.timestamp = timestamp
        self.url = url

    def SerializeToString(self) -> bytes:
        data = {"timestamp": self.timestamp, "url": self.url}
        return json.dumps(data).encode("utf-8")

    @classmethod
    def FromString(cls, data: bytes):
        payload = json.loads(data.decode("utf-8"))
        return cls(timestamp=payload.get("timestamp", ""), url=payload.get("url", ""))

class HitResponse:
    def __init__(self, success: bool = False):
        self.success = success

    def SerializeToString(self) -> bytes:
        data = {"success": self.success}
        return json.dumps(data).encode("utf-8")

    @classmethod
    def FromString(cls, data: bytes):
        payload = json.loads(data.decode("utf-8"))
        return cls(success=payload.get("success", False))
