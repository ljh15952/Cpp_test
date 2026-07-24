#include <iostream>

int main() {
    int* value = new int{42};
    delete value;

    // Intentional undefined behavior for AddressSanitizer practice.
    std::cout << *value << '\n';
}
