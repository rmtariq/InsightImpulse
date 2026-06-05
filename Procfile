web: uvicorn web_backend.app:app --host 0.0.0.0 --port $PORT --workers 2
worker: python -m celery worker -A web_backend.app:celery_app --loglevel=info
beat: python -m celery beat -A web_backend.app:celery_app --loglevel=info
