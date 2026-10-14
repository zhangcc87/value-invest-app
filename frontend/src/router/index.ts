import { createRouter, createWebHistory } from "vue-router";
const routes = [
    { path: "/login", component: () => import("../views/Login.vue") },
    {
        path: "/",
        component: () => import("../layouts/MainLayout.vue"),
        redirect: "/dashboard",
        children: [
            {
                path: "/dashboard",
                component: () => import("../views/Dashboard.vue"),
            },
            { path: "/users", component: () => import("../views/Users.vue") },
            {
                path: "/stocks",
                name: "stock-list",
                component: () => import("../views/StockList.vue"),
            },
            {
                path: "/stocks/:code",
                name: "stock-detail",
                component: () => import("../views/StockDetail.vue"),
            },
            {
                path: "/settings",
                component: () => import("../views/Settings.vue"),
            },
        ],
    },
    { path: "/:pathMatch(.*)*", redirect: "/login" },
];

const router = createRouter({ history: createWebHistory(), routes });

// 全局路由守卫
router.beforeEach((to, _from, next) => {
    const token = localStorage.getItem("token");
    if (to.path !== "/login" && !token) return next("/login");
    if (to.path === "/login" && token) return next("/");
    next();
});
export default router;
