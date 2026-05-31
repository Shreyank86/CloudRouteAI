/*
 * CloudRouteAI — Phase 1: NS-3 Network Simulation Foundation
 * ===========================================================
 *
 * Topology (1-indexed in spec, 0-indexed in code):
 *
 *   Node0 — Node1 — Node2 — Node3 — Node4 — Node5 — Node6 — Node7
 *                      \                /
 *                       Node8 — Node9
 *
 *   Primary path:   0-1-2-3-4-5-6-7  (10 Mbps, 2ms)
 *   Alternate path: 2-8-9-4          (5 Mbps, 5ms)
 *
 * Scenarios:
 *   normal     — baseline, no overrides
 *   congestion — bottleneck on link 3-4 (1 Mbps, 10ms, 20pkt queue), high traffic
 *   failure    — link 3-4 disabled at t=8s
 *   spike      — traffic burst 1500 pkt/sec during t=5-10s
 *
 * Outputs:
 *   flowmon.xml    — FlowMonitor metrics
 *   animation.xml  — NetAnim visualization
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/netanim-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/ipv4-static-routing-helper.h"
#include "ns3/ipv4-static-routing.h"
#include <fstream>
#include <map>
#include <queue>
#include <algorithm>
#include <limits>

using namespace ns3;


// ============================================================
// Phase 4: Adaptive Routing State
// ============================================================
std::map<double, std::map<std::pair<int, int>, double>> g_mlCosts;
std::vector<int> g_currentPath = {0, 1, 2, 3, 4, 5, 6, 7};
double g_previousPathCost = 0.0;
std::string g_scenarioName;
NodeContainer* g_nodesPtr = nullptr;
Ipv4InterfaceContainer* g_interfacesPtr = nullptr;
std::map<std::pair<int, int>, Ipv4Address> g_nextHopIps;
std::map<std::pair<int, int>, uint32_t> g_outInterfaces;
const double THRESHOLD_ALPHA = 0.15;
bool g_mlCostsLoaded = false;  // True if external ML costs were loaded
AnimationInterface* g_anim = nullptr; // Global pointer for NetAnim updates

// ── Inline Cost Computation (mimics the ML model) ─────────────────────
// Uses the same philosophy as the RandomForest training data:
//   Healthy:          cost ≈ 10–50
//   Mild congestion:  cost ≈ 100–400
//   Severe congestion: cost ≈ 800–1500
//   Failed (dead):    cost = 9999
double ComputeInlineCost(double queueUtil, double delayMs, double packetLoss,
                         double throughputMbps, double prevThroughputMbps) {
    // Dead link detection: throughput dropped to 0 from a previously active link
    if (throughputMbps == 0.0 && prevThroughputMbps > 0.0) {
        return 9999.0;
    }
    // Weighted cost formula matching the ML training philosophy
    double cost = 10.0
                + (queueUtil * 1000.0)        // queue pressure
                + (delayMs * 5.0)             // latency penalty
                + (packetLoss * 5000.0);      // loss penalty
    if (cost < 10.0) cost = 10.0;
    return cost;
}

// Routing decision log — collected in memory, exported at end
struct RoutingDecision {
    double timestamp;
    std::vector<int> currentPath;
    double currentCost;
    double baselineCost;
    double thresholdRatio;
    bool thresholdBreached;
    bool rerouted;
    std::vector<int> dijkstraPath;
    double dijkstraCost;
    std::string action;
};
std::vector<RoutingDecision> g_routingDecisions;

void LoadRoutingCosts(const std::string& scenario) {
    std::string path = "/home/shreyasplays/CloudRouteAI/outputs/ml/costs.json";
    std::ifstream ifs(path);
    if (!ifs.is_open()) {
        std::cerr << "  [INFO] No pre-computed ML costs found. Using INLINE cost computation for real-time rerouting." << std::endl;
        g_mlCostsLoaded = false;
        return;
    }
    std::string line;
    double current_ts = 0;
    int src = -1, dst = -1;
    while (std::getline(ifs, line)) {
        if (line.find("\"timestamp\":") != std::string::npos) {
            size_t pos = line.find(":");
            size_t comma = line.find(",");
            current_ts = std::stod(line.substr(pos+1, comma - pos - 1));
        } else if (line.find("\"source\":") != std::string::npos) {
            size_t pos = line.find(":");
            size_t comma = line.find(",");
            src = std::stoi(line.substr(pos+1, comma - pos - 1));
        } else if (line.find("\"destination\":") != std::string::npos) {
            size_t pos = line.find(":");
            size_t comma = line.find(",");
            dst = std::stoi(line.substr(pos+1, comma - pos - 1));
        } else if (line.find("\"routing_cost\":") != std::string::npos) {
            size_t pos = line.find(":");
            std::string valStr = line.substr(pos+1);
            valStr.erase(std::remove_if(valStr.begin(), valStr.end(), ::isspace), valStr.end());
            if (!valStr.empty() && valStr.back() == ',') valStr.pop_back();
            double cost = std::stod(valStr);
            if (src != -1 && dst != -1) {
                g_mlCosts[current_ts][{src, dst}] = cost;
            }
            src = -1; dst = -1;
        }
    }
    g_mlCostsLoaded = true;
    std::cout << "  [ML] Pre-computed costs loaded from " << path << std::endl;
}

double CalculatePathCost(double timestamp, const std::vector<int>& path) {
    if (g_mlCosts.find(timestamp) == g_mlCosts.end()) return 0;
    auto& costs = g_mlCosts[timestamp];
    double total = 0;
    for (size_t i = 0; i < path.size() - 1; i++) {
        if (costs.find({path[i], path[i+1]}) != costs.end()) {
            total += costs[{path[i], path[i+1]}];
        } else {
            total += 9999.0;
        }
    }
    return total;
}

std::vector<int> RunDijkstra(double timestamp) {
    auto& costs = g_mlCosts[timestamp];
    std::vector<double> dist(11, 999999.0);
    std::vector<int> prev(11, -1);
    dist[0] = 0;
    std::priority_queue<std::pair<double, int>, std::vector<std::pair<double, int>>, std::greater<std::pair<double, int>>> pq;
    pq.push({0, 0});
    
    while (!pq.empty()) {
        double d = pq.top().first;
        int u = pq.top().second;
        pq.pop();
        if (d > dist[u]) continue;
        if (u == 7) break;
        for (const auto& kv : costs) {
            if (kv.first.first == u) {
                int v = kv.first.second;
                double weight = kv.second;
                if (dist[u] + weight < dist[v]) {
                    dist[v] = dist[u] + weight;
                    prev[v] = u;
                    pq.push({dist[v], v});
                }
            }
        }
    }
    std::vector<int> path;
    int curr = 7;
    while (curr != -1) {
        path.push_back(curr);
        curr = prev[curr];
    }
    std::reverse(path.begin(), path.end());
    if (path.empty() || path[0] != 0) return g_currentPath;
    return path;
}

// Install explicit static host routes for a given path (removes old ones first)
void InstallPathRoutes(const std::vector<int>& path) {
    Ipv4Address destIp = g_interfacesPtr[6].GetAddress(1); // Node 7 IP
    Ipv4StaticRoutingHelper ipv4RoutingHelper;

    // Clear ALL existing host routes to destIp on ALL 10 nodes
    for (uint32_t n = 0; n < 10; n++) {
        Ptr<Ipv4> ipv4 = g_nodesPtr->Get(n)->GetObject<Ipv4>();
        Ptr<Ipv4StaticRouting> sr = ipv4RoutingHelper.GetStaticRouting(ipv4);
        for (uint32_t r = 0; r < sr->GetNRoutes(); ) {
            Ipv4RoutingTableEntry entry = sr->GetRoute(r);
            if (entry.GetDest() == destIp &&
                entry.GetDestNetworkMask() == Ipv4Mask("255.255.255.255")) {
                sr->RemoveRoute(r);
            } else {
                r++;
            }
        }
    }

    // Install new host routes for every hop in the path
    for (size_t i = 0; i < path.size() - 1; i++) {
        int u = path[i];
        int v = path[i + 1];
        Ptr<Ipv4> ipv4 = g_nodesPtr->Get(u)->GetObject<Ipv4>();
        Ptr<Ipv4StaticRouting> sr = ipv4RoutingHelper.GetStaticRouting(ipv4);
        uint32_t outIf = g_outInterfaces[{u, v}];
        Ipv4Address nextHop = g_nextHopIps[{u, v}];
        sr->AddHostRouteTo(destIp, nextHop, outIf);
    }
}

void UpdateRoutes(const std::vector<int>& newPath, double timestamp, double pathCost) {
    // Install the new path routes
    InstallPathRoutes(newPath);

    // Visually highlight the new path in NetAnim
    if (g_anim) {
        // Mark failed-path nodes back to default
        g_anim->UpdateNodeColor(g_nodesPtr->Get(3), 255, 0, 0);   // Node 3: red (failed)
        g_anim->UpdateNodeDescription(g_nodesPtr->Get(3), "N4-FAILED");

        // Highlight alternate-path nodes
        g_anim->UpdateNodeColor(g_nodesPtr->Get(8), 0, 255, 0);   // bright green
        g_anim->UpdateNodeColor(g_nodesPtr->Get(9), 0, 255, 0);
        g_anim->UpdateNodeColor(g_nodesPtr->Get(2), 0, 255, 255); // cyan junction
        g_anim->UpdateNodeSize(g_nodesPtr->Get(8), 6.0, 6.0);
        g_anim->UpdateNodeSize(g_nodesPtr->Get(9), 6.0, 6.0);
    }

    std::cout << "  [REROUTE] t=" << timestamp << "s | Path updated to: ";
    for (size_t i = 0; i < newPath.size(); i++) {
        std::cout << newPath[i] << (i < newPath.size()-1 ? "->" : "");
    }
    std::cout << " (Cost: " << pathCost << ")" << std::endl;
}

void AdaptiveRoutingController() {
    double now = Simulator::Now().GetSeconds();
    if (g_mlCosts.find(now) == g_mlCosts.end()) {
        if (now + 2.0 <= 20.0) Simulator::Schedule(Seconds(2.0), &AdaptiveRoutingController);
        return;
    }
    
    double currentPathCost = CalculatePathCost(now, g_currentPath);
    bool needsReroute = false;
    
    if (g_previousPathCost == 0.0) {
        g_previousPathCost = currentPathCost;
    } else {
        if (currentPathCost > g_previousPathCost * (1.0 + THRESHOLD_ALPHA)) {
            needsReroute = true;
        }
    }
    if (currentPathCost < g_previousPathCost) {
        g_previousPathCost = currentPathCost;
    }
    
    // Always run Dijkstra so we can log what it would choose
    std::vector<int> bestPath = RunDijkstra(now);
    double bestPathCost = CalculatePathCost(now, bestPath);
    double thresholdRatio = (g_previousPathCost > 0) ? currentPathCost / g_previousPathCost : 1.0;
    
    RoutingDecision decision;
    decision.timestamp = now;
    decision.currentPath = g_currentPath;
    decision.currentCost = currentPathCost;
    decision.baselineCost = g_previousPathCost;
    decision.thresholdRatio = thresholdRatio;
    decision.thresholdBreached = needsReroute;
    decision.dijkstraPath = bestPath;
    decision.dijkstraCost = bestPathCost;
    decision.rerouted = false;
    decision.action = "STABLE";
    
    if (needsReroute) {
        if (bestPath != g_currentPath) {
            UpdateRoutes(bestPath, now, bestPathCost);
            g_currentPath = bestPath;
            g_previousPathCost = bestPathCost;
            decision.rerouted = true;
            decision.action = "REROUTED";
        } else {
            g_previousPathCost = currentPathCost;
            decision.action = "THRESHOLD_BREACHED_NO_BETTER_PATH";
        }
    }
    
    g_routingDecisions.push_back(decision);
    
    // Console log for every evaluation
    std::cout << "  [ROUTING] t=" << now << "s | Cost=" << currentPathCost
              << " Baseline=" << g_previousPathCost
              << " Ratio=" << thresholdRatio
              << " Action=" << decision.action << std::endl;
    
    if (now + 2.0 <= 20.0) Simulator::Schedule(Seconds(2.0), &AdaptiveRoutingController);
}

void ExportRoutingDecisions() {
    std::string outPath = "/home/shreyasplays/CloudRouteAI/outputs/routing/routing.json";
    
    // Read existing decisions if file exists
    std::vector<std::string> existingEntries;
    {
        std::ifstream ifs(outPath);
        if (ifs.is_open()) {
            std::string content((std::istreambuf_iterator<char>(ifs)), std::istreambuf_iterator<char>());
            ifs.close();
            // Find existing entries between [ and ]
            // We'll just overwrite with all decisions for this run
        }
    }
    
    std::ofstream ofs(outPath);
    if (!ofs.is_open()) {
        std::cerr << "  [WARNING] Cannot write routing decisions to " << outPath << std::endl;
        return;
    }
    
    ofs << "{\n";
    ofs << "  \"scenario\": \"" << g_scenarioName << "\",\n";
    ofs << "  \"threshold_alpha\": " << THRESHOLD_ALPHA << ",\n";
    ofs << "  \"total_evaluations\": " << g_routingDecisions.size() << ",\n";
    ofs << "  \"decisions\": [\n";
    
    for (size_t d = 0; d < g_routingDecisions.size(); d++) {
        const RoutingDecision& dec = g_routingDecisions[d];
        ofs << "    {\n";
        ofs << "      \"timestamp\": " << dec.timestamp << ",\n";
        ofs << "      \"action\": \"" << dec.action << "\",\n";
        ofs << "      \"current_path\": [";
        for (size_t i = 0; i < dec.currentPath.size(); i++) {
            ofs << dec.currentPath[i] << (i < dec.currentPath.size()-1 ? "," : "");
        }
        ofs << "],\n";
        ofs << "      \"current_cost\": " << dec.currentCost << ",\n";
        ofs << "      \"baseline_cost\": " << dec.baselineCost << ",\n";
        ofs << "      \"threshold_ratio\": " << dec.thresholdRatio << ",\n";
        ofs << "      \"threshold_breached\": " << (dec.thresholdBreached ? "true" : "false") << ",\n";
        ofs << "      \"dijkstra_best_path\": [";
        for (size_t i = 0; i < dec.dijkstraPath.size(); i++) {
            ofs << dec.dijkstraPath[i] << (i < dec.dijkstraPath.size()-1 ? "," : "");
        }
        ofs << "],\n";
        ofs << "      \"dijkstra_best_cost\": " << dec.dijkstraCost << ",\n";
        ofs << "      \"rerouted\": " << (dec.rerouted ? "true" : "false") << "\n";
        ofs << "    }";
        if (d + 1 < g_routingDecisions.size()) ofs << ",";
        ofs << "\n";
    }
    ofs << "  ]\n}\n";
    ofs.close();
    std::cout << "  [EXPORT] Routing decisions written to " << outPath
              << " (" << g_routingDecisions.size() << " evaluations)" << std::endl;
}

// ============================================================
// Phase 2: Runtime Monitoring Infrastructure
// ============================================================

struct LinkInfo {
    int srcNode;
    int dstNode;
    double capacityBps;
    double delayMs;
};

// 11 links — same order as devices[0..10]
const int NUM_LINKS = 11;
const LinkInfo LINK_TABLE[11] = {
    {0, 1, 10e6, 2.0},   // link 0: primary 0-1
    {1, 2, 10e6, 2.0},   // link 1: primary 1-2
    {2, 3, 10e6, 2.0},   // link 2: primary 2-3
    {3, 4, 10e6, 2.0},   // link 3: primary 3-4  (overridden in congestion)
    {4, 5, 10e6, 2.0},   // link 4: primary 4-5
    {5, 6, 10e6, 2.0},   // link 5: primary 5-6
    {6, 7, 10e6, 2.0},   // link 6: primary 6-7
    {2, 8,  5e6, 5.0},   // link 7: alt 2-8
    {8, 9,  5e6, 5.0},   // link 8: alt 8-9
    {9, 4,  5e6, 5.0},   // link 9: alt 9-4
    {10, 3, 10e6, 2.0},  // link 10: congestion endpoint 10-3
};

struct LinkCounters {
    uint64_t txBytes = 0;
    uint64_t dropCount = 0;
    uint64_t prevTxBytes = 0;
    uint64_t prevDropCount = 0;
};

LinkCounters g_linkCounters[11];

static void
MacTxCallback (uint32_t linkIndex, Ptr<const Packet> p)
{
    g_linkCounters[linkIndex].txBytes += p->GetSize ();
}

static void
QueueDropCallback (uint32_t linkIndex, Ptr<const Packet> p)
{
    g_linkCounters[linkIndex].dropCount++;
}

struct LinkSnapshot {
    int source;
    int destination;
    double delay_ms;
    double throughput_mbps;
    double packet_loss;
    double queue_utilization;
    double link_utilization;
    uint32_t queue_packets;
    uint32_t queue_max;
};

struct MonitoringSnapshot {
    double timestamp;
    std::vector<LinkSnapshot> links;
};

std::vector<MonitoringSnapshot> g_snapshots;
NetDeviceContainer* g_devices = nullptr;
double g_monitoringInterval = 2.0;
double g_simDuration = 20.0;
double g_linkCapacity[11];

static void
CollectMetrics ()
{
    double now = Simulator::Now ().GetSeconds ();
    MonitoringSnapshot snapshot;
    snapshot.timestamp = now;

    for (int i = 0; i < NUM_LINKS; i++)
    {
        LinkSnapshot ls;
        ls.source = LINK_TABLE[i].srcNode;
        ls.destination = LINK_TABLE[i].dstNode;

        // Queue monitoring
        Ptr<NetDevice> dev = g_devices[i].Get (0);
        Ptr<PointToPointNetDevice> p2pDev = DynamicCast<PointToPointNetDevice> (dev);
        Ptr<Queue<Packet>> queue = p2pDev->GetQueue ();

        ls.queue_packets = queue->GetCurrentSize ().GetValue ();
        ls.queue_max = queue->GetMaxSize ().GetValue ();
        ls.queue_utilization = (ls.queue_max > 0) ? (double)ls.queue_packets / ls.queue_max : 0.0;

        // Throughput & link utilization
        uint64_t bytesDelta = g_linkCounters[i].txBytes - g_linkCounters[i].prevTxBytes;
        double throughputBps = (bytesDelta * 8.0) / g_monitoringInterval;
        ls.throughput_mbps = throughputBps / 1e6;
        ls.link_utilization = (g_linkCapacity[i] > 0) ? throughputBps / g_linkCapacity[i] : 0.0;
        if (ls.link_utilization > 1.0) ls.link_utilization = 1.0;

        // Packet loss
        uint64_t dropDelta = g_linkCounters[i].dropCount - g_linkCounters[i].prevDropCount;
        uint64_t estPackets = (bytesDelta > 0) ? bytesDelta / 1024 + dropDelta : dropDelta;
        ls.packet_loss = (estPackets > 0) ? (double)dropDelta / estPackets : 0.0;

        // Delay estimate
        double queueDelayMs = 0.0;
        if (g_linkCapacity[i] > 0 && ls.queue_packets > 0)
        {
            queueDelayMs = (ls.queue_packets * 1024.0 * 8.0 / g_linkCapacity[i]) * 1000.0;
        }
        ls.delay_ms = LINK_TABLE[i].delayMs + queueDelayMs;

        g_linkCounters[i].prevTxBytes = g_linkCounters[i].txBytes;
        g_linkCounters[i].prevDropCount = g_linkCounters[i].dropCount;

        // Inline cost computation for real-time routing (if ML costs not loaded)
        if (!g_mlCostsLoaded) {
            double prevThroughput = 0.0;
            if (!g_snapshots.empty()) {
                prevThroughput = g_snapshots.back().links[i].throughput_mbps;
            }
            double cost = ComputeInlineCost(ls.queue_utilization, ls.delay_ms, ls.packet_loss, ls.throughput_mbps, prevThroughput);
            g_mlCosts[now][{ls.source, ls.destination}] = cost;
        }

        snapshot.links.push_back (ls);
    }

    g_snapshots.push_back (snapshot);

    std::cout << "  [MONITOR] t=" << now << "s | ";
    if (snapshot.links.size () > 3)
    {
        std::cout << "Link 3->4: queue=" << snapshot.links[3].queue_packets << "/" << snapshot.links[3].queue_max
                  << " throughput=" << snapshot.links[3].throughput_mbps << "Mbps loss=" << snapshot.links[3].packet_loss;
    }
    std::cout << std::endl;

    if (now + g_monitoringInterval <= g_simDuration)
    {
        Simulator::Schedule (Seconds (g_monitoringInterval), &CollectMetrics);
    }
}

static void
ExportRuntimeMetrics (const std::string& scenario)
{
    std::ofstream ofs ("runtime_metrics.json");
    ofs << "{\n";
    ofs << "  \"version\": \"1.0\",\n";
    ofs << "  \"scenario_id\": \"" << scenario << "\",\n";
    ofs << "  \"monitoring_interval_sec\": " << g_monitoringInterval << ",\n";
    ofs << "  \"num_snapshots\": " << g_snapshots.size () << ",\n";
    ofs << "  \"snapshots\": [\n";

    for (size_t s = 0; s < g_snapshots.size (); s++)
    {
        ofs << "    {\n";
        ofs << "      \"timestamp\": " << g_snapshots[s].timestamp << ",\n";
        ofs << "      \"links\": [\n";

        for (size_t l = 0; l < g_snapshots[s].links.size (); l++)
        {
            const LinkSnapshot& ls = g_snapshots[s].links[l];
            ofs << "        {\n";
            ofs << "          \"source\": " << ls.source << ",\n";
            ofs << "          \"destination\": " << ls.destination << ",\n";
            ofs << "          \"delay_ms\": " << ls.delay_ms << ",\n";
            ofs << "          \"throughput_mbps\": " << ls.throughput_mbps << ",\n";
            ofs << "          \"packet_loss\": " << ls.packet_loss << ",\n";
            ofs << "          \"queue_utilization\": " << ls.queue_utilization << ",\n";
            ofs << "          \"link_utilization\": " << ls.link_utilization << ",\n";
            ofs << "          \"queue_packets\": " << ls.queue_packets << ",\n";
            ofs << "          \"queue_max\": " << ls.queue_max << "\n";
            ofs << "        }";
            if (l + 1 < g_snapshots[s].links.size ()) ofs << ",";
            ofs << "\n";
        }
        ofs << "      ]\n";
        ofs << "    }";
        if (s + 1 < g_snapshots.size ()) ofs << ",";
        ofs << "\n";
    }
    ofs << "  ]\n";
    ofs << "}\n";
    ofs.close ();

    std::cout << "  [EXPORT] runtime_metrics.json written (" << g_snapshots.size () << " snapshots)" << std::endl;
}

// ============================================================
// Link Failure Helper
// ============================================================

static uint32_t g_ifIndex_node3 = 0;
static uint32_t g_ifIndex_node4 = 0;

// Immediate failover: bring link down AND reroute in one atomic step
static void
ImmediateFailover ()
{
    double now = Simulator::Now().GetSeconds();
    std::cout << "  [EVENT] === LINK FAILURE at t=" << now << "s ===" << std::endl;

    // 1. Bring both interfaces DOWN
    Ptr<Ipv4> ipv4_3 = g_nodesPtr->Get(3)->GetObject<Ipv4>();
    ipv4_3->SetDown(g_ifIndex_node3);
    std::cout << "  [EVENT] Node 3 interface " << g_ifIndex_node3 << " set DOWN" << std::endl;

    Ptr<Ipv4> ipv4_4 = g_nodesPtr->Get(4)->GetObject<Ipv4>();
    ipv4_4->SetDown(g_ifIndex_node4);
    std::cout << "  [EVENT] Node 4 interface " << g_ifIndex_node4 << " set DOWN" << std::endl;

    // 2. Immediately install alternate-path routes
    std::vector<int> altPath = {0, 1, 2, 8, 9, 4, 5, 6, 7};
    InstallPathRoutes(altPath);

    // 3. Also recompute global routing so it agrees with our static routes
    Ipv4GlobalRoutingHelper::RecomputeRoutingTables();

    // 4. Update adaptive routing state
    g_currentPath = altPath;
    g_previousPathCost = 0.0; // reset baseline for new path

    // 5. Inject failure cost into inline cost map so controller stays in sync
    g_mlCosts[now][{3, 4}] = 9999.0;

    // 6. Visual feedback in NetAnim
    if (g_anim) {
        g_anim->UpdateNodeColor(g_nodesPtr->Get(3), 255, 0, 0);
        g_anim->UpdateNodeDescription(g_nodesPtr->Get(3), "N4-FAILED");
        g_anim->UpdateNodeColor(g_nodesPtr->Get(8), 0, 255, 0);
        g_anim->UpdateNodeColor(g_nodesPtr->Get(9), 0, 255, 0);
        g_anim->UpdateNodeColor(g_nodesPtr->Get(2), 0, 255, 255);
        g_anim->UpdateNodeSize(g_nodesPtr->Get(8), 6.0, 6.0);
        g_anim->UpdateNodeSize(g_nodesPtr->Get(9), 6.0, 6.0);
    }

    // 7. Log the routing decision
    RoutingDecision decision;
    decision.timestamp = now;
    decision.currentPath = {0,1,2,3,4,5,6,7};
    decision.currentCost = 9999.0;
    decision.baselineCost = 0;
    decision.thresholdRatio = 99.0;
    decision.thresholdBreached = true;
    decision.dijkstraPath = altPath;
    decision.dijkstraCost = 0;
    decision.rerouted = true;
    decision.action = "IMMEDIATE_FAILOVER";
    g_routingDecisions.push_back(decision);

    std::cout << "  [REROUTE] t=" << now << "s | IMMEDIATE failover to: 0->1->2->8->9->4->5->6->7" << std::endl;
}

// ============================================================
// Main Simulation
// ============================================================

int
main (int argc, char *argv[])
{
    // --------------------------------------------------------
    // 1. Parse command-line scenario selection
    // --------------------------------------------------------
    std::string scenario = "normal";
    bool adaptiveEnabled = true;

    CommandLine cmd;
    cmd.AddValue ("scenario", "Scenario type: normal|congestion|failure|spike", scenario);
    cmd.AddValue ("adaptive", "Enable adaptive routing (true/false)", adaptiveEnabled);
    cmd.Parse (argc, argv);

    std::cout << "========================================" << std::endl;
    std::cout << "  CloudRouteAI — Phase 1 Simulation" << std::endl;
    std::cout << "  Scenario: " << scenario << std::endl;
    std::cout << "========================================" << std::endl;

    // --------------------------------------------------------
    // 2. Base configuration constants
    // --------------------------------------------------------
    // These are the defaults shared by ALL scenarios.
    // Individual scenarios override ONLY what they need.

    const uint32_t NUM_NODES         = 11;
    const double   SIM_DURATION      = 20.0;   // seconds

    // Primary path link defaults
    const std::string PRIMARY_BW     = "10Mbps";
    const std::string PRIMARY_DELAY  = "2ms";
    const uint32_t    PRIMARY_QUEUE   = 100;     // packets

    // Alternate path link defaults
    const std::string ALT_BW         = "5Mbps";
    const std::string ALT_DELAY      = "5ms";
    const uint32_t    ALT_QUEUE       = 100;     // packets

    // Traffic defaults
    const uint32_t PACKET_SIZE       = 1024;    // bytes
    const uint32_t DEFAULT_PKT_RATE  = 200;     // packets/sec
    const uint16_t PORT              = 9;

    // --------------------------------------------------------
    // 3. Create nodes
    // --------------------------------------------------------
    NodeContainer nodes;
    nodes.Create (NUM_NODES);

    // --------------------------------------------------------
    // 4. Install Internet stack
    // --------------------------------------------------------
    InternetStackHelper stack;
    stack.Install (nodes);

    // --------------------------------------------------------
    // 5. Define link helpers
    // --------------------------------------------------------

    // Primary path helper (default: 10 Mbps, 2ms, 100p queue)
    PointToPointHelper primaryP2P;
    primaryP2P.SetDeviceAttribute ("DataRate", StringValue (PRIMARY_BW));
    primaryP2P.SetChannelAttribute ("Delay", StringValue (PRIMARY_DELAY));
    primaryP2P.SetQueue ("ns3::DropTailQueue", "MaxSize",
                         StringValue (std::to_string (PRIMARY_QUEUE) + "p"));

    // Alternate path helper (default: 5 Mbps, 5ms, 100p queue)
    PointToPointHelper altP2P;
    altP2P.SetDeviceAttribute ("DataRate", StringValue (ALT_BW));
    altP2P.SetChannelAttribute ("Delay", StringValue (ALT_DELAY));
    altP2P.SetQueue ("ns3::DropTailQueue", "MaxSize",
                     StringValue (std::to_string (ALT_QUEUE) + "p"));

    // Congestion bottleneck helper — used ONLY in congestion scenario for link 3-4
    PointToPointHelper bottleneckP2P;
    bottleneckP2P.SetDeviceAttribute ("DataRate", StringValue ("1Mbps"));
    bottleneckP2P.SetChannelAttribute ("Delay", StringValue ("10ms"));
    bottleneckP2P.SetQueue ("ns3::DropTailQueue", "MaxSize",
                            StringValue ("20p"));

    // --------------------------------------------------------
    // 6. Install point-to-point links
    // --------------------------------------------------------
    // Primary path: 7 links (0-1, 1-2, 2-3, 3-4, 4-5, 5-6, 6-7)
    // Alternate path: 3 links (2-8, 8-9, 9-4)
    // Total: 10 links

    NetDeviceContainer devices[11];
    // Index mapping:
    //   0: link 0-1   (primary)
    //   1: link 1-2   (primary)
    //   2: link 2-3   (primary)
    //   3: link 3-4   (primary — or bottleneck in congestion)
    //   4: link 4-5   (primary)
    //   5: link 5-6   (primary)
    //   6: link 6-7   (primary)
    //   7: link 2-8   (alternate)
    //   8: link 8-9   (alternate)
    //   9: link 9-4   (alternate)

    // --- Primary path links ---
    devices[0] = primaryP2P.Install (nodes.Get (0), nodes.Get (1));  // 0-1
    devices[1] = primaryP2P.Install (nodes.Get (1), nodes.Get (2));  // 1-2
    devices[2] = primaryP2P.Install (nodes.Get (2), nodes.Get (3));  // 2-3

    // Link 3-4: use bottleneck config in congestion scenario, primary otherwise
    if (scenario == "congestion")
    {
        devices[3] = bottleneckP2P.Install (nodes.Get (3), nodes.Get (4));  // 3-4 bottleneck
        std::cout << "  [CONFIG] Link 3-4: 1Mbps, 10ms, 20p queue (bottleneck)" << std::endl;
    }
    else
    {
        devices[3] = primaryP2P.Install (nodes.Get (3), nodes.Get (4));  // 3-4 normal
    }

    devices[4] = primaryP2P.Install (nodes.Get (4), nodes.Get (5));  // 4-5
    devices[5] = primaryP2P.Install (nodes.Get (5), nodes.Get (6));  // 5-6
    devices[6] = primaryP2P.Install (nodes.Get (6), nodes.Get (7));  // 6-7

    // --- Alternate path links ---
    devices[7] = altP2P.Install (nodes.Get (2), nodes.Get (8));      // 2-8 (spec: 3-9)
    devices[8] = altP2P.Install (nodes.Get (8), nodes.Get (9));      // 8-9 (spec: 9-10)
    devices[9] = altP2P.Install (nodes.Get (9), nodes.Get (4));      // 9-4 (spec: 10-5)
    devices[10] = primaryP2P.Install (nodes.Get (10), nodes.Get (3)); // 10-3 (congestion endpoint)

    // --------------------------------------------------------
    // 7. Assign IP addresses
    // --------------------------------------------------------
    // Each link gets its own /24 subnet: 10.1.{1..10}.0

    Ipv4AddressHelper address;
    Ipv4InterfaceContainer interfaces[11];

    for (int i = 0; i < 11; i++)
    {
        std::ostringstream subnet;
        subnet << "10.1." << (i + 1) << ".0";
        address.SetBase (subnet.str ().c_str (), "255.255.255.0");
        interfaces[i] = address.Assign (devices[i]);
    }

    // --------------------------------------------------------
    // 8. Populate routing tables
    // --------------------------------------------------------
    // Use global routing for initial setup, then we override with static routes
    Ipv4GlobalRoutingHelper::PopulateRoutingTables ();

    g_scenarioName = scenario;
    g_nodesPtr = &nodes;
    g_interfacesPtr = interfaces;
    
    // Phase 4 Lookup Tables
    for (int i = 0; i < 11; i++) {
        int u = LINK_TABLE[i].srcNode;
        int v = LINK_TABLE[i].dstNode;
        Ptr<Ipv4> ipv4_u = nodes.Get(u)->GetObject<Ipv4>();
        for (uint32_t j = 1; j < ipv4_u->GetNInterfaces(); j++) {
            if (ipv4_u->GetAddress(j, 0).GetLocal() == interfaces[i].GetAddress(0)) {
                g_outInterfaces[{u, v}] = j;
                g_nextHopIps[{u, v}] = interfaces[i].GetAddress(1);
            }
        }
        Ptr<Ipv4> ipv4_v = nodes.Get(v)->GetObject<Ipv4>();
        for (uint32_t j = 1; j < ipv4_v->GetNInterfaces(); j++) {
            if (ipv4_v->GetAddress(j, 0).GetLocal() == interfaces[i].GetAddress(1)) {
                g_outInterfaces[{v, u}] = j;
                g_nextHopIps[{v, u}] = interfaces[i].GetAddress(0);
            }
        }
    }
    // Install explicit static routes for the primary path so
    // Ipv4StaticRouting (priority 0) controls routing instead of
    // Ipv4GlobalRouting (priority -10). This is critical for failover
    // to work — when we swap static routes, packets actually reroute.
    InstallPathRoutes(g_currentPath);
    std::cout << "  [ROUTING] Initial static routes installed for primary path: 0->1->2->3->4->5->6->7" << std::endl;

    LoadRoutingCosts(scenario);
    if (adaptiveEnabled) {
        Simulator::Schedule(Seconds(2.0), &AdaptiveRoutingController);
    }
    

    // --------------------------------------------------------
    // Phase 2: Connect trace callbacks
    // --------------------------------------------------------
    g_devices = devices;  // store global reference

    for (int i = 0; i < NUM_LINKS; i++)
    {
        // Set actual link capacity (default from LINK_TABLE)
        g_linkCapacity[i] = LINK_TABLE[i].capacityBps;

        // Connect MacTx trace on src-side device
        devices[i].Get(0)->TraceConnectWithoutContext(
            "MacTx", MakeBoundCallback(&MacTxCallback, (uint32_t)i));

        // Connect Drop trace on src-side device's queue
        Ptr<PointToPointNetDevice> p2pDev = DynamicCast<PointToPointNetDevice>(devices[i].Get(0));
        p2pDev->GetQueue()->TraceConnectWithoutContext(
            "Drop", MakeBoundCallback(&QueueDropCallback, (uint32_t)i));
    }

    // Patch congestion link capacity
    if (scenario == "congestion")
    {
        g_linkCapacity[3] = 1e6;  // 1 Mbps bottleneck
    }

    // Schedule first monitoring callback
    g_monitoringInterval = 2.0;
    g_simDuration = SIM_DURATION;
    Simulator::Schedule(Seconds(g_monitoringInterval), &CollectMetrics);

    // --------------------------------------------------------
    // 9. Identify interface indices for link failure
    // --------------------------------------------------------
    // For the failure scenario, we need interface indices on nodes 3 and 4
    // for the link between them (devices[3]).
    //
    // devices[3].Get(0) is the NetDevice on node 3 (facing node 4)
    // devices[3].Get(1) is the NetDevice on node 4 (facing node 3)

    uint32_t ifIndex_node3_to_node4 = 0;
    uint32_t ifIndex_node4_to_node3 = 0;

    if (scenario == "failure")
    {
        // Find interface index on node 3 for the device facing node 4
        Ptr<Ipv4> ipv4_node3 = nodes.Get (3)->GetObject<Ipv4> ();
        for (uint32_t i = 1; i < ipv4_node3->GetNInterfaces (); i++)
        {
            if (ipv4_node3->GetNetDevice (i) == devices[3].Get (0))
            {
                ifIndex_node3_to_node4 = i;
                break;
            }
        }

        // Find interface index on node 4 for the device facing node 3
        Ptr<Ipv4> ipv4_node4 = nodes.Get (4)->GetObject<Ipv4> ();
        for (uint32_t i = 1; i < ipv4_node4->GetNInterfaces (); i++)
        {
            if (ipv4_node4->GetNetDevice (i) == devices[3].Get (1))
            {
                ifIndex_node4_to_node3 = i;
                break;
            }
        }

        std::cout << "  [CONFIG] Failure scheduled at t=8s on link 3-4" << std::endl;
        std::cout << "           Node3 ifIndex=" << ifIndex_node3_to_node4
                  << ", Node4 ifIndex=" << ifIndex_node4_to_node3 << std::endl;
    }

    // --------------------------------------------------------
    // 10. Configure traffic applications
    // --------------------------------------------------------

    // Destination address: Node 7's address on the link 6-7
    // interfaces[6].GetAddress(1) = Node 7's IP on subnet 10.1.7.0/24
    Ipv4Address destAddr = interfaces[6].GetAddress (1);

    std::cout << "  [CONFIG] Traffic: Node 0 -> Node 7 (" << destAddr << ")" << std::endl;

    // -- Packet sink on Node 7 --
    PacketSinkHelper sink ("ns3::UdpSocketFactory",
                           InetSocketAddress (Ipv4Address::GetAny (), PORT));
    ApplicationContainer sinkApp = sink.Install (nodes.Get (7));
    sinkApp.Start (Seconds (0.0));
    sinkApp.Stop (Seconds (SIM_DURATION));

    // -- Traffic source(s) on Node 0 --
    // Compute data rate from packet rate:
    //   rate_bps = packet_rate * packet_size * 8

    if (scenario == "normal")
    {
        // Normal: 200 pkt/sec * 1024 bytes = ~1.6 Mbps, continuous
        uint64_t dataRateBps = (uint64_t)DEFAULT_PKT_RATE * PACKET_SIZE * 8;
        OnOffHelper onoff ("ns3::UdpSocketFactory",
                           Address (InetSocketAddress (destAddr, PORT)));
        onoff.SetConstantRate (DataRate (dataRateBps), PACKET_SIZE);
        ApplicationContainer app = onoff.Install (nodes.Get (0));
        app.Start (Seconds (1.0));
        app.Stop (Seconds (SIM_DURATION));

        std::cout << "  [TRAFFIC] Normal: " << DEFAULT_PKT_RATE
                  << " pkt/sec, " << PACKET_SIZE << " bytes" << std::endl;
    }
    else if (scenario == "congestion")
    {
        // ── Congestion scenario ──
        // Node 10 sends high traffic through the main chain (10→3→4→...→7) starting at t=4.0
        // Node 0 sends normal traffic through the primary path initially

        // Node 0 traffic: normal rate through primary path
        uint64_t dataRateBps = (uint64_t)DEFAULT_PKT_RATE * PACKET_SIZE * 8;
        OnOffHelper onoff0 ("ns3::UdpSocketFactory",
                           Address (InetSocketAddress (destAddr, PORT)));
        onoff0.SetConstantRate (DataRate (dataRateBps), PACKET_SIZE);
        ApplicationContainer app0 = onoff0.Install (nodes.Get (0));
        app0.Start (Seconds (1.0));
        app0.Stop (Seconds (SIM_DURATION));

        // Node 10 traffic: high rate through main chain (10→3→4→5→6→7)
        // Install explicit static routes for Node 10's traffic
        {
            Ipv4StaticRoutingHelper srHelper;
            Ptr<Ipv4StaticRouting> sr10 = srHelper.GetStaticRouting(
                nodes.Get(10)->GetObject<Ipv4>());
            sr10->AddHostRouteTo(destAddr, g_nextHopIps[{10, 3}], g_outInterfaces[{10, 3}]);
        }

        uint32_t congestionPktRate = 800;
        uint64_t congRateBps = (uint64_t)congestionPktRate * PACKET_SIZE * 8;
        OnOffHelper onoff10 ("ns3::UdpSocketFactory",
                            Address (InetSocketAddress (destAddr, PORT)));
        onoff10.SetConstantRate (DataRate (congRateBps), PACKET_SIZE);
        ApplicationContainer app10 = onoff10.Install (nodes.Get (10));
        app10.Start (Seconds (4.0));
        app10.Stop (Seconds (SIM_DURATION));

        std::cout << "  [TRAFFIC] Congestion: Node 0 at " << DEFAULT_PKT_RATE
                  << " pkt/sec (primary path), Node 10 at " << congestionPktRate
                  << " pkt/sec starting t=4.0s" << std::endl;
    }
    else if (scenario == "failure")
    {
        // ── Failure scenario ──
        // Starts on primary path. Link 3-4 is FAILED at t=4.0s.
        std::cout << "  [EVENT] Link 3-4 failure scheduled for t=4.0s" << std::endl;

        // Save interface indices for the failover callback
        g_ifIndex_node3 = ifIndex_node3_to_node4;
        g_ifIndex_node4 = ifIndex_node4_to_node3;

        // Normal traffic from Node 0
        uint64_t dataRateBps = (uint64_t)DEFAULT_PKT_RATE * PACKET_SIZE * 8;
        OnOffHelper onoff ("ns3::UdpSocketFactory",
                           Address (InetSocketAddress (destAddr, PORT)));
        onoff.SetConstantRate (DataRate (dataRateBps), PACKET_SIZE);
        ApplicationContainer app = onoff.Install (nodes.Get (0));
        app.Start (Seconds (1.0));
        app.Stop (Seconds (SIM_DURATION));

        // Schedule the failure at t=4.0s
        Simulator::Schedule(Seconds(4.0), &ImmediateFailover);

        std::cout << "  [TRAFFIC] Failure: " << DEFAULT_PKT_RATE
                  << " pkt/sec, link 3-4 will fail at t=4.0s" << std::endl;
    }
    else if (scenario == "spike")
    {
        // Spike scenario — traffic rate changes over time:
        //   t=1-5s:   200 pkt/sec (baseline)
        //   t=5-10s: 1500 pkt/sec (burst)
        //   t=10-20s: 200 pkt/sec (recovery)
        //
        // Implementation: baseline app runs entire duration,
        // burst app adds extra traffic during t=5-10s
        //   Baseline: 200 pkt/sec from t=1s to t=20s
        //   Burst:   1300 pkt/sec from t=5s to t=10s (200+1300 = 1500 total)

        uint64_t baseRateBps  = (uint64_t)DEFAULT_PKT_RATE * PACKET_SIZE * 8;   // 200 pkt/sec
        uint64_t burstRateBps = (uint64_t)1300 * PACKET_SIZE * 8;               // 1300 pkt/sec extra

        // Baseline flow: entire simulation
        OnOffHelper baseOnoff ("ns3::UdpSocketFactory",
                               Address (InetSocketAddress (destAddr, PORT)));
        baseOnoff.SetConstantRate (DataRate (baseRateBps), PACKET_SIZE);
        ApplicationContainer baseApp = baseOnoff.Install (nodes.Get (0));
        baseApp.Start (Seconds (1.0));
        baseApp.Stop (Seconds (SIM_DURATION));

        // Burst flow: t=5s to t=10s
        OnOffHelper burstOnoff ("ns3::UdpSocketFactory",
                                Address (InetSocketAddress (destAddr, PORT)));
        burstOnoff.SetConstantRate (DataRate (burstRateBps), PACKET_SIZE);
        ApplicationContainer burstApp = burstOnoff.Install (nodes.Get (0));
        burstApp.Start (Seconds (5.0));
        burstApp.Stop (Seconds (10.0));

        std::cout << "  [TRAFFIC] Spike: 200 pkt/sec base + 1300 pkt/sec burst (t=5-10s)"
                  << std::endl;
    }
    else
    {
        std::cerr << "ERROR: Unknown scenario '" << scenario << "'" << std::endl;
        std::cerr << "Valid scenarios: normal, congestion, failure, spike" << std::endl;
        return 1;
    }

    // --------------------------------------------------------
    // 11. Install FlowMonitor
    // --------------------------------------------------------
    FlowMonitorHelper flowHelper;
    Ptr<FlowMonitor> monitor = flowHelper.InstallAll ();

    // --------------------------------------------------------
    // 12. Configure NetAnim
    // --------------------------------------------------------
    std::string animFile = "animation.xml";
    AnimationInterface anim (animFile);
    g_anim = &anim; // Set global pointer
    anim.EnablePacketMetadata(true); // Enable packet tracking for better visualization

    // Node positions — primary chain on y=30, alternate path on y=120 (Large gap for visibility)
    anim.SetConstantPosition (nodes.Get (0),   0.0,  30.0);   // Node 0 (spec: 1)
    anim.SetConstantPosition (nodes.Get (1),  20.0,  30.0);   // Node 1 (spec: 2)
    anim.SetConstantPosition (nodes.Get (2),  40.0,  30.0);   // Node 2 (spec: 3)
    anim.SetConstantPosition (nodes.Get (3),  60.0,  30.0);   // Node 3 (spec: 4)
    anim.SetConstantPosition (nodes.Get (4),  80.0,  30.0);   // Node 4 (spec: 5)
    anim.SetConstantPosition (nodes.Get (5), 100.0,  30.0);   // Node 5 (spec: 6)
    anim.SetConstantPosition (nodes.Get (6), 120.0,  30.0);   // Node 6 (spec: 7)
    anim.SetConstantPosition (nodes.Get (7), 140.0,  30.0);   // Node 7 (spec: 8)
    
    // Alternate Path Nodes
    anim.SetConstantPosition (nodes.Get (8),  50.0, 120.0);   // Node 8 (spec: 9)
    anim.SetConstantPosition (nodes.Get (9),  70.0, 120.0);   // Node 9 (spec: 10)

    // Congestion Endpoint Node (above Node 3)
    anim.SetConstantPosition (nodes.Get (10), 60.0, -40.0);   // Node 10 (congestion src)

    // Node descriptions
    anim.UpdateNodeDescription (nodes.Get (0), "N1-Src");
    anim.UpdateNodeDescription (nodes.Get (1), "N2");
    anim.UpdateNodeDescription (nodes.Get (2), "N3-Junction");
    anim.UpdateNodeDescription (nodes.Get (3), "N4-Primary");
    anim.UpdateNodeDescription (nodes.Get (4), "N5");
    anim.UpdateNodeDescription (nodes.Get (5), "N6");
    anim.UpdateNodeDescription (nodes.Get (6), "N7");
    anim.UpdateNodeDescription (nodes.Get (7), "N8-Dst");
    anim.UpdateNodeDescription (nodes.Get (8), "N9-Alternate");
    anim.UpdateNodeDescription (nodes.Get (9), "N10-Alternate");
    anim.UpdateNodeDescription (nodes.Get (10), "N11-CongSrc");

    // Node colors
    if (scenario != "normal") {
        anim.UpdateNodeColor (nodes.Get (0), 0, 200, 0);     // Source: green
        anim.UpdateNodeColor (nodes.Get (7), 200, 0, 0);     // Destination: red
        anim.UpdateNodeColor (nodes.Get (8), 255, 165, 0);   // Alt path: bright orange
        anim.UpdateNodeColor (nodes.Get (9), 255, 165, 0);   // Alt path: bright orange
        anim.UpdateNodeColor (nodes.Get (10), 0, 100, 255);  // Congestion source: blue
    } else {
        // Normal scenario: all nodes same color
        for (uint32_t i = 0; i < nodes.GetN(); i++) {
            anim.UpdateNodeColor (nodes.Get (i), 0, 0, 255); // Blue
        }
    }
    
    // Make key nodes slightly larger for visibility
    anim.UpdateNodeSize (nodes.Get(8), 5.0, 5.0);
    anim.UpdateNodeSize (nodes.Get(9), 5.0, 5.0);
    anim.UpdateNodeSize (nodes.Get(2), 5.0, 5.0); // Junction node

    // Scenario-specific visual highlighting
    if (scenario == "failure") {
        anim.UpdateNodeColor (nodes.Get(3), 255, 0, 0);   // Failed node: RED
        anim.UpdateNodeDescription (nodes.Get(3), "N4-FAILED");
        anim.UpdateNodeSize (nodes.Get(3), 6.0, 6.0);
        // Highlight active alternate path
        anim.UpdateNodeColor (nodes.Get(8), 0, 255, 0);   // Active alt: green
        anim.UpdateNodeColor (nodes.Get(9), 0, 255, 0);
        anim.UpdateNodeSize (nodes.Get(8), 6.0, 6.0);
        anim.UpdateNodeSize (nodes.Get(9), 6.0, 6.0);
    }
    if (scenario == "congestion") {
        anim.UpdateNodeColor (nodes.Get(10), 255, 100, 0); // Congestion src: orange
        anim.UpdateNodeSize (nodes.Get(10), 6.0, 6.0);
        // Highlight active alternate path for Node 0 traffic
        anim.UpdateNodeColor (nodes.Get(8), 0, 255, 0);
        anim.UpdateNodeColor (nodes.Get(9), 0, 255, 0);
        anim.UpdateNodeSize (nodes.Get(8), 6.0, 6.0);
        anim.UpdateNodeSize (nodes.Get(9), 6.0, 6.0);
    }

    // --------------------------------------------------------
    // 13. Run simulation
    // --------------------------------------------------------
    std::cout << std::endl << "Simulation Started..." << std::endl;

    Simulator::Stop (Seconds (SIM_DURATION));
    Simulator::Run ();

    // Phase 2: Export runtime metrics
    ExportRuntimeMetrics(scenario);
    ExportRoutingDecisions();

    // --------------------------------------------------------
    // 14. Export FlowMonitor metrics
    // --------------------------------------------------------
    monitor->SerializeToXmlFile ("flowmon.xml", true, true);

    // --------------------------------------------------------
    // 15. Print summary statistics
    // --------------------------------------------------------
    std::cout << std::endl << "--- FlowMonitor Summary ---" << std::endl;

    Ptr<Ipv4FlowClassifier> classifier =
        DynamicCast<Ipv4FlowClassifier> (flowHelper.GetClassifier ());
    FlowMonitor::FlowStatsContainer stats = monitor->GetFlowStats ();

    for (auto it = stats.begin (); it != stats.end (); ++it)
    {
        Ipv4FlowClassifier::FiveTuple ft = classifier->FindFlow (it->first);
        std::cout << "Flow " << it->first << " ("
                  << ft.sourceAddress << " -> " << ft.destinationAddress << ")"
                  << std::endl;
        std::cout << "  Tx Packets:   " << it->second.txPackets << std::endl;
        std::cout << "  Rx Packets:   " << it->second.rxPackets << std::endl;
        std::cout << "  Lost Packets: " << it->second.lostPackets << std::endl;

        if (it->second.rxPackets > 0)
        {
            double avgDelay = it->second.delaySum.GetSeconds () / it->second.rxPackets;
            double avgJitter = it->second.jitterSum.GetSeconds () / it->second.rxPackets;
            double throughput = it->second.rxBytes * 8.0 /
                                (it->second.timeLastRxPacket.GetSeconds () -
                                 it->second.timeFirstTxPacket.GetSeconds ()) / 1e6;

            std::cout << "  Avg Delay:    " << avgDelay * 1000.0 << " ms" << std::endl;
            std::cout << "  Avg Jitter:   " << avgJitter * 1000.0 << " ms" << std::endl;
            std::cout << "  Throughput:   " << throughput << " Mbps" << std::endl;
        }

        if (it->second.txPackets > 0)
        {
            double lossRate = (double)it->second.lostPackets / it->second.txPackets * 100.0;
            std::cout << "  Packet Loss:  " << lossRate << "%" << std::endl;
        }
        std::cout << std::endl;
    }

    // --------------------------------------------------------
    // 16. Cleanup
    // --------------------------------------------------------
    Simulator::Destroy ();

    std::cout << "========================================" << std::endl;
    std::cout << "  Simulation Finished!" << std::endl;
    std::cout << "  Outputs: flowmon.xml, " << animFile << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
