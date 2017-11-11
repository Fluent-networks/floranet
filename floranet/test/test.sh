#!/bin/bash
# Get script path
SCRIPTPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Derive the project path
PROJECTPATH="${SCRIPTPATH}/../.."

# Add the project path to PYTHONPATH
export PYTHONPATH="${PROJECTPATH}:${PYTHONPATH}"

# Run the unit tests. Web tests run in a separate reactor.
unittests=(floranet web)
for u in "${unittests[@]}"
do
    (cd /tmp; trial -x floranet.test.unit.${u})
done

# Run the integration tests
# (cd /tmp; trial -x floranet.test.integration)
