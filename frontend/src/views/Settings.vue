<template>
    <div class="settings-page">
        <el-card>
            <template #header>
                <div>
                    <h2>User Settings</h2>
                    <p class="sub-title">
                        Manage your account settings and preferences
                    </p>
                </div>
            </template>

            <el-tabs v-model="activeTab">
                <!-- 个人资料 Tab -->
                <el-tab-pane label="My profile" name="profile">
                    <div class="profile-form">
                        <el-form :model="profileForm" label-width="100px">
                            <el-form-item label="Full name">
                                <el-input
                                    v-model="profileForm.full_name"
                                    :disabled="!isEdit"
                                ></el-input>
                            </el-form-item>
                            <el-form-item label="Email">
                                <el-input
                                    v-model="profileForm.email"
                                    disabled
                                ></el-input>
                            </el-form-item>
                            <el-form-item>
                                <template v-if="!isEdit">
                                    <el-button
                                        type="primary"
                                        @click="isEdit = true"
                                        >Edit</el-button
                                    >
                                </template>
                                <template v-else>
                                    <el-button
                                        type="primary"
                                        :loading="saving"
                                        @click="saveProfile"
                                        >Save</el-button
                                    >
                                    <el-button @click="cancelEdit"
                                        >Cancel</el-button
                                    >
                                </template>
                            </el-form-item>
                        </el-form>
                    </div>
                </el-tab-pane>

                <!-- 密码设置 Tab -->
                <el-tab-pane label="Password" name="password">
                    <el-form :model="passwordForm" label-width="160px">
                        <el-form-item label="Current password">
                            <el-input
                                v-model="passwordForm.current_password"
                                show-password
                                style="width: 360px"
                            ></el-input>
                        </el-form-item>
                        <el-form-item
                            label="New password"
                            :error="pwdLengthError"
                        >
                            <el-input
                                v-model="passwordForm.new_password"
                                show-password
                                style="width: 360px"
                                @input="validatePasswordForm"
                            ></el-input>
                        </el-form-item>
                        <el-form-item
                            label="Confirm password"
                            class="inline-pwd-item"
                            :error="pwdConfirmError"
                        >
                            <el-input
                                v-model="passwordForm.new_password_confirm"
                                show-password
                                style="width: 360px"
                                @input="validatePasswordForm"
                            ></el-input>
                        </el-form-item>
                        <el-form-item>
                            <el-button
                                type="primary"
                                :loading="pwdSaving"
                                @click="updatePassword"
                                >Update Password</el-button
                            >
                        </el-form-item>
                    </el-form>
                </el-tab-pane>
            </el-tabs>
        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import request from "@/api/request";
import { ElMessage } from "element-plus";

const activeTab = ref("profile");
const isEdit = ref(false);
const saving = ref(false);
const pwdSaving = ref(false);

// 个人资料表单
const profileForm = ref({
    full_name: "",
    email: "",
});
// 密码表单
const passwordForm = ref({
    current_password: "",
    new_password: "",
    new_password_confirm: "",
});

// 密码校验错误信息
const pwdLengthError = ref("");
const pwdConfirmError = ref("");

/**
 * 密码整体校验：长度 + 一致性
 */
const validatePasswordForm = () => {
    const form = passwordForm.value;
    pwdLengthError.value = "";
    pwdConfirmError.value = "";

    // 新密码不为空时校验长度
    if (form.new_password) {
        if (form.new_password.length < 8) {
            pwdLengthError.value = "新密码长度最少8位";
        }
    }

    // 两次密码一致性校验，两个字段都有值才校验
    if (form.new_password && form.new_password_confirm) {
        if (form.new_password !== form.new_password_confirm) {
            pwdConfirmError.value = "两次输入的新密码不一致";
        }
    }

    // 返回是否全部校验通过
    return !pwdLengthError.value && !pwdConfirmError.value;
};

// 获取用户信息
const loadUserInfo = async () => {
    try {
        const res = await request.get("/users/me");
        profileForm.value.full_name = res.full_name || "";
        profileForm.value.email = res.email;
    } catch (err) {
        ElMessage.error("加载用户信息失败");
    }
};

// 进入编辑
const cancelEdit = () => {
    isEdit.value = false;
    loadUserInfo();
};

// 保存个人信息 PATCH /users/me
const saveProfile = async () => {
    saving.value = true;
    try {
        await request.patch("/users/me", {
            full_name: profileForm.value.full_name,
        });
        ElMessage.success("保存成功");
        isEdit.value = false;
        await loadUserInfo();
    } catch (err) {
        ElMessage.error("保存失败，请检查输入");
    } finally {
        saving.value = false;
    }
};

// 更新密码 PATCH /users/me/password
const updatePassword = async () => {
    // 提交前再次校验
    if (!validatePasswordForm()) {
        return;
    }
    const pwd = passwordForm.value;
    if (!pwd.current_password || !pwd.new_password) {
        ElMessage.warning("请填写完整密码");
        return;
    }
    pwdSaving.value = true;
    try {
        await request.patch("/users/me/password", {
            current_password: pwd.current_password,
            new_password: pwd.new_password,
        });
        ElMessage.success("密码修改成功，请重新登录");
        // 清空表单
        passwordForm.value.current_password = "";
        passwordForm.value.new_password = "";
        passwordForm.value.new_password_confirm = "";
    } catch (err) {
        ElMessage.error("密码更新失败，原密码可能错误");
    } finally {
        pwdSaving.value = false;
    }
};

onMounted(() => {
    loadUserInfo();
});
</script>

<style scoped>
.settings-page {
    padding: 20px;
}
.sub-title {
    color: var(--el-text-color-secondary);
    margin: 4px 0 16px;
}
/* 确认密码行：label和输入框同行，不换行 */
.inline-pwd-item :deep(.el-form-item__content) {
    flex-wrap: nowrap !important;
}
.inline-pwd-item :deep(.el-form-item__label) {
    white-space: nowrap;
}
</style>
