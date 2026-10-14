<template>
    <div class="stock-detail-page">
        <el-card>
            <div class="header-bar">
                <el-button @click="router.back()">返回</el-button>
                <template v-if="stock">
                    <h2 class="stock-name">{{ stock.name }}</h2>
                    <el-tag type="info">{{ stock.code }}</el-tag>
                </template>
            </div>

            <el-empty
                v-if="notFound"
                description="未找到该股票"
                style="margin-top: 20px"
            />

            <template v-else-if="stock">
                <el-descriptions
                    :column="3"
                    border
                    style="margin-top: 16px"
                    title="基本信息"
                >
                    <el-descriptions-item label="代码">
                        {{ stock.code }}
                    </el-descriptions-item>
                    <el-descriptions-item label="名称">
                        {{ stock.name }}
                    </el-descriptions-item>
                    <el-descriptions-item label="交易所">
                        {{ stock.exchange }}
                    </el-descriptions-item>
                    <el-descriptions-item label="板块">
                        {{ stock.board }}
                    </el-descriptions-item>
                    <el-descriptions-item label="行业">
                        {{ stock.industry ?? "—" }}
                    </el-descriptions-item>
                    <el-descriptions-item label="状态">
                        {{ stock.status === 1 ? "上市" : "退市" }}
                    </el-descriptions-item>
                    <el-descriptions-item label="上市日期">
                        {{ stock.ipo_date ?? "—" }}
                    </el-descriptions-item>
                    <el-descriptions-item label="退市日期">
                        {{ stock.out_date ?? "—" }}
                    </el-descriptions-item>
                    <el-descriptions-item label="更新时间">
                        {{ stock.updated_at ?? "—" }}
                    </el-descriptions-item>
                </el-descriptions>
            </template>
        </el-card>

        <template v-if="stock">
            <!-- 行情走势 -->
            <el-card style="margin-top: 16px">
                <div class="card-header-bar">
                    <h3 class="card-title">行情走势</h3>
                    <el-date-picker
                        v-model="dateRange"
                        type="daterange"
                        value-format="YYYY-MM-DD"
                        start-placeholder="开始日期"
                        end-placeholder="结束日期"
                        @change="fetchQuotes"
                    />
                </div>
                <el-empty
                    v-if="!hasQuotes"
                    description="暂无行情数据"
                />
                <BaseChart
                    v-else
                    :option="priceOption"
                    :height="420"
                    style="margin-top: 12px"
                />
            </el-card>

            <!-- 估值走势 -->
            <el-card v-if="hasQuotes" style="margin-top: 16px">
                <div class="card-header-bar">
                    <h3 class="card-title">估值走势</h3>
                </div>
                <BaseChart :option="valuationOption" :height="320" />
            </el-card>

            <!-- 行情数据 -->
            <el-card style="margin-top: 16px">
                <div class="card-header-bar">
                    <h3 class="card-title">行情数据</h3>
                </div>
                <el-empty v-if="!hasQuotes" description="暂无行情数据" />
                <el-table
                    v-else
                    :data="quotesDesc"
                    border
                    max-height="420"
                    style="margin-top: 12px"
                >
                    <el-table-column prop="trade_date" label="日期" width="120" />
                    <el-table-column label="开盘" width="90">
                        <template #default="scope">{{ num(scope.row.open) }}</template>
                    </el-table-column>
                    <el-table-column label="最高" width="90">
                        <template #default="scope">{{ num(scope.row.high) }}</template>
                    </el-table-column>
                    <el-table-column label="最低" width="90">
                        <template #default="scope">{{ num(scope.row.low) }}</template>
                    </el-table-column>
                    <el-table-column label="收盘" width="90">
                        <template #default="scope">{{ num(scope.row.close) }}</template>
                    </el-table-column>
                    <el-table-column label="涨跌幅" width="100">
                        <template #default="scope">
                            {{ formatPercentValue(scope.row.pct_chg) }}
                        </template>
                    </el-table-column>
                    <el-table-column label="成交量" min-width="110">
                        <template #default="scope">
                            {{ formatAmount(scope.row.volume) }}
                        </template>
                    </el-table-column>
                    <el-table-column label="成交额" min-width="110">
                        <template #default="scope">
                            {{ formatAmount(scope.row.amount) }}
                        </template>
                    </el-table-column>
                    <el-table-column label="换手率" width="100">
                        <template #default="scope">
                            {{ formatPercentValue(scope.row.turn) }}
                        </template>
                    </el-table-column>
                    <el-table-column label="PE(TTM)" width="100">
                        <template #default="scope">{{ num(scope.row.pe_ttm) }}</template>
                    </el-table-column>
                    <el-table-column label="PB(MRQ)" width="100">
                        <template #default="scope">{{ num(scope.row.pb_mrq) }}</template>
                    </el-table-column>
                </el-table>
            </el-card>

            <!-- 财务指标 -->
            <el-card style="margin-top: 16px">
                <div class="card-header-bar">
                    <h3 class="card-title">财务指标</h3>
                    <el-select
                        v-model="finMetric"
                        style="width: 240px"
                        placeholder="选择指标"
                    >
                        <el-option-group
                            v-for="group in METRIC_GROUPS"
                            :key="group.key"
                            :label="group.label"
                        >
                            <el-option
                                v-for="m in group.metrics"
                                :key="m.key"
                                :label="m.label"
                                :value="m.key"
                            />
                        </el-option-group>
                    </el-select>
                </div>

                <el-empty v-if="!hasFinancials" description="暂无财务数据" />
                <template v-else>
                    <BaseChart
                        :option="finChartOption"
                        :height="300"
                        style="margin-top: 12px"
                    />
                    <el-tabs v-model="activeGroup" style="margin-top: 12px">
                        <el-tab-pane
                            v-for="group in METRIC_GROUPS"
                            :key="group.key"
                            :label="group.label"
                            :name="group.key"
                        >
                            <el-table :data="financialsDesc" border>
                                <el-table-column label="报告期" width="100">
                                    <template #default="scope">
                                        {{ periodLabel(scope.row.stat_date) }}
                                    </template>
                                </el-table-column>
                                <el-table-column label="公告日" width="120">
                                    <template #default="scope">
                                        {{ scope.row.pub_date ?? "—" }}
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    v-for="m in group.metrics"
                                    :key="m.key"
                                    :label="m.label"
                                    :min-width="130"
                                >
                                    <template #default="scope">
                                        {{ formatMetric(scope.row[m.key], m.kind) }}
                                    </template>
                                </el-table-column>
                            </el-table>
                        </el-tab-pane>
                    </el-tabs>
                </template>
            </el-card>
        </template>
    </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import request from "@/api/request";
