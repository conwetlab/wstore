#!/bin/bash

# Check if there are a X server running
if [[ -z "$DISPLAY" ]]; then
    Xvfb ":98" &
    export DISPLAY=":98"
fi

/usr/bin/wkhtmltopdf "$1" "$2"
