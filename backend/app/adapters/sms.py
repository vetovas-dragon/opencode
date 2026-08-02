"""短信验证码适配层（Mock/真实）。"""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class SmsAdapter:
    def __init__(self) -> None:
        self.provider = settings.sms_provider

    async def send_code(self, phone: str, code: str) -> bool:
        if self.provider == "mock":
            logger.info("[MOCK SMS] to=%s code=%s", phone, code)
            return True
        # TODO: 接入阿里云/腾讯云短信服务
        return True


sms_adapter = SmsAdapter()