import BaseChart from "@/components/BaseChart.vue";
import {
    ALL_METRICS,
    METRIC_GROUPS,
    formatAmount,
    formatMetric,
    formatPercentValue,
    type ECOption,
    type FinancialItem,
    type QuoteItem,
    type StockItem,
} from "@/types/stock";

const route = useRoute();
const router = useRouter();
const code = computed(() => String(route.params.code));

const stock = ref<StockItem | null>(null);
const notFound = ref(false);
const quotes = ref<QuoteItem[]>([]);
const financials = ref<FinancialItem[]>([]);
const dateRange = ref<[string, string] | null>(null);
const finMetric = ref("roe_avg");
const activeGroup = ref("profit");

const hasQuotes = computed(() => quotes.value.length > 0);
const hasFinancials = computed(() => financials.value.length > 0);
const quotesDesc = computed(() => [...quotes.value].reverse());
const financialsDesc = computed(() => [...financials.value].reverse());

const num = (v: number | null | undefined): string =>
    v === null || v === undefined ? "—" : v.toFixed(2);

// "2024-12-31" → "2024Q4"
const periodLabel = (statDate: string): string => {
    const [year, month] = statDate.split("-");
    return `${year}Q${Math.floor((Number(month) - 1) / 3) + 1}`;
};

// ---- 数据加载 --------------------------------------------------------------
const fetchStock = async () => {
    try {
        stock.value = await request.get<StockItem>(`/stocks/${code.value}`);
        notFound.value = false;
    } catch {
        // 拦截器已提示错误（如 404 Stock not found），这里只标记空态。
        notFound.value = true;
    }
};

const fetchQuotes = async () => {
    const params: Record<string, string> = {};
    if (dateRange.value && dateRange.value.length === 2) {
        params.start = dateRange.value[0];
        params.end = dateRange.value[1];
    }
    quotes.value = await request.get<QuoteItem[]>(
        `/stocks/${code.value}/quotes`,
        { params }
    );
};

const fetchFinancials = async () => {
    financials.value = await request.get<FinancialItem[]>(
        `/stocks/${code.value}/financials`
    );
};

