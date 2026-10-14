// 股票数据相关的共享类型 + 财报指标元数据。
// 字段名与后端 app/schemas/stock.py 一一对应。
import type { ComposeOption } from "echarts/core";
import type {
    BarSeriesOption,
    CandlestickSeriesOption,
    LineSeriesOption,
} from "echarts/charts";
import type {
    DataZoomComponentOption,
    GridComponentOption,
    LegendComponentOption,
    TitleComponentOption,
    TooltipComponentOption,
} from "echarts/components";

// ECharts 按需引入后的 option 类型（只包含本项目用到的图表/组件）。
export type ECOption = ComposeOption<
    | BarSeriesOption
    | CandlestickSeriesOption
    | LineSeriesOption
    | DataZoomComponentOption
    | GridComponentOption
    | LegendComponentOption
    | TitleComponentOption
    | TooltipComponentOption
>;

// ---- 主数据 ----------------------------------------------------------------
export interface StockItem {
    code: string;
    symbol: string;
    exchange: string;
    board: string;
    name: string;
    industry: string | null;
    sec_type: number;
    status: number;
    ipo_date: string | null;
    out_date: string | null;
    updated_at: string | null;
}

export interface StockListResp {
    data: StockItem[];
    count: number;
}

// ---- 日行情 + 估值 ---------------------------------------------------------
// 注意：pct_chg / turn 已是百分数（0.5562 即 0.56%），其余估值字段是原始倍数。
export interface QuoteItem {
    code: string;
    trade_date: string;
    open: number | null;
    high: number | null;
    low: number | null;
    close: number | null;
    preclose: number | null;
    volume: number | null;
    amount: number | null;
    pct_chg: number | null;
    turn: number | null;
    tradestatus: number | null;
    is_st: number | null;
    pe_ttm: number | null;
    pb_mrq: number | null;
    ps_ttm: number | null;
    pcf_ncf_ttm: number | null;
}

// ---- 季频财务 --------------------------------------------------------------
// 所有比率都是**小数**（roe_avg=0.3446 即 34.46%）。索引签名让指标表可以按 key 动态取值。
export interface FinancialItem {
    code: string;
    stat_date: string;
    pub_date: string | null;
    [metric: string]: string | number | null;
}

// ---- 指标元数据（表格与图表都由它生成） ------------------------------------
// kind 决定显示格式：
//   percent —— 小数比率，×100 后加 "%"
//   number  —— 倍数/次数/天数，原样保留 2 位小数（不可 ×100）
//   amount  —— 绝对数（元/股），按 亿/万 缩写
export type MetricKind = "percent" | "number" | "amount";

export interface MetricDef {
    key: string;
    label: string;
    kind: MetricKind;
}

export interface MetricGroup {
    key: string;
    label: string;
    metrics: MetricDef[];
}

