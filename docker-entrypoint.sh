#!/usr/bin/env bash

set -e

printf '\n$ ( cd %s && ./waved -listen ":%s" & )\n\n' "/usr/wave" "10101"
(cd "/usr/wave" && ./waved -listen ":10101" &)

sleep 3

printf '\n$ wave run --no-reload --no-autostart %s\n\n' "app"

exec wave run --no-reload --no-autostart "app"