#pragma once

#include <algorithm>
#include <cmath>
#include <numeric>
#include <span>
#include <stdexcept>
#include <vector>

namespace cppbook {

inline double mean(std::span<const double> values) {
    if (values.empty()) {
        throw std::invalid_argument("mean requires non-empty input");
    }
    return std::accumulate(values.begin(), values.end(), 0.0) /
           static_cast<double>(values.size());
}

inline double percentile(std::span<const double> input, double p) {
    if (input.empty()) {
        throw std::invalid_argument("percentile requires non-empty input");
    }
    if (p < 0.0 || p > 1.0) {
        throw std::invalid_argument("percentile p must be within [0, 1]");
    }

    std::vector<double> values(input.begin(), input.end());
    std::sort(values.begin(), values.end());

    const double index = p * static_cast<double>(values.size() - 1U);
    const auto low = static_cast<std::size_t>(std::floor(index));
    const auto high = static_cast<std::size_t>(std::ceil(index));
    const double t = index - static_cast<double>(low);
    return values[low] * (1.0 - t) + values[high] * t;
}

} // namespace cppbook
