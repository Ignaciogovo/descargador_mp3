---
name: flask-background-tasks
description: Best practices for implementing long-running background tasks in Flask applications using threading or task queues
---

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
