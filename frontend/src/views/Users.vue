<template>
  <el-card>
    <el-table :data="userList" border>
      <el-table-column prop="id" label="ID"/>
      <el-table-column prop="email" label="邮箱"/>
      <el-table-column prop="is_active" label="是否激活">
        <template #default="scope">
          <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
            {{ scope.row.is_active ? '激活' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_superuser" label="超级管理员">
        <template #default="scope">
          <el-tag v-if="scope.row.is_superuser" type="warning">是</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/api/request'

interface UserItem {
  id: number
  email: string
  is_active: boolean
  is_superuser: boolean
}
const userList = ref<UserItem[]>([])

const fetchUsers = async () => {
  const res = await request.get('/users')
  userList.value = res.data
}

onMounted(() => {
  fetchUsers()
})
</script>