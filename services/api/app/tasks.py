from app.celery_app import celery_app

@celery_app.task(name="app.tasks.say_hello")
def say_hello(name: str) -> str:
    return f"hello, {name}!"