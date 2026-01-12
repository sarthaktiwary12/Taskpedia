module.exports = [
"[project]/Documents/Python-Things/Praxis-10M/visualize/.next-internal/server/app/api/search/route/actions.js [app-rsc] (server actions loader, ecmascript)", ((__turbopack_context__, module, exports) => {

}),
"[externals]/next/dist/compiled/next-server/app-route-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-route-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/@opentelemetry/api [external] (next/dist/compiled/@opentelemetry/api, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/@opentelemetry/api", () => require("next/dist/compiled/@opentelemetry/api"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/after-task-async-storage.external.js [external] (next/dist/server/app-render/after-task-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/after-task-async-storage.external.js", () => require("next/dist/server/app-render/after-task-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/action-async-storage.external.js [external] (next/dist/server/app-render/action-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/action-async-storage.external.js", () => require("next/dist/server/app-render/action-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/fs/promises [external] (fs/promises, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("fs/promises", () => require("fs/promises"));

module.exports = mod;
}),
"[externals]/path [external] (path, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("path", () => require("path"));

module.exports = mod;
}),
"[project]/Documents/Python-Things/Praxis-10M/visualize/lib/data.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
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
"[project]/Documents/Python-Things/Praxis-10M/visualize/app/api/search/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "GET",
    ()=>GET
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/node_modules/next/server.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$lib$2f$data$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Documents/Python-Things/Praxis-10M/visualize/lib/data.ts [app-route] (ecmascript)");
;
;
async function GET(request) {
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get('q') || '';
    const limit = parseInt(searchParams.get('limit') || '50');
    try {
        const results = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$lib$2f$data$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["searchTasks"])(query, limit);
        return __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            success: true,
            query,
            count: results.length,
            results
        });
    } catch (error) {
        console.error('Search API error:', error);
        return __TURBOPACK__imported__module__$5b$project$5d2f$Documents$2f$Python$2d$Things$2f$Praxis$2d$10M$2f$visualize$2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            success: false,
            error: 'Search failed'
        }, {
            status: 500
        });
    }
}
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__b7e544b0._.js.map