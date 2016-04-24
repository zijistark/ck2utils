
#include "an_province.h"


void an_province::write_event(FILE* f, uint event_id) const {

    fprintf(f, "# emf_nomad.%u [%u - %s]\n", event_id, _id, _name.c_str());

    fprintf(f, "province_event = {\n");
    fprintf(f, "\tid = emf_nomad.%u\n\n", event_id);
    fprintf(f, "\tis_triggered_only = yes\n");
    fprintf(f, "\thide_window = yes\n\n");
    fprintf(f, "\ttrigger = {\n");
    fprintf(f, "\t\towner = { is_nomadic = yes }\n");
    fprintf(f, "\t\tNOT = { any_province_holding = { NOT = { holding_type = nomad } } }\n");
    fprintf(f, "\t\thas_empty_holding = yes\n");
    fprintf(f, "\t}\n\n");
    fprintf(f, "\timmediate = {\n");

    for (uint i = 0; i < _hist_list.size()-1; ++i) {
        const hist_entry& e = _hist_list[i];

        fprintf(f, "\t\tif = {\n");
        fprintf(f, "\t\t\tlimit = { NOT = { year = %u } }\n", _hist_list[i+1].year);
        fprintf(f, "\t\t\tif = {\n");

        fprintf(f, "\t\t\t\tlimit = { culture = %s religion = %s }\n",
                e.culture.c_str(), e.religion.c_str());

        fprintf(f, "\t\t\t\tbreak = yes # Not necessary to build a settlement\n");
        fprintf(f, "\t\t\t}\n"); // END: if
        fprintf(f, "\t\t\tbuild_holding = { type = %s }\n", e.holding_type());
        fprintf(f, "\t\t\tculture  = %s\n", e.culture.c_str());
        fprintf(f, "\t\t\treligion = %s\n", e.religion.c_str());
        fprintf(f, "\t\t\temf_nomad_antinomad_%s_effect = yes\n", e.holding_type());
        fprintf(f, "\t\t\tlog = \"emf_antinomad(%u, '[Root.GetName]') => %s / %s / %s\"\n",
                _id, e.holding_type(), e.culture.c_str(), e.religion.c_str());
        fprintf(f, "\t\t\tbreak = yes\n");
        fprintf(f, "\t\t}\n"); // END: if
    }

    const hist_entry& e = _hist_list.back();
    fprintf(f, "\t\tif = {\n");

    fprintf(f, "\t\t\tlimit = { culture = %s religion = %s }\n",
            e.culture.c_str(), e.religion.c_str());

    fprintf(f, "\t\t\tbreak = yes # Not necessary to build a settlement\n");
    fprintf(f, "\t\t}\n"); // END: if
    fprintf(f, "\t\tbuild_holding = { type = %s }\n", e.holding_type());
    fprintf(f, "\t\tculture  = %s\n", e.culture.c_str());
    fprintf(f, "\t\treligion = %s\n", e.religion.c_str());
    fprintf(f, "\t\temf_nomad_antinomad_%s_effect = yes\n", e.holding_type());
    fprintf(f, "\t\tlog = \"emf_antinomad(%u, '[Root.GetName]') => %s / %s / %s\"\n",
            _id, e.holding_type(), e.culture.c_str(), e.religion.c_str());

    fprintf(f, "\t}\n}\n\n\n");
}