const init = async () => {
    notFound.value = false;
    stock.value = null;
    quotes.value = [];
    financials.value = [];
    dateRange.value = null;
    await fetchStock();
    if (notFound.value) return;
    await Promise.all([fetchQuotes(), fetchFinancials()]);
};

// ---- 行情图：K线 + 成交量 --------------------------------------------------
const priceOption = computed<ECOption>(() => {
    const rows = quotes.value.filter(
        (q) => q.open != null && q.close != null && q.low != null && q.high != null
    );
    // ECharts 蜡烛图数据顺序固定为 [open, close, low, high]。
    const candles = rows.map((r) => [r.open!, r.close!, r.low!, r.high!]);
    const volumes = rows.map((r) => r.volume ?? 0);
    const dates = rows.map((r) => r.trade_date);
    return {
        tooltip: { trigger: "axis", axisPointer: { type: "cross" } },
        legend: { data: ["K线", "成交量"], top: 0 },
        grid: [
            { left: 60, right: 20, top: 40, height: "48%" },
            { left: 60, right: 20, top: "78%", height: "14%" },
        ],
        xAxis: [
            {
                type: "category",
                data: dates,
                boundaryGap: true,
                axisLine: { onZero: false },
            },
            {
                type: "category",
                gridIndex: 1,
                data: dates,
                axisLabel: { show: false },
            },
        ],
        yAxis: [
            { scale: true, name: "价格" },
            {
                gridIndex: 1,
                name: "成交量",
                splitNumber: 2,
                axisLabel: { show: false },
            },
        ],
        dataZoom: [
            { type: "inside", xAxisIndex: [0, 1] },
            { type: "slider", xAxisIndex: [0, 1], height: 18, bottom: 6 },
        ],
        series: [
            {
                name: "K线",
                type: "candlestick",
                xAxisIndex: 0,
                yAxisIndex: 0,
                data: candles,
                itemStyle: {
                    color: "#ef232a",
                    color0: "#14b143",
                    borderColor: "#ef232a",
                    borderColor0: "#14b143",
                },
            },
            {
                name: "成交量",
                type: "bar",
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: volumes,
            },
        ],
    };
});

// ---- 估值图：PE / PB -------------------------------------------------------
const valuationOption = computed<ECOption>(() => {
    const dates = quotes.value.map((q) => q.trade_date);
    return {
        tooltip: { trigger: "axis" },
        legend: { data: ["PE(TTM)", "PB(MRQ)"], top: 0 },
        grid: { left: 60, right: 60, top: 40, bottom: 40 },
        xAxis: { type: "category", data: dates },
        yAxis: [
            { type: "value", name: "PE(TTM)", scale: true },
            { type: "value", name: "PB(MRQ)", scale: true },
        ],
        series: [
            {
                name: "PE(TTM)",
                type: "line",
                data: quotes.value.map((q) => q.pe_ttm),
                yAxisIndex: 0,
                showSymbol: false,
                connectNulls: true,
            },
            {
                name: "PB(MRQ)",
                type: "line",
                data: quotes.value.map((q) => q.pb_mrq),
                yAxisIndex: 1,
                showSymbol: false,
                connectNulls: true,
            },
        ],
    };
});

// ---- 财报柱状图：选定指标按报告期 -----------------------------------------
const finChartOption = computed<ECOption>(() => {
    const def =
        ALL_METRICS.find((m) => m.key === finMetric.value) ?? ALL_METRICS[0];
    const scale = def.kind === "percent" ? 100 : 1;
    const unit = def.kind === "percent" ? "%" : def.kind === "amount" ? "元" : "";
    const periods = financials.value.map((r) => periodLabel(r.stat_date));
    const values = financials.value.map((r) => {
        const v = r[def.key];
        return typeof v === "number" ? +(v * scale).toFixed(4) : null;
    });
    return {
        tooltip: { trigger: "axis" },
        grid: { left: 70, right: 20, top: 30, bottom: 40 },
        xAxis: { type: "category", data: periods },
        yAxis: { type: "value", name: `${def.label}${unit ? `(${unit})` : ""}` },
        series: [{ name: def.label, type: "bar", data: values }],
    };
});

watch(code, init);

onMounted(init);
</script>

<style scoped>
.stock-detail-page {
    padding: 20px;
}
.header-bar {
    display: flex;
    align-items: center;
    gap: 12px;
}
.stock-name {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: var(--el-text-color-primary);
}
.card-header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.card-title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
}
</style>
