from app2.celery_worker import celery_app


@celery_app.task(name="app2.task.email_tasks.send_reset_email")
def send_reset_email(email, token):
    print(email)
    print(token)
    return "email sent"