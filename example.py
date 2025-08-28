from dash_event_callback import stream_props, event_callback

from dash_iconify import DashIconify
from plotly.express import data
from dash import Dash, Input, clientside_callback, ALL, MATCH, State, Output, callback, set_props
import dash_mantine_components as dmc
from flask import request
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
                    id=self.ids.container,
                    transitionDuration=500,
                    position="top-right"
                ),
            ]
        )


class TabsComponent(dmc.Tabs):

    class ids:
        tabs = "main-tabs"
        stream_tab = "stream-tab"
        cicd_tab = "cicd-tab"

    def __init__(self):
        super().__init__(
            [
                dmc.TabsList(
                    [
                        dmc.TabsTab("Data Stream", value="stream", id=self.ids.stream_tab, leftSection=DashIconify(icon="material-symbols:download-rounded")),
                        dmc.TabsTab("CI/CD Pipeline", value="cicd", id=self.ids.cicd_tab, leftSection=DashIconify(icon="material-symbols:play-arrow-rounded")),
                    ]
                ),
                dmc.TabsPanel(
                    TestComponentStream(),
                    value="stream",
                    pt="lg"
                ),
                dmc.TabsPanel(
                    CiCdComponent(),
                    value="cicd",
                    pt="lg"
                ),
            ],
            id=self.ids.tabs,
            value="stream",
            color="grape",
            persistence=True,
            persisted_props=["value"]
        )


class CiCdComponent(dmc.Box):

    class ids:
        button = "cicd-btn"
        reset_button = "cicd-reset-btn"
        stepper = "cicd-stepper"
        step = lambda idx: {"type": "cicd-step", "index": idx}

    @callback(
        Output(ids.stepper, "active"),
        Input(ids.reset_button, "n_clicks"),
        State(ids.stepper, "active"),
        prevent_initial_call=True
    )
    def cancel_cicd(reset, active):
        if not reset:
            return

        set_props(CiCdComponent.ids.step(active), {"loading": False})
        return 0

    @event_callback(
        Input(ids.button, "n_clicks"),
        on_error=lambda e: NotificationComponent.send_notification(
            title="Error occurred during CI/CD pipeline - please reload the page",
            message=str(e),
            color="red.6",
            autoClose=False
        ),
        cancel=[
            (Input(ids.reset_button, "n_clicks"), 1),
            (Input(TabsComponent.ids.tabs, "value"), "stream")
        ],
        reset_props={
            ids.button: {"disabled": False, "children": "Start CI/CD Pipeline"},
            ids.reset_button: {"display": "none"},
        }
    )
    def run_cicd(n_clicks):

        # Set start button to loading and show reset button
        yield stream_props(CiCdComponent.ids.button, {"disabled": True})
        yield stream_props(CiCdComponent.ids.reset_button, {"display": "flex"})

        for step in range(0, 7):
            # Update stepper active step
            if step == 6:
                yield stream_props(CiCdComponent.ids.stepper, {"active": 7})
                break

            # Set loading state for current step
            yield stream_props(CiCdComponent.ids.stepper, {"active": step})
            yield stream_props(CiCdComponent.ids.step(step), {"loading": True})
            time.sleep(2)
            # Remove loading state for current step
            yield stream_props(CiCdComponent.ids.step(step), {"loading": False})

        # Update button states after completion
        yield stream_props(CiCdComponent.ids.button, {"disabled": False, "children": "Restart CI/CD Pipeline"})
        yield stream_props(CiCdComponent.ids.reset_button, {"display": "none"})

    def __init__(self) -> None:
        super().__init__(
            style={"width": "fit-content"},
            children=[
                dmc.Group([
                    dmc.Button(
                        "Start CI/CD Pipeline",
                        id=self.ids.button,
                        color="grape",
                        leftSection=DashIconify(
                            icon="material-symbols:play-arrow-rounded", height=20
                        ),
                        fullWidth=False,
                    ),
                    dmc.Button(
                        "Cancel CI/CD",
                        id=self.ids.reset_button,
                        variant="light",
                        fullWidth=False,
                        color="red",
                        display="none",
                        leftSection=DashIconify(icon="mdi:cancel-circle-outline")
                    ),
                ], mb="md"),
                dmc.Stepper(
                    id=self.ids.stepper,
                    active=0,
                    orientation="vertical",
                    allowNextStepsSelect=False,
                    children=[
                        dmc.StepperStep(
                            id=self.ids.step(0),
                            label="Code Checkout",
                            description="Fetching latest code from repository",
                            children=dmc.Text("🔍 Checking out latest code from main branch...", ta="center"),
                        ),
                        dmc.StepperStep(
                            id=self.ids.step(1),
                            label="Dependencies",
                            description="Installing and updating dependencies",
                            children=dmc.Text("📦 Installing project dependencies...", ta="center"),
                        ),
                        dmc.StepperStep(
                            id=self.ids.step(2),
                            label="Build",
                            description="Compiling and building the application",
                            children=dmc.Text("🔨 Compiling TypeScript files...", ta="center"),
                        ),
                        dmc.StepperStep(
                            id=self.ids.step(3),
                            label="Test",
                            description="Running unit and integration tests",
                            children=dmc.Text("🧪 Running unit tests...", ta="center"),
                        ),
                        dmc.StepperStep(
                            id=self.ids.step(4),
                            label="Security Scan",
                            description="Checking for vulnerabilities and compliance",
                            children=dmc.Text("🔒 Running security vulnerability scan...", ta="center"),
                        ),
                        dmc.StepperStep(
                            id=self.ids.step(5),
                            label="Deploy",
                            description="Deploying to production environment",
                            children=dmc.Text("🚀 Preparing deployment to production...", ta="center"),
                        ),
                        dmc.StepperCompleted(
                            children=dmc.Text(
                                "✅ CI/CD Pipeline completed successfully! Application deployed to production.",
                                ta="center",
                                c="green",
                                fw="bold",
                            )
                        ),
                    ],
                ),
            ],
        )


