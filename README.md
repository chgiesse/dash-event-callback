# Dash Event Callback

A powerful Dash plugin that enables generator function callbacks with real-time streaming updates, making it easy to create dynamic, interactive applications with progressive UI updates.

## 🚀 Features

- **Generator Function Callbacks**: Use Python generators to yield progressive updates
- **Real-time Streaming**: Update UI components as data becomes available
- **Error Handling**: Built-in error handling with custom error callbacks
- **Cancellation Support**: Cancel long-running operations with ease
- **State Management**: Automatic state reset and cleanup

## 📦 Installation

```bash
pip install dash-event-callback
```

## 🎯 Quick Start

```python
from dash_event_callback import stream_props, event_callback
from dash import Dash, Input, Output, State
import time

app = Dash(__name__)

@event_callback(
    Input("start-button", "n_clicks"),
    Output("progress-bar", "value"),
    on_error=lambda e: print(f"Error: {e}")
)
def streaming_progress(n_clicks):
    for i in range(0, 101, 10):
        yield stream_props("progress-bar", {"value": i})
        time.sleep(0.5)

app.layout = html.Button("Start Progress", id="start-button")
```

## 📚 Core Components

### `stream_props(component_id, props)`

Updates component properties in real-time during generator execution.

**Parameters:**
- `component_id` (str): The ID of the component to update
- `props` (dict): Properties to update on the component

**Example:**
```python
yield stream_props("my-button", {"loading": True, "children": "Processing..."})
yield stream_props("my-table", {"rowData": new_data})
```

### `event_callback`

Decorator that transforms generator functions into Dash callbacks with streaming capabilities.

**Parameters:**
- `inputs` (list): Dash Input objects
- `outputs` (list, optional): Dash Output objects
- `states` (list, optional): Dash State objects
- `on_error` (callable, optional): Error handler function
- `cancel` (list, optional): Conditions to cancel the callback
- `reset_props` (dict, optional): Properties to reset when callback doesn't completes correctly

## 🔧 Advanced Usage

### Error Handling

```python
@event_callback(
    Input("process-btn", "n_clicks"),
    on_error=lambda e: print(f"Error occurred: {e}")
)
def process_with_error_handling(n_clicks):
    try:
        # Your processing logic
        yield stream_props("status", {"children": "Processing..."})
        # ... more processing
    except Exception as e:
        # Error will be handled by on_error callback
        raise e
```

### Cancellation Support

```python
@event_callback(
    Input("start-btn", "n_clicks"),
    cancel=[
        (Input("cancel-btn", "n_clicks"), 1),
        (Input("tabs", "value"), "other-tab")
    ],
    reset_props={
        "start-btn": {"loading": False},
        "cancel-btn": {"display": "none"}
    }
)
def cancellable_operation(n_clicks):
    yield stream_props("start-btn", {"loading": True})
    yield stream_props("cancel-btn", {"display": "block"})

    for step in range(10):
        # Operation can be cancelled by clicking cancel-btn or switching tabs
        yield stream_props("progress", {"value": step * 10})
        time.sleep(1)
```

### State Management

The library automatically handles state management:

- **Initial State**: Components start in their initial state
- **Reset on Cancel**: Components return to initial state when cancelled
- **Reset on Complete**: Components can be reset to specified properties
- **Memory Cleanup**: Automatic cleanup of resources

## 📋 Best Practices

1. **Always handle errors**: Use `on_error` parameter for robust error handling
2. **Provide cancellation**: Allow users to cancel long-running operations
3. **Reset state**: Always reset components to a known state
4. **Yield frequently**: Update UI often for better user experience
5. **Handle cleanup**: Use `reset_props` to restore component states

## 🛠️ Configuration

### Custom Error Handlers

```python
def custom_error_handler(error):
    return stream_props("error-display", {
        "children": f"An error occurred: {str(error)}",
        "color": "red"
    })

@event_callback(
    Input("btn", "n_clicks"),
    on_error=custom_error_handler
)
def my_callback(n_clicks):
    # Your logic here
    pass
```


## 🔗 Integration Examples

### Basic Progress Bar

```python
@event_callback(
    Input("start-btn", "n_clicks"),
    Output("progress", "value")
)
def update_progress(n_clicks):
    for i in range(0, 101, 5):
        yield stream_props("progress", {"value": i})
        time.sleep(0.1)
```

### Data Streaming

```python
@event_callback(Input("load-data", "n_clicks"))
def stream_data(n_clicks):
    for chunk in data_generator():
        yield stream_props("data-table", {
            "rowTransaction": {"add": chunk}
        })
        time.sleep(0.1)
```

### Multi-step Process

```python
@event_callback(
    Input("process-btn", "n_clicks"),
    cancel=[(Input("cancel-btn", "n_clicks"), 1)]
)
def multi_step_process(n_clicks):
    steps = ["Initializing", "Processing", "Validating", "Finalizing"]

    for i, step in enumerate(steps):
        yield stream_props("status", {"children": step})
        yield stream_props("step-indicator", {"active": i})
        time.sleep(2)
```

## 📖 API Reference

### `stream_props(component_id, props)`

Updates component properties during generator execution.

**Parameters:**
- `component_id` (str): The ID of the component to update
- `props` (dict): Properties to update on the component

**Returns:** Generator yield value for event_callback

### `event_callback(inputs, outputs=None, states=None, on_error=None, cancel=None, reset_props=None)`

Decorator for creating streaming callbacks.

**Parameters:**
- `inputs`: List of Dash Input objects
- `outputs`: List of Dash Output objects (optional)
- `states`: List of Dash State objects (optional)
- `on_error`: Callable for error handling (optional)
- `cancel`: List of (Input, value) tuples for cancellation (optional)
- `reset_props`: Dict of component_id: props for reset (optional)

**Returns:** Decorated generator function

## 🔄 Callback Lifecycle

1. **Initialization**: Callback starts with initial component states
2. **Execution**: Generator yields `stream_props` updates
3. **Cancellation**: If cancel conditions are met, execution stops
4. **Completion**: Final state is set, reset_props applied
5. **Cleanup**: Resources are cleaned up automatically

## 🚨 Error Handling

Errors in generator functions are automatically caught and can be handled by:

- `on_error` callback function
- Global error handler
- Default error handling (prints to console)

## 🔧 Advanced Patterns

### Conditional Updates

```python
@event_callback(Input("toggle-btn", "n_clicks"))
def conditional_updates(n_clicks):
    for i in range(10):
        if i % 2 == 0:
            yield stream_props("even-counter", {"children": i})
        else:
            yield stream_props("odd-counter", {"children": i})
        time.sleep(1)
```

### Batch Updates

```python
@event_callback(Input("batch-btn", "n_clicks"))
def batch_updates(n_clicks):
    for batch in data_batches():
        # Update multiple components at once
        yield stream_props("table", {"rowData": batch["data"]})
        yield stream_props("counter", {"children": batch["count"]})
        yield stream_props("status", {"children": batch["status"]})
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.