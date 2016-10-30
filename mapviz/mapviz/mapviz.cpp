
#include "default_map.h"
#include "province_map.h"
#include <boost/filesystem.hpp>

using namespace boost::filesystem;

const path ROOT_PATH("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings II");

int main()
{
	default_map dm(ROOT_PATH);
	province_map pm(dm);
    return 0;
}

