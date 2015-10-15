// -*- c++ -*-

#ifndef _MDH_ERROR_H_
#define _MDH_ERROR_H_

#include <exception>
#include <stdexcept>
#include <cstdio>
#include <cstdarg>
#include <cstdlib>

class va_error : public std::exception {
  char* msg;

public:
  explicit va_error(const char* format, ...) : msg(0) {
    va_list vl;
    va_start(vl, format);
    int n = vasprintf(&msg, format, vl);
    va_end(vl);
    
    if (n < 0)
      throw std::runtime_error("va_error: vasprintf");
  }

  const char* what() const throw() {
    return msg;
  }

  ~va_error() throw() {
    free(msg);
    msg = 0;
  }
};


#endif

