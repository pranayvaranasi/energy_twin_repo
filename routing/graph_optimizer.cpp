#include <vector>
#include <queue>
#include <limits>
#include <unordered_set>
#include <utility>
#include <functional>

extern "C" double calculate_optimal_route(
    int* nodes, int node_count,
    int* disrupted_nodes, int disrupted_count,
    int* edge_u, int* edge_v, double* edge_w, int edge_count,
    int target_node, int max_node_id
) {
    if (nodes == nullptr || node_count <= 0) return 0.0;

    std::unordered_set<int> high_risk_zones;
    if (disrupted_nodes != nullptr && disrupted_count > 0) {
        for (int i = 0; i < disrupted_count; ++i) {
            high_risk_zones.insert(disrupted_nodes[i]);
        }
    }

    int GRAPH_SIZE = max_node_id + 1;
    if (GRAPH_SIZE <= 0) return 0.0;
    std::vector<std::vector<std::pair<int, double>>> adj(GRAPH_SIZE);

    for (int i = 0; i < edge_count; ++i) {
        int u = edge_u[i];
        int v = edge_v[i];
        double w = edge_w[i];
        if (u >= 0 && u < GRAPH_SIZE && v >= 0 && v < GRAPH_SIZE) {
            adj[u].push_back({v, w});
        }
    }

    double best_overall_cost = std::numeric_limits<double>::infinity();

    for (int i = 0; i < node_count; ++i) {
        int start_node = nodes[i];
        if (start_node < 0 || start_node >= GRAPH_SIZE || start_node == target_node) continue;

        std::vector<double> min_cost(GRAPH_SIZE, std::numeric_limits<double>::infinity());
        std::priority_queue<std::pair<double, int>, std::vector<std::pair<double, int>>, std::greater<>> pq;

        min_cost[start_node] = 0;
        pq.push({0.0, start_node});

        while (!pq.empty()) {
            auto [current_cost, u] = pq.top();
            pq.pop();

            if (current_cost > min_cost[u]) continue;
            if (u == target_node) break;

            for (auto& edge : adj[u]) {
                int v = edge.first;
                double weight = edge.second;

                if (high_risk_zones.count(v)) weight += 10000.0;

                if (current_cost + weight < min_cost[v]) {
                    min_cost[v] = current_cost + weight;
                    pq.push({min_cost[v], v});
                }
            }
        }

        if (min_cost[target_node] < best_overall_cost) {
            best_overall_cost = min_cost[target_node];
        }
    }

    return best_overall_cost >= 10000.0 ? -1.0 : best_overall_cost;
}
