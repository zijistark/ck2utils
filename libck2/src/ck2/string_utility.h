#ifndef __LIBCK2_STRING_UTILITY_H__
#define __LIBCK2_STRING_UTILITY_H__

#include "common.h"

#include <string_view>
#include <algorithm>
#include <cstring>


_CK2_NAMESPACE_BEGIN;


// works like linux's strsep(), although implementation may differ. thread-safe way to quickly split a *mutable*
// C-style character string by a given delimeter.
//
// ==> TODO: ultimately should be phased out in favor of a generic tokenizer (templated on char type, delimeter,
// and probably essence parameters such as whether to respect quoting and what type of escape sequences should be
// translated to what) which produces string_view objects and does not require a mutable C-style string as input
// (i.e., can work on other string_views or on const pointers to character arrays).
static inline auto strsep(char** sptr, int delim)
{
    auto start = *sptr;
    
    if (auto p = (start) ? strchr(start, delim) : nullptr) {
        *p = '\0';
        *sptr = p + 1;
    }
    else
        *sptr = nullptr;

    return start;
}


// test if an entire string is effectively empty (literally or just full of blank characters or EOL characters)
static inline constexpr auto str_is_blank(string_view s)
{
    for (const auto& c : s)
        if ( !(c == ' ' || c == '\t' || c == '\n' || c == '\r') )
            return false;

    return true;
}


_CK2_NAMESPACE_END;
#endif
