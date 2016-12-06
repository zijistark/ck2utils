// -*- c++ -*-

#pragma once

#include <cassert>
#include <cstring>
#include <cstdint>
#include <stdexcept>
#include <forward_list>
#include <memory>

/* cstr_pool -- An efficient data structure for allocating memory for C-string style[1] sequences when sequences are
 * typically small but varied in size, and bulk, exception-safe (de)allocation is desirable.
 *
 * [1] With different CharT, this could be used for any such memory sequence that is terminated with a NUL (or
 * sizeof(CharT) zeroes, to be precise).
 *
 * Automatically manages optimal memory alignment of the allocated sequences, but alignment can be forced via the
 * _ALIGNMENT template parameter. E.g., default alignment for x86_64-cygwin-gcc of a byte sequence in RAM is
 * on address boundaries that are modulo 8 bytes (i.e., many memory computations on these strings will be much
 * faster if they start upon a 64-bit alignment boundary in RAM, but it may be desirable for compactness to reduce
 * this alignment to as low as 8-bit, since most unoptimized string algorithms already operate upon byte-by-byte
 * access patterns).
 */

typedef unsigned char byte_t;

/* note that _CHUNK_SZ is just a hint for the size in which we'd like our chunks to be allocated (bytes) */
template<typename CharT = char, const size_t _CHUNK_SZ = 1024, const size_t _ALIGNMENT = alignof(CharT*)>
class cstr_pool {
public:
    // 1 pointer overhead assumed per chunk
    static const size_t MAX_UNALIGNED_BYTES = sizeof(CharT[_CHUNK_SZ]) - sizeof(void*);
    static const size_t MAX_BYTES = MAX_UNALIGNED_BYTES - MAX_UNALIGNED_BYTES % _ALIGNMENT;
    static const size_t MAX_SZ = MAX_BYTES / sizeof(CharT);
    static_assert(MAX_BYTES % sizeof(CharT) == 0, "cstr_pool type/alignment parameters contradict each other and cannot be implemented");

private:
    struct chunk {
        alignas(CharT) byte_t data[MAX_BYTES];
    };

    typedef std::forward_list<chunk> list_t; // singly-linked list, hence the 1 pointer overhead assumed
    list_t  _chunks; // buffers
    void*   _p; // ptr to beginning of usable buffer space
    size_t  _capacity; // _capacity bytes remaining in _p_buf

    void grow() {
        _chunks.emplace_front();
        _p = _chunks.front().data;
        _capacity = MAX_BYTES;
    }

    CharT* aligned_alloc(size_t sz) {
        size_t sz_bytes = sz * sizeof(CharT);

        if (std::align(_ALIGNMENT, sz_bytes, _p, _capacity)) {
            /* alignment criteria satisfied!
             * _p_buf & _capacity were modified according to alignment needs but nothing else */
            CharT* str = reinterpret_cast<CharT*>(_p);
            _p = (byte_t*)_p + sz_bytes;
            _capacity -= sz_bytes;
            return str;
        }

        return nullptr;
    }

public:
    /* provided for easy override via template specialization */
    static inline size_t generic_strlen(const CharT* s) { return strlen(s); }

    /* default ctor, only ctor */
    cstr_pool() : _p(nullptr), _capacity(0) {}

    /* strdup -- duplicate a string (allocate, copy, and return) */
    CharT* strdup(const CharT* src) {
        size_t len = generic_strlen(src);
        size_t sz = len + 1;

        if (sz > MAX_SZ)
            throw std::logic_error("cstr_pool::strdup() tried to allocate string larger than maximum chunk length");

        CharT* dst;

        if ((dst = aligned_alloc(sz)) == nullptr) {
            /* will have to allocate a new chunk to satisfy that request */
            grow();
            dst = aligned_alloc(sz);

            /* should never have failed after grabbing a fresh, new chunk, because sz <= MAX_SZ */
            assert(dst != nullptr && "could not satisfy aligned_alloc even after allocating new chunk");
        }

        memcpy(dst, src, sz * sizeof(CharT));
        return dst;
    }
};
