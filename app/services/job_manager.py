import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import redis
from app.core.config import settings

class JobManager:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.job_timeout = timedelta(minutes=30)

    async def create_job(self, job_data: Dict[str, Any]) -> str:
        """Create a new processing job"""
        job_id = self._generate_job_id()
        job_data["status"] = "pending"
        job_data["created_at"] = datetime.utcnow().isoformat()
        
        # Store job data with expiration
        self.redis_client.setex(
            f"job:{job_id}",
            self.job_timeout.total_seconds(),
            job_data
        )
        
        return job_id

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status"""
        job_data = self.redis_client.get(f"job:{job_id}")
        if job_data:
            return job_data
        return None

    async def update_job_status(self, job_id: str, status: str, result: Optional[Dict[str, Any]] = None):
        """Update job status"""
        job_data = self.redis_client.get(f"job:{job_id}")
        if job_data:
            job_data["status"] = status
            if result:
                job_data["result"] = result
            self.redis_client.setex(
                f"job:{job_id}",
                self.job_timeout.total_seconds(),
                job_data
            )

    def _generate_job_id(self) -> str:
        """Generate unique job ID"""
        return f"job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

# Initialize job manager
job_manager = JobManager()
