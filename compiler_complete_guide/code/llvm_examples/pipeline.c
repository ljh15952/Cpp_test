struct Pair {
    long left;
    long right;
};

long dot(struct Pair a, struct Pair b) {
    return a.left * b.left + a.right * b.right;
}

long sum_to(long n) {
    long result = 0;
    for (long i = 1; i <= n; ++i) {
        result += i;
    }
    return result;
}

int main(void) {
    struct Pair a = {2, 3};
    struct Pair b = {5, 7};
    return (int)(dot(a, b) + sum_to(10));
}
