<template>
  <div class="voice-recorder">
    <el-button
      v-if="!recording"
      type="primary"
      plain
      circle
      icon="Microphone"
      title="点击开始录音（最长60秒）"
      @click="start"
    />
    <el-button v-else type="danger" circle @click="stop">
      <span class="rec-dot" />
    </el-button>
    <span v-if="recording" class="timer">{{ mmss }}</span>
  </div>
</template>

<script setup lang="ts">
import { onUnmounted, ref } from 'vue'

const emit = defineEmits<{ finish: [blob: Blob] }>()

const recording = ref(false)
const mmss = ref('00:00')
const MAX_SECONDS = 60

let mediaRecorder: MediaRecorder | null = null
let chunks: Blob[] = []
let timer: ReturnType<typeof setInterval> | null = null
let seconds = 0
let stream: MediaStream | null = null

function tick() {
  seconds += 1
  mmss.value = `00:${String(seconds).padStart(2, '0')}`
  if (seconds >= MAX_SECONDS) stop()
}

async function start() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  } catch {
    return
  }
  chunks = []
  seconds = 0
  mmss.value = '00:00'
  const mime = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : ''
  mediaRecorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream)
  mediaRecorder.ondataavailable = (e) => chunks.push(e.data)
  mediaRecorder.onstop = () => {
    const blob = new Blob(chunks, { type: mediaRecorder?.mimeType || 'audio/webm' })
    emit('finish', blob)
    stream?.getTracks().forEach((t) => t.stop())
  }
  mediaRecorder.start()
  recording.value = true
  timer = setInterval(tick, 1000)
}

function stop() {
  if (timer) clearInterval(timer)
  timer = null
  recording.value = false
  mediaRecorder?.stop()
}

onUnmounted(() => {
  if (timer) clearInterval(timer)
  stream?.getTracks().forEach((t) => t.stop())
})
</script>

<style scoped>
.voice-recorder { display: flex; align-items: center; gap: 6px; }
.rec-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #fff; }
.timer { color: #f56c6c; font-size: 12px; }
</style>
