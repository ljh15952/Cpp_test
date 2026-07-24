#pragma once

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>

namespace apex {

class WalKv {
public:
    static constexpr std::size_t kMaxKeyBytes = 4096U;
    static constexpr std::size_t kMaxValueBytes = 1024U * 1024U;

    explicit WalKv(std::filesystem::path path);

    void open_or_recover();
    void put(std::string key, std::string value);
    void erase(std::string_view key);
    [[nodiscard]] std::optional<std::string> get(std::string_view key) const;
    [[nodiscard]] std::size_t size() const noexcept { return values_.size(); }
    [[nodiscard]] std::uint64_t next_sequence() const noexcept { return next_sequence_; }

private:
    enum class RecordType : std::uint8_t { Put = 1, Erase = 2 };
    void append_record(RecordType type, std::string_view key, std::string_view value);

    std::filesystem::path path_;
    std::unordered_map<std::string, std::string> values_;
    std::uint64_t next_sequence_{1U};
};

} // namespace apex
