<script setup lang="ts">
import { ref } from 'vue'
import request from '@/api/request'
import { useRouter } from 'vue-router'
const router = useRouter()
const form = ref({ email: '', password: '' })

const handleLogin = async () => {
  const res = await request.post('/login/access-token', new URLSearchParams({
    username: form.value.email,
    password: form.value.password
  }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
  // 只保存 access_token
  localStorage.setItem('token', res.access_token)
  router.push('/')
}
</script>
