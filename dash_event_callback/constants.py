from typing import Literal


SSE_CALLBACK_MAP = {}
WS_CALLBACK_MAP = {}

WS_CALLBACK_ENDPOINT = "/stream_dash_update_component"
SSE_CALLBACK_ENDPOINT = "/dash_update_component_sse"

STEAM_SEPERATOR = "__concatsep__"
SSE_CALLBACK_ID_KEY = "sse_callback_id"

ERROR_TOKEN = "[ERROR]"
INIT_TOKEN = "[INIT]"
DONE_TOKEN = "[DONE]"

signal_type = Literal[ERROR_TOKEN, INIT_TOKEN, DONE_TOKEN]
