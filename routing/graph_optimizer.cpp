#include <cmath>

extern "C" double calculate_optimal_route(int* nodes, int node_count) {
    if (nodes == nullptr || node_count <= 0) {
        return 0.0;
    }

    double score = 0.0;
    for (int i = 0; i < node_count; ++i) {
        double value = static_cast<double>(nodes[i]);
        score += std::sqrt(value * 3.14) * 1.4;
    }

    // A placeholder scoring function for route optimization.
    return score;
}
