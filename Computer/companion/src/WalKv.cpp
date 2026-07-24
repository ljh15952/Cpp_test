#include "apex/WalKv.hpp"

#include <array>
#include <fstream>
#include <limits>
#include <span>
#include <utility>
#include <stdexcept>
#include <vector>

namespace apex {
namespace {
constexpr std::uint32_t kMagic = 0x31564B53U; // "SKV1" in little endian bytes
constexpr std::uint16_t kVersion = 1U;
constexpr std::size_t kHeaderBytes = 4U + 2U + 1U + 1U + 8U + 4U + 4U + 4U;

void set_u16(std::uint8_t* p, std::uint16_t v) noexcept {
    p[0] = static_cast<std::uint8_t>(v);
    p[1] = static_cast<std::uint8_t>(v >> 8U);
}
void set_u32(std::uint8_t* p, std::uint32_t v) noexcept {
    for (unsigned i = 0; i < 4U; ++i) p[i] = static_cast<std::uint8_t>(v >> (i * 8U));
}
void set_u64(std::uint8_t* p, std::uint64_t v) noexcept {
    for (unsigned i = 0; i < 8U; ++i) p[i] = static_cast<std::uint8_t>(v >> (i * 8U));
}

std::uint16_t get_u16(const std::uint8_t* p) {
    return static_cast<std::uint16_t>(p[0]) | static_cast<std::uint16_t>(p[1] << 8U);
}
std::uint32_t get_u32(const std::uint8_t* p) {
    std::uint32_t v{};
    for (unsigned i = 0; i < 4U; ++i) v |= static_cast<std::uint32_t>(p[i]) << (i * 8U);
    return v;
}
std::uint64_t get_u64(const std::uint8_t* p) {
    std::uint64_t v{};
    for (unsigned i = 0; i < 8U; ++i) v |= static_cast<std::uint64_t>(p[i]) << (i * 8U);
    return v;
}

std::uint32_t fnv1a(std::span<const std::uint8_t> bytes) {
    std::uint32_t h = 2166136261U;
    for (const auto b : bytes) { h ^= b; h *= 16777619U; }
    return h;
}

bool read_exact(std::istream& in, std::span<std::uint8_t> out) {
    in.read(reinterpret_cast<char*>(out.data()), static_cast<std::streamsize>(out.size()));
    return static_cast<std::size_t>(in.gcount()) == out.size();
}
} // namespace

WalKv::WalKv(std::filesystem::path path) : path_(std::move(path)) {}

void WalKv::open_or_recover() {
    values_.clear();
    next_sequence_ = 1U;
    if (!std::filesystem::exists(path_)) {
        std::ofstream create(path_, std::ios::binary);
        if (!create) throw std::runtime_error("cannot create WAL file");
        return;
    }
    std::ifstream in(path_, std::ios::binary);
    if (!in) throw std::runtime_error("cannot open WAL file");

    std::uint64_t last_sequence = 0U;
    for (;;) {
        std::array<std::uint8_t, kHeaderBytes> header{};
        in.read(reinterpret_cast<char*>(header.data()), static_cast<std::streamsize>(header.size()));
        const auto got = static_cast<std::size_t>(in.gcount());
        if (got == 0U) break;
        if (got != header.size()) break; // final partial record is ignored

        const auto magic = get_u32(header.data());
        const auto version = get_u16(header.data() + 4U);
        const auto type_raw = header[6U];
        const auto sequence = get_u64(header.data() + 8U);
        const auto key_length = get_u32(header.data() + 16U);
        const auto value_length = get_u32(header.data() + 20U);
        const auto expected_checksum = get_u32(header.data() + 24U);

        if (magic != kMagic || version != kVersion) throw std::runtime_error("invalid WAL header");
        if (key_length > kMaxKeyBytes || value_length > kMaxValueBytes) throw std::runtime_error("WAL record too large");
        if (sequence <= last_sequence) throw std::runtime_error("non-monotonic WAL sequence");
        if (type_raw != static_cast<std::uint8_t>(RecordType::Put) &&
            type_raw != static_cast<std::uint8_t>(RecordType::Erase)) {
            throw std::runtime_error("invalid WAL record type");
        }

        const auto payload_size = static_cast<std::size_t>(key_length) + static_cast<std::size_t>(value_length);
        std::vector<std::uint8_t> payload(payload_size);
        if (!read_exact(in, payload)) break; // final partial payload is ignored
        if (fnv1a(payload) != expected_checksum) throw std::runtime_error("WAL checksum mismatch");

        std::string key(reinterpret_cast<const char*>(payload.data()), key_length);
        std::string value(reinterpret_cast<const char*>(payload.data() + key_length), value_length);
        if (type_raw == static_cast<std::uint8_t>(RecordType::Put)) values_[std::move(key)] = std::move(value);
        else values_.erase(key);
        last_sequence = sequence;
        next_sequence_ = sequence + 1U;
    }
}

void WalKv::append_record(RecordType type, std::string_view key, std::string_view value) {
    if (key.empty() || key.size() > kMaxKeyBytes || value.size() > kMaxValueBytes) {
        throw std::invalid_argument("invalid key or value size");
    }
    if (key.size() > std::numeric_limits<std::uint32_t>::max() ||
        value.size() > std::numeric_limits<std::uint32_t>::max()) {
        throw std::length_error("record length does not fit format");
    }

    std::vector<std::uint8_t> payload;
    payload.reserve(key.size() + value.size());
    payload.insert(payload.end(), key.begin(), key.end());
    payload.insert(payload.end(), value.begin(), value.end());

    std::array<std::uint8_t, kHeaderBytes> header{};
    set_u32(header.data(), kMagic);
    set_u16(header.data() + 4U, kVersion);
    header[6U] = static_cast<std::uint8_t>(type);
    header[7U] = 0U;
    set_u64(header.data() + 8U, next_sequence_);
    set_u32(header.data() + 16U, static_cast<std::uint32_t>(key.size()));
    set_u32(header.data() + 20U, static_cast<std::uint32_t>(value.size()));
    set_u32(header.data() + 24U, fnv1a(payload));

    std::ofstream out(path_, std::ios::binary | std::ios::app);
    if (!out) throw std::runtime_error("cannot append WAL");
    out.write(reinterpret_cast<const char*>(header.data()), static_cast<std::streamsize>(header.size()));
    out.write(reinterpret_cast<const char*>(payload.data()), static_cast<std::streamsize>(payload.size()));
    out.flush();
    if (!out) throw std::runtime_error("WAL write failed");
    ++next_sequence_;
}

void WalKv::put(std::string key, std::string value) {
    append_record(RecordType::Put, key, value);
    values_[std::move(key)] = std::move(value);
}

void WalKv::erase(std::string_view key) {
    append_record(RecordType::Erase, key, {});
    values_.erase(std::string(key));
}

std::optional<std::string> WalKv::get(std::string_view key) const {
    const auto it = values_.find(std::string(key));
    if (it == values_.end()) return std::nullopt;
    return it->second;
}

} // namespace apex
