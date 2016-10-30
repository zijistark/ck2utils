// -*- c++ -*-

#ifndef _MDH_ERROR_H_
#define _MDH_ERROR_H_

#include <exception>
#include <stdexcept>
#include <cstdio>
#include <cstdarg>
#include <cstdlib>

class va_error : public std::exception {
  char msg[512];

public:
  explicit va_error(const char* format, ...) {
    va_list vl;
    va_start(vl, format);
    int n = vsnprintf(&msg[0], sizeof(msg), format, vl);
    va_end(vl);
    
    if (n < 0 || n < sizeof(msg)-1)
      throw std::runtime_error("va_error: vasprintf");
  }

  const char* what() const throw() {
    return msg;
  }

  ~va_error() throw() {
  }
};


#endif

