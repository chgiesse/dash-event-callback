from .constants import SSE_CALLBACK_ENDPOINT

from dash_extensions import SSE
from dash.dcc import Store
from dash import html, get_app


class SSECallbackComponent(html.Div):

    class ids:
        sse = "component-update-stream-sse"
        store = "component-update-processing-store"

    def __init__(self):
        super().__init__(
            [
                SSE(id=self.ids.sse, concat=True, url=SSE_CALLBACK_ENDPOINT),
                Store(id=self.ids.store, data={}, storage_type="memory"),
            ]
        )
