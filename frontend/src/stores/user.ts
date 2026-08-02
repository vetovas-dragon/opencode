import { defineStore } from 'pinia'
import http from '@/api/http'

interface UserState {
  token: string
  role: string
  name: string
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    token: localStorage.getItem('otc_token') || '',
    role: localStorage.getItem('otc_role') || '',
    name: localStorage.getItem('otc_name') || '',
  }),
  getters: {
    isDoctor: (s) => s.role === 'doctor',
    isStudent: (s) => s.role === 'student',
    isPatient: (s) => s.role === 'patient',
  },
  actions: {
    setSession(token: string, role: string, name: string) {
      this.token = token
      this.role = role
      this.name = name
      localStorage.setItem('otc_token', token)
      localStorage.setItem('otc_role', role)
      localStorage.setItem('otc_name', name)
    },
    async login(contact: string, password: string) {
      const data: any = await http.post('/auth/login', { contact, password })
      this.setSession(data.access_token, data.role, data.name)
      return data.role
    },
    async register(payload: any) {
      return http.post('/auth/register', payload)
    },
    async sendCode(contact: string) {
      const isPhone = /^1\d{10}$/.test(contact)
      return http.post('/auth/send-code', isPhone ? { phone: contact } : { email: contact })
    },
    logout() {
      this.token = ''
      this.role = ''
      this.name = ''
      localStorage.clear()
    },
  },
})
