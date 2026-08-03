<template>
  <div class="voice-page">
    <van-nav-bar title="语音互转（汉 ⇄ 彝）" left-arrow @click-left="$router.back()" />
    <van-cell-group inset style="margin-top: 12px">
      <van-cell title="转换方向">
        <template #value>
          <van-radio-group v-model="direction" direction="horizontal" @change="resetAll">
            <van-radio name="zh2yi">汉→彝</van-radio>
            <van-radio name="yi2zh">彝→汉</van-radio>
          </van-radio-group>
        </template>
      </van-cell>
    </van-cell-group>

    <div class="stage">
      <div v-if="!recording && !processing" class="tip">点击下方按钮开始录音（最长 60 秒）</div>
      <div v-if="recording" class="tip recording">正在录音… {{ mmss }}</div>
      <div v-if="processing" class="tip">正在互转…</div>
      <div class="mic-wrap">
        <button class="mic-btn" :class="{ on: recording }" @mousedown="start" @mouseup="stop" @touchstart.prevent="start" @touchend.prevent="stop" @touchcancel.prevent="stop">
          <van-icon name="audio" size="40" />
        </button>
      </div>
      <div class="hint">{{ recording ? '松开发送' : '按住说话' }}</div>
    </div>

    <van-cell-group inset title="互转结果">
      <van-cell title="转写文本" :label="sourceText || '（待转写）'" />
      <van-cell title="译文" :label="targetText || '（待翻译）'" />
      <van-cell v-if="termHit > 0" title="医疗术语识别" :label="`命中 ${termHit} 条术语，已按标准医学术语翻译`" />
      <van-cell v-if="targetAudioUrl && targetAudioUrl.startsWith('http')" title="合成语音">
        <template #label><audio :src="targetAudioUrl" controls style="height: 32px; margin-top: 4px"></audio></template>
      </van-cell>
    </van-cell-group>
  </div>
</template>

<script setup lang="ts">
import { onUnmounted, ref } from 'vue'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const direction = ref<'zh2yi' | 'yi2zh'>('zh2yi')
const recording = ref(false)
const processing = ref(false)
const mmss = ref('00:00')
const sourceText = ref('')
const targetText = ref('')
const targetAudioUrl = ref('')
const termHit = ref(0)

let ws: WebSocket | null = null
let mediaRecorder: MediaRecorder | null = null
let stream: MediaStream | null = null
let chunks: Blob[] = []
let timer: ReturnType<typeof setInterval> | null = null
let seconds = 0
const MAX_SECONDS = 60

function connect() {
  if (ws && ws.readyState === WebSocket.OPEN) return
  ws = new WebSocket(`ws://${location.host}/ws/voice?token=${userStore.token}`)
  ws.onmessage = (e) => {
    const frame = JSON.parse(e.data)
    if (frame.type === 'partial') {
      processing.value = true
    } else if (frame.type === 'final') {
      processing.value = false
      sourceText.value = frame.source_text || ''
      targetText.value = frame.target_text || ''
      targetAudioUrl.value = frame.target_audio_url || ''
      termHit.value = frame.term_hit || 0
    }
  }
}

function resetAll() {
  sourceText.value = targetText.value = targetAudioUrl.value = ''
  termHit.value = 0
}

async function start() {
  if (recording.value) return
  connect()
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  } catch {
    showToast('无法访问麦克风')
    return
  }
  chunks = []
  seconds = 0
  mmss.value = '00:00'
  const mime = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : ''
  mediaRecorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream)
  mediaRecorder.ondataavailable = (e) => chunks.push(e.data)
  mediaRecorder.onstop = sendAudio
  mediaRecorder.start()
  recording.value = true
  timer = setInterval(() => {
    seconds += 1
    mmss.value = `00:${String(seconds).padStart(2, '0')}`
    if (seconds >= MAX_SECONDS) stop()
  }, 1000)
}

function stop() {
  if (timer) clearInterval(timer)
  timer = null
  recording.value = false
  mediaRecorder?.stop()
}

async function sendAudio() {
  stream?.getTracks().forEach((t) => t.stop())
  processing.value = true
  const blob = new Blob(chunks, { type: mediaRecorder?.mimeType || 'audio/webm' })
  const arrayBuffer = await blob.arrayBuffer()
  const base64 = arrayBufferToBase64(arrayBuffer)
  const chunkSize = 16 * 1024
  for (let i = 0; i < base64.length; i += chunkSize) {
    const final = i + chunkSize >= base64.length
    ws?.send(
      JSON.stringify({
        type: 'audio',
        chunk: base64.slice(i, i + chunkSize),
        source_lang: direction.value === 'zh2yi' ? 'zh' : 'yi',
        target_lang: direction.value === 'zh2yi' ? 'yi' : 'zh',
        final,
      }),
    )
    await new Promise((r) => setTimeout(r, 50))
  }
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.length; i += 1) binary += String.fromCharCode(bytes[i])
  return btoa(binary)
}

onUnmounted(() => {
  ws?.close()
  stream?.getTracks().forEach((t) => t.stop())
})
</script>

<style scoped>
.voice-page { min-height: 100vh; }
.stage { padding: 32px 0; text-align: center; }
.tip { color: #969799; font-size: 13px; margin-bottom: 16px; }
.tip.recording { color: #ee0a24; }
.mic-wrap { display: inline-flex; }
.mic-btn {
  width: 88px; height: 88px; border-radius: 50%; border: none; outline: none;
  background: #1989fa; color: #fff; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(25, 137, 250, 0.35);
}
.mic-btn.on { background: #ee0a24; box-shadow: 0 0 0 8px rgba(238, 10, 36, 0.15); }
.hint { margin-top: 12px; color: #646566; font-size: 12px; }
</style>
