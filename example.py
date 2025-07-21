from dash_event_callback import stream_props, event_callback

from dash_iconify import DashIconify
from plotly.express import data
from dash import Dash, Input
import dash_mantine_components as dmc
import dash_ag_grid as dag
import pandas as pd
import random
import time


def get_data(chunk_size):
    df: pd.DataFrame = data.gapminder()
    total_rows = df.shape[0]

    while total_rows > 0:
        time.sleep(2)
        end = len(df) - total_rows + chunk_size
        total_rows -= chunk_size
        update_data = df[:end].to_dict("records")
        df.drop(df.index[:end], inplace=True)
        yield update_data, df.columns


class NotificationComponent(dmc.Box):

    class ids:
        container = "notifications-container"
        notification = "default-notifixcation-id"

    @classmethod
    def send_notification(
        cls,
        title: str,
        message: str,
        id: str | None = None,
        color: str = "primary",
        autoClose=True,
        **kwargs,
    ):
        _id = id if id else random.randint(0, 1000)
        return stream_props(
            cls.ids.container,
            {
                "sendNotifications": [
                    dict(
                        title=title,
                        id=_id,
                        action="show",
                        message=message,
                        color=color,
                        autoClose=autoClose,
                        **kwargs,
                    )
                ]
            },
        )

    def __init__(self):
        super().__init__(
            [
                dmc.NotificationContainer(
                    id=self.ids.container, transitionDuration=500
                ),
            ]
        )


class TestComponentStream(dmc.Stack):

    class ids:
        button = "stream-button"
        table = "stream-table"

    @event_callback(
        Input(ids.button, "n_clicks"),
        # on_error=lambda e: NotificationComponent.send_notification(
        #     title="Error occured durings stream - please reload the page",
        #     message=str(e),
        #     color="red.6",
        #     autoClose=False
        # )
    )
    def update_table(n_clicks):

        yield stream_props(TestComponentStream.ids.button, {"loading": True})

        yield NotificationComponent.send_notification(
            title="Starting Download!",
            message="Notifications in Dash, Awesome!",
            color="lime",
        )
        yield None
        progress = 0
        chunck_size = 500
        for data_chunk, colnames in get_data(chunck_size):
            update = {"rowTransaction": {"add": data_chunk}}
            if progress == 0:
                update = {"rowData": data_chunk}
                columnDefs = [{"field": col} for col in colnames]

                yield stream_props(
                    TestComponentStream.ids.table,
                    props={"columnDefs": columnDefs}
                )

            yield stream_props(TestComponentStream.ids.table, update)

            if len(data_chunk) == chunck_size:
                yield NotificationComponent.send_notification(
                    title="Progress",
                    message=f"Processed {chunck_size + (chunck_size * progress)} items",
                    color="violet",
                )

            progress += 1

        yield stream_props(
            TestComponentStream.ids.button,
            {
                "loading": False,
                "children": "Reload",
            },
        )

        yield NotificationComponent.send_notification(
            title="Finished Callback!",
            message="Notifications in Dash, Awesome!",
            icon=DashIconify(icon="akar-icons:circle-check"),
            color="lime",
        )

    def __init__(self):
        super().__init__(
            justify="flex-start",
            align="flex-start",
            children=[
                dmc.Button(
                    "Start",
                    id=self.ids.button,
                    variant="gradient",
                    gradient={"from": "grape", "to": "violet", "deg": 35},
                    leftSection=DashIconify(
                        icon="material-symbols:download-rounded", height=20
                    ),
                    fullWidth=False,
                    styles={"section": {"marginRight": "var(--mantine-spacing-md)"}},
                ),
                dag.AgGrid(
                    id=self.ids.table,
                    style={"height": "75vh"},
                    dashGridOptions={
                        "pagination": True,
                    },
                ),
            ],
        )


app = Dash(
    __name__
)

app.layout = dmc.MantineProvider(
    dmc.Stack(
        [
            dmc.Title("Stream Components"),
            TestComponentStream(),
            NotificationComponent(),
        ],
        p="md",
        px="xl",
    ),
    forceColorScheme="light",
)

if __name__ == "__main__":
    app.run(debug=True)
