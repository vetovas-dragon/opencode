"""科大讯飞语音互转适配层（对应 M9）。

未配置 XFYUN 凭证时自动降级为 Mock 实现（直接回显输入），
配置后切换为真实 STT/TTS/翻译调用。医疗术语词典为本地内置表。
"""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

MEDICAL_TERMS: dict[str, str] = {
    # 汉语 -> 彝语（示意条目，正式词库由管理员后台维护）
    "血压": "ꆺꐛꉻꇮ",
    "血糖": "ꋍꉉꌩꋉꇮ",
    "糖尿病": "ꌩꇮꋌꈁꌋꃀ",
    "高血压": "ꆺꐛꉻꂸꄻ",
    "复诊": "ꀊꏂꑮꉉꅉ",
    "服药": "ꑉꎆꄁ",
    "体温": "ꋍꐛꈭꐨ",
}

TERM_DB_PLACEHOLDER = True  # 后续对接管理员后台词库维护接口


class VoiceAdapter:
    """语音互转适配器：STT / 翻译（含医疗术语）/ TTS / 流式转写。"""

    def __init__(self) -> None:
        self.enabled = bool(settings.xfyun_app_id and settings.xfyun_api_key and settings.xfyun_api_secret)
        if not self.enabled:
            logger.warning("未配置科大讯飞凭证，语音互转使用 Mock 实现")

    def _mock_text(self, text: str, target_lang: str) -> str:
        if target_lang == "yi":
            for zh, yi in MEDICAL_TERMS.items():
                if zh in text:
                    return f"{text}（彝语：{yi}）[MOCK]"
            return f"{text} [彝语译文 MOCK]"
        return f"{text} [汉语译文 MOCK]"

    async def translate(self, source_text: str, source_lang: str, target_lang: str) -> dict:
        """语音转文字 + 翻译（简化：入参为已转写文本）。返回目标文本与术语命中数。"""
        if not self.enabled:
            target = self._mock_text(source_text, target_lang)
        else:
            # TODO: 接入讯飞翻译 API（https://www.xfyun.cn/doc/nlp/translation/API.html）
            target = source_text  # 占位：真实实现返回翻译结果
        hit = sum(1 for term in MEDICAL_TERMS if term in source_text)
        return {"target_text": target, "term_hit": hit}

    async def stt(self, audio_url: str, language: str) -> dict:
        """语音转文字。返回文本与置信度。"""
        if not self.enabled:
            return {"text": f"[MOCK STT] 语音转写结果（{language}）", "confidence": 0.5}
        # TODO: 接入讯飞语音听写/流式 API
        return {"text": "", "confidence": 0.0}

    async def tts(self, text: str, language: str) -> str:
        """文字转语音。返回合成语音 URL。"""
        if not self.enabled:
            return f"mock://tts/{language}/{hash(text)}.mp3"
        # TODO: 接入讯飞在线语音合成 API，文件上传 MinIO 后返回 URL
        return f"mock://tts/{language}/{hash(text)}.mp3"

    async def streaming_translate(self, chunks, source_lang: str, target_lang: str):
        """实时流式语音互转（边说边转）。chunks 为音频分片迭代器。"""
        if not self.enabled:
            for chunk in chunks:
                yield {"partial": True, "text": f"[流式] 分片 {len(str(chunk))} 字节", "confidence": 0.5}
        else:
            # TODO: 接入讯飞流式语音听写 WebSocket API
            async for chunk in chunks:
                yield {"partial": True, "text": "", "confidence": 0.0}


voice_adapter = VoiceAdapter()
