"""
Scheduler service for automated movie pipeline runs
"""
import os
import sys
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

# Add parent directory to path to import movie_pipeline
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from movie_pipeline import MovieETLPipeline

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineScheduler:
    """Scheduler for automated movie data pipeline runs"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.tmdb_api_key = os.getenv('TMDB_API_KEY')
        self.database_url = os.getenv('DATABASE_URL')
        
        if not self.tmdb_api_key:
            raise ValueError("TMDB_API_KEY not found in environment")
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment")
        
        self.pipeline = MovieETLPipeline(self.tmdb_api_key, self.database_url)
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Setup scheduled jobs"""
        
        # Quick update: Every 6 hours (popular + trending)
        self.scheduler.add_job(
            func=self._quick_update,
            trigger=IntervalTrigger(hours=6),
            id='quick_update',
            name='Quick Update (Popular + Trending)',
            replace_existing=True,
            max_instances=1
        )
        logger.info("✓ Scheduled: Quick update every 6 hours")
        
        # Daily update: Every day at 3 AM (all categories, no enrichment)
        self.scheduler.add_job(
            func=self._daily_update,
            trigger=CronTrigger(hour=3, minute=0),
            id='daily_update',
            name='Daily Update (All Categories)',
            replace_existing=True,
            max_instances=1
        )
        logger.info("✓ Scheduled: Daily update at 3:00 AM")
        
        # Weekly enrichment: Every Sunday at 2 AM (with full enrichment)
        self.scheduler.add_job(
            func=self._weekly_enrichment,
            trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
            id='weekly_enrichment',
            name='Weekly Enrichment (Full Data)',
            replace_existing=True,
            max_instances=1
        )
        logger.info("✓ Scheduled: Weekly enrichment on Sundays at 2:00 AM")
    
    def _quick_update(self):
        """Quick update with popular and trending movies"""
        logger.info("🚀 Starting quick update...")
        try:
            self.pipeline.run_quick_update()
            logger.info("✅ Quick update completed successfully")
        except Exception as e:
            logger.error(f"❌ Quick update failed: {e}", exc_info=True)
    
    def _daily_update(self):
        """Daily update with all categories"""
        logger.info("🚀 Starting daily update...")
        try:
            self.pipeline.run(
                categories=['popular', 'top_rated', 'upcoming', 'now_playing'],
                pages_per_category=5,
                include_trending=True,
                enrich_data=False,
                incremental=True
            )
            logger.info("✅ Daily update completed successfully")
        except Exception as e:
            logger.error(f"❌ Daily update failed: {e}", exc_info=True)
    
    def _weekly_enrichment(self):
        """Weekly enrichment with detailed data"""
        logger.info("🚀 Starting weekly enrichment...")
        try:
            self.pipeline.run_full_enrichment()
            logger.info("✅ Weekly enrichment completed successfully")
        except Exception as e:
            logger.error(f"❌ Weekly enrichment failed: {e}", exc_info=True)
    
    def run_manual_update(self, update_type: str = 'quick'):
        """
        Manually trigger a pipeline update
        
        Args:
            update_type: 'quick', 'daily', or 'full'
        """
        logger.info(f"🔧 Manual {update_type} update triggered")
        
        if update_type == 'quick':
            self._quick_update()
        elif update_type == 'daily':
            self._daily_update()
        elif update_type == 'full':
            self._weekly_enrichment()
        else:
            logger.error(f"Unknown update type: {update_type}")
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("🎬 Pipeline scheduler started")
            logger.info(f"Current jobs: {len(self.scheduler.get_jobs())}")
            self._print_schedule()
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Pipeline scheduler stopped")
    
    def _print_schedule(self):
        """Print current schedule"""
        logger.info("\n📅 Scheduled Jobs:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name} (ID: {job.id})")
            logger.info(f"    Next run: {job.next_run_time}")
    
    def get_job_status(self):
        """Get status of all scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs


# Global scheduler instance
_scheduler_instance = None


def get_scheduler() -> PipelineScheduler:
    """Get or create scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = PipelineScheduler()
    return _scheduler_instance


if __name__ == "__main__":
    # Run scheduler as standalone service
    try:
        scheduler = get_scheduler()
        scheduler.start()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎬 Movie Pipeline Scheduler Running")
        logger.info("=" * 60)
        logger.info("Press Ctrl+C to exit")
        logger.info("=" * 60 + "\n")
        
        # Keep the script running
        import time
        while True:
            time.sleep(1)
            
    except (KeyboardInterrupt, SystemExit):
        logger.info("\n🛑 Shutting down scheduler...")
        scheduler.stop()
        logger.info("✅ Scheduler stopped gracefully")

