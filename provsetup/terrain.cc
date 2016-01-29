
#include "terrain.h"


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

const int NUM_TERRAIN = sizeof(TERRAIN) / sizeof(TERRAIN[0]);
const int TERRAIN_ID_WATER = 15;

const int TERRAIN_COLOR_TO_TERRAIN_ID[] = {
    11,
    4,
    11,
    14,
    8,
    6,
    8,
    8,
    8,
    12,
    15,
    15,
    15,
    5,
};

const int NUM_TERRAIN_COLORS = sizeof(TERRAIN_COLOR_TO_TERRAIN_ID) / sizeof(TERRAIN_COLOR_TO_TERRAIN_ID[0]);
