#!/usr/bin/env python3

from itertools import combinations, product
import math
import pathlib
import re
import string
import sys

from lupa import LuaRuntime
from ck2parser import Obj, SimpleParser
from print_time import print_time

# python 3.11 for lupa for now
# py -3.11 ck2_combat.py ../../wh-geheimnisnacht_v1.3.7.1

debug = False

constants = {
    "max_tech": 8,
    "basic_troop_types": [
        "light_infantry",
        "heavy_infantry",
        "pikemen",
        "light_cavalry",
        "knights",
        "archers",
        "special_troops",
    ],
    "light_troops": ["light_cavalry", "archers"],
    "heavy_troops": ["heavy_infantry", "pikemen", "knights"],
    "phases": ["skirmish", "melee", "pursue"],
    "standard_oe": {
        "skirmish": 0.02772713643178411,
        "melee": 0.05585845927520144,
        "pursue": 0.02,
    },
    "standard_de": {
        "skirmish": 17.006246555208527,
        "melee": 16.153846153846153,
        "pursue": 21.362994350282488,
    },
    "standard_me": {
        "skirmish": 0.2574063368809628,
        "melee": 0.364950801483255,
    },
    "standard_m": {
        "skirmish": 0.2714466825290153,
        "melee": 0.8819644369178662,
    },
    "standard_o": {
        "skirmish": 0.029239525691699606,
        "melee": 0.13499127658173682,
    },
}


def get_modpath():
    if len(sys.argv) <= 1:
        return []
    return [pathlib.Path(arg) for arg in sys.argv[1:]]


def get_defines(parser):
    lua = LuaRuntime()
    defines = {}
    paths = [parser.file("common/defines.lua")]
    paths.extend(parser.files("common/defines/*.lua"))
    for path in paths:
        with open(path) as f:
            lua.execute(f.read())
    defines = lua.globals()
    return defines["NDefines"]


def get_cultures(parser):
    culture_group = {}
    for _, tree in parser.parse_files("common/cultures/*.txt"):
        for n, v in tree:
            for n2, v2 in v:
                if n2.val not in [
                    "graphical_cultures",
                    "unit_graphical_cultures",
                    "alternate_start",
                ]:
                    culture_group[n2.val] = n.val
    return culture_group


def get_religions(parser):
    religion_group = {}
    for _, tree in parser.parse_files("common/religions/*.txt"):
        for n, v in tree:
            if n.val == "secret_religion_visibility_trigger":
                continue
            for n2, v2 in v:
                if isinstance(v2, Obj) and n2.val not in [
                    "color",
                    "male_names",
                    "female_names",
                    "interface_skin",
                ]:
                    religion_group[n2.val] = n.val
    return religion_group


def get_governments(parser):
    government_group = {}
    for _, tree in parser.parse_files("common/governments/*.txt"):
        for n, v in tree:
            for n2, v2 in v:
                government_group[n2.val] = n.val
    return government_group


def get_troops(parser, game_data):
    defines = game_data["defines"]["NMilitary"]
    attrs = ["morale", "maintenance"] + [
        f"phase_{p}_{x}" for p, x in product(constants["phases"], ["attack", "defense"])
    ]
    troops = {
        t: {a: defines[f"{t}_{a}".upper()] for a in attrs}
        for t in constants["basic_troop_types"]
        if t != "special_troops"
    }
    for _, tree in parser.parse_files("common/special_troops/*.txt"):
        for n, v in tree:
            troops[n.val] = {n2.val: v2.val for n2, v2 in v}
    return troops


def get_buildings(parser, game_data):
    troop_effect_p = (
        "("
        + "|".join(re.escape(t) for t in game_data["troops"])
        + ")(_(morale|offensive|defensive))?"
    )
    buildings = {}
    for _, tree in parser.parse_files("common/buildings/*.txt"):
        for n, v in tree:
            for n2, v2 in v:
                b = {"holding_type": n.val}
                for n3, v3 in v2:
                    match n3.val:
                        case (
                            "land_morale"
                            | "land_organisation"
                            | "levy_size"
                            | "port"
                            | "replaces"
                        ):
                            b[n3.val] = v3.val
                        case ("potential" | "trigger" | "is_active_trigger"):
                            if not (x := b.get("potential")):
                                b["potential"] = x = []
                            x.extend(v3.contents)
                        case "prerequisites":
                            b[n3.val] = v3.contents
                        case "upgrades_from":
                            b[n3.val] = v3.val
                            buildings[v3.val]["upgrades_to"] = n3.val
                        case _:
                            if re.fullmatch(troop_effect_p, n3.val, re.I):
                                b[n3.val.lower()] = v3.val
                buildings[n2.val] = b
    return buildings


