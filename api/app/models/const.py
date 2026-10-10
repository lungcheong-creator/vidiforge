"""Provider & status enums used across the API."""

from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    MOONSHOT = "moonshot"
    QWEN = "qwen"
    OPENAI_COMPATIBLE = "openai_compatible"


class VoiceProvider(str, Enum):
    EDGE = "edge"
    AZURE = "azure"
    ELEVENLABS = "elevenlabs"
    SILICONFLOW = "siliconflow"


class SubtitleProvider(str, Enum):
    EDGE = "edge"
    WHISPER = "whisper"


class MaterialProvider(str, Enum):
    PEXELS = "pexels"
    PIXABAY = "pixabay"
    UPLOAD = "upload"


class AspectRatio(str, Enum):
    VERTICAL = "9:16"
    HORIZONTAL = "16:9"
    SQUARE = "1:1"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Language(str, Enum):
    ZH = "zh-CN"
    EN = "en-US"
    JA = "ja-JP"


# Voice catalogue surfaced via /api/v1/voice/providers
EDGE_VOICES = [
    {"id": "zh-CN-XiaoxiaoNeural", "name": "曉曉", "gender": "female", "language": "zh-CN"},
    {"id": "zh-CN-YunxiNeural", "name": "雲希", "gender": "male", "language": "zh-CN"},
    {"id": "zh-CN-YunjianNeural", "name": "雲健", "gender": "male", "language": "zh-CN"},
    {"id": "zh-CN-XiaoyiNeural", "name": "曉伊", "gender": "female", "language": "zh-CN"},
    {"id": "en-US-AriaNeural", "name": "Aria", "gender": "female", "language": "en-US"},
    {"id": "en-US-JennyNeural", "name": "Jenny", "gender": "female", "language": "en-US"},
    {"id": "en-US-GuyNeural", "name": "Guy", "gender": "male", "language": "en-US"},
    {"id": "ja-JP-NanamiNeural", "name": "Nanami", "gender": "female", "language": "ja-JP"},
]