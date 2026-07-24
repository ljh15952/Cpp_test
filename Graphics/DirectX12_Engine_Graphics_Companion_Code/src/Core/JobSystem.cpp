#include "Aster/Core/JobSystem.hpp"

#include <algorithm>
#include <stdexcept>

namespace aster {

bool JobHandle::IsComplete() const noexcept
{
    return !counter_ || counter_->load(std::memory_order_acquire) == 0;
}

JobSystem::JobSystem(std::uint32_t workerCount)
{
    if (workerCount == 0) {
        const auto hardware = std::max(1u, std::thread::hardware_concurrency());
        workerCount = hardware > 1 ? hardware - 1 : 1;
    }
    workers_.reserve(workerCount);
    for (std::uint32_t i = 0; i < workerCount; ++i) {
        workers_.emplace_back([this] { WorkerLoop(); });
    }
}

JobSystem::~JobSystem()
{
    stopping_.store(true, std::memory_order_release);
    cv_.notify_all();
    for (std::thread& worker : workers_) {
        if (worker.joinable()) worker.join();
    }
}

JobHandle JobSystem::Dispatch(std::uint32_t count,
                              std::uint32_t groupSize,
                              std::function<void(std::uint32_t)> function)
{
    if (!function) throw std::invalid_argument("job function is empty");
    if (groupSize == 0) throw std::invalid_argument("group size must be positive");
    if (count == 0) return JobHandle{};

    const std::uint32_t groupCount = (count + groupSize - 1) / groupSize;
    auto counter = std::make_shared<std::atomic_uint32_t>(groupCount);

    {
        std::scoped_lock lock(mutex_);
        for (std::uint32_t group = 0; group < groupCount; ++group) {
            const std::uint32_t begin = group * groupSize;
            const std::uint32_t end = std::min(count, begin + groupSize);
            queue_.push_back(Job{
                [begin, end, function] {
                    for (std::uint32_t i = begin; i < end; ++i) function(i);
                },
                counter
            });
        }
    }
    cv_.notify_all();
    return JobHandle{std::move(counter)};
}

void JobSystem::Wait(const JobHandle& handle)
{
    while (!handle.IsComplete()) {
        if (!TryExecuteOne()) {
            std::this_thread::yield();
        }
    }
}

std::uint32_t JobSystem::WorkerCount() const noexcept
{
    return static_cast<std::uint32_t>(workers_.size());
}

bool JobSystem::TryExecuteOne()
{
    Job job;
    {
        std::scoped_lock lock(mutex_);
        if (queue_.empty()) return false;
        job = std::move(queue_.front());
        queue_.pop_front();
    }

    job.function();
    job.counter->fetch_sub(1, std::memory_order_release);
    return true;
}

void JobSystem::WorkerLoop()
{
    while (true) {
        Job job;
        {
            std::unique_lock lock(mutex_);
            cv_.wait(lock, [this] {
                return stopping_.load(std::memory_order_acquire) || !queue_.empty();
            });
            if (stopping_.load(std::memory_order_acquire) && queue_.empty()) return;
            job = std::move(queue_.front());
            queue_.pop_front();
        }

        job.function();
        job.counter->fetch_sub(1, std::memory_order_release);
    }
}

} // namespace aster