def get_retinues(parser, game_data):
    # initial cost (gold per troop)
    #     = troop maintenance number * RETINUE_HIRE_COST_MULTIPLIER(0.14)
    #  OR = hire_cost of retinue / number of troops
    # monthly reinforcement cost (gold per month per troop) (the upkeep also doesn't stop)
    #     = RETINUE_REINFORCE_COST(3)/1000 * troop maintenance number * maintenance_multiplier
    # cost per casualty (gold per troop)
    #     = monthly reinforcement cost / RETINUE_REINFORCE_RATE(0.025)
    # monthly upkeep (gold per month per troop)
    #     = RETINUE_CONSTANT_COST(0.25)/1000 * troop maintenance number * maintenance_multiplier
    # retinue cap usage (per troop)
    #     = troop maintenance number
    retinues = {}
    for _, tree in parser.parse_files("common/retinue_subunits/*.txt"):
        for n, v in tree:
            r = {}
            r[constants["basic_troop_types"][v["first_type"].val]] = v[
                "first_amount"
            ].val
            if t2 := v.get("second_type"):
                r[constants["basic_troop_types"][t2.val]] = v["second_amount"].val
            if "special_troops" in r:
                r[v["special_troops"]] = r["special_troops"]
                del r["special_troops"]
            r["potential"] = v["potential"].contents if "potential" in v else []
            cost_type = (
                "prestige"
                if v.get("costs_prestige")
                else "piety"
                if v.get("costs_piety")
                else "gold"
            )
            if hc := v.get("hire_cost"):
                r["hire_cost"] = hc, cost_type
            else:
                # todo compute actual hire cost here using troop data?
                pass
            if mm := v.get("maintenance_multiplier"):
                r["maintenance_multiplier"] = mm.val
            r["modifier"] = v["modifier"] if "modifier" in v else Obj([])
            r["usage"] = sum(
                r.get(t, 0) * d["maintenance"] for t, d in game_data["troops"].items()
            )
            retinues[n.val] = r
    return retinues


def get_tactics(parser, game_data):
    troop_modifier_p = (
        "("
        + "|".join(re.escape(t) for t in game_data["troops"])
        + ")_(morale|offensive|defensive)"
    )
    tactics = {}
    for _, tree in parser.parse_files("common/combat_tactics/*.txt"):
        for n, v in tree:
            if n.val in ["flank_retreat_odds", "flank_pursue_odds"]:
                continue
            if "siege" in v:
                continue
            t = {"days": v["days"].val}
            if "group" in v:
                t["group"] = v["group"]
            if "change_phase_to" in v:
                t["change_phase_to"] = v["change_phase_to"].val
            for k in ["trigger", "mean_time_to_happen", "enemy"]:
                if k in v:
                    t[k] = v[k]
            for n2, v2 in v:
                if re.fullmatch(troop_modifier_p, n2.val):
                    t[n2.val] = v2.val
            tactics[n.val] = t
    return tactics


def get_tech(parser):
    tech = {}
    for _, v in parser.parse_file("common/technology.txt"):
        for n2, v2 in v:
            for _, v3 in v2:
                for n4, _ in v3:
                    if isinstance(n4.val, str):
                        n4.val = n4.val.lower()
            tech[n2.val] = v2
    return tech


# build set of true triggers given tech level, culture, religion, govt, etc
# include holding type of capital (assume all levies come from it too?)
def build_state(
    game_data,
    tech_level=0,
    religion="",
    culture="",
    government="",
    holding_type="feudal",
    vassals=[],
):
    # would need more flexible system for merchant republic's family palaces
    # since they do have e.g. + morale buildings
    religion_group = game_data["religions"].get(religion)
    culture_group = game_data["cultures"].get(culture)
    state = {
        "capital_holding": {
            "location": "capital_province",  # scope
            "holding_type": [holding_type],  # todo compute from government?
            # no specifics
            "title": [],
            "has_building": [],
        },
        "capital_province": {
            "holder_scope": "ruler",  # scope
            "location": "capital_province",  # scope
            "empire": "capital_empire",  # scope
            "culture": [culture],
            "culture_group": [culture_group],
            "religion": [religion],
            "religion_group": [religion_group],
            # no specifics
            "terrain": [],
            "region": [],
            "province": 0,
            "port": [],
            "borders_major_river": [],
            "borders_lake": [],
            "has_trade_post": [],
            "has_building": [],
            "has_province_flag": [],
            "has_province_modifier": [],
            "herdstone_location_trigger": ["no"],
        },
        "capital_empire": {
            # no specifics
            "title": [],
        },
        "ruler": {
            "capital_scope": "capital_province",  # scope
            "any_vassal": "vassal",  # scope
            "can_use_retinue_trigger": ["yes"],
            "ai": ["no"],
            "culture": [culture],
            "culture_group": [culture_group],
            "religion": [religion],
            "religion_group": [religion_group],
            "higher_tier_than": ["BARON", "COUNT", "DUKE", "KING"],
            "government": [government],
            "is_nomadic": [
                "yes"
                if game_data["govt"].get(government) == "nomadic_governments"
                else "no"
            ],
            "is_tribal": [
                "yes"
                if game_data["govt"].get(government) == "tribal_governments"
                else "no"
            ],
            "high_engineering_tech_trigger": ["yes" if tech_level >= 5 else "no"],
            "prestige": math.inf,
            # no specifics
            "trait": ["creature_human"],  # hardcoded for now
            "has_landed_title": [],
            "has_law": [],
            "is_daemon_prince_trigger": ["no"],
            "is_vampire_visible_trigger": ["no"],
        },
        "vassal": {"has_landed_title": vassals},
        "battle": {
            "leader": "commander",  # scope
            "location": "battle_province",  # scope
            "always": ["yes"],
            "is_flanking": ["no"],
            "flank_has_leader": ["yes"],
        },
        "commander": {
            "liege": "ruler",  # scope
            "location": "battle_province",  # scope
            "martial": 18,
            "learning": 12,
            # no specifics
            "is_ruler": ["no"],
            "culture": [culture],
            "culture_group": [culture_group],
            "religion": [religion],
            "religion_group": [religion_group],
            "trait": ["creature_human"],  # hardcoded for now
            "is_trained_mage_trigger": [],
            "has_character_modifier": [],
            "society_member_of": [],
        },
        "battle_province": {
            # no specifics
            "num_of_settlements": 3,
            "terrain": [],
        },
        "tech_level": tech_level,
    }

    for t in game_data["tech"]:
        state["capital_province"][t.lower()] = tech_level
        state["ruler"][t.lower()] = tech_level

    # keys should never be strings, only numbers or lists of strings,
    # unless they're scope relations like location
    return state