export const METRIC_GROUPS: MetricGroup[] = [
    {
        key: "profit",
        label: "盈利能力",
        metrics: [
            { key: "roe_avg", label: "净资产收益率(ROE)", kind: "percent" },
            { key: "np_margin", label: "销售净利率", kind: "percent" },
            { key: "gp_margin", label: "销售毛利率", kind: "percent" },
            { key: "net_profit", label: "净利润", kind: "amount" },
            { key: "eps_ttm", label: "每股收益(TTM)", kind: "number" },
            { key: "mb_revenue", label: "营业收入", kind: "amount" },
            { key: "total_share", label: "总股本", kind: "amount" },
            { key: "liqa_share", label: "流通股本", kind: "amount" },
        ],
    },
    {
        key: "growth",
        label: "成长能力",
        metrics: [
            { key: "yoy_equity", label: "净资产同比", kind: "percent" },
            { key: "yoy_asset", label: "总资产同比", kind: "percent" },
            { key: "yoy_ni", label: "净利润同比", kind: "percent" },
            { key: "yoy_eps_basic", label: "每股收益同比", kind: "percent" },
            { key: "yoy_pni", label: "归母净利润同比", kind: "percent" },
        ],
    },
    {
        key: "balance",
        label: "偿债能力",
        metrics: [
            { key: "current_ratio", label: "流动比率", kind: "number" },
            { key: "quick_ratio", label: "速动比率", kind: "number" },
            { key: "cash_ratio", label: "现金比率", kind: "number" },
            { key: "yoy_liability", label: "负债同比", kind: "percent" },
            { key: "liability_to_asset", label: "资产负债率", kind: "percent" },
            { key: "asset_to_equity", label: "权益乘数", kind: "number" },
        ],
    },
    {
        key: "cashflow",
        label: "现金流",
        metrics: [
            { key: "cato_asset", label: "流动资产/总资产", kind: "percent" },
            { key: "ncato_asset", label: "非流动资产/总资产", kind: "percent" },
            {
                key: "tangible_asset_to_asset",
                label: "有形资产/总资产",
                kind: "percent",
            },
            { key: "ebit_to_interest", label: "利息保障倍数", kind: "number" },
            { key: "cfo_to_or", label: "经营现金流/营收", kind: "percent" },
            { key: "cfo_to_np", label: "经营现金流/净利润", kind: "percent" },
            { key: "cfo_to_gr", label: "经营现金流/毛利", kind: "percent" },
        ],
    },
    {
        key: "operation",
        label: "营运能力",
        metrics: [
            { key: "nr_turn_ratio", label: "应收账款周转率", kind: "number" },
            { key: "nr_turn_days", label: "应收账款周转天数", kind: "number" },
            { key: "inv_turn_ratio", label: "存货周转率", kind: "number" },
            { key: "inv_turn_days", label: "存货周转天数", kind: "number" },
            { key: "ca_turn_ratio", label: "流动资产周转率", kind: "number" },
            { key: "asset_turn_ratio", label: "总资产周转率", kind: "number" },
        ],
    },
    {
        key: "dupont",
        label: "杜邦分析",
        metrics: [
            { key: "dupont_roe", label: "杜邦ROE", kind: "percent" },
            {
                key: "dupont_asset_sto_equity",
                label: "权益乘数",
                kind: "number",
            },
            { key: "dupont_asset_turn", label: "总资产周转率", kind: "number" },
            { key: "dupont_pnitoni", label: "净利润/归母净利润", kind: "percent" },
            { key: "dupont_nitogr", label: "归母净利润/营收", kind: "percent" },
            { key: "dupont_tax_burden", label: "税收负担", kind: "percent" },
            { key: "dupont_intburden", label: "利息负担", kind: "number" },
            { key: "dupont_ebittogr", label: "EBIT/营收", kind: "percent" },
        ],
    },
];

// 扁平化的全部指标，供「选一个指标画柱状图」下拉使用。
export const ALL_METRICS: MetricDef[] = METRIC_GROUPS.flatMap(
    (group) => group.metrics
);

// ---- 格式化 ----------------------------------------------------------------
const DASH = "—";

// 绝对数按 亿/万 缩写，便于阅读（net_profit=8.9e10 → 893.35亿）。
export function formatAmount(value: number | null | undefined): string {
    if (value === null || value === undefined) return DASH;
    const abs = Math.abs(value);
    if (abs >= 1e8) return (value / 1e8).toFixed(2) + "亿";
    if (abs >= 1e4) return (value / 1e4).toFixed(2) + "万";
    return value.toFixed(2);
}

// 普通数值（倍数/次数/天数）。
export function formatNumber(value: number | null | undefined): string {
    if (value === null || value === undefined) return DASH;
    return value.toFixed(2);
}

// 财报指标按 kind 格式化。
export function formatMetric(
    value: number | string | null | undefined,
    kind: MetricKind
): string {
    if (value === null || value === undefined || typeof value === "string") {
        return DASH;
    }
    if (kind === "percent") return (value * 100).toFixed(2) + "%";
    if (kind === "amount") return formatAmount(value);
    return formatNumber(value);
}

// 行情表里已是百分数的字段（pct_chg / turn）。
export function formatPercentValue(value: number | null | undefined): string {
    if (value === null || value === undefined) return DASH;
    return value.toFixed(2) + "%";
}
