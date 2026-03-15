# Flask Background Tasks Skill

When implementing long-running tasks in Flask:

- Never block Flask request threads
- Use background workers or threading
- Use queues for task processing
- Return status immediately to the client
- Log task progress

Recommended approaches:

- threading
- Celery
- Redis queue
