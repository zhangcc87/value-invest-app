<template>
    <div class="users-page">
        <el-card>
            <div class="table-header-bar">
                <h3 class="page-title">用户列表</h3>
                <el-button type="primary" @click="openAddDialog"
                    >添加用户</el-button
                >
            </div>

            <el-table :data="userList" border style="margin-top: 16px">
                <el-table-column prop="id" label="ID" />
                <el-table-column prop="full_name" label="姓名" />
                <el-table-column prop="email" label="邮箱" />
                <el-table-column label="角色">
                    <template #default="scope">
                        <el-tag
                            :type="scope.row.is_superuser ? 'primary' : 'info'"
                        >
                            {{ scope.row.is_superuser ? "管理员" : "用户" }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="is_active" label="状态">
                    <template #default="scope">
                        <el-tag
                            :type="scope.row.is_active ? 'success' : 'danger'"
                        >
                            {{ scope.row.is_active ? "活跃" : "不活跃" }}
                        </el-tag>
                    </template>
                </el-table-column>
            </el-table>

            <!-- 分页：外层容器右对齐 -->
            <div class="pagination-wrap">
                <el-pagination
                    background
                    :current-page="pageNum"
                    :page-size="pageSize"
                    :page-sizes="[1, 10, 20, 50]"
                    :total="total"
                    layout="sizes, prev, pager, next"
                    @update:current-page="handlePageChange"
                    @update:page-size="handleSizeChange"
                />
            </div>
        </el-card>

        <!-- 添加用户弹窗，加宽至620px，表单居中 -->
        <el-dialog v-model="addDialogVisible" title="添加用户" width="620px">
            <el-form :model="addForm" label-width="130px" class="add-user-form">
                <el-form-item label="姓名">
                    <el-input
                        v-model="addForm.full_name"
                        placeholder="请输入姓名"
                    ></el-input>
                </el-form-item>
                <el-form-item label="邮箱">
                    <el-input
                        v-model="addForm.email"
                        placeholder="请输入邮箱"
                    ></el-input>
                </el-form-item>
                <el-form-item label="密码" :error="pwdLengthErr">
                    <el-input
                        v-model="addForm.password"
                        show-password
                        placeholder="最少8位"
                        @input="validatePwd"
                    ></el-input>
                </el-form-item>
                <el-form-item label="确认密码" :error="pwdConfirmErr">
                    <el-input
                        v-model="addForm.password_confirm"
                        show-password
                        placeholder="再次输入密码"
                        @input="validatePwd"
                    ></el-input>
                </el-form-item>
                <el-form-item label="角色">
                    <el-select
                        v-model="addForm.is_superuser"
                        style="width: 100%"
                    >
                        <el-option label="管理员" :value="true"></el-option>
                        <el-option label="普通用户" :value="false"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item label="是否激活">
                    <el-switch
                        v-model="addForm.is_active"
                        active-text="激活"
                        inactive-text="禁用"
                    ></el-switch>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="addDialogVisible = false">取消</el-button>
                <el-button
                    type="primary"
                    :loading="submitLoading"
                    @click="submitAddUser"
                    >确定</el-button
                >
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import request from "@/api/request";
import { ElMessage } from "element-plus";

interface UserItem {
    id: string;
    full_name: string;
    email: string;
    is_active: boolean;
    is_superuser: boolean;
}
const userList = ref<UserItem[]>([]);

// 分页
const pageNum = ref(1);
const pageSize = ref(20);
const total = ref(0);

// 添加弹窗
const addDialogVisible = ref(false);
const submitLoading = ref(false);

// 密码校验提示
const pwdLengthErr = ref("");
const pwdConfirmErr = ref("");

// 新增用户表单（增加password_confirm）
const addForm = ref({
    full_name: "",
    email: "",
    password: "",
    password_confirm: "",
    is_superuser: false,
    is_active: true,
});

// 密码实时校验
const validatePwd = () => {
    pwdLengthErr.value = "";
    pwdConfirmErr.value = "";
    const f = addForm.value;

    if (f.password && f.password.length < 8) {
        pwdLengthErr.value = "密码长度最少8位";
    }
    if (f.password && f.password_confirm && f.password !== f.password_confirm) {
        pwdConfirmErr.value = "两次输入密码不一致";
    }
};

// 打开弹窗，重置表单、清空错误
const openAddDialog = () => {
    addForm.value = {
        full_name: "",
        email: "",
        password: "",
        password_confirm: "",
        is_superuser: false,
        is_active: true,
    };
    pwdLengthErr.value = "";
    pwdConfirmErr.value = "";
    addDialogVisible.value = true;
};

// 提交新增用户
const submitAddUser = async () => {
    validatePwd();
    const form = addForm.value;

    if (!form.full_name || !form.email || !form.password) {
        ElMessage.warning("姓名、邮箱、密码为必填项");
        return;
    }
    if (pwdLengthErr.value || pwdConfirmErr.value) {
        ElMessage.warning("请检查密码输入");
        return;
    }

    submitLoading.value = true;
    try {
        await request.post("/users", {
            full_name: form.full_name,
            email: form.email,
            password: form.password,
            is_superuser: form.is_superuser,
            is_active: form.is_active,
        });
        ElMessage.success("新增用户成功");
        addDialogVisible.value = false;
        await fetchUsers();
    } catch (err) {
        ElMessage.error("新增用户失败");
    } finally {
        submitLoading.value = false;
    }
};

// 获取用户列表
const fetchUsers = async () => {
    const res = await request.get("/users", {
        params: {
            page: pageNum.value,
            size: pageSize.value,
        },
    });
    userList.value = res.data;
    total.value = res.count;
};

// 切换页码
const handlePageChange = (page: number) => {
    pageNum.value = page;
    fetchUsers();
};

// 切换每页条数
const handleSizeChange = (newSize: number) => {
    pageSize.value = newSize;
    pageNum.value = 1; // 切换条数强制回到第一页
    fetchUsers();
};

onMounted(() => {
    fetchUsers();
});
</script>

<style scoped>
.users-page {
    padding: 20px;
}
.table-header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.page-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
}
/* 弹窗表单居中，限制输入框最大宽度，消除右侧大片空白 */
.add-user-form {
    max-width: 440px;
    margin: 0 auto;
}
/* 分页容器：靠右 + 上边距 */
.pagination-wrap {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
}
</style>
