from src.celery_app import celery_app

# TODO: cleanup_old_files()
@celery_app.task(bind=True, max_retries=3)
async def cleanup_old_files(self):
    pass


# TODO: retry_failed_webhooks()
@celery_app.task(bind=True, max_retries=3)
async def retry_failed_webhooks(self):
    pass