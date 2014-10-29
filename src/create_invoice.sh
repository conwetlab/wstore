#!/bin/bash

# Check if there are a X server running
if [[ -z "$DISPLAY" ]]; then
    Xvfb ":98" &
    export DISPLAY=":98"
fi

/usr/local/bin/wkhtmltopdf "$1" "$2"

if [ $? -ne 0 ]; then
    /usr/bin/wkhtmltopdf "$1" "$2"
fi

