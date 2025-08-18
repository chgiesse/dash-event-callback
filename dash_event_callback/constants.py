from typing import Literal, Final

STREAMING_TIMEOUT: Final[int] = 60

WS_CALLBACK_ENDPOINT: Final[str] = "/stream_dash_update_component"
SSE_CALLBACK_ENDPOINT: Final[str] = "/dash_update_component_sse"

STEAM_SEPERATOR: Final[str] = "__concatsep__"
SSE_CALLBACK_ID_KEY: Final[str] = "sse_callback_id"

ERROR_TOKEN: Final = "[ERROR]"
INIT_TOKEN: Final = "[INIT]"
DONE_TOKEN: Final = "[DONE]"

signal_type = Literal["[ERROR]", "[INIT]", "[DONE]"]