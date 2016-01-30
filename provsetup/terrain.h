// -*- c++ -*-

#ifndef _MDH_TERRAIN_H_
#define _MDH_TERRAIN_H_

#include <string>

struct terrain {
    std::string name;
    // ... some day, more fields ...

    terrain(const char* _name) : name(_name) { }
};

const terrain TERRAIN[] = {
    "pti",                    // 0
    "ocean",                  // 1
    "inland_ocean",           // 2
    "arctic",                 // 3
    "farmlands",              // 4
    "forest",                 // 5
    "hills",                  // 6
    "woods",                  // 7
    "mountain",               // 8
    "impassable_mountains",   // 9
    "steppe",                 // 10
    "plains",                 // 11
    "jungle",                 // 12
    "marsh",                  // 13
    "desert",                 // 14
    "coastal_desert"          // 15
};

const int TERRAIN_ID_WATER = 15; // apparently used for water provinces (coastal_desert)

const int TERRAIN_COLOR_TO_ID[] = {
    11,   // 0
    4,    // 1
    11,   // 2
    14,   // 3
    8,    // 4
    10,   // 5
    3,    // 6
    8,    // 7
    6,    // 8
    8,    // 9
    8,    // 10
    8,    // 11
    12,   // 12
    15,   // 13
    15,   // 14
    15,   // 15
    5,    // 16
};

const int  NUM_TERRAIN = sizeof(TERRAIN) / sizeof(TERRAIN[0]);
const int  NUM_TERRAIN_COLORS = sizeof(TERRAIN_COLOR_TO_ID) / sizeof(TERRAIN_COLOR_TO_ID[0]);
const uint MAX_TERRAIN_COLOR = NUM_TERRAIN_COLORS - 1;

#endif
