module.exports = [
"[project]/Documents/Python-Things/Praxis-10M/visualize/.next-internal/server/app/stats/page/actions.js [app-rsc] (server actions loader, ecmascript)", ((__turbopack_context__, module, exports) => {

}),
"[project]/Documents/Python-Things/Praxis-10M/visualize/app/layout.tsx [app-rsc] (ecmascript, Next.js Server Component)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/app/layout.tsx [app-rsc] (ecmascript)"));
}),
"[externals]/fs/promises [external] (fs/promises, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("fs/promises", () => require("fs/promises"));

module.exports = mod;
}),
"[project]/Documents/Python-Things/Praxis-10M/visualize/lib/data.ts [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "generateStaticData",
    ()=>generateStaticData,
    "getAtomicVerbs",
    ()=>getAtomicVerbs,
    "getChildNodes",
    ()=>getChildNodes,
    "getDatasetStats",
    ()=>getDatasetStats,
    "getDomains",
    ()=>getDomains,
    "getNodeById",
    ()=>getNodeById,
    "getNodePath",
    ()=>getNodePath,
    "getNodesByDomain",
    ()=>getNodesByDomain,
    "getNodesByType",
    ()=>getNodesByType,
    "loadManifest",
    ()=>loadManifest,
    "searchTasks",
    ()=>searchTasks
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f$fs$2f$promises__$5b$external$5d$__$28$fs$2f$promises$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/fs/promises [external] (fs/promises, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/path [external] (path, cjs)");
;
;
const DATA_DIR = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(process.cwd(), 'public', 'data');
const CACHE_FILE = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(DATA_DIR, 'dataset-cache.json');
// Cache for dataset operations
let cachedManifest = null;
let cachedStats = null;
async function loadManifest() {
    if (cachedManifest) return cachedManifest;
    try {
        const manifestPath = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(DATA_DIR, 'manifest.json');
        const data = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs$2f$promises__$5b$external$5d$__$28$fs$2f$promises$2c$__cjs$29$__["default"].readFile(manifestPath, 'utf-8');
        cachedManifest = JSON.parse(data);
        return cachedManifest;
    } catch (error) {
        console.warn('Manifest not found, returning empty dataset:', error);
        return {};
    }
}
async function getDatasetStats() {
    if (cachedStats) return cachedStats;
    try {
        const statsPath = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(DATA_DIR, 'stats.json');
        const data = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs$2f$promises__$5b$external$5d$__$28$fs$2f$promises$2c$__cjs$29$__["default"].readFile(statsPath, 'utf-8');
        cachedStats = JSON.parse(data);
        return cachedStats;
    } catch (error) {
        // Generate mock stats if file doesn't exist
        console.warn('Stats file not found, generating mock data');
        const mockStats = {
            totalNodes: 1000000,
            atomicActions: 750000,
            domains: 35,
            verbs: 3479,
            avgDepth: 4.2,
            maxDepth: 8,
            nodesByType: {
                DOMAIN: 35,
                TASK: 50000,
                SUBTASK: 200000,
                ATOMIC: 750000
            },
            nodesByDomain: {
                'work_healthcare': 120000,
                'work_manufacturing': 95000,
                'work_construction': 88000,
                'life_household': 150000,
                'life_personal_care': 75000
            },
            topVerbs: [
                {
                    verb: 'grasp',
                    count: 45000
                },
                {
                    verb: 'move_to',
                    count: 42000
                },
                {
                    verb: 'release',
                    count: 38000
                },
                {
                    verb: 'inspect',
                    count: 35000
                },
                {
                    verb: 'clean',
                    count: 32000
                }
            ]
        };
        cachedStats = mockStats;
        return mockStats;
    }
}
async function searchTasks(query, limit = 50) {
    const manifest = await loadManifest();
    const lowerQuery = query.toLowerCase();
    const results = Object.values(manifest).filter((node)=>node.name.toLowerCase().includes(lowerQuery) || node.id.toLowerCase().includes(lowerQuery) || node.description?.toLowerCase().includes(lowerQuery)).slice(0, limit);
    return results;
}
async function getNodeById(id) {
    const manifest = await loadManifest();
    return manifest[id] || null;
}
async function getNodesByDomain(domain) {
    const manifest = await loadManifest();
    return Object.values(manifest).filter((node)=>node.domain === domain);
}
async function getNodesByType(type) {
    const manifest = await loadManifest();
    return Object.values(manifest).filter((node)=>node.node_type === type);
}
async function getChildNodes(parentId) {
    const manifest = await loadManifest();
    const parent = manifest[parentId];
    if (!parent || !parent.children_ids) return [];
    return parent.children_ids.map((id)=>manifest[id]).filter(Boolean);
}
async function getNodePath(nodeId) {
    const manifest = await loadManifest();
    const path = [];
    let currentNode = manifest[nodeId];
    while(currentNode){
        path.unshift(currentNode);
        if (!currentNode.parent_id) break;
        currentNode = manifest[currentNode.parent_id];
    }
    return path;
}
async function getDomains() {
    const manifest = await loadManifest();
    return Object.values(manifest).filter((node)=>node.node_type === 'DOMAIN');
}
async function getAtomicVerbs() {
    const manifest = await loadManifest();
    const verbs = new Set();
    Object.values(manifest).forEach((node)=>{
        if (node.node_type === 'ATOMIC' && node.verb) {
            verbs.add(node.verb);
        }
    });
    return Array.from(verbs).sort();
}
async function generateStaticData() {
    // This would be called during build time to export data from taskpedia CLI
    console.log('Generating static data from taskpedia...');
// Implementation would call: taskpedia export -f json
}
}),
"[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsDashboard.tsx [app-rsc] (client reference proxy) <module evaluation>", ((__turbopack_context__) => {
"use strict";

// This file is generated by next-core EcmascriptClientReferenceModule.
__turbopack_context__.s([
    "StatsDashboard",
    ()=>StatsDashboard
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$server$2d$dom$2d$turbopack$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-server-dom-turbopack-server.js [app-rsc] (ecmascript)");
;
const StatsDashboard = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$server$2d$dom$2d$turbopack$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["registerClientReference"])(function() {
    throw new Error("Attempted to call StatsDashboard() from the server but StatsDashboard is on the client. It's not possible to invoke a client function from the server, it can only be rendered as a Component or passed to props of a Client Component.");
}, "[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsDashboard.tsx <module evaluation>", "StatsDashboard");
}),
"[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsDashboard.tsx [app-rsc] (client reference proxy)", ((__turbopack_context__) => {
"use strict";

// This file is generated by next-core EcmascriptClientReferenceModule.
__turbopack_context__.s([
    "StatsDashboard",
    ()=>StatsDashboard
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$server$2d$dom$2d$turbopack$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-server-dom-turbopack-server.js [app-rsc] (ecmascript)");
;
const StatsDashboard = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$server$2d$dom$2d$turbopack$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["registerClientReference"])(function() {
    throw new Error("Attempted to call StatsDashboard() from the server but StatsDashboard is on the client. It's not possible to invoke a client function from the server, it can only be rendered as a Component or passed to props of a Client Component.");
}, "[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsDashboard.tsx", "StatsDashboard");
}),
"[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsDashboard.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$components$2f$StatsDashboard$2e$tsx__$5b$app$2d$rsc$5d$__$28$client__reference__proxy$29$__$3c$module__evaluation$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsDashboard.tsx [app-rsc] (client reference proxy) <module evaluation>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$components$2f$StatsDashboard$2e$tsx__$5b$app$2d$rsc$5d$__$28$client__reference__proxy$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsDashboard.tsx [app-rsc] (client reference proxy)");
;
__turbopack_context__.n(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$components$2f$StatsDashboard$2e$tsx__$5b$app$2d$rsc$5d$__$28$client__reference__proxy$29$__);
}),
"[project]/Documents/Python-Things/Praxis-10M/visualize/app/stats/page.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>StatsPage,
    "metadata",
    ()=>metadata,
    "revalidate",
    ()=>revalidate
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-jsx-dev-runtime.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$lib$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/lib/data.ts [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$components$2f$StatsDashboard$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/components/StatsDashboard.tsx [app-rsc] (ecmascript)");
;
;
;
;
const metadata = {
    title: 'Statistics',
    description: 'Comprehensive statistics and analytics for the TASKPEDIA hierarchical task decomposition dataset.',
    openGraph: {
        title: 'Statistics - TASKPEDIA',
        description: 'Comprehensive statistics and analytics for the TASKPEDIA dataset'
    }
};
const revalidate = 3600;
async function StatsPage() {
    const stats = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$lib$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getDatasetStats"])();
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 py-12 px-4 sm:px-6 lg:px-8",
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "max-w-7xl mx-auto",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "text-center mb-12",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                            className: "text-4xl lg:text-5xl font-bold text-gray-900 mb-4",
                            children: "Dataset Statistics"
                        }, void 0, false, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/stats/page.tsx",
                            lineNumber: 24,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            className: "text-xl text-gray-600 max-w-3xl mx-auto",
                            children: "Comprehensive analytics and insights into the TASKPEDIA dataset"
                        }, void 0, false, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/stats/page.tsx",
                            lineNumber: 27,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/stats/page.tsx",
                    lineNumber: 23,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["Suspense"], {
                    fallback: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "h-96 skeleton rounded-2xl"
                    }, void 0, false, {
                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/stats/page.tsx",
                        lineNumber: 32,
                        columnNumber: 29
                    }, void 0),
                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$components$2f$StatsDashboard$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["StatsDashboard"], {
                        stats: stats
                    }, void 0, false, {
                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/stats/page.tsx",
                        lineNumber: 33,
                        columnNumber: 11
                    }, this)
                }, void 0, false, {
                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/stats/page.tsx",
                    lineNumber: 32,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/stats/page.tsx",
            lineNumber: 22,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/stats/page.tsx",
        lineNumber: 21,
        columnNumber: 5
    }, this);
}
}),
"[project]/Documents/Python-Things/Praxis-10M/visualize/app/stats/page.tsx [app-rsc] (ecmascript, Next.js Server Component)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/app/stats/page.tsx [app-rsc] (ecmascript)"));
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__80e93e3a._.js.map