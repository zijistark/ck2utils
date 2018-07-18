#ifndef __LIBCK2_LEGACY_COMPAT_H__
#define __LIBCK2_LEGACY_COMPAT_H__

#include "common.h"


_CK2_NAMESPACE_BEGIN;


static inline char* strsep(char** stringp, const char* delim) {
    char* start = *stringp;
    char* p;

    p = (start != NULL) ? strpbrk(start, delim) : NULL;

    if (p == NULL)
        *stringp = NULL;
    else {
        *p = '\0';
        *stringp = p + 1;
    }

    return start;
}

_CK2_NAMESPACE_END;
#endif
