"""The app's software version: the release version, or "dev" for a USB deploy."""

try:
    from src.version import VERSION  # pyrefly: ignore[missing-import]
except ImportError:
    VERSION = "dev"
