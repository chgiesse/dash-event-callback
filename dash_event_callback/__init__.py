from .event_callback import (
    SSECallbackComponent,
    ServerSentEvent,
    SSEServerObjects,
    event_callback,
    stream_props,
)
from .constants import (
    SSE_CALLBACK_ENDPOINT,
    STEAM_SEPERATOR,
    SSE_CALLBACK_ID_KEY,
    ERROR_TOKEN,
    DONE_TOKEN,
    INIT_TOKEN,
    STREAMING_TIMEOUT,
    signal_type,
)
from .helper import get_callback_id

from typing import Dict
from dash import hooks, Input, Output, State, Dash, MATCH
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
    callback_id = get_callback_id(content.pop(SSE_CALLBACK_ID_KEY))

    if not callback_id:
        raise ValueError("callback_id is required")

    def send_signal(signal: signal_type, payload: Dict = {}):
        response = [signal, payload, callback_id]
        event = ServerSentEvent(json.dumps(response) + STEAM_SEPERATOR)
        return event.encode()

    @stream_with_context
    def callback_generator():
        yield send_signal(INIT_TOKEN)
        sse_obj = SSEServerObjects.get_func(callback_id)

        if not sse_obj:
            error_message = f"Could not find function for sse id {callback_id}"
            yield send_signal(ERROR_TOKEN, {"error": error_message})
            return

        callback_func = sse_obj.func
        on_error = sse_obj.on_error

        try:
            start_time = time.time()
            for item in callback_func(**content):
                elapsed = time.time() - start_time
                if elapsed > STREAMING_TIMEOUT:
                   raise TimeoutError(f"Timeout for callback: {sse_obj.func_name} | {callback_id}")

                if item is None:
                    warnings.warn(
                        f"Callback generator functions should not return None values - Callback: {sse_obj.func_name} | {callback_id}"
                    )
                    continue

                yield item
                time.sleep(0.05)
            yield send_signal(DONE_TOKEN)

        except Exception as e:
            handle_error = True
            if on_error:
                handle_error = False
                yield on_error(e)

            yield send_signal(
                ERROR_TOKEN,
                {
                    "error": str(e),
                    "handle_error": handle_error,
                    "reset_props": sse_obj.reset_props
                }
            )

    response = make_response(callback_generator())
    response.headers.update({
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Transfer-Encoding": "chunked",
    })
    return response


hooks.clientside_callback(
    """
    function(message, processedData, sseId) {
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
                        console.log("INIT SSE", sseId)
                        processedData[callbackId] = 1;
                        setProps(sseId, {done: false})
                        break;
                    case TOKENS.DONE:
                        console.log("SET SSE DONE")
                        processedData[callbackId] = 0;
                        setProps(sseId, {done: true, url: null})
                        break;
                    case TOKENS.ERROR:
                        processedData[callbackId] = 0;
                        resetProps = props.reset_props ? props.reset_props : {};
                        if ( props.handle_error ) {
                            window.alert("Error occurred while processing stream - " + props.error);
                        }
                        for ( const [rcid, rprops] of Object.entries(resetProps)) {
                            setProps(rcid, rprops)
                        }
                        setProps(sseId, {done: true, url: null});
                        break;
                    default:
                        setProps(componentId, props);
                        processedData[callbackId]++;
                }
            } catch (e) {
                processedData[cbId] = 0;
                setProps(sseId, {done: true});
                console.error("Error processing message:", e, messageStr);
            }
        });

        return processedData;
    }""",
    Output(SSECallbackComponent.ids.store(MATCH), "data"),
    Input(SSECallbackComponent.ids.sse(MATCH), "value"),
    State(SSECallbackComponent.ids.store(MATCH), "data"),
    State(SSECallbackComponent.ids.sse(MATCH), "id"),
    # prevent_initial_call=True,
)
from dash import ALL
hooks.clientside_callback(
    """( done, id, url ) => { console.log(done, id, url) }""",
    Input(SSECallbackComponent.ids.sse(ALL), "done"),
    Input(SSECallbackComponent.ids.sse(ALL), "id"),
    Input(SSECallbackComponent.ids.sse(ALL), "url"),
)

__all__ = ["event_callback", "stream_props"]
