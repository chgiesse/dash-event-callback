# AUTO GENERATED FILE - DO NOT EDIT

#' @export
sSE <- function(id=NULL, concat=NULL, done=NULL, options=NULL, update_component=NULL, url=NULL, value=NULL) {
    
    props <- list(id=id, concat=concat, done=done, options=options, update_component=update_component, url=url, value=value)
    if (length(props) > 0) {
        props <- props[!vapply(props, is.null, logical(1))]
    }
    component <- list(
        props = props,
        type = 'SSE',
        namespace = 'dash_event_callback',
        propNames = c('id', 'concat', 'done', 'options', 'update_component', 'url', 'value'),
        package = 'dashEventCallback'
        )

    structure(component, class = c('dash_component', 'list'))
}
