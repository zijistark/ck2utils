
#include "date.h"

#include <cstring>
#include <cstdlib>


_CK2_NAMESPACE_BEGIN


/* construct a `date` from a well-formed date-string non-const `src` (we assume the str is thrown away, as we modify it)
 * intended to be used when `src` is already known to be well-formed due to lexical analysis, as we skip error-checking.
 */
date::date(char* src, const floc& loc, error_queue& errors) {
    char* part[3];
    part[0] = src;

    for (int i = 0; i < 2; ++i) {
        char* end = strchr(part[i], '.');
        part[i + 1] = end + 1;
        *end = '\0';
    }

    /* part[] now contains 3 null-terminated strings for the year, month, and day.
     * make sure our object will be able to hold the parsed values.
     * be permissive of all other problems w/ date components so that we can later report what was actually parsed.
     */

    const char* name[3] = { "year", "month", "day" };
    const int   min[3]  = { INT16_MIN, INT8_MIN, INT8_MIN };
    const int   max[3]  = { INT16_MAX, INT8_MAX, INT8_MAX };

    int num[3];

    for (int i = 0; i < 3; ++i) {
        num[i] = atoi( part[i] );

        if (num[i] > max[i])
            errors.push(loc, "Cannot represent %s %d (maximum is %d) in date value", name[i], num[i], max[i]);
        if (num[i] < min[i])
            errors.push(loc, "Cannot represent %s %d (minimum is %d) in date value", name[i], num[i], min[i]);
    }

    _y = static_cast<int16_t>( num[0] );
    _m = static_cast<int8_t> ( num[1] );
    _d = static_cast<int8_t> ( num[2] );
}


_CK2_NAMESPACE_END
