from celery import Celery

celery_app = Celery(
    'app2', 
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
    )
celery_app.conf.imports = (
    "app2.task.email_tasks",
    "app2.task.files_task",
    "app2.task.meet_task",
    "app2.task.transcript_task"
)

celery_app.conf.update(
    worker_pool="solo",
    worker_concurrency=1,
)