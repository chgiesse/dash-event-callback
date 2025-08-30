# Dash Event Callback
Server sent event based callbacks for `Dash`

## Event Callback
Server-Sent Events (SSEs) are a server push technology that keeps an HTTP connection open, allowing servers to continuously stream updates to clients. They are typically used for sending messages, data streams, or real-time updates directly to the browser via the native JavaScript EventSource API.

**NOTE**: Dash/Flask are synchronus, which leads to SSE's blocking a **whole** worker for the durtion of the execution. Thats why this package has 60sec timeout integrated. If you want to use event callbacks extensively - you should consider using [Flash](https://github.com/chgiesse/flash).

fvent callbacks build on this principle by using generator functions that yield updates instead of returning once. This enables:

* Progressive UI updates (e.g., streaming partial results).

The API mirrors Dash’s callback design, but with two key differences:

1. No explicit output needed – updates are applied with stream_props.
2. `stream_props` behaves like set_props, needs to be yield.

### Stream Props
The stream_props function allows you to send UI updates on the fly and follows the set_props API by Dash, while enhancing it with batch updates which reduces network overhead and quicker UI updates. The function can be used as follows:

```python
# Single updates
yield stream_props(component_id="cid", props={"children": "Hello Stream"})
yield stream_props("cid", {"children": "Hello Stream"})
# Batch updates
yield stream_props(batch=[
    ("cid", {"children": "Hello Stream"}),
    ("btn", {"disablesd": True}),
])
yield stream_props([
    ("cid", {"children": "Hello Stream"}),
    ("btn", {"disablesd": True}),
])
```

### Basic Event Callback

This example (from Dash’s background callback docs) shows how a background callback is no longer necessary—eliminating the need for extra services like Celery + Redis.


```python
# data.py
import pandas as pd
import time

def get_data(chunk_size: int):
    df: pd.DataFrame = data.gapminder()
    total_rows = df.shape[0]

    while total_rows > 0:
        time.sleep(2)
        end = len(df) - total_rows + chunk_size
        total_rows -= chunk_size
        update_data = df[:end].to_dict("records")
        df.drop(df.index[:end], inplace=True)
        yield update_data, df.columns
```

A more realistic use case would be streaming query results with *SQLAlchemy async*:


```python
# data.py
from sqlalchemy import Connection

def get_data(connection: Connection):
    result = connection.execute(select(users_table))

    for partition in partition_results(result, 100):
        print("list of rows: %s" % partition)
        yield partition

# Helper function to partition results
def partition_results(result, size):
    partition = []
    for row in result:
        partition.append(row)
        if len(partition) == size:
            yield partition
            partition = []
    if partition:
        yield partition
```
Hooking it into your app with `event_callback`:

```python
# app.py
from flash import Input, event_callback, stream_props

@event_callback(Input("start-stream-button", "n_clicks"))
def update_table(_):
    yield stream_props([
        ("start-stream-button", {"loading": True}),
        ("cancel-stream-button", {"display": "flex"})
    ])

    progress = 0
    chunk_size = 500
    for data_chunk, colnames in get_data(chunk_size):
        if progress == 0:
            columnDefs = [{"field": col} for col in colnames]
            update = {"rowData": data_chunk, "columnDefs": columnDefs}
        else:
            update = {"rowTransaction": {"add": data_chunk}}

        yield stream_props("dash-ag-grid", update)

        if len(data_chunk) == chunk_size:
            yield NotificationsContainer.send_notification(
                title="Starting stream!",
                message="Notifications in Dash, Awesome!",
                color="lime",
            )

        progress += 1

    yield stream_props("start-stream-button", {"loading": False, "children": "Reload"})
    yield stream_props("reset-strea-button", {"display": "none"})
```
