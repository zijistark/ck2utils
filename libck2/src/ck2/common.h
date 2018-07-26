#ifndef __LIBCK2_COMMON_H__
#define __LIBCK2_COMMON_H__


#define _CK2_NAMESPACE_BEGIN namespace ck2 {
#define _CK2_NAMESPACE_END }


#include <iosfwd>
#include <limits>
#include <cstdint>

// TODO: remove these from this common header soon:
#include <cassert>
#include <cstring>
#include "Error.h"


// std forward-decls for convenience/consistency inside CK2 namespace

namespace std {
    template<class T, class Deleter> class unique_ptr;
};


_CK2_NAMESPACE_BEGIN;


using std::string_view;
using std::string;
using std::numeric_limits;
using std::ostream;
using std::unique_ptr;
using unique_file_ptr = std::unique_ptr< std::FILE, int (*)(std::FILE*) >;

typedef unsigned int uint;

inline constexpr char const* EOL = "\n";
inline constexpr char const* TAB = "\t";


/* generate_int_array< N, template<size_t> F >::result
 * - N is the number of elements in the array result::data
 * - F is a parameterized type s.t. F<I>::value will be the value of result::data[I]
 *
 * template metaprogramming technique for constructing const int arrays at compile time -- could easily be generalized
 * to any constant value type */
template<int... args> struct IntArrayHolder {
    static const int data[sizeof...(args)];
};

template<int... args>
const int IntArrayHolder<args...>::data[sizeof...(args)] = { args... };

// recursive case
template<size_t N, template<size_t> class F, int... args>
struct generate_int_array_impl {
    typedef typename generate_int_array_impl<N-1, F, F<N>::value, args...>::result result;
};

// base case
template<template<size_t> class F, int... args>
struct generate_int_array_impl<0, F, args...> {
    typedef IntArrayHolder<F<0>::value, args...> result;
};

template<size_t N, template<size_t> class F>
struct generate_int_array {
    typedef typename generate_int_array_impl<N-1, F>::result result;
};


// mdh_strncpy

// copy not more than `length` characters from the string `src` (including any NULL terminator) to the string `dst`
// while never overflowing the `dst_sz` memory available to `dst`. return value: actual amount of characters copied.

// - precondition: `length <= strlen(src)`; we do not check the actual length ourselves for performance reasons.
// - precondition: `dst_sz` is the max size of the memory for `dst` (not max length but max length + null terminator)
// - precondition: the memory backing `src` and `dst` may not overlap; if it does, UNDEFINED BEHAVIOR! CHAOS! SIN!

// - `dst` is always NULL-terminated when done (unlike strncpy)
// - performance of the bounded copy should be virtually as good as you can get.
// --> `dst` will never be unnecessarily padded with O(N) NULLs in a lot of cases (unlike strncpy)
// --> memcpy is intensively optimized for non-overlapping block memory transfer (SIMD, etc.)

// motivation for creation: strncpy is practically obsolete and broken -- but it's also slow due to a poor POSIX
// standardization choice, sprintf and similar are also slower, and of course, strcpy can overflow its output buffer.
static inline size_t mdh_strncpy(char* dst, size_t dst_sz, const char* const src, size_t length) {
    size_t n = (length > dst_sz) ? dst_sz : length;
    memcpy(dst, src, n);
    dst[n] = '\0'; // only sometimes necessary (when not using as a replacement for strcpy on well-formed input)
    return n;
}


_CK2_NAMESPACE_END;
#endif
