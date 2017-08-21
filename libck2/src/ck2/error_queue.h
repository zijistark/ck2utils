// -*- c++ -*-

#pragma once
#include "common.h"

#include <string>
#include <vector>
#include <utility>
#include <cstdio>

#include "file_location.h"


_CK2_NAMESPACE_BEGIN;


struct error {
    /* will want to add more useful fields to this in the future than just an opaque character msg */
    enum priority : uint { NORMAL = 0, WARNING } _prio;
    floc _location;
    char _msg[256]; // probably want this dynamically-allocated w/ move-semantics but ehhh

    template<class... Args>
    error(priority prio, const floc& location, const char* format, Args&&... args)
        : _prio(prio), _location(location)
    {
        snprintf(&_msg[0], sizeof(_msg), format, std::forward<Args>(args)...);
    }

    template<class... Args>
    error(const floc& location, const char* format, Args&&... args)
        : _prio(priority::NORMAL), _location(location)
    {
        snprintf(&_msg[0], sizeof(_msg), format, std::forward<Args>(args)...);
    }

    const char* what() const noexcept { return _msg; }
};


class error_queue {
    typedef std::vector<error> vec_t;
    vec_t _vec;

public:
    template<class... Args>
    void push(Args&&... args) { _vec.emplace_back( std::forward<Args>(args)... ); }

    vec_t::size_type      size()  const noexcept { return _vec.size(); }
    bool                  empty() const noexcept { return size() == 0; }
    vec_t::iterator       begin()       noexcept { return _vec.begin(); }
    vec_t::iterator       end()         noexcept { return _vec.end(); }
    vec_t::const_iterator begin() const noexcept { return _vec.cbegin(); }
    vec_t::const_iterator end()   const noexcept { return _vec.cend(); }
};


_CK2_NAMESPACE_END;
