<template>
  <div>
    <van-nav-bar title="问诊会话" left-arrow @click-left="$router.back()" />
    <ChatPanel v-if="conversationId" :conversation-id="conversationId" />
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import ChatPanel from '@/components/ChatPanel.vue'

const route = useRoute()
const conversationId = Number(route.query.id)
</script>
