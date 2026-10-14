<template>
    <div class="stocks-page">
        <el-card>
            <div class="table-header-bar">
                <h3 class="page-title">股票列表</h3>
            </div>

            <!-- 搜索 / 筛选 -->
            <div class="filter-bar">
                <el-input
                    v-model="q"
                    placeholder="代码或名称"
                    clearable
                    class="filter-q"
                    @keyup.enter="handleSearch"
                    @clear="handleSearch"
                />
                <el-select v-model="board" placeholder="板块" style="width: 140px">
                    <el-option label="全部板块" value="" />
                    <el-option
                        v-for="b in BOARD_OPTIONS"
                        :key="b"
                        :label="b"
                        :value="b"
                    />
                </el-select>
                <el-select
                    v-model="industry"
                    filterable
                    placeholder="行业"
                    style="width: 240px"
                >
                    <el-option label="全部行业" value="" />
                    <el-option
                        v-for="item in industries"
                        :key="item"
                        :label="item"
                        :value="item"
                    />
                </el-select>
                <el-select v-model="status" placeholder="状态" style="width: 120px">
                    <el-option label="全部状态" value="" />
                    <el-option label="上市" :value="1" />
                    <el-option label="退市" :value="0" />
                </el-select>
                <el-button type="primary" @click="handleSearch">搜索</el-button>
                <el-button @click="handleReset">重置</el-button>
            </div>

            <el-table
                v-loading="loading"
                :data="stockList"
                border
                style="margin-top: 16px"
            >
                <el-table-column prop="code" label="代码" width="120" />
                <el-table-column prop="name" label="名称" min-width="140" />
                <el-table-column
                    prop="exchange"
                    label="交易所"
                    width="90"
                />
                <el-table-column prop="board" label="板块" width="100" />
                <el-table-column label="行业" min-width="200">
                    <template #default="scope">
                        {{ scope.row.industry ?? "—" }}
                    </template>
                </el-table-column>
                <el-table-column label="上市日期" width="120">
                    <template #default="scope">
                        {{ scope.row.ipo_date ?? "—" }}
                    </template>
                </el-table-column>
                <el-table-column label="状态" width="90">
                    <template #default="scope">
                        <el-tag
                            :type="scope.row.status === 1 ? 'success' : 'info'"
                        >
                            {{ scope.row.status === 1 ? "上市" : "退市" }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="110">
                    <template #default="scope">
                        <el-button
                            size="small"
                            type="primary"
                            @click="goDetail(scope.row)"
                            >查看详情</el-button
                        >
                    </template>
                </el-table-column>
            </el-table>

            <div class="pagination-wrap">
                <el-pagination
                    background
                    :current-page="pageNum"
                    :page-size="pageSize"
                    :page-sizes="[10, 20, 50]"
                    :total="total"
                    layout="sizes, prev, pager, next"
                    @update:current-page="handlePageChange"
                    @update:page-size="handleSizeChange"
                />
            </div>
        </el-card>
    </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import request from "@/api/request";
import type { StockItem, StockListResp } from "@/types/stock";

const BOARD_OPTIONS = ["主板", "创业板", "科创板", "北交所"];

const router = useRouter();

const stockList = ref<StockItem[]>([]);
const loading = ref(false);

// 分页
const pageNum = ref(1);
const pageSize = ref(20);
const total = ref(0);

// 筛选条件
const q = ref("");
const board = ref("");
const industry = ref("");
const status = ref<number | "">("");
const industries = ref<string[]>([]);

const fetchIndustries = async () => {
    industries.value = await request.get<string[]>("/stocks/industries");
};

const fetchStocks = async () => {
    loading.value = true;
    try {
        const res = await request.get<StockListResp>("/stocks/", {
            params: {
                page: pageNum.value,
                size: pageSize.value,
                q: q.value || undefined,
                board: board.value || undefined,
                industry: industry.value || undefined,
                status: status.value === "" ? undefined : status.value,
            },
        });
        stockList.value = res.data;
        total.value = res.count;
    } finally {
        loading.value = false;
    }
};

const handleSearch = () => {
    pageNum.value = 1;
    fetchStocks();
};

const handleReset = () => {
    q.value = "";
    board.value = "";
    industry.value = "";
    status.value = "";
    pageNum.value = 1;
    fetchStocks();
};

const handlePageChange = (page: number) => {
    pageNum.value = page;
    fetchStocks();
};

const handleSizeChange = (newSize: number) => {
    pageSize.value = newSize;
    pageNum.value = 1;
    fetchStocks();
};

// 命名路由跳转，交给 vue-router 处理 sh.600519 里的点号。
const goDetail = (row: StockItem) => {
    router.push({ name: "stock-detail", params: { code: row.code } });
};

onMounted(() => {
    fetchIndustries();
    fetchStocks();
});
</script>

<style scoped>
.stocks-page {
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
.filter-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 16px;
    flex-wrap: wrap;
}
.filter-q {
    width: 220px;
}
.pagination-wrap {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
}
</style>
