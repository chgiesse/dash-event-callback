
module DashEventCallback
using Dash

const resources_path = realpath(joinpath( @__DIR__, "..", "deps"))
const version = "1.2.0"

include("jl/sse.jl")

function __init__()
    DashBase.register_package(
        DashBase.ResourcePkg(
            "dash_event_callback",
            resources_path,
            version = version,
            [
                DashBase.Resource(
    relative_package_path = "async-SSE.js",
    external_url = "https://unpkg.com/dash_event_callback@1.2.0/dash_event_callback/async-SSE.js",
    dynamic = nothing,
    async = :true,
    type = :js
),
DashBase.Resource(
    relative_package_path = "async-SSE.js.map",
    external_url = "https://unpkg.com/dash_event_callback@1.2.0/dash_event_callback/async-SSE.js.map",
    dynamic = true,
    async = nothing,
    type = :js
),
DashBase.Resource(
    relative_package_path = "dash_event_callback.js",
    external_url = nothing,
    dynamic = nothing,
    async = nothing,
    type = :js
),
DashBase.Resource(
    relative_package_path = "dash_event_callback.js.map",
    external_url = nothing,
    dynamic = true,
    async = nothing,
    type = :js
)
            ]
        )

    )
end
end
