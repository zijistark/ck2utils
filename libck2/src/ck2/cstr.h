// -*- c++ -*-

#pragma once

#include "common.h"
#include <cstring>


_CK2_NAMESPACE_BEGIN


/* CSTR -- light wrapper class for a pointer to a zero-terminated, C-style string.
 *         its only purpose is to instrument such raw pointers to characters
 *         with equality, comparison/ordering, and hash functionality.
 *
 * it might be useful in the future to template this class for different types
 * of characters, but I've no use case presently.
 */

class cstr {
    char const* _ptr;

public:
    cstr(char const* ptr = nullptr) : _ptr(ptr) {}

    /* equivalence & lexicographical ordering */
    bool operator==(const cstr& other) const noexcept { return strcmp(_ptr, other._ptr) == 0; }
    bool operator<(const cstr& other) const noexcept { return strcmp(_ptr, other._ptr) < 0; }

    /* gimme that pointer back! */
    char const* data() const noexcept { return _ptr; }
};


_CK2_NAMESPACE_END


/* inject std::hash<ck2::cstr> specialization */

namespace std {
    template<> struct hash<ck2::cstr> {
        typedef ck2::cstr argument_type;
        typedef size_t result_type;

        static_assert(sizeof(size_t) == 8,
                      "ck2::cstr's hash implementation requires 64-bit target to function correctly");

        /* FNV/1a algorithm applied to null-terminated string with unknown length, 64-bit */
        size_t operator()(const ck2::cstr& cs) const noexcept {
            size_t hash = 0xCBF29CE484222325;
            auto ptr = cs.data();

            while (*ptr) {
                hash ^= (unsigned) *ptr++;
                hash *= 0x100000001B3;
            }

            return hash;
        }
    };
}
