from .components import SSECallbackComponent
from .helper import recursive_to_plotly_json, get_callback_id
from .constants import (
    STEAM_SEPERATOR,
    SSE_CALLBACK_ID_KEY,
    SSE_CALLBACK_MAP,
    SSE_CALLBACK_ENDPOINT,
)

from dash import clientside_callback, hooks, Dash, Input
from dash.dependencies import DashDependency
from flask import request
from dataclasses import dataclass
from typing import Callable
import typing as _t
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


def generate_reset_callback_function(callback_id: str, close_on: _t.List[_t.Tuple[DashDependency, _t.Any]], reset_props: _t.Dict = {}):
    """Generate a clientside callback function to reset SSE connection based on close_on conditions."""

    # Generate component IDs
    store_id = SSECallbackComponent.ids.store(callback_id)
    store_id_obj = json.dumps(store_id)

    sse_id = SSECallbackComponent.ids.sse(callback_id)
    sse_id_obj = json.dumps(sse_id)

    # Create the close_on conditions check
    close_conditions = []
    for i, (dependency, desired_state) in enumerate(close_on):
        if isinstance(desired_state, str):
            condition = f'value{i} === "{desired_state}"'
        elif isinstance(desired_state, bool):
            condition = f'value{i} === {str(desired_state).lower()}'
        elif isinstance(desired_state, (int, float)):
            condition = f'value{i} === {desired_state}'
        else:
            condition = f'value{i} === {json.dumps(desired_state)}'
        close_conditions.append(condition)

    # Create the reset_props assignments
    reset_props_assignments = []
    for component_id, props in reset_props.items():
        if isinstance(props, dict):
            props_str = json.dumps(props)
            reset_props_assignments.append(f'setProps("{component_id}", {props_str});')
        else:
            reset_props_assignments.append(f'setProps("{component_id}", {{value: {json.dumps(props)}}});')

    reset_props_code = '\n                '.join(reset_props_assignments)

    # Create the function parameters
    param_names = [f'value{i}' for i in range(len(close_on))]
    args_str = ', '.join(param_names)

    # Create the condition check
    condition_check = ' && '.join(close_conditions)

    js_code = f"""
        function({args_str}) {{
            if (!{condition_check}) {{
                return window.dash_clientside.no_update;
            }}

            setProps = window.dash_clientside.set_props;
            setProps({sse_id_obj}, {{done: true, url: null}});
            setProps({store_id_obj}, {{data: {{}}}});

            {reset_props_code}
        }}
    """

    return js_code


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


def stream_props(component_id: str | _t.Dict, props):
    """Generate notification props for the specified component ID."""
    r = request.get_json()
    r_id = get_callback_id(r["content"].get(SSE_CALLBACK_ID_KEY))
    response = [component_id, recursive_to_plotly_json(props), r_id]
    event = ServerSentEvent(json.dumps(response) + STEAM_SEPERATOR)
    return event.encode()


def event_callback(
    *dependencies,
    on_error=None,
    cancel: _t.Optional[_t.List[_t.Tuple[DashDependency, _t.Any]]]=None,
    reset_props: _t.Dict={},
    prevent_initital_call=True,
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

        # Generate and register reset callback if close_on is specified
        if cancel:
            reset_callback_function = generate_reset_callback_function(callback_id, cancel, reset_props)
            if reset_callback_function:
                # Extract the dependencies from close_on tuples
                reset_dependencies = [dependency for dependency, _ in cancel]
                hooks.clientside_callback(
                    reset_callback_function,
                    *reset_dependencies,
                    prevent_initial_call=True,
                )

        return func

    return decorator