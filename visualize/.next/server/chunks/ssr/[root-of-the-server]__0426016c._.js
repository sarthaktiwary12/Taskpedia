module.exports = [
"[project]/Documents/Python-Things/Praxis-10M/visualize/.next-internal/server/app/node/[id]/page/actions.js [app-rsc] (server actions loader, ecmascript)", ((__turbopack_context__, module, exports) => {

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
"[project]/Documents/Python-Things/Praxis-10M/visualize/lib/utils.ts [app-rsc] (ecmascript)", ((__turbopack_context__) => {
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
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$clsx$2f$dist$2f$clsx$2e$mjs__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/clsx/dist/clsx.mjs [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/tailwind-merge/dist/bundle-mjs.mjs [app-rsc] (ecmascript)");
;
;
function cn(...inputs) {
    return (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["twMerge"])((0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$clsx$2f$dist$2f$clsx$2e$mjs__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["clsx"])(inputs));
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
"[project]/Documents/Python-Things/Praxis-10M/visualize/components/TaskCard.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "TaskCard",
    ()=>TaskCard
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-jsx-dev-runtime.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/client/app-dir/link.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$right$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronRight$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/chevron-right.js [app-rsc] (ecmascript) <export default as ChevronRight>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$zap$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__$3c$export__default__as__Zap$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/zap.js [app-rsc] (ecmascript) <export default as Zap>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$lib$2f$utils$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/lib/utils.ts [app-rsc] (ecmascript)");
;
;
;
;
function TaskCard({ task }) {
    const color = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$lib$2f$utils$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getNodeTypeColor"])(task.node_type);
    const colorClasses = {
        blue: 'bg-blue-100 text-blue-700 border-blue-200',
        purple: 'bg-purple-100 text-purple-700 border-purple-200',
        orange: 'bg-orange-100 text-orange-700 border-orange-200',
        green: 'bg-green-100 text-green-700 border-green-200',
        gray: 'bg-gray-100 text-gray-700 border-gray-200'
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
        href: `/node/${encodeURIComponent(task.id)}`,
        className: "group block bg-white rounded-xl p-5 shadow-md hover:shadow-xl transition-all duration-300 border border-gray-200 hover:border-primary-300",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-start justify-between mb-3",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex items-center space-x-2",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: `px-2.5 py-1 rounded-lg text-xs font-semibold border ${colorClasses[color]}`,
                                children: task.node_type
                            }, void 0, false, {
                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/TaskCard.tsx",
                                lineNumber: 27,
                                columnNumber: 11
                            }, this),
                            task.node_type === 'ATOMIC' && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$zap$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__$3c$export__default__as__Zap$3e$__["Zap"], {
                                className: "w-4 h-4 text-green-600"
                            }, void 0, false, {
                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/TaskCard.tsx",
                                lineNumber: 35,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/TaskCard.tsx",
                        lineNumber: 26,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$right$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronRight$3e$__["ChevronRight"], {
                        className: "w-5 h-5 text-gray-400 group-hover:text-primary-600 group-hover:translate-x-1 transition-all"
                    }, void 0, false, {
                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/TaskCard.tsx",
                        lineNumber: 38,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/TaskCard.tsx",
                lineNumber: 25,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                className: "text-lg font-semibold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors",
                children: task.name
            }, void 0, false, {
                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/TaskCard.tsx",
                lineNumber: 41,
                columnNumber: 7
            }, this),
            task.description && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                className: "text-sm text-gray-600 mb-3 line-clamp-2",
                children: task.description
            }, void 0, false, {
                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/TaskCard.tsx",
                lineNumber: 46,
                columnNumber: 9
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center justify-between text-xs text-gray-500",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "font-mono truncate",
                        children: task.id
                    }, void 0, false, {
                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/TaskCard.tsx",
                        lineNumber: 52,
                        columnNumber: 9
                    }, this),
                    task.children_ids && task.children_ids.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "bg-gray-100 px-2 py-1 rounded",
                        children: [
                            task.children_ids.length,
                            " children"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/TaskCard.tsx",
                        lineNumber: 54,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/TaskCard.tsx",
                lineNumber: 51,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/components/TaskCard.tsx",
        lineNumber: 21,
        columnNumber: 5
    }, this);
}
}),
"[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>NodePage,
    "generateMetadata",
    ()=>generateMetadata
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-jsx-dev-runtime.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$api$2f$navigation$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/api/navigation.react-server.js [app-rsc] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$client$2f$components$2f$navigation$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/client/components/navigation.react-server.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/dist/client/app-dir/link.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$right$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronRight$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/chevron-right.js [app-rsc] (ecmascript) <export default as ChevronRight>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$arrow$2d$left$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__$3c$export__default__as__ArrowLeft$3e$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/lucide-react/dist/esm/icons/arrow-left.js [app-rsc] (ecmascript) <export default as ArrowLeft>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$lib$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/lib/data.ts [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$components$2f$TaskCard$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/components/TaskCard.tsx [app-rsc] (ecmascript)");
;
;
;
;
;
;
async function generateMetadata({ params }) {
    const { id } = await params;
    const node = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$lib$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getNodeById"])(decodeURIComponent(id));
    if (!node) {
        return {
            title: 'Node Not Found'
        };
    }
    return {
        title: node.name,
        description: `Explore the ${node.node_type.toLowerCase()} "${node.name}" in TASKPEDIA. ${node.description || ''}`
    };
}
async function NodePage({ params }) {
    const { id } = await params;
    const nodeId = decodeURIComponent(id);
    const node = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$lib$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getNodeById"])(nodeId);
    if (!node) {
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$client$2f$components$2f$navigation$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["notFound"])();
    }
    const children = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$lib$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getChildNodes"])(nodeId);
    const path = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$lib$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getNodePath"])(nodeId);
    const typeColors = {
        DOMAIN: 'bg-blue-100 text-blue-700',
        TASK: 'bg-purple-100 text-purple-700',
        SUBTASK: 'bg-orange-100 text-orange-700',
        ATOMIC: 'bg-green-100 text-green-700'
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 py-12 px-4 sm:px-6 lg:px-8",
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "max-w-5xl mx-auto",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
                    href: "/explore",
                    className: "inline-flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-6",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$arrow$2d$left$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__$3c$export__default__as__ArrowLeft$3e$__["ArrowLeft"], {
                            className: "w-4 h-4"
                        }, void 0, false, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                            lineNumber: 52,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                            children: "Back to Explore"
                        }, void 0, false, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                            lineNumber: 53,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                    lineNumber: 48,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("nav", {
                    className: "flex items-center space-x-2 text-sm mb-8 overflow-x-auto pb-2",
                    children: path.map((p, idx)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                            className: "flex items-center space-x-2 whitespace-nowrap",
                            children: [
                                idx > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$right$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronRight$3e$__["ChevronRight"], {
                                    className: "w-4 h-4 text-gray-400"
                                }, void 0, false, {
                                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                    lineNumber: 59,
                                    columnNumber: 27
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
                                    href: `/node/${encodeURIComponent(p.id)}`,
                                    className: `hover:text-primary-600 ${idx === path.length - 1 ? 'text-gray-900 font-medium' : 'text-gray-500'}`,
                                    children: p.name
                                }, void 0, false, {
                                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                    lineNumber: 60,
                                    columnNumber: 15
                                }, this)
                            ]
                        }, p.id, true, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                            lineNumber: 58,
                            columnNumber: 13
                        }, this))
                }, void 0, false, {
                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                    lineNumber: 56,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "bg-white rounded-2xl shadow-lg p-8 border border-gray-200 mb-8",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex items-start justify-between mb-4",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: `px-3 py-1 rounded-lg text-sm font-semibold ${typeColors[node.node_type]}`,
                                children: node.node_type
                            }, void 0, false, {
                                fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                lineNumber: 74,
                                columnNumber: 13
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                            lineNumber: 73,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                            className: "text-3xl lg:text-4xl font-bold text-gray-900 mb-4",
                            children: node.name
                        }, void 0, false, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                            lineNumber: 79,
                            columnNumber: 11
                        }, this),
                        node.description && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            className: "text-lg text-gray-600 mb-6",
                            children: node.description
                        }, void 0, false, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                            lineNumber: 84,
                            columnNumber: 13
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-xl",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "text-xs text-gray-500 uppercase font-medium",
                                            children: "ID"
                                        }, void 0, false, {
                                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                            lineNumber: 89,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "text-sm font-mono text-gray-900 truncate",
                                            children: node.id
                                        }, void 0, false, {
                                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                            lineNumber: 90,
                                            columnNumber: 15
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                    lineNumber: 88,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "text-xs text-gray-500 uppercase font-medium",
                                            children: "Type"
                                        }, void 0, false, {
                                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                            lineNumber: 93,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "text-sm text-gray-900",
                                            children: node.node_type
                                        }, void 0, false, {
                                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                            lineNumber: 94,
                                            columnNumber: 15
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                    lineNumber: 92,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "text-xs text-gray-500 uppercase font-medium",
                                            children: "Children"
                                        }, void 0, false, {
                                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                            lineNumber: 97,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "text-sm text-gray-900",
                                            children: children.length
                                        }, void 0, false, {
                                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                            lineNumber: 98,
                                            columnNumber: 15
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                    lineNumber: 96,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "text-xs text-gray-500 uppercase font-medium",
                                            children: "Sources"
                                        }, void 0, false, {
                                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                            lineNumber: 101,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "text-sm text-gray-900",
                                            children: node.sources?.join(', ') || 'N/A'
                                        }, void 0, false, {
                                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                            lineNumber: 102,
                                            columnNumber: 15
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                    lineNumber: 100,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                            lineNumber: 87,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                    lineNumber: 72,
                    columnNumber: 9
                }, this),
                children.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                            className: "text-2xl font-bold text-gray-900 mb-6",
                            children: [
                                "Child Nodes (",
                                children.length,
                                ")"
                            ]
                        }, void 0, true, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                            lineNumber: 109,
                            columnNumber: 13
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "grid grid-cols-1 md:grid-cols-2 gap-4",
                            children: children.map((child)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$components$2f$TaskCard$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["TaskCard"], {
                                    task: child
                                }, child.id, false, {
                                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                                    lineNumber: 114,
                                    columnNumber: 17
                                }, this))
                        }, void 0, false, {
                            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                            lineNumber: 112,
                            columnNumber: 13
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
                    lineNumber: 108,
                    columnNumber: 11
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
            lineNumber: 47,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx",
        lineNumber: 46,
        columnNumber: 5
    }, this);
}
}),
"[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx [app-rsc] (ecmascript, Next.js Server Component)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/app/node/[id]/page.tsx [app-rsc] (ecmascript)"));
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__0426016c._.js.map