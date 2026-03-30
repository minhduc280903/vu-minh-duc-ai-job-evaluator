# backend/app/api/websocket.py
import logging
from typing import List
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections and broadcast messages."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.active_connections.remove(conn)

    async def send_scraper_progress(self, platform: str, page: int, jobs_found: int, status: str):
        await self.broadcast({
            "type": "scraper_progress",
            "platform": platform,
            "page": page,
            "jobs_found": jobs_found,
            "status": status,
        })

    async def send_scraper_log(self, platform: str, level: str, message: str):
        import time
        await self.broadcast({
            "type": "scraper_log",
            "platform": platform,
            "level": level,
            "message": message,
            "timestamp": time.time(),
        })

    async def send_scraper_complete(self, platform: str, total_new: int, total_updated: int):
        await self.broadcast({
            "type": "scraper_complete",
            "platform": platform,
            "total_new": total_new,
            "total_updated": total_updated,
        })

    async def send_eval_progress(self, evaluated: int, total: int, current_job: str):
        await self.broadcast({
            "type": "eval_progress",
            "evaluated": evaluated,
            "total": total,
            "current_job": current_job,
        })

    async def send_new_match(self, job_title: str, score: int, tier: str):
        await self.broadcast({
            "type": "new_match",
            "job_title": job_title,
            "score": score,
            "tier": tier,
        })

    async def send_notification_sent(self, channel: str, job_count: int):
        await self.broadcast({
            "type": "notification_sent",
            "channel": channel,
            "job_count": job_count,
        })


# Singleton instance
ws_manager = ConnectionManager()
