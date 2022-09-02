from dataclasses import dataclass, field
from cai.storage import change_config_dir, change_cache_dir
from typing import Literal, Union, Optional
from pathlib import Path


@dataclass(unsafe_hash=True)
class CAIConfig:
    account: Union[str, int]
    password: str
    protocol: Literal["IPAD", "ANDROID_PHONE", "ANDROID_WATCH", "MACOS"] = field(default="IPAD")
    cache_siginfo: bool = field(default=True, repr=False)
    cache_root: Optional[str] = field(default=".cache", repr=False)
    config_root: Optional[str] = field(default=None, repr=False)

    def init_dir(self):
        if self.cache_root:
            change_cache_dir(self.cache_root)
        if self.config_root:
            change_config_dir(self.config_root)

    @property
    def cache_path(self) -> Path:
        return Path(self.cache_root) / f"{self.account}" / "siginfo.sig"
