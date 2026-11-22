from dataclasses import dataclass


@dataclass
class ShortenRequest:
    long_url: str


@dataclass
class Url:
    id: int
    hash: str
    long_url: str
