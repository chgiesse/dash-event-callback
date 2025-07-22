from .event_callback import (
    SSECallbackComponent,
    ServerSentEvent,
    event_callback,
    stream_props,
)
from .constants import (
    SSE_CALLBACK_ENDPOINT,
    STEAM_SEPERATOR,
    SSE_CALLBACK_ID_KEY,
    SSE_CALLBACK_MAP,
    ERROR_TOKEN,
    DONE_TOKEN,
    INIT_TOKEN,
    signal_type,
)

from typing import Dict
from dash import hooks, Input, Output, State
from flask import stream_with_context, make_response, request, abort
import warnings
import time
import json


@hooks.route(SSE_CALLBACK_ENDPOINT, methods=["POST"])
def sync_sse_callback_endpoint():

    if "text/event-stream" not in request.accept_mimetypes:
        abort(400)

    data = request.get_json()
    content = data["content"].copy()
    ctx = content.pop("callback_context", {})
    callback_id = content.pop(SSE_CALLBACK_ID_KEY)
    callback = SSE_CALLBACK_MAP.get(callback_id, {})
    callback_func = callback.get("function")
    on_error = callback.get("on_error")

    def send_signal(signal: signal_type, payload: Dict = {}):
        response = [signal, payload, callback_id]
        event = ServerSentEvent(json.dumps(response) + STEAM_SEPERATOR)
        return event.encode()

    @stream_with_context
    def callback_generator():
        yield send_signal(INIT_TOKEN)

        if not callback_func:
            error_message = f"Could not find function for sse id {callback_id}"
            yield (
                on_error(error_message)
                if on_error
                else send_signal(ERROR_TOKEN, {"error": error_message})
            )
            return

        try:
            for item in callback_func(**content):
                if item is None:
                    warnings.warn(
                        f"Callback generator functions should not return None values - Callback ID :{callback_id}"
                    )
                    continue
                yield item
                time.sleep(0.05)
            yield send_signal(DONE_TOKEN)
        except Exception as e:
            yield (
                on_error(e) if on_error else send_signal(ERROR_TOKEN, {"error": str(e)})
            )

    response = make_response(
        callback_generator(),
        {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked",
        },
    )

    response.timeout = 30 
    return response


@hooks.layout(priority=1)
def add_sse_component(layout):
    return (
        [SSECallbackComponent()] + layout
        if isinstance(layout, list)
        else [SSECallbackComponent(), layout]
    )


hooks.clientside_callback(
    """
    function(message, processedData) {
        if (!message) { return processedData || {} };
        
        const TOKENS = {
            DONE: "[DONE]",
            INIT: "[INIT]",
            ERROR: "[ERROR]"
        };
        
        const setProps = window.dash_clientside.set_props;
        const messageList = message.split('__concatsep__');
        processedData = processedData || {};
        
        if (messageList[messageList.length - 1] === '') {
            messageList.pop();
        }
        
        const cbId = JSON.parse(messageList[0])[2];
        const startIdx = processedData[cbId] || 0;
        const newMessages = messageList.slice(startIdx);
        
        newMessages.forEach(messageStr => {
            try {
                const [componentId, props, callbackId] = JSON.parse(messageStr);
                
                switch (componentId) {
                    case TOKENS.INIT:
                        processedData[callbackId] = 1;
                        break;
                    case TOKENS.DONE:
                        processedData[callbackId] = 0;
                        break;
                    case TOKENS.ERROR:
                        processedData[callbackId] = 0;
                        window.alert("Error occurred while processing stream", props);
                        break;
                    default:
                        setProps(componentId, props);
                        processedData[callbackId]++;
                }
            } catch (e) {
                console.error("Error processing message:", e, messageStr);
            }
        });
        
        return processedData;
    }""",
    Output(SSECallbackComponent.ids.store, "data"),
    Input(SSECallbackComponent.ids.sse, "value"),
    State(SSECallbackComponent.ids.store, "data"),
    prevent_initial_call=True,
)

hooks.clientside_callback(
    f"""
    function ( pathChange ) {{
        if ( !pathChange ) {{
            return window.dash_clientside.no_update
        }}
        window.dash_clientside.set_props('{SSECallbackComponent.ids.sse}', {{done: true, url: null}});
        window.dash_clientside.set_props('{SSECallbackComponent.ids.store}', {{data: {{}}}});
    }}""",
    Input("_pages_location", "pathname", allow_optional=True),
    prevent_initial_call=True,
)

__all__ = ["event_callback", "stream_props"]
