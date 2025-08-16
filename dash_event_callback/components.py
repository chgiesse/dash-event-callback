from .constants import SSE_CALLBACK_ENDPOINT

from dash_extensions import SSE
from dash.dcc import Store
from dash import html


class SSECallbackComponent(html.Div):

    class ids:
        sse = lambda idx: {"type": "dash-event-stream", "index": idx}
        store = lambda idx: {"type": "dash-event-stream-store", "index": idx}

    def __init__(self, callback_id: str):
        super().__init__(
            [
                SSE(id=self.ids.sse(callback_id), concat=True, url=SSE_CALLBACK_ENDPOINT),
                Store(id=self.ids.store(callback_id), data={}, storage_type="memory"),
            ],
        )
