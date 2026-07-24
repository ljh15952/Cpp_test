#include <iostream>
#include <vector>

int main() {
    std::vector<int> values{10};
    int* first = &values[0];

    for (int i = 0; i < 1000; ++i) {
        values.push_back(i);
    }

    // Intentional undefined behavior: vector growth may invalidate first.
    std::cout << *first << '\n';
}
