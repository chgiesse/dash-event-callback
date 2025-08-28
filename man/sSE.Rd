% Auto-generated: do not edit by hand
\name{sSE}

\alias{sSE}

\title{SSE component}

\description{
The SSE component makes it possible to collect data from e.g. a ResponseStream. It's a wrapper around the SSE.js library. https://github.com/mpetazzoni/sse.js
}

\usage{
sSE(id=NULL, concat=NULL, done=NULL, options=NULL,
update_component=NULL, url=NULL, value=NULL)
}

\arguments{
\item{id}{Character. Unique ID to identify this component in Dash callbacks.}

\item{concat}{Logical. A boolean indicating if the stream values should be concatenated.}

\item{done}{Logical. A boolean indicating if the (current) stream has ended.}

\item{options}{Lists containing elements 'headers', 'payload', 'method', 'withcredentials', 'start', 'debug'.
those elements have the following types:
  - headers (list with named elements and values of type character; optional): - headers
  - payload (character; optional): - payload as a blob, arraybuffer, dataview, formdata, urlsearchparams, or string
  - method (character; optional): - http method
  - withcredentials (logical; optional): - flag, if credentials needed
  - start (logical; optional): - flag, if streaming should start automatically
  - debug (logical; optional): - debugging flag. Options passed to the SSE constructor.}

\item{update_component}{Logical. A boolean indicating if the strea, should update components.}

\item{url}{Character. URL of the endpoint.}

\item{value}{Character. The data value. Either the latest, or the concatenated depending on the `concat` property.}
}

\value{named list of JSON elements corresponding to React.js properties and their values}