def evaluate_trigger(trigger, state, context, game_data):
    if debug:
        # vanilla wrong-culture wrong-government
        # wh reiklander sigmarite urban feudal
        known = {
            "ai",
            "always",
            "and",
            "any_current_enemy",
            "any_demesne_title",
            "any_liege",
            "any_owned_bloodline",
            "any_vassal",
            "borders_lake",
            "borders_major_river",
            "can_use_retinue_trigger",
            "capital_holding",
            "capital_scope",
            "culture_group",
            "culture",
            "custom_tooltip",
            "days",
            "empire",
            "enemy",
            "factor",
            "flank_has_leader",
            "from",
            "fromfrom",
            "government",
            "has_building",
            "has_character_modifier",
            "has_landed_title",
            "has_law",
            "has_province_flag",
            "has_province_modifier",
            "has_trade_post",
            "heavy_troops",
            "herdstone_location_trigger",
            "hidden_tooltip",
            "high_engineering_tech_trigger",
            "higher_tier_than",
            "holder_scope",
            "is_daemon_prince_trigger",
            "is_flanking",
            "is_nomadic",
            "is_ruler",
            "is_trained_mage_trigger",
            "is_tribal",
            "is_vampire_visible_trigger",
            "leader",
            "learning",
            "liege",
            "light_troops",
            "location",
            "martial",
            "nor",
            "not",
            "num_of_settlements",
            "or",
            "phase",
            "port",
            "prestige",
            "province",
            "region",
            "religion_group",
            "religion",
            "root",
            "society_member_of",
            "terrain",
            "text",
            "title",
            "trait",
            "troops",
        }

    def evaluate(trigger, context):
        match context["op"]:
            case "AND":
                short_circuit = False
            case "OR" | "NOR" | "NOT":
                short_circuit = True
            case _:
                print(context["op"])
                assert False
        for p in trigger:
            n, v = p
            key = n.val.lower()
            if (
                debug
                and key not in known
                and not key.startswith("tech_")
                and not key in game_data["troops"]
            ):
                print(context["THIS"], n.val)
                assert False
            if isinstance(v, Obj):
                next_context = context | {"op": "AND"}
                if key in ["from", "fromfrom", "root"]:
                    next_context = next_context | {
                        "THIS": context[key.upper()],
                        "PREV": context["THIS"],  # put PREVPREV if needed
                    }
                elif key in [
                    "any_vassal",
                    "capital_scope",
                    "empire",
                    "holder_scope",
                    "leader",
                    "liege",
                    "location",
                ]:
                    next_context = next_context | {
                        "THIS": state[context["THIS"]][key],
                        "PREV": context["THIS"],
                    }
                elif key in ["or", "nor"]:
                    next_context = next_context | {"op": key.upper()}
                elif key == "not":
                    next_context = next_context | {"op": "NOR"}
                if key in [
                    "any_current_enemy",
                    "any_demesne_title",
                    "any_liege",
                    "any_owned_bloodline",
                    "capital_holding",
                    "enemy",
                ]:
                    # special case preemptive always false
                    result = False
                elif key in ["troops", "light_troops", "heavy_troops"]:
                    try:
                        result = (
                            state[context["THIS"]][key][v["who"].val] >= v["value"].val
                        )
                    except:
                        print(state[context["THIS"]])
                        raise
                else:
                    result = evaluate(v, next_context)
                if next_context["op"] in ["NOR", "NOT"]:
                    result = not result
            elif isinstance(v.val, str):
                if key == "text":
                    continue
                assert p.op.val == "="
                result = v.val in state[context["THIS"]][key]
            else:
                if key == "factor":
                    continue
                if p.op.val == "=":
                    # not correct for all numbers... e.g. province = 1234
                    result = state[context["THIS"]][key] >= v.val
                elif p.op.val == ">":
                    result = state[context["THIS"]][key] > v.val
                else:
                    assert False
            if result == short_circuit:
                return result
        return not short_circuit

    return evaluate(trigger, context | {"op": "AND", "THIS": context["ROOT"]})


# todo for levies,
# need settlement base modifiers from common/static_modifiers.txt for troops.


# given tech level, culture, religion, and government,
# list all possible buildings
def filter_buildings(game_data, state):
    result = {}
    replaced = set()
    context = {
        "ROOT": "capital_province",
        "FROM": "ruler",
        "FROMFROM": "capital_holding",
    }
    for n, b in game_data["buildings"].items():
        if b.get("port") == "yes":
            continue  # skip port-only buildings for now
        if b["holding_type"] not in state["capital_holding"]["holding_type"]:
            continue
        try:
            if not evaluate_trigger(b["potential"], state, context, game_data):
                continue
        except:
            print(n)
            raise
        # todo filter out buildings with missing prerequisite or upgrades_from
        # building is possible
        result[n] = b
        if b2 := b.get("replaces"):
            replaced.add(b2)
    for n in replaced:
        if n in result:
            del result[n]
    return result


