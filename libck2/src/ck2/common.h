// -*- c++ -*-

#ifndef _CK2_COMMON_H_
#define _CK2_COMMON_H_

// TODO: define these 2 macros s.t. it can have a semicolon after it so as not to confuse syntax highlighters.
#define _CK2_NAMESPACE_BEGIN namespace ck2 {
#define _CK2_NAMESPACE_END }


#include <cstdint>
#include <cassert>
#include <ostream>
#include <cstring>


_CK2_NAMESPACE_BEGIN


typedef unsigned int uint;

#ifndef SIZE_MAX
#define SIZE_MAX (~(size_t)0)
#endif


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


// stark_fast_strncpy
// - copy not more than `length` characters from the string `src` (including any NULL terminator) to the buffer `dst`
// - precondition: `length` <= strlen(src); we do not check the actual length ourselves for performance reasons.
// - precondition: - `dst_sz` is the max size of the memory for `dst` (not max length but max length + null terminator)
// - returns actual number of characters copied (might be less than requested `length`)
// - `dst` is always NULL-terminated when done
// - the memory ranges occupied by the strings `src` and `dst` may never overlap; if they, do UNDEFINED BEHAVIOR!
// - resolves would-be buffer overflow of `dst` with truncation (the return value will be less than `length`)
// - gives literally optimal performance when the length of `src` is already known (or length of some prefix of `src`)
// --> dst will never be unnecessarily padded with NULLs at end & memcpy is optimized for general case (SIMD, etc.)
size_t stark_fast_strncpy(char* dst, size_t dst_sz, const char* src, size_t length) {
    if (length == 0 || dst_sz == 0) return 0;
    size_t n = (length > dst_sz) ? dst_sz : length;
    memcpy(dst, src, n);
    // make SURE `dst` is NULL-terminated (`src` doesn't have to be -- also matters if copying only a prefix of `src`)
    dst[n-1] = '\0';
    return n;
}

_CK2_NAMESPACE_END


#endif
