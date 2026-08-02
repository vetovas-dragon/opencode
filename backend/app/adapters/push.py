"""消息推送适配层（Mock/真实）。"""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class PushAdapter:
    def __init__(self) -> None:
        self.provider = settings.push_provider

    async def push(self, user_id: int, title: str, body: str, data: dict | None = None) -> bool:
        if self.provider == "mock":
            logger.info("[MOCK PUSH] user=%s title=%s body=%s", user_id, title, body)
            return True
        # TODO: 接入极光/个推等推送服务
        return True


push_adapter = PushAdapter()