def compute_troop_bonuses(game_data, state, built):
    state["troop_bonus"] = {}
    for troop in game_data["troops"]:
        for stat in ["offensive", "defensive", "morale"]:
            troop_stat_modifier = f"{troop}_{stat}"
            state["troop_bonus"][troop_stat_modifier] = 0
            for tech in game_data["tech"].values():
                if v := tech["modifier"].get(troop_stat_modifier):
                    # assume all military bonuses are constant per tech level
                    state["troop_bonus"][troop_stat_modifier] += (
                        v.val * state["tech_level"] / constants["max_tech"]
                    )
            for building in built.values():
                state["troop_bonus"][troop_stat_modifier] += building.get(
                    troop_stat_modifier, 0
                )


# given tech level, culture, religion, and government,
# list all possible retinues
def filter_retinues(game_data, state):
    result = {}
    context = {"ROOT": "ruler"}
    for n, b in game_data["retinues"].items():
        try:
            if not evaluate_trigger(b["potential"], state, context, game_data):
                continue
        except:
            print(n)
            raise
        # retinue is possible
        result[n] = b
    return result


def flank_calc_tactics(game_data, state, flank):
    # compute troops from retinues
    flank["troops"] = {}
    flank["total_troops"] = 0
    for retinue, number in flank["retinues"].items():
        r = game_data["retinues"][retinue]
        for troop_name in game_data["troops"]:
            if n := r.get(troop_name):
                if troop_name not in flank["troops"]:
                    flank["troops"][troop_name] = 0
                flank["troops"][troop_name] += n * number
                flank["total_troops"] += n * number
    # build troop state
    state = dict(state)
    troop_state = {k: 0 for k in game_data["troops"]}
    troop_state["troops"] = {}
    troop_state["light_troops"] = {}
    troop_state["heavy_troops"] = {}
    troop_groups = {"light_troops": 0, "heavy_troops": 0}
    # naked %, precise %, group %
    for troop_name, troop in game_data["troops"].items():
        # assume no base types have base types of their own
        troop_count = flank["troops"].get(troop_name, 0)
        proportion = troop_count / flank["total_troops"]
        troop_state[troop_name] += proportion
        troop_state["troops"][troop_name] = proportion
        # little unclear what to do with war elephants -
        # logic would dictate they are not heavy troops, but spreadsheet
        # and wiki both think they are, in places. here, not heavy.
        if (base_type := troop.get("base_type")) and base_type in game_data["troops"]:
            troop_state[base_type] += proportion
            group_check = base_type
        else:
            group_check = troop_name
        for group in troop_groups:
            troop_state[group][troop_name] = troop_count
            if group_check in constants[group]:
                troop_groups[group] += troop_count
    # divide by total
    for group, total_group in troop_groups.items():
        if total_group > 0:
            for k, v in troop_state[group].items():
                troop_state[group][k] = v / total_group

    flank["tactics"] = {}
    flank["phase_change"] = {}
    context = {"ROOT": "battle"}
    phase_states = [
        {"name": "skirmish", "phase": "skirmish", "days": 0},
        {"name": "skirmish10", "phase": "skirmish", "days": 10},
        {"name": "melee", "phase": "melee", "days": 10},
        {"name": "pursue", "phase": "pursue", "days": 10},
    ]
    for phase_state in phase_states:
        total_weight = 0
        flank["tactics"][phase_state["name"]] = {}
        for t_name, tactic in game_data["tactics"].items():
            this_state = state | {"battle": state["battle"] | troop_state | phase_state}
            try:
                if not evaluate_trigger(
                    tactic["trigger"], this_state, context, game_data
                ):
                    continue
            except:
                print(t_name)
                raise
            # tactic is possible
            weight = tactic["mean_time_to_happen"]["days"].val
            for n, v in tactic["mean_time_to_happen"]:
                if n.val == "modifier":
                    factor = v["factor"].val
                    try:
                        if evaluate_trigger(v, this_state, context, game_data):
                            weight *= factor
                    except:
                        print(t_name)
                        raise
            # weight calculated
            total_weight += weight
            flank["tactics"][phase_state["name"]][t_name] = weight
        # divide by total
        for k, v in flank["tactics"][phase_state["name"]].items():
            chance = v / total_weight
            flank["tactics"][phase_state["name"]][k] = chance
            if v := game_data["tactics"][k].get("change_phase_to"):
                if phase_state["name"] not in flank["phase_change"]:
                    flank["phase_change"][phase_state["name"]] = {}
                if v not in flank["phase_change"][phase_state["name"]]:
                    flank["phase_change"][phase_state["name"]][v] = 0
                flank["phase_change"][phase_state["name"]][v] += chance
            # else:
            #     flank["phase_change"][phase_state["name"]][phase_state["phase"]] += chance


