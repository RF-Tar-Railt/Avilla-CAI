from dataclasses import dataclass, field
from typing import Literal, Union


@dataclass(unsafe_hash=True)
class CAIConfig:
    account: Union[str, int]
    password: str
    protocol: Literal["IPAD", "ANDROID_PHONE", "ANDROID_WATCH", "MACOS"] = field(default="IPAD")
