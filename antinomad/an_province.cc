
#include "an_province.h"


void an_province::write_event(FILE* f, uint event_id) const {

    fprintf(f, "# emf_nomad.%u [%u - %s]\n", event_id, _id, _name.c_str());

    fprintf(f, "province_event = {\n");
    fprintf(f, "\tid = emf_nomad.%u\n", event_id);
    fprintf(f, "\thide_window = yes\n");
    fprintf(f, "\tis_triggered_only = yes\n\n");
    fprintf(f, "\ttrigger = {\n");
    fprintf(f, "\t\towner = { is_nomadic = yes }\n");
    fprintf(f, "\t\tnot = { any_province_holding = { not = { holding_type = nomad } } }\n");
    fprintf(f, "\t\thas_empty_holding = yes\n");
    fprintf(f, "\t}\n\n");
    fprintf(f, "\timmediate = {\n");

    for (uint i = 0; i < _hist_list.size()-1; ++i) {
        const hist_entry& e = _hist_list[i];

        fprintf(f, "\t\tif = {\n");
        fprintf(f, "\t\t\tlimit = { not = { year = %u } }\n", _hist_list[i+1].year);
        fprintf(f, "\t\t\tif = {\n");

        fprintf(f, "\t\t\t\tlimit = { culture = %s religion = %s }\n",
                e.culture.c_str(), e.religion.c_str());

        fprintf(f, "\t\t\t\tbreak = yes # Not necessary to build a settlement\n");
        fprintf(f, "\t\t\t}\n"); // END: if
        fprintf(f, "\t\t\tbuild_holding = { type = %s }\n", (e.has_temple) ? "temple" : "tribal");
        fprintf(f, "\t\t\tculture  = %s\n", e.culture.c_str());
        fprintf(f, "\t\t\treligion = %s\n", e.religion.c_str());
        fprintf(f, "\t\t\temf_nomad_antinomad_effect = yes\n");
        fprintf(f, "\t\t\tlog = \"emf_antinomad(%u, '%s')\"\n", _id, _name.c_str());
        fprintf(f, "\t\t\tbreak = yes\n");
        fprintf(f, "\t\t}\n"); // END: if
    }

    const hist_entry& e = _hist_list.back();
    fprintf(f, "\t\tif = {\n");

    fprintf(f, "\t\t\tlimit = { culture = %s religion = %s }\n",
            e.culture.c_str(), e.religion.c_str());

    fprintf(f, "\t\t\tbreak = yes # Not necessary to build a settlement\n");
    fprintf(f, "\t\t}\n"); // END: if
    fprintf(f, "\t\tbuild_holding = { type = %s }\n", (e.has_temple) ? "temple" : "tribal");
    fprintf(f, "\t\tculture  = %s\n", e.culture.c_str());
    fprintf(f, "\t\treligion = %s\n", e.religion.c_str());
    fprintf(f, "\t\temf_nomad_antinomad_effect = yes\n");
    fprintf(f, "\t\tlog = \"emf_antinomad(%u, '%s')\"\n", _id, _name.c_str());

    fprintf(f, "\t}\n}\n\n\n");
}


