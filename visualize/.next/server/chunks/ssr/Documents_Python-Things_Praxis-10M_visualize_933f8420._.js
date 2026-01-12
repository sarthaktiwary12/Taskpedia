module.exports = [
"[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsOverview.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "StatsOverview",
    ()=>StatsOverview
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$activity$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Activity$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/activity.js [app-ssr] (ecmascript) <export default as Activity>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$box$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Box$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/box.js [app-ssr] (ecmascript) <export default as Box>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$git$2d$branch$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__GitBranch$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/git-branch.js [app-ssr] (ecmascript) <export default as GitBranch>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$layers$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Layers$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/layers.js [app-ssr] (ecmascript) <export default as Layers>");
'use client';
;
;
function StatsOverview({ stats }) {
    const statCards = [
        {
            icon: __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$box$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Box$3e$__["Box"],
            label: 'Node Types',
            data: Object.entries(stats.nodesByType).map(([type, count])=>({
                    name: type,
                    value: count,
                    percentage: (count / stats.totalNodes * 100).toFixed(1)
                })),
            color: 'from-blue-500 to-blue-600'
        },
        {
            icon: __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$git$2d$branch$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__GitBranch$3e$__["GitBranch"],
            label: 'Tree Depth',
            data: [
                {
                    name: 'Average',
                    value: stats.avgDepth.toFixed(1),
                    unit: 'levels'
                },
                {
                    name: 'Maximum',
                    value: stats.maxDepth,
                    unit: 'levels'
                }
            ],
            color: 'from-green-500 to-green-600'
        },
        {
            icon: __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$activity$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Activity$3e$__["Activity"],
            label: 'Top Verbs',
            data: stats.topVerbs.slice(0, 5).map((v)=>({
                    name: v.verb,
                    value: v.count.toLocaleString(),
                    percentage: (v.count / stats.atomicActions * 100).toFixed(1)
                })),
            color: 'from-purple-500 to-purple-600'
        },
        {
            icon: __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$layers$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Layers$3e$__["Layers"],
            label: 'Top Domains',
            data: Object.entries(stats.nodesByDomain).sort(([, a], [, b])=>b - a).slice(0, 5).map(([domain, count])=>({
                    name: domain.replace(/_/g, ' '),
                    value: count.toLocaleString(),
                    percentage: (count / stats.totalNodes * 100).toFixed(1)
                })),
            color: 'from-orange-500 to-orange-600'
        }
    ];
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6",
        children: statCards.map((card)=>{
            const Icon = card.icon;
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow border border-gray-100",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex items-center space-x-3 mb-4",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: `w-10 h-10 bg-gradient-to-br ${card.color} rounded-lg flex items-center justify-center`,
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Icon, {
                                    className: "w-5 h-5 text-white"
                                }, void 0, false, {
                                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsOverview.tsx",
                                    lineNumber: 67,
                                    columnNumber: 17
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsOverview.tsx",
                                lineNumber: 66,
                                columnNumber: 15
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                className: "font-semibold text-gray-900",
                                children: card.label
                            }, void 0, false, {
                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsOverview.tsx",
                                lineNumber: 69,
                                columnNumber: 15
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsOverview.tsx",
                        lineNumber: 65,
                        columnNumber: 13
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "space-y-3",
                        children: card.data.map((item, idx)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex justify-between items-center",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-sm text-gray-600 capitalize",
                                        children: item.name
                                    }, void 0, false, {
                                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsOverview.tsx",
                                        lineNumber: 75,
                                        columnNumber: 19
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center space-x-2",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-sm font-semibold text-gray-900",
                                                children: [
                                                    item.value,
                                                    item.unit && ` ${item.unit}`
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsOverview.tsx",
                                                lineNumber: 79,
                                                columnNumber: 21
                                            }, this),
                                            item.percentage && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-xs text-gray-500",
                                                children: [
                                                    "(",
                                                    item.percentage,
                                                    "%)"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsOverview.tsx",
                                                lineNumber: 84,
                                                columnNumber: 23
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsOverview.tsx",
                                        lineNumber: 78,
                                        columnNumber: 19
                                    }, this)
                                ]
                            }, idx, true, {
                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsOverview.tsx",
                                lineNumber: 74,
                                columnNumber: 17
                            }, this))
                    }, void 0, false, {
                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsOverview.tsx",
                        lineNumber: 72,
                        columnNumber: 13
                    }, this)
                ]
            }, card.label, true, {
                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsOverview.tsx",
                lineNumber: 61,
                columnNumber: 11
            }, this);
        })
    }, void 0, false, {
        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsOverview.tsx",
        lineNumber: 57,
        columnNumber: 5
    }, this);
}
}),
"[project]/Documents/Python-Things/Praxis-10M/visualize/components/FeaturedDomains.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "FeaturedDomains",
    ()=>FeaturedDomains
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/client/app-dir/link.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$stethoscope$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Stethoscope$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/stethoscope.js [app-ssr] (ecmascript) <export default as Stethoscope>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$wrench$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Wrench$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/wrench.js [app-ssr] (ecmascript) <export default as Wrench>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$hard$2d$hat$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__HardHat$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/hard-hat.js [app-ssr] (ecmascript) <export default as HardHat>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$house$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Home$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/house.js [app-ssr] (ecmascript) <export default as Home>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$utensils$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Utensils$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/utensils.js [app-ssr] (ecmascript) <export default as Utensils>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$shopping$2d$cart$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__ShoppingCart$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/shopping-cart.js [app-ssr] (ecmascript) <export default as ShoppingCart>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$graduation$2d$cap$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__GraduationCap$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/graduation-cap.js [app-ssr] (ecmascript) <export default as GraduationCap>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$truck$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Truck$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/truck.js [app-ssr] (ecmascript) <export default as Truck>");
'use client';
;
;
;
const featuredDomains = [
    {
        id: 'work_healthcare',
        name: 'Healthcare',
        description: 'Medical procedures, patient care, and clinical tasks',
        icon: __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$stethoscope$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Stethoscope$3e$__["Stethoscope"],
        color: 'from-red-500 to-pink-500',
        taskCount: '120K+'
    },
    {
        id: 'work_manufacturing',
        name: 'Manufacturing',
        description: 'Assembly, quality control, and production workflows',
        icon: __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$wrench$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Wrench$3e$__["Wrench"],
        color: 'from-blue-500 to-cyan-500',
        taskCount: '95K+'
    },
    {
        id: 'work_construction',
        name: 'Construction',
        description: 'Building, installation, and maintenance tasks',
        icon: __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$hard$2d$hat$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__HardHat$3e$__["HardHat"],
        color: 'from-orange-500 to-amber-500',
        taskCount: '88K+'
    },
    {
        id: 'life_household',
        name: 'Household',
        description: 'Cleaning, organizing, and home maintenance',
        icon: __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$house$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Home$3e$__["Home"],
        color: 'from-green-500 to-emerald-500',
        taskCount: '150K+'
    },
    {
        id: 'life_food_prep',
        name: 'Food Preparation',
        description: 'Cooking, meal prep, and kitchen tasks',
        icon: __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$utensils$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Utensils$3e$__["Utensils"],
        color: 'from-purple-500 to-violet-500',
        taskCount: '85K+'
    },
    {
        id: 'work_retail',
        name: 'Retail',
        description: 'Inventory, merchandising, and customer service',
        icon: __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$shopping$2d$cart$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__ShoppingCart$3e$__["ShoppingCart"],
        color: 'from-pink-500 to-rose-500',
        taskCount: '72K+'
    },
    {
        id: 'work_education',
        name: 'Education',
        description: 'Teaching, lab work, and educational activities',
        icon: __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$graduation$2d$cap$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__GraduationCap$3e$__["GraduationCap"],
        color: 'from-indigo-500 to-blue-500',
        taskCount: '68K+'
    },
    {
        id: 'work_logistics',
        name: 'Logistics',
        description: 'Warehousing, transport, and supply chain tasks',
        icon: __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$truck$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Truck$3e$__["Truck"],
        color: 'from-teal-500 to-cyan-500',
        taskCount: '92K+'
    }
];
function FeaturedDomains() {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6",
        children: featuredDomains.map((domain)=>{
            const Icon = domain.icon;
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["default"], {
                href: `/domain/${domain.id}`,
                className: "group bg-white rounded-2xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border border-gray-100 hover:scale-105",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex flex-col h-full",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: `w-14 h-14 bg-gradient-to-br ${domain.color} rounded-xl flex items-center justify-center mb-4 shadow-lg group-hover:shadow-xl transition-shadow`,
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Icon, {
                                className: "w-7 h-7 text-white"
                            }, void 0, false, {
                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/FeaturedDomains.tsx",
                                lineNumber: 95,
                                columnNumber: 17
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/FeaturedDomains.tsx",
                            lineNumber: 94,
                            columnNumber: 15
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                            className: "text-xl font-bold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors",
                            children: domain.name
                        }, void 0, false, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/FeaturedDomains.tsx",
                            lineNumber: 98,
                            columnNumber: 15
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            className: "text-sm text-gray-600 mb-4 flex-grow",
                            children: domain.description
                        }, void 0, false, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/FeaturedDomains.tsx",
                            lineNumber: 102,
                            columnNumber: 15
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex items-center justify-between",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    className: "text-sm font-semibold text-gray-500",
                                    children: [
                                        domain.taskCount,
                                        " tasks"
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/FeaturedDomains.tsx",
                                    lineNumber: 107,
                                    columnNumber: 17
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    className: "text-primary-600 group-hover:translate-x-1 transition-transform",
                                    children: "→"
                                }, void 0, false, {
                                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/FeaturedDomains.tsx",
                                    lineNumber: 110,
                                    columnNumber: 17
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/FeaturedDomains.tsx",
                            lineNumber: 106,
                            columnNumber: 15
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/FeaturedDomains.tsx",
                    lineNumber: 93,
                    columnNumber: 13
                }, this)
            }, domain.id, false, {
                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/FeaturedDomains.tsx",
                lineNumber: 88,
                columnNumber: 11
            }, this);
        })
    }, void 0, false, {
        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/FeaturedDomains.tsx",
        lineNumber: 84,
        columnNumber: 5
    }, this);
}
}),
"[project]/Documents/Python-Things/Praxis-10M/visualize/lib/utils.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "capitalize",
    ()=>capitalize,
    "cn",
    ()=>cn,
    "debounce",
    ()=>debounce,
    "formatNumber",
    ()=>formatNumber,
    "getNodeTypeColor",
    ()=>getNodeTypeColor,
    "getNodeTypeIcon",
    ()=>getNodeTypeIcon,
    "slugify",
    ()=>slugify
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$clsx$2f$dist$2f$clsx$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/clsx/dist/clsx.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/tailwind-merge/dist/bundle-mjs.mjs [app-ssr] (ecmascript)");
;
;
function cn(...inputs) {
    return (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["twMerge"])((0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$clsx$2f$dist$2f$clsx$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["clsx"])(inputs));
}
function debounce(func, wait) {
    let timeout = null;
    return function executedFunction(...args) {
        const later = ()=>{
            timeout = null;
            func(...args);
        };
        if (timeout) {
            clearTimeout(timeout);
        }
        timeout = setTimeout(later, wait);
    };
}
function formatNumber(num) {
    if (num >= 1000000) {
        return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
        return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
}
function slugify(text) {
    return text.toLowerCase().replace(/[^\w\s-]/g, '').replace(/[\s_-]+/g, '-').replace(/^-+|-+$/g, '');
}
function capitalize(text) {
    return text.charAt(0).toUpperCase() + text.slice(1);
}
function getNodeTypeColor(type) {
    const colors = {
        DOMAIN: 'blue',
        TASK: 'purple',
        SUBTASK: 'orange',
        ATOMIC: 'green'
    };
    return colors[type] || 'gray';
}
function getNodeTypeIcon(type) {
    const icons = {
        DOMAIN: '🌐',
        TASK: '📋',
        SUBTASK: '📝',
        ATOMIC: '⚡'
    };
    return icons[type] || '•';
}
}),
"[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "QuickSearch",
    ()=>QuickSearch
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$search$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Search$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/search.js [app-ssr] (ecmascript) <export default as Search>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$x$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__X$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/x.js [app-ssr] (ecmascript) <export default as X>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$right$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronRight$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/chevron-right.js [app-ssr] (ecmascript) <export default as ChevronRight>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/navigation.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/lib/utils.ts [app-ssr] (ecmascript)");
'use client';
;
;
;
;
;
function QuickSearch() {
    const [query, setQuery] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])('');
    const [results, setResults] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])([]);
    const [isLoading, setIsLoading] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(false);
    const [isOpen, setIsOpen] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(false);
    const router = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useRouter"])();
    const searchTasks = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useCallback"])((0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["debounce"])(async (searchQuery)=>{
        if (!searchQuery.trim()) {
            setResults([]);
            return;
        }
        setIsLoading(true);
        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(searchQuery)}`);
            const data = await response.json();
            setResults(data.results || []);
        } catch (error) {
            console.error('Search error:', error);
            setResults([]);
        } finally{
            setIsLoading(false);
        }
    }, 300), []);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        searchTasks(query);
    }, [
        query,
        searchTasks
    ]);
    const handleSelect = (nodeId)=>{
        router.push(`/node/${encodeURIComponent(nodeId)}`);
        setQuery('');
        setIsOpen(false);
    };
    const handleSubmit = (e)=>{
        e.preventDefault();
        if (query.trim()) {
            router.push(`/explore?q=${encodeURIComponent(query)}`);
            setIsOpen(false);
        }
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "relative max-w-3xl mx-auto",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("form", {
                onSubmit: handleSubmit,
                className: "relative",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "relative",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$search$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Search$3e$__["Search"], {
                            className: "absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
                        }, void 0, false, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                            lineNumber: 66,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                            type: "text",
                            value: query,
                            onChange: (e)=>{
                                setQuery(e.target.value);
                                setIsOpen(true);
                            },
                            onFocus: ()=>setIsOpen(true),
                            placeholder: "Search tasks, actions, or domains...",
                            className: "w-full pl-12 pr-12 py-4 bg-white rounded-2xl shadow-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-lg"
                        }, void 0, false, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                            lineNumber: 67,
                            columnNumber: 11
                        }, this),
                        query && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                            type: "button",
                            onClick: ()=>{
                                setQuery('');
                                setResults([]);
                            },
                            className: "absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$x$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__X$3e$__["X"], {
                                className: "w-5 h-5"
                            }, void 0, false, {
                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                                lineNumber: 87,
                                columnNumber: 15
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                            lineNumber: 79,
                            columnNumber: 13
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                    lineNumber: 65,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                lineNumber: 64,
                columnNumber: 7
            }, this),
            isOpen && (query || results.length > 0) && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Fragment"], {
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "fixed inset-0 z-10",
                        onClick: ()=>setIsOpen(false)
                    }, void 0, false, {
                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                        lineNumber: 96,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "absolute top-full mt-2 w-full bg-white rounded-2xl shadow-2xl border border-gray-200 max-h-96 overflow-y-auto z-20",
                        children: [
                            isLoading ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "p-4 text-center text-gray-500",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "inline-block w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"
                                }, void 0, false, {
                                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                                    lineNumber: 103,
                                    columnNumber: 17
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                                lineNumber: 102,
                                columnNumber: 15
                            }, this) : results.length > 0 ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "py-2",
                                children: results.map((result)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                        onClick: ()=>handleSelect(result.id),
                                        className: "w-full px-4 py-3 hover:bg-gray-50 flex items-center justify-between group transition-colors",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "flex items-center space-x-3",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        className: `px-2 py-1 rounded text-xs font-medium ${result.node_type === 'ATOMIC' ? 'bg-green-100 text-green-700' : result.node_type === 'DOMAIN' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'}`,
                                                        children: result.node_type
                                                    }, void 0, false, {
                                                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                                                        lineNumber: 114,
                                                        columnNumber: 23
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "text-left",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                className: "font-medium text-gray-900",
                                                                children: result.name
                                                            }, void 0, false, {
                                                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                                                                lineNumber: 126,
                                                                columnNumber: 25
                                                            }, this),
                                                            result.domain && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                className: "text-xs text-gray-500",
                                                                children: result.domain
                                                            }, void 0, false, {
                                                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                                                                lineNumber: 128,
                                                                columnNumber: 27
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                                                        lineNumber: 125,
                                                        columnNumber: 23
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                                                lineNumber: 113,
                                                columnNumber: 21
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$right$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronRight$3e$__["ChevronRight"], {
                                                className: "w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-1 transition-all"
                                            }, void 0, false, {
                                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                                                lineNumber: 132,
                                                columnNumber: 21
                                            }, this)
                                        ]
                                    }, result.id, true, {
                                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                                        lineNumber: 108,
                                        columnNumber: 19
                                    }, this))
                            }, void 0, false, {
                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                                lineNumber: 106,
                                columnNumber: 15
                            }, this) : query.trim() ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "p-8 text-center text-gray-500",
                                children: [
                                    'No results found for "',
                                    query,
                                    '"'
                                ]
                            }, void 0, true, {
                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                                lineNumber: 137,
                                columnNumber: 15
                            }, this) : null,
                            query.trim() && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "border-t border-gray-200 p-3 bg-gray-50",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                    onClick: handleSubmit,
                                    className: "w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium text-sm",
                                    children: [
                                        'View all results for "',
                                        query,
                                        '"'
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                                    lineNumber: 144,
                                    columnNumber: 17
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                                lineNumber: 143,
                                columnNumber: 15
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
                        lineNumber: 100,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true)
        ]
    }, void 0, true, {
        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/QuickSearch.tsx",
        lineNumber: 63,
        columnNumber: 5
    }, this);
}
}),
];

//# sourceMappingURL=Documents_Python-Things_Praxis-10M_visualize_933f8420._.js.map