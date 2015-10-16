
#include "an_province.h"


void an_province::write_event(FILE* f, uint event_id) const {

    fprintf(f, "# emf_nomad.%u [%u - %s]\n", event_id, _id, _name.c_str());

    fprintf(f, "province_event = {\n");
    fprintf(f, "\tid = emf_nomad.%u\n", event_id);
    fprintf(f, "\thide_window = yes\n");
    fprintf(f, "\tis_triggered_only = yes\n\n");
    fprintf(f, "\ttrigger = { not = { any_province_holding = { not = { holding_type = nomad } } } }\n\n");
    fprintf(f, "\timmediate = {\n");

    for (auto&& e : _hist_list) {
        fprintf(f, "\t\tif = {\n");
        fprintf(f, "\t\t\tlimit = { not = { year = %u } }\n", e.year + 1);
        fprintf(f, "\t\t\tif = {\n");

        fprintf(f, "\t\t\t\tlimit = { culture = %s religion = %s }\n",
                e.culture.c_str(), e.religion.c_str());

        fprintf(f, "\t\t\t\tbreak = yes # Not necessary to build a settlement\n");
        fprintf(f, "\t\t\t}\n"); // END: if
        fprintf(f, "\t\t\temf_nomad_autobuild_%s_effect = yes\n", (e.has_temple) ? "temple" : "tribal");
        fprintf(f, "\t\t\tbreak = yes\n");
        fprintf(f, "\t\t}\n"); // END: if
    }

    fprintf(f, "\t}\n}\n\n\n");

}