class TestComponentStream(dmc.Stack):

    class ids:
        init_button = "stream-button"
        reset_button = "reset-button"
        table = "stream-table"

    @event_callback(
        Input(ids.init_button, "n_clicks"),
        on_error=lambda e: NotificationComponent.send_notification(
            title="Error occured durings stream - please reload the page",
            message=str(e),
            color="red.6",
            autoClose=False
        ),
        cancel=[
            (Input(ids.reset_button, "n_clicks"), 1),
            (Input(TabsComponent.ids.tabs, "value"), "cicd")
        ],
        reset_props={
            ids.init_button: {"loading": False},
            ids.reset_button: {"display": "none"},
            ids.table: {"rowData": []}
        },
    )
    def update_table(n_clicks):
        yield stream_props(TestComponentStream.ids.init_button, {"loading": True})

        yield NotificationComponent.send_notification(
            title="Starting Download!",
            message="Notifications in Dash, Awesome!",
            color="lime",
        )

        yield stream_props(TestComponentStream.ids.reset_button, {"display": "flex"})

        progress = 0
        chunck_size = 500
        for data_chunk, colnames in get_data(chunck_size):
            if progress == 0:
                columnDefs = [{"field": col} for col in colnames]
                update = {"rowData": data_chunk, "columnDefs": columnDefs}
            else:
                update = {"rowTransaction": {"add": data_chunk}}

            yield stream_props(TestComponentStream.ids.table, update)

            if len(data_chunk) == chunck_size:
                yield NotificationComponent.send_notification(
                    title="Progress",
                    message=f"Processed {chunck_size + (chunck_size * progress)} items",
                    color="violet",
                )

            progress += 1

        yield stream_props(
            TestComponentStream.ids.init_button,
            {
                "loading": False,
                "children": "Reload",
            },
        )

        yield stream_props(TestComponentStream.ids.reset_button, {"display": "none"})

        yield NotificationComponent.send_notification(
            title="Finished Callback!",
            message="Notifications in Dash, Awesome!",
            icon=DashIconify(icon="akar-icons:circle-check"),
            color="lime",
        )

    def __init__(self):

        buttons = dmc.Group(
            [
                dmc.Button(
                    "Start",
                    id=self.ids.init_button,
                    color="grape",
                    leftSection=DashIconify(
                        icon="material-symbols:download-rounded", height=20
                    ),
                    fullWidth=False,
                    styles={"section": {"marginRight": "var(--mantine-spacing-md)"}},
                ),
                dmc.Button(
                    "Cancel Query",
                    id=self.ids.reset_button,
                    variant="light",
                    fullWidth=False,
                    styles={"section": {"marginRight": "var(--mantine-spacing-md)"}},
                    color="red",
                    display="none",
                    leftSection=DashIconify(icon="mdi:cancel-circle-outline")
                ),
            ]
        )

        super().__init__(
            justify="flex-start",
            align="flex-start",
            children=[
                buttons,
                dag.AgGrid(
                    id=self.ids.table,
                    style={"height": "70vh"},
                    className="ag-theme-quartz-auto-dark",
                    dashGridOptions={
                        "pagination": True,
                    },
                ),
            ],
        )


# class ChatComponent(dmc.Affix):

#     class ids:
#         expand_button = "chat-expand-btn"
#         drawer = "chat-drawer"

#     clientside_callback(
#         """( click, isOpen ) => { return !isOpen }""",
#         Output(ids.drawer, "opened"),
#         Input(ids.expand_button, "n_clicks"),
#         State(ids.drawer, "opened"),
#         prevent_initial_call=True
#     )

