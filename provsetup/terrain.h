// -*- c++ -*-

#ifndef _MDH_TERRAIN_H_
#define _MDH_TERRAIN_H_

#include <string>

struct terrain {
    std::string name;
    // ... some day more fields ...

    terrain(const char* _name) : name(_name) { }
};

extern const terrain TERRAIN[];
extern const int NUM_TERRAIN;
extern const int TERRAIN_ID_WATER;
extern const int TERRAIN_COLOR_TO_TERRAIN_ID[];
extern const int NUM_TERRAIN_COLORS;

#endif
