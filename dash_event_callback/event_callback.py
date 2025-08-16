from .components import SSECallbackComponent
from .helper import recursive_to_plotly_json
from .constants import (
    STEAM_SEPERATOR,
    SSE_CALLBACK_ID_KEY,
    SSE_CALLBACK_MAP,
    SSE_CALLBACK_ENDPOINT,
)

from dash import clientside_callback, hooks
from flask import request
from dataclasses import dataclass
from typing import Callable
import json
import inspect
import hashlib
import asyncio


@dataclass
class ServerSentEvent:
    data: str
    event: str | None = None
    id: int | None = None
    retry: int | None = None

    def encode(self) -> bytes:
        message = f"data: {self.data}"
        if self.event is not None:
            message = f"{message}\nevent: {self.event}"
        if self.id is not None:
            message = f"{message}\nid: {self.id}"
        if self.retry is not None:
            message = f"{message}\nretry: {self.retry}"
        message = f"{message}\n\n"
        return message.encode("utf-8")


def generate_clientside_callback(input_ids, sse_callback_id):
    args_str = ", ".join(input_ids)

    sse_id_obj = SSECallbackComponent.ids.sse(sse_callback_id)
    str_sse_id = json.dumps(sse_id_obj)
    property_assignments = [f"    'sse_callback_id': '{str_sse_id}'"]
    for input_id in input_ids:
        property_assignments.append(f'    "{input_id}": {input_id}')

    payload_obj = "{\n" + ",\n".join(property_assignments) + "\n}"

    js_code = f"""
        function({args_str}) {{
            if ( !window.dash_clientside.callback_context.triggered_id ) {{
                return window.dash_clientside.no_update;
            }}

            // Create payload object with all inputs
            const payload = {{
                ...{payload_obj},
                callback_context: window.dash_clientside.callback_context
            }};

            // Prepare SSE options with the payload
            console.log("payload", {{ payload }});
            const sse_options = {{
                payload: JSON.stringify({{ content: payload }}),
                headers: {{ "Content-Type": "application/json" }},
                method: "POST"
            }};

            // Set props for the SSE component
            window.dash_clientside.set_props(
                {str_sse_id},
                {{
                    options: sse_options,
                    url: "{SSE_CALLBACK_ENDPOINT}",
                }}
            );
        }}
    """

    return js_code


def generate_deterministic_id(func: Callable, dependencies: tuple) -> str:
    """Should align more with dashs callback id generation."""
    func_identity = f"{func.__module__}.{func.__qualname__}"
    dependency_reprs = sorted([repr(d) for d in dependencies])
    dependencies_string = ";".join(dependency_reprs)
    unique_string = f"{func_identity}|{dependencies_string}"
    return hashlib.sha256(unique_string.encode("utf-8")).hexdigest()


def stream_props(component_id: str, props):
    """Generate notification props for the specified component ID."""
    r = request.get_json()
    r_id = r["content"].get(SSE_CALLBACK_ID_KEY)
    response = [component_id, recursive_to_plotly_json(props), r_id]
    event = ServerSentEvent(json.dumps(response) + STEAM_SEPERATOR)
    return event.encode()


def event_callback(
    *dependencies,
    prevent_initital_call=True,
    on_error=None,
    reset_props={}
):

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutine(func):
            raise ValueError("Event callback needs to be a normal function, not async")

        if not inspect.isgeneratorfunction(func):
            raise ValueError("Event callback must be a generator function")

        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())
        callback_id = generate_deterministic_id(func, dependencies)
        SSE_CALLBACK_MAP[callback_id] = {"function": func, "on_error": on_error}

        # Generate and register clientside callback
        clientside_function = generate_clientside_callback(param_names, callback_id)
        clientside_callback(
            clientside_function,
            *dependencies,
            prevent_initial_call=prevent_initital_call,
        )

        @hooks.layout()
        def add_sse_component(layout):
            return (
                [SSECallbackComponent(callback_id)] + layout
                if isinstance(layout, list)
                else [SSECallbackComponent(callback_id), layout]
            )

        return func

    return decorator
