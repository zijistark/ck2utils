
#include <pdx.h>
#include <cstdio>


int main(int argc, char** argv) {
    const char* input_path = (argc == 2) ? argv[1] : "test_input.txt";

    try {
        pdx::parser parse(input_path);
    }
    catch (std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }

    return 0;
}
