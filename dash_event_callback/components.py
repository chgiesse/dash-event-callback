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


def create_error_layout(e):
    app = get_app()
    app_on_error = app._on_error

    if not app_on_error:
        return html.Div(
            children=[
                html.Div(
                    f"⚠️ An error occurred {str(e)}",
                    style={
                        "backgroundColor": "#dc3545",  # Bootstrap danger red
                        "color": "white",
                        "padding": "12px 20px",
                        "margin": "10px",
                        "borderRadius": "4px",
                        "fontFamily": "Arial, sans-serif",
                        "fontSize": "14px",
                        "fontWeight": "bold",
                        "textAlign": "center",
                        "border": "1px solid #c82333",
                        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                    },
                )
            ],
            style={
                "width": "100%",
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "minHeight": "60px",
            },
        )

    if isinstance(app_on_error, callable):
        return app_on_error(e)

    return app_on_error
