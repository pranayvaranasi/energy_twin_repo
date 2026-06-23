#include <vector>
#include <queue>
#include <limits>
#include <unordered_set>
#include <utility>
#include <functional>

extern "C" double calculate_optimal_route(int* nodes, int node_count, int* disrupted_nodes, int disrupted_count) {
    if (nodes == nullptr || node_count <= 0) return 0.0;

    // Convert disrupted nodes array to a fast lookup set for penalty application
    std::unordered_set<int> high_risk_zones;
    if (disrupted_nodes != nullptr && disrupted_count > 0) {
        for(int i = 0; i < disrupted_count; ++i) {
            high_risk_zones.insert(disrupted_nodes[i]);
        }
    }

    // MOCK GRAPH: Adjacency list representing global supply routes (Cost/Time mapping)
    // 1: US Gulf, 2: West Africa, 3: Middle East, 4: Jamnagar Refinery (Destination), 5: Cape of Good Hope, 6: Red Sea/Suez
    const int GRAPH_SIZE = 7; 
    std::vector<std::vector<std::pair<int, double>>> adj(GRAPH_SIZE);

    adj[1].push_back({6, 12.0}); // US Gulf -> Red Sea
    adj[1].push_back({5, 18.0}); // US Gulf -> Cape of Good Hope
    adj[2].push_back({5, 10.0}); // West Africa -> Cape of Good Hope
    adj[3].push_back({6, 4.0});  // Middle East -> Red Sea
    adj[3].push_back({4, 6.0});  // Middle East -> Jamnagar (Direct pipeline/tanker)
    adj[5].push_back({4, 14.0}); // Cape of Good Hope -> Jamnagar
    adj[6].push_back({4, 8.0});  // Red Sea -> Jamnagar

    double best_overall_cost = std::numeric_limits<double>::infinity();

    // Run Dijkstra's from all available, undisrupted supply origins to find the absolute cheapest route
    for (int i = 0; i < node_count; ++i) {
        int start_node = nodes[i];
        if (start_node <= 0 || start_node >= GRAPH_SIZE || start_node == 4) continue;  // Validate bounds and skip destination 

        std::vector<double> min_cost(GRAPH_SIZE, std::numeric_limits<double>::infinity());
        std::priority_queue<std::pair<double, int>, std::vector<std::pair<double, int>>, std::greater<>> pq;

        min_cost[start_node] = 0;
        pq.push({0.0, start_node});

        while (!pq.empty()) {
            auto [current_cost, u] = pq.top();
            pq.pop();

            if (current_cost > min_cost[u]) continue;
            if (u == 4) break; // Destination reached

            for (auto& edge : adj[u]) {
                int v = edge.first;
                double weight = edge.second;

                // CRITICAL LOGIC: Apply massive mathematical penalty if route goes through a disrupted node
                if (high_risk_zones.count(v)) weight += 1000.0; 

                if (current_cost + weight < min_cost[v]) {
                    min_cost[v] = current_cost + weight;
                    pq.push({min_cost[v], v});
                }
            }
        }
        if (min_cost[4] < best_overall_cost) best_overall_cost = min_cost[4];
    }
    
    // Return -1.0 if all maritime routes are blocked (forces SPR reliance)
    return best_overall_cost >= 1000.0 ? -1.0 : best_overall_cost; 
}
