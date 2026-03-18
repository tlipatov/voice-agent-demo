#!/bin/sh
set -e

python grpc_server.py &
exec uvicorn app:app --host 0.0.0.0 --port 8010
