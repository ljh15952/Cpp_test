#pragma once

#include <atomic>
#include <condition_variable>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
#include <memory>
#include <mutex>
#include <thread>
#include <vector>

namespace aster {

class JobHandle {
public:
    JobHandle() = default;
    [[nodiscard]] bool IsComplete() const noexcept;

private:
    explicit JobHandle(std::shared_ptr<std::atomic_uint32_t> counter)
        : counter_(std::move(counter)) {}
    std::shared_ptr<std::atomic_uint32_t> counter_;
    friend class JobSystem;
};

class JobSystem {
public:
    explicit JobSystem(std::uint32_t workerCount = 0);
    ~JobSystem();

    JobSystem(const JobSystem&) = delete;
    JobSystem& operator=(const JobSystem&) = delete;

    JobHandle Dispatch(std::uint32_t count,
                       std::uint32_t groupSize,
                       std::function<void(std::uint32_t)> function);
    void Wait(const JobHandle& handle);
    [[nodiscard]] std::uint32_t WorkerCount() const noexcept;

private:
    struct Job {
        std::function<void()> function;
        std::shared_ptr<std::atomic_uint32_t> counter;
    };

    bool TryExecuteOne();
    void WorkerLoop();

    std::vector<std::thread> workers_;
    std::deque<Job> queue_;
    mutable std::mutex mutex_;
    std::condition_variable cv_;
    std::atomic_bool stopping_{false};
};

} // namespace aster