#     def __init__(self) -> None:
#         # Sample messages for demonstration
#         sample_messages = [
#             dmc.Group(
#                 [
#                     dmc.Space(w="auto"),
#                     dmc.Paper(
#                         dmc.Text("Hello! How can I help you today?", size="sm"),
#                         p="xs",
#                         bg="blue",
#                         style={"maxWidth": "80%", "borderRadius": "12px 12px 4px 12px"}
#                     )
#                 ],
#                 justify="flex-end"
#             ),
#             dmc.Group(
#                 [
#                     dmc.Paper(
#                         dmc.Text("I need help with my project", size="sm"),
#                         p="xs",
#                         bg="gray",
#                         style={"maxWidth": "80%", "borderRadius": "12px 12px 12px 4px"}
#                     ),
#                     dmc.Space(w="auto")
#                 ],
#                 justify="flex-start"
#             ),
#             dmc.Group(
#                 [
#                     dmc.Space(w="auto"),
#                     dmc.Paper(
#                         dmc.Text("I'd be happy to help! What kind of project are you working on?", size="sm"),
#                         p="xs",
#                         bg="blue",
#                         style={"maxWidth": "80%", "borderRadius": "12px 12px 4px 12px"}
#                     )
#                 ],
#                 justify="flex-end"
#             )
#         ]

#         # Chat header
#         chat_header = dmc.Group(
#             [
#                 dmc.Avatar(
#                     DashIconify(icon="material-symbols:smart-toy-outline"),
#                     size="md",
#                     color="blue"
#                 ),
#                 dmc.Stack(
#                     [
#                         dmc.Text("AI Assistant", fw="bold", size="sm"),
#                         dmc.Text("Online", size="xs", c="gray")
#                     ],
#                     gap=0
#                 ),
#             ],
#             p="md",
#             style={"borderBottom": "1px solid var(--mantine-color-dark-4)"}
#         )

#         # Messages container
#         messages_container = dmc.ScrollArea(
#             dmc.Stack(
#                 sample_messages,
#                 gap="md",
#                 p="md",
#                 style={"minHeight": "300px"}
#             ),
#             h=400,
#             scrollbarSize=6,
#             offsetScrollbars="y"
#         )

#         # Input area
#         input_area = dmc.Stack(
#             [
#                 dmc.Textarea(
#                     placeholder="Type your message...",
#                     minRows=1,
#                     maxRows=4,
#                     autosize=True,
#                     style={"flex": 1}
#                 ),
#                 dmc.Button(
#                     [
#                         DashIconify(icon="material-symbols:send", width=16),
#                         dmc.Text("Send", ml="xs")
#                     ],
#                     variant="filled",
#                     color="blue",
#                     size="sm",
#                     fullWidth=False,
#                     style={"alignSelf": "flex-end"}
#                 )
#             ],
#             gap="xs",
#             p="md",
#             style={"borderTop": "1px solid var(--mantine-color-dark-4)"}
#         )

#         # Chat drawer content
#         chat_content = dmc.Stack(
#             [
#                 chat_header,
#                 messages_container,
#                 input_area
#             ],
#             h="100%",
#             gap=0
#         )

#         super().__init__(
#             [
#                 dmc.Button(
#                     [
#                         DashIconify(icon="material-symbols:chat", width=20),
#                         dmc.Text("Chat", ml="xs")
#                     ],
#                     id=self.ids.expand_button,
#                     variant="gradient",
#                     gradient={"from": "blue", "to": "cyan", "deg": 35},
#                     size="md"
#                 ),
#                 dmc.Drawer(
#                     chat_content,
#                     size=450,
#                     id=self.ids.drawer,
#                     title=None,
#                     withCloseButton=False,
#                     styles={
#                         "body": {"padding": 0, "height": "100%"},
#                         "inner": {"padding": 0}
#                     }
#                 )
#             ],
#             position={"bottom": 20, "right": 20}
#         )


app = Dash(__name__)

app.layout = dmc.MantineProvider(
    dmc.Stack(
        [
            dmc.Title("Stream Components"),
            TabsComponent(),
            NotificationComponent(),
            # ChatComponent()
        ],
        p="md",
        px="xl",
    ),
    forceColorScheme="dark",
    theme={
        "defaultRadius": "md",
        "colors": {
            "dark": [
                "#d3d4d6",
                "#7a7e83",
                "#383e46",
                "#4a5d79",
                "#222831",
                "#1f242c",
                "#181c22",
                "#0e1014",
                "#14181d",
                "#1b2027",
            ],
            "blue": [
                "#ecf4ff",
                "#dce4f5",
                "#b9c7e2",
                "#94a8d0",
                "#748dc0",
                "#5f7cb7",
                "#5474b4",
                "#44639f",
                "#3a5890",
                "#2c4b80",
            ],
        },
    }
)

if __name__ == "__main__":
    app.run(debug=True, port=8123)
