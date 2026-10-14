<template>
    <div ref="el" :style="{ width: '100%', height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts/core";
import { BarChart, CandlestickChart, LineChart } from "echarts/charts";
import {
    DataZoomComponent,
    GridComponent,
    LegendComponent,
    TitleComponent,
    TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { useResizeObserver } from "@vueuse/core";
import type { ECOption } from "@/types/stock";

// 按需注册用到的图表与组件（tree-shaking，别把没用到的加进来）。
echarts.use([
    BarChart,
    CandlestickChart,
    LineChart,
    DataZoomComponent,
    GridComponent,
    LegendComponent,
    TitleComponent,
    TooltipComponent,
    CanvasRenderer,
]);

const props = withDefaults(
    defineProps<{ option: ECOption; height?: number }>(),
    { height: 360 }
);

const el = ref<HTMLDivElement>();
let chart: echarts.EChartsType | null = null;

onMounted(() => {
    if (!el.value) return;
    chart = echarts.init(el.value);
    chart.setOption(props.option);
});

// 切换股票/日期范围后 option 会被替换：notMerge=true 清掉旧 series。
watch(
    () => props.option,
    (opt) => chart?.setOption(opt, true),
    { deep: true }
);

// 容器尺寸变化（含侧边栏收起、窗口缩放）时自适应。
useResizeObserver(el, () => chart?.resize());

onBeforeUnmount(() => {
    chart?.dispose();
    chart = null;
});
</script>
