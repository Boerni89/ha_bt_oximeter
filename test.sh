#!/bin/bash
# Test runner script inspired by ics_calendar
# Run tests with coverage reporting

if test -n "$1" ; then
    TEST=$1
else
    TEST=tests/
fi

TOP=$(pwd)
rm -rf htmlcov/* coverage.xml .coverage

echo "Running tests in ${TEST}..."
PYTHONDONTWRITEBYTECODE=1 pytest ${TEST} \
    --cov=custom_components.bt_oximeter \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-config=.coveragerc \
    -v

echo ""
echo "Coverage report generated:"
echo "  HTML: ${TOP}/htmlcov/index.html"
