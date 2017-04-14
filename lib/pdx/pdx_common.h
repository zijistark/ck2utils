// -*- c++ -*-

#ifndef _PDX_COMMON_H_
#define _PDX_COMMON_H_


#define _PDX_NAMESPACE_BEGIN namespace pdx {
#define _PDX_NAMESPACE_END }


#include <cstdint>
#include <ostream>


_PDX_NAMESPACE_BEGIN


typedef unsigned int uint;


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


_PDX_NAMESPACE_END


#endif
