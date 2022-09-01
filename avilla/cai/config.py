from dataclasses import dataclass, field
from typing import Literal, Union
from pathlib import Path
import sys


@dataclass(unsafe_hash=True)
class CAIConfig:
    account: Union[str, int]
    password: str
    protocol: Literal["IPAD", "ANDROID_PHONE", "ANDROID_WATCH", "MACOS"] = field(default="IPAD")
    cache_siginfo: bool = field(default=True)
    cache_root: Path = field(default=Path(".cache"))

    @property
    def cache_path(self) -> Path:
        root = Path(sys.modules["__main__"].__file__).parent
        return root / self.cache_root / f"{self.account}.sig"

