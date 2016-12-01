#!/bin/bash
cd ..
export PYTHONPATH="$PYTHONPATH:`pwd`/."
trial floranet.test.unit
cd floranet