# given tech level, retinues, and buildings,
# ...
def flank_calc(game_data, state, flank):
    defines_m = game_data["defines"]["NMilitary"]
    # 0.01 dmg / atk
    k = defines_m["ATTACK_TO_DAMAGE_MULT"]
    # 2.5% / month
    r = defines_m["RETINUE_REINFORCE_RATE"]
    # 0.12 gold (baseline casualty cost)
    casualty = defines_m["RETINUE_REINFORCE_COST"] / 1000 / r
    omega = (1 - defines_m["MORALE_COLLAPSE_THRESHOLD"]) / defines_m[
        "MORALELOSS_FACTOR"
    ]
    kappa = defines_m["DEATH_MORALE_DAMAGE"]

    flank["usage"] = sum(
        n * game_data["retinues"][r]["usage"] for r, n in flank["retinues"].items()
    )
    flank["c"] = {}
    for stat_name, stat_adj in [
        ("attack", "offensive"),
        ("defense", "defensive"),
        ("morale", "morale"),
    ]:
        flank[stat_name] = {}
        for this_phase, tactics in flank["tactics"].items():
            if stat_name == "morale":
                if not isinstance(flank[stat_name], dict):
                    continue
                flank[stat_name] = 0
            else:
                flank[stat_name][this_phase] = 0
            if stat_name == "defense":
                flank["c"][this_phase] = 0  # avg cost per casualty (C_θ)
            for troop_type, troop_data in game_data["troops"].items():
                troop_stat_modifier = f"{troop_type}_{stat_adj}"
                for retinue, number in flank["retinues"].items():
                    bonus = 1
                    # retinue bonus
                    retinue_data = game_data["retinues"][retinue]
                    if v := retinue_data["modifier"].get(troop_stat_modifier):
                        bonus += v.val
                    # tech and building bonuses
                    bonus += state["troop_bonus"][troop_stat_modifier]
                    # terrain bonus
                    pass
                    if stat_name == "morale":
                        stat = troop_data["morale"]
                    else:
                        # tactic bonuses
                        pre_tactics_bonus = bonus
                        for t_name, chance in tactics.items():
                            tactic = game_data["tactics"][t_name]
                            if v := tactic.get(troop_stat_modifier):
                                # overall, attack < 0 is clamped to 0
                                # negative bonus here can offset positives but not to below zero
                                bonus += chance * max(v, -pre_tactics_bonus)
                        # base stat of the tactic's phase
                        stat = 0
                        no_change = 1
                        if pc := flank["phase_change"].get(this_phase):
                            no_change -= sum(pc.values())
                            for phase, c in pc.items():
                                stat += c * troop_data[f"phase_{phase}_{stat_name}"]
                        mod = f"phase_{this_phase.rstrip('10')}_{stat_name}"
                        stat += no_change * troop_data[mod]
                    retinue_troop_count = retinue_data.get(troop_type, 0) * number
                    if stat_name == "attack":
                        # A = sum_troop(troop_count * troop_attack) * k / total_troops
                        flank[stat_name][this_phase] += (
                            retinue_troop_count * stat * bonus
                        )
                    elif stat_name == "defense":
                        # θ/ND (something like unit type casualty rate per troop, 1 / dmg)
                        casualty_rate = retinue_troop_count / (stat * bonus)
                        flank[stat_name][this_phase] += casualty_rate
                        this_cost = (
                            casualty
                            * troop_data["maintenance"]
                            * game_data["retinues"][retinue].get(
                                "maintenance_multiplier", 1
                            )
                            * casualty_rate
                        )
                        flank["c"][this_phase] += this_cost
                    else:
                        flank[stat_name] += retinue_troop_count * stat * bonus
            if stat_name == "defense":
                # sum(troop_casualty_cost * troop_count / troop_defense) / sum(troop_count / troop_defense)
                flank["c"][this_phase] /= flank[stat_name][this_phase]
                # Δ = 1/sum_troop(troop_count / troop_defense) * total_troops
                flank[stat_name][this_phase] = 1 / flank[stat_name][this_phase]

    flank["o"] = {}  # offense (offense parameter A, dmg/trp)
    flank["no"] = {}  # normalized offense (1)
    flank["oe"] = {}  # offensive efficiency (cost-effectiveness CE_o, dmg/usg)
    flank["noe"] = {}  # normalized offensive efficiency (η_o, 1)
    flank["d"] = {}  # defense (defense parameter Δ, dmg/trp)
    flank["de"] = {}  # defensive efficiency (cost-effectiveness CE_d, dmg/gold)
    flank["nde"] = {}  # normalized defensive efficiency (η_d, 1)
    flank["u"] = flank["usage"] / flank["total_troops"]  # usage (U, usg/trp)
    flank["m"] = {}  # morale (morale parameter F, dmg/trp)
    flank["nm"] = {}  # normalized morale (1)
    flank["me"] = {}  # defensive efficiency (cost-effectiveness CE_m, dmg/usg)
    flank["nme"] = {}  # normalized morale efficiency (η_m, 1)
    for phase, attack in flank["attack"].items():
        flank["o"][phase] = k * attack / flank["total_troops"]
        if standard := constants["standard_o"].get(phase):
            flank["no"][phase] = flank["o"][phase] / standard
        flank["oe"][phase] = flank["o"][phase] / flank["u"]
        if standard := constants["standard_oe"].get(phase):
            flank["noe"][phase] = flank["oe"][phase] / standard
    # monthly reinforcement cost (gold per month per troop) (the upkeep also doesn't stop)
    #     = RETINUE_REINFORCE_COST(3)/1000 * troop maintenance number * maintenance_multiplier
    # cost per casualty (gold per troop)
    #     = monthly reinforcement cost / RETINUE_REINFORCE_RATE(0.025)
    total_cost = 0
    for retinue, number in flank["retinues"].items():
        maint_mult = game_data["retinues"][retinue].get("maintenance_multiplier", 1)
        for troop_type, troop_data in game_data["troops"].items():
            retinue_troop_count = retinue_data.get(troop_type, 0) * number
            total_cost += (
                casualty * troop_data["maintenance"] * maint_mult * retinue_troop_count
            )
    for phase, defense in flank["defense"].items():
        flank["d"][phase] = defense * flank["total_troops"]
        flank["de"][phase] = flank["d"][phase] / flank["c"][phase]
        if standard := constants["standard_de"].get(phase):
            flank["nde"][phase] = flank["de"][phase] / standard
        if phase != "pursue":
            flank["m"][phase] = (omega * flank["morale"]) / (
                flank["total_troops"] * (1 + kappa / flank["d"][phase])
            )
            if standard := constants["standard_m"].get(phase):
                flank["nm"][phase] = flank["m"][phase] / standard
            flank["me"][phase] = flank["m"][phase] / flank["u"]
            if standard := constants["standard_me"].get(phase):
                flank["nme"][phase] = flank["me"][phase] / standard
    flank["sarcem"] = math.sqrt(flank["noe"]["skirmish"] * flank["nme"]["skirmish"])
    flank["marcem"] = math.sqrt(flank["noe"]["melee"] * flank["nme"]["melee"])
    flank["parcem"] = math.sqrt(flank["noe"]["pursue"] * flank["nde"]["pursue"])
    flank["slash"] = " / ".join(f"{flank[x + 'arcem']:.3f}" for x in "smp")


