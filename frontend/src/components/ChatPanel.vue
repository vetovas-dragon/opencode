<template>
  <div class="chat-panel">
    <div class="msgs" ref="scrollRef">
      <div v-for="m in messages" :key="m.id" :class="['msg', m.sender_role]">
        <div class="meta">[{{ roleLabel[m.sender_role] }}] {{ m.created_at }}</div>
        <div v-if="m.msg_type === 'text' || !['image', 'voice', 'file'].includes(m.msg_type)" class="bubble">{{ m.content }}</div>
        <img v-else-if="m.msg_type === 'image'" :src="m.content" class="img" />
        <div v-else-if="m.msg_type === 'voice'" class="bubble voice">
          <audio :src="m.content" controls style="height: 30px"></audio>
        </div>
        <a v-else-if="m.msg_type === 'file'" :href="m.content" target="_blank" class="file-link">{{ fileLabel(m.content) }}</a>
        <div v-if="m.translated_text" class="trans">双语译文：{{ m.translated_text }}</div>
        <audio v-if="m.target_audio_url" :src="m.target_audio_url" controls style="height: 28px; margin-top: 4px"></audio>
      </div>
      <el-empty v-if="!messages.length" description="暂无消息" :image-size="80" />
    </div>

    <div class="input">
      <input ref="imageInput" type="file" accept="image/*" hidden @change="upload('image', $event)" />
      <input ref="fileInput" type="file" accept=".pdf,.doc,.docx,.xlsx,.jpg,.jpeg,.png" hidden @change="upload('file', $event)" />
      <el-button title="发送图片" icon="Picture" circle plain @click="imageInput?.click()" />
      <el-button title="发送文件" icon="Document" circle plain @click="fileInput?.click()" />
      <VoiceRecorder @finish="sendVoice" />
      <el-input v-model="draft" placeholder="输入消息，回车发送" @keyup.enter="sendText" />
      <el-button type="primary" @click="sendText">发送</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import VoiceRecorder from '@/components/VoiceRecorder.vue'
import http from '@/api/http'
import { useUserStore } from '@/stores/user'

const props = defineProps<{ conversationId: number }>()
const emit = defineEmits<{ ended: [] }>()

const userStore = useUserStore()
const messages = ref<any[]>([])
const draft = ref('')
const scrollRef = ref<HTMLDivElement>()
const imageInput = ref<HTMLInputElement>()
const fileInput = ref<HTMLInputElement>()
let ws: WebSocket | null = null

const roleLabel: Record<string, string> = { patient: '患者', student: '医学生', doctor: '医生', system: '系统' }

function fileLabel(url: string): string {
  try {
    const name = decodeURIComponent(url.split('/').pop() || '文件')
    return `📎 ${name}`
  } catch {
    return '📎 文件'
  }
}

async function load() {
  messages.value = await http.get(`/conversations/${props.conversationId}/messages`)
  await http.post(`/conversations/${props.conversationId}/read`)
  scrollBottom()
  connect()
}

function connect() {
  ws?.close()
  ws = new WebSocket(`ws://${location.host}/ws/chat?token=${userStore.token}`)
  ws.onmessage = (e) => {
    const frame = JSON.parse(e.data)
    if (frame.type === 'message' && frame.message.conversation_id === props.conversationId) {
      messages.value.push(frame.message)
      scrollBottom()
    }
  }
}

function scrollBottom() {
  nextTick(() => {
    const el = scrollRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function sendFrame(msgType: string, content: string) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    ElMessage.warning('连接尚未建立，请稍候')
    return
  }
  ws.send(JSON.stringify({ type: 'chat', conversation_id: props.conversationId, msg_type: msgType, content }))
}

function sendText() {
  const content = draft.value.trim()
  if (!content) return
  sendFrame('text', content)
  draft.value = ''
}

async function upload(kind: 'image' | 'file', event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  const form = new FormData()
  form.append('file', file)
  const res: any = await http.post('/files/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  sendFrame(kind, res.url)
}

async function sendVoice(blob: Blob) {
  const form = new FormData()
  form.append('file', blob, `voice-${Date.now()}.webm`)
  try {
    const res: any = await http.post('/files/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    sendFrame('voice', res.url)
  } catch {
    ElMessage.error('语音上传失败')
  }
}

watch(
  () => props.conversationId,
  () => {
    if (props.conversationId) load()
  },
  { immediate: true },
)

onUnmounted(() => ws?.close())
</script>

<style scoped>
.chat-panel { display: flex; flex-direction: column; height: 100%; }
.msgs {
  flex: 1;
  min-height: 300px;
  max-height: 460px;
  overflow-y: auto;
  background: #f7f9fc;
  border: 1px solid #eef1f6;
  border-radius: 12px;
  padding: 14px;
}
.msg { margin-bottom: 12px; }
.meta { color: #a0a9b8; font-size: 11px; margin-bottom: 4px; }
.bubble {
  background: #fff;
  border-radius: 12px 12px 12px 4px;
  padding: 9px 12px;
  display: inline-block;
  max-width: 70%;
  box-shadow: 0 1px 3px rgba(31, 45, 80, 0.08);
  line-height: 1.6;
  word-break: break-word;
}
.msg.patient .bubble {
  background: var(--el-color-primary-light-9);
  border-radius: 12px 12px 4px 12px;
}
.msg.doctor .bubble { background: #ecf9ef; border-radius: 12px 12px 12px 4px; }
.msg.system .bubble { background: #fdf6ec; color: #b08a3c; }
.img { max-width: 220px; border-radius: 10px; display: block; box-shadow: 0 1px 4px rgba(31, 45, 80, 0.12); }
.voice .bubble { background: #fff; }
.voice audio { display: block; }
.trans { color: #52b788; font-size: 12px; margin-top: 4px; background: rgba(82, 183, 136, 0.08); display: inline-block; padding: 2px 8px; border-radius: 6px; }
.file-link { color: #1677ff; text-decoration: underline; }
.input {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 12px;
  background: #fff;
  border: 1px solid #eef1f6;
  border-radius: 12px;
  padding: 10px;
  box-shadow: 0 1px 4px rgba(31, 45, 80, 0.04);
}
.input :deep(.el-input__wrapper) { box-shadow: none; background: #f7f9fc; border-radius: 8px; }
</style>
