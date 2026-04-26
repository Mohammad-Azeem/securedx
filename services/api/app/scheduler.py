# services/api/app/scheduler.py

"""
The Bedtime Alarm Clock

Runs tasks at specific times:
- 11:00 PM: Nightly AI training
- 12:00 AM: Generate daily reports
- 1:00 AM: Backup database
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler():
    """
    Start the task scheduler.
    
    For a 15-year-old:
    Turn on all the alarms!
    """
    from services.ml_training.nightly_trainer import run_nightly_training_job
    
    # Schedule nightly training at 11 PM
    scheduler.add_job(
        run_nightly_training_job,
        trigger=CronTrigger(hour=23, minute=0),  # 11:00 PM
        id='nightly_training',
        name='AI Nightly Training Session',
        replace_existing=True,
    )
    
    logger.info("✅ Scheduler started - AI will train at 11 PM every night")
    scheduler.start()


def stop_scheduler():
    """Stop all scheduled tasks"""
    scheduler.shutdown()
    logger.info("Scheduler stopped")