#!/bin/sh

black .
isort .
xenon --no-assert -a A -m B -b B .
pylint event_horizon tests wsgi
mypy .
