#ifndef __LIBCK2_CSV_READER_H__
#define __LIBCK2_CSV_READER_H__

#include "common.h"
#include "filesystem.h"
#include <cstdio>


_CK2_NAMESPACE_BEGIN;


// appropriately, this code assumes CK2-style CSV files. that is, semicolon-separated, and quoting of fields is not
// a thing.


template<class TupleT, class RecordCallbackT, const char Delim = ';'>
class CSVReader {
private:
    fs::path _path;
    FILE* _if;
};


_CK2_NAMESPACE_END;
#endif