def evaluate_flank(game_data, state, flank):
    flank_calc_tactics(game_data, state, flank)
    flank_calc(game_data, state, flank)


def output_flank_summary(flank):
    print(
        {
            k: v
            for k, v in flank.items()
            if k in ["retinues", "troops", "total_troops", "tactics", "phase_change"]
        }
    )
    print(flank["slash"])
    ps = "skirmish", "melee"
    print(f"         {ps[0]}          |           {ps[1]}")
    print(" | ".join(f"   morale efficiency {flank['nme'][p]:5.0%}" for p in ps))
    print(" | ".join(f"offensive efficiency {flank['noe'][p]:5.0%}" for p in ps))
    print(" | ".join(f"           fortitude {flank['nm'][p]:5.0%}" for p in ps))
    print(" | ".join(f"           intensity {flank['no'][p]:5.0%}" for p in ps))
    # todo print tactics breakdown more nicely
    # todo iterate over singles, pairs, and triples of retinues
    #   with, idk, 1-10 magnitudes
    # sort by sarcem + marcem?
    # (sarcem * A_s + marcem * A_m)?


@print_time
def main():
    # neglects religion unit bonuses e.g. reformed tengri
    parser = SimpleParser()
    parser.moddirs = get_modpath()
    game_data = {}
    game_data["defines"] = get_defines(parser)
    game_data["troops"] = get_troops(parser, game_data)
    game_data["buildings"] = get_buildings(parser, game_data)
    game_data["retinues"] = get_retinues(parser, game_data)
    game_data["tactics"] = get_tactics(parser, game_data)
    game_data["tech"] = get_tech(parser)
    game_data["cultures"] = get_cultures(parser)
    game_data["religions"] = get_religions(parser)
    game_data["govt"] = get_governments(parser)
    # state = build_state(
    #     game_data,
    #     tech_level=4,
    #     religion="sigmarite",
    #     culture="reiklander",
    #     government="imperial_government",
    #     vassals=[
    #         "k_stirland",
    #         "k_nordland",
    #         "k_talabecland",
    #         "k_averland",
    #         "k_middenland",
    #         "k_reikland",
    #         "k_hochland",
    #         "k_ostland",
    #         "k_ostermark",
    #         "k_westerland",
    #         "k_wissenland",
    #     ],
    # )
    # state = build_state(
    #     game_data,
    #     tech_level=8,
    #     religion="stromfels",
    #     culture="sartosan_tilean",
    #     government="pirate_government",
    # state = build_state(
    #     game_data,
    #     tech_level=8,
    #     religion="slaanesh",
    #     culture="gharhar",
    #     government="chaos_horde_government",
    #     holding_type="nomad",
    # )
    # state["capital_empire"]["title"] = ["e_chaos_wastes"]
    # )
    state = build_state(
        game_data,
        tech_level=8,
        religion="ulrican",
        culture="albion_main",
        government="feudal",
    )
    # state = build_state(game_data, tech_level=0)
    # state = build_state(game_data, culture="bedouin_arabic", tech_level=0)

    # full tech for the sake of buildings (spreadsheet emulation)
    # for t in game_data["tech"]:
    #     state["capital_province"][t.lower()] = 8
    built = filter_buildings(game_data, state)
    # reset tech for the sake of combat (spreadsheet emulation)
    # for t in game_data["tech"]:
    #     state["capital_province"][t.lower()] = state["tech_level"]

    compute_troop_bonuses(game_data, state, built)
    retinue_options = filter_retinues(game_data, state)

    built_display = list(built)
    for b in built.values():
        if b2 := b.get("upgrades_from"):
            if b2 in built_display:
                built_display.remove(b2)
    print(*built_display)
    print(*retinue_options)
    print()

    # flank = {"retinues": {list(retinue_options)[4]: 1}}
    # flank = {"retinues": {"RETTYPE_OSTLANDEROGRES": 1}}

    # evaluate_flank(game_data, state, built, flank)
    # output_flank_summary(flank)

    comps = []
    # # melee oriented
    # {"RETTYPE_CUL_ITA": 11, "RETTYPE_INF2": 1},
    # {"RETTYPE_CUL_SCOT": 11, "RETTYPE_INF2": 1},
    # {"RETTYPE_CUL_ITA": 1, "RETTYPE_INF1": 1},
    # {"RETTYPE_CUL_ROMAN": 6, "RETTYPE_INF1": 1},
    # {"RETTYPE_CUL_SCOT": 13, "RETTYPE_SKIR2": 4},
    # {"RETTYPE_INF2": 1},
    # {"RETTYPE_CUL_JEWISH": 23, "RETTYPE_INF1": 1},
    # {"RETTYPE_CUL_NORTHGER": 23, "RETTYPE_INF1": 1},
    # {"RETTYPE_CUL_RUS": 19, "RETTYPE_INF1": 1},
    # {"RETTYPE_CUL_IRISH": 23, "RETTYPE_INF1": 1},
    # {"RETTYPE_CUL_FRA": 23, "RETTYPE_INF1": 1},
    # {"RETTYPE_CUL_LOM": 15, "RETTYPE_INF1": 1},
    # {"RETTYPE_CUL_BALT": 15, "RETTYPE_INF1": 1},
    # {"RETTYPE_CUL_ASSYRIAN": 15, "RETTYPE_INF1": 1},
    # {"RETTYPE_INF1": 1},
    # skirmish oriented (melee change <33%)
    # {"RETTYPE_CUL_ETHIO": 22, "RETTYPE_INF2": 1, "RETTYPE_INF1": 1},
    # {"RETTYPE_CUL_SOMALI": 22, "RETTYPE_INF2": 1, "RETTYPE_INF1": 1},
    # {"RETTYPE_CUL_PICTISH": 1},
    # {"RETTYPE_CUL_W_AFR": 1},
    # {"RETTYPE_SKIR2": 1},
    # {"RETTYPE_CUL_ENG": 4, "RETTYPE_SKIR2": 9},
    # {"RETTYPE_CUL_NUBIAN": 3, "RETTYPE_SKIR2": 8},
    # {"RETTYPE_CUL_ENG": 7, "RETTYPE_SKIR2": 4},
    # {"RETTYPE_CUL_ENG": 4, "RETTYPE_INF1": 1, "RETTYPE_INF2": 1, "RETTYPE_SKIR2": 1},
    # {"RETTYPE_CUL_NUBIAN": 3, "RETTYPE_SKIR2": 2},
    # balanced
    # {"RETTYPE_CUL_ARAB": 6, "RETTYPE_SKIR2": 1},
    # {"RETTYPE_CUL_ARAB": 1},
    # {"RETTYPE_CUL_TIBET": 1},
    # {"RETTYPE_CUL_OUTREMER": 1},
    # {"RETTYPE_CUL_BERBER": 4, "RETTYPE_SKIR2": 1},
    # {"RETTYPE_CUL_ANDALUSIAN": 4, "RETTYPE_SKIR2": 1},
    # {"RETTYPE_CUL_DUTCH": 11, "RETTYPE_INF2": 1},
    # {"RETTYPE_CUL_SUEBI": 13, "RETTYPE_INF2": 1},
    # {"RETTYPE_CUL_ARBERIAN": 8, "RETTYPE_SKIR2": 1},
    # {"RETTYPE_CUL_NAHUA": 28, "RETTYPE_SKIR2": 1},
    # {"RETTYPE_CUL_NAHUA": 9, "RETTYPE_INF1": 1},
    # {"RETTYPE_CUL_JURCHEN": 1},
    # {"RETTYPE_CUL_FRANK_NOR_GER": 1},
    # {"RETTYPE_CUL_IBER": 4, "RETTYPE_SKIR2": 1},
    # {"RETTYPE_CUL_SOUTH_SLA": 1},
    # {"RETTYPE_CUL_IBER": 4, "RETTYPE_SKIR2": 1},
    # {"RETTYPE_CUL_HUNG": 5, "RETTYPE_SKIR2": 1},
    # {"RETTYPE_CUL_HUNG": 5, "RETTYPE_SKIR2": 1},
    # {"RETTYPE_CUL_ITA": 2, "RETTYPE_SKIR2": 3, "RETTYPE_INF1": 2},
    # {"RETTYPE_CAV1": 6, "RETTYPE_CUL_FRANK_NOR_GER": 1},
    # {"RETTYPE_CUL_FRANK_NOR_GER": 4, "RETTYPE_INF2": 1},
    # {"RETTYPE_CUL_ROMAN": 4, "RETTYPE_SKIR2": 3, "RETTYPE_SKIR1": 2},
    # {"RETTYPE_CUL_BYZ": 1},
    # {"RETTYPE_CAV1": 7, "RETTYPE_INF2": 1},
    # {"RETTYPE_CAV1": 32, "RETTYPE_SKIR2": 1},
    # {"RETTYPE_CUL_BYZ": 2, "RETTYPE_CAV1": 1},
    # {"RETTYPE_CUL_SCOT": 5, "RETTYPE_SKIR2": 9, "RETTYPE_INF1": 5},
    # {"RETTYPE_CUL_NORTHGER": 5, "RETTYPE_SKIR2": 4, "RETTYPE_INF2": 2},
    # {"RETTYPE_CUL_COPTIC": 1},
    # {"RETTYPE_INF2": 5, "RETTYPE_INF1": 3, "RETTYPE_SKIR2": 1},
    # {"RETTYPE_INF2": 5, "RETTYPE_INF1": 3, "RETTYPE_SKIR2": 1},
    # {"RETTYPE_CUL_ALTAIC": 1},
    # {"RETTYPE_CUL_HAN": 3, "RETTYPE_INF2": 1},
    # {"RETTYPE_CUL_SAR": 1},
    # {"RETTYPE_SKIR1": 7, "RETTYPE_INF1": 15},
    # {"RETTYPE_SKIR1": 7, "RETTYPE_INF2": 2},
    # {"RETTYPE_CUL_INDIAN": 13, "RETTYPE_INF2": 7},
    # {"RETTYPE_SKIR1": 11, "RETTYPE_INF1": 6},
    if not comps:
        for r in retinue_options:
            comps.append({r: 1})
        for r1, r2 in combinations(retinue_options, 2):
            # if {'chaosspawn', 'chaosforsaken'} & {r1, r2} and 'chaostrolls' not in {r1, r2}:
            #     continue
            seen = set()
            for n1 in range(1, 24):
                for n2 in range(1, 24):
                    gcd = math.gcd(n1, n2)
                    n1 //= gcd
                    n2 //= gcd
                    if (n1, n2) not in seen:
                        comps.append({r1: n1, r2: n2})
                        seen.add((n1, n2))
        # for r1, r2, r3 in combinations(retinue_options, 3):
        #     seen = set()
        #     for n1 in range(1, 10):
        #         for n2 in range(1, 10 if n1 == 1 else 2):
        #             for n3 in range(1, 10 if n1 == 1 and n2 == 1 else 2):
        #                 gcd = math.gcd(n1, n2, n3)
        #                 n1 //= gcd
        #                 n2 //= gcd
        #                 n3 //= gcd
        #                 if (n1, n2, n3) not in seen:
        #                     comps.append({r1: n1, r2: n2, r3: n3})
        #                     seen.add((n1, n2, n3))
    flanks = []
    for i, comp in enumerate(comps):
        flank = {"retinues": comp}
        # if "RETTYPE_CUL_ENG" in comp:
        #     state["commander"]["culture"].append("english")
        # if "RETTYPE_CUL_ALTAIC" in comp:
        #     state["commander"]["culture_group"].append("altaic")
        # if "RETTYPE_CUL_OUTREMER" in comp or "RETTYPE_CUL_FRANK_NOR_GER" in comp:
        #     state["commander"]["culture"].append("german")
        # if "RETTYPE_CUL_ITA" in comp or "RETTYPE_CUL_ROMAN" in comp:
        #     state["commander"]["culture"].append("italian")
        # if "RETTYPE_CUL_SCOT" in comp:
        #     state["commander"]["culture"].append("scottish")
        # if "RETTYPE_CUL_NORTHGER" in comp:
        #     state["commander"]["culture_group"].append("north_germanic")
        evaluate_flank(game_data, state, flank)
        # if "RETTYPE_CUL_ENG" in comp:
        #     state["commander"]["culture"].remove("english")
        # if "RETTYPE_CUL_ALTAIC" in comp:
        #     state["commander"]["culture_group"].remove("altaic")
        # if "RETTYPE_CUL_OUTREMER" in comp or "RETTYPE_CUL_FRANK_NOR_GER" in comp:
        #     state["commander"]["culture"].remove("german")
        # if "RETTYPE_CUL_ITA" in comp or "RETTYPE_CUL_ROMAN" in comp:
        #     state["commander"]["culture"].remove("italian")
        # if "RETTYPE_CUL_SCOT" in comp:
        #     state["commander"]["culture"].remove("scottish")
        # if "RETTYPE_CUL_NORTHGER" in comp:
        #     state["commander"]["culture_group"].remove("north_germanic")
        # score1 = flank["sarcem"] + flank["marcem"]
        # score1 = flank["marcem"]
        # score1 = (
        #     flank["noe"]["skirmish"] * flank["nme"]["skirmish"]
        #     + flank["noe"]["melee"] * flank["nme"]["melee"]
        # )
        charge = flank["phase_change"].get("skirmish10", {}).get("melee", 0.5)
        score1 = (1 - charge) * flank["noe"]["skirmish"] * flank["nme"][
            "skirmish"
        ] + charge * flank["noe"]["melee"] * flank["nme"]["melee"]
        # score1 = (
        #     (1 - charge) * flank["noe"]["skirmish"] * flank["nme"]["skirmish"]
        #     + flank["noe"]["melee"] * flank["nme"]["melee"]
        # )
        # score1 = (1 - charge) * flank["o"]["skirmish"] * flank["m"]["skirmish"] + flank[
        #     "o"
        # ]["melee"] * flank["m"]["melee"]
        # score1 = flank["sarcem"] + flank["marcem"] + 0.5 * flank["parcem"]
        # score2 = flank["sarcem"] * flank["marcem"]
        # score3 = (
        #     flank["sarcem"] * flank["o"]["skirmish"]
        #     + flank["marcem"] * flank["o"]["melee"]
        # )
        flanks.append((score1, flank))
        if i % 500 == 0:
            print(f"{i/len(comps):.1%}")
    flanks.sort(key=(lambda x: -x[0]))
    for *_, flank in reversed(flanks[:10]):
        print("--------------------")
        output_flank_summary(flank)
    # for *_, flank in flanks:
    #     print(flank["retinues"])
    #     print(f"{flank['phase_change']['skirmish10']['melee']:2.1%}")
    # print("--------------------")
    # print("--------------------")
    # flanks.sort(key=(lambda x: -x[1]))
    # for *_, flank in reversed(flanks[:10]):
    #     print("--------------------")
    #     output_flank_summary(flank)
    # print("--------------------")
    # flanks.sort(key=(lambda x: -x[2]))
    # for *_, flank in reversed(flanks[:10]):
    #     print("--------------------")
    #     output_flank_summary(flank)


if __name__ == "__main__":
    main()
