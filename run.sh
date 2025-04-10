#!/bin/bash
uvicorn server:app --host 127.0.0.1 --port 5500 --workers 1 --reload