import os, sys
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from eu4.paths import eu4_major_version, eu4outpath
from eu4.mapparser import Eu4Parser
from eu4.eu4lib import Idea, Policy

class ModifierType():
    def __init__(self, name, icons):
        self.name = name
        self.icons = icons

    def format_value(self, value, other_values):
        if isinstance(value, str):
            return value
        else:
#             if type(value) == float and round(value) != value:
            if self.max_decimal_places(other_values) > 0:
                formatstring = ':.{}f'.format(self.max_decimal_places(other_values))
            else:
                formatstring = ''
            if value > 0:
                return ('+{'+formatstring + '}').format(value)
            else:
                return ('−{'+formatstring + '}').format(value * -1)

    def max_decimal_places(self, value_list):
        return max([self.count_decimal_places(value) for value in value_list])

    def count_decimal_places(self, value):
        str_value = str(value)
        if '.' in str_value:
            str_value = re.sub('0+$', '', str_value)
            return len(str_value.split('.')[1])
        else:
            return 0

class MultiplicativeModifier(ModifierType):
    def modify_value(self, value):
        value = value*100
        if value == round(value): # no decimal places
            value = int(value)
        return value

    def format_value(self, value, other_values):
        return super().format_value(self.modify_value(value), [self.modify_value(v) for v in other_values]) + '%'

class AdditiveModifier(ModifierType):
    pass

class ConstantModifier(ModifierType):
    pass

class LibertyDesireModifier(MultiplicativeModifier):
    def modify_value(self, value):
        return value * (-1)

all_modifiers = [
        AdditiveModifier('num_accepted_cultures', ['max promoted cultures']),
        MultiplicativeModifier('adm_tech_cost_modifier', ['adm tech cost']),
        MultiplicativeModifier('advisor_cost', ['advisor cost']),
        AdditiveModifier('advisor_pool', ['possible advisors', 'advisor pool']),
        MultiplicativeModifier('ae_impact', ['aggressive expansion impact', 'ae impact']),
        AdditiveModifier('army_tradition', ['army tradition', 'yearly army tradition']),
        MultiplicativeModifier('army_tradition_decay', ['army tradition decay']),
        MultiplicativeModifier('artillery_cost', ['art cost', 'artillery cost']),
        MultiplicativeModifier('artillery_power', ['art power', 'artillery combat ability', 'artillery power']),
        MultiplicativeModifier('blockade_efficiency', ['blockade efficiency']),
        MultiplicativeModifier('build_cost', ['construction cost']),
        MultiplicativeModifier('development_cost', ['development cost']),
        MultiplicativeModifier('cavalry_cost', ['cavalry cost', 'cav cost']),
        MultiplicativeModifier('cavalry_power', ['cav power', 'cavalry combat ability', 'cavalry power']),
        AdditiveModifier('colonists', ['colonists']),
        MultiplicativeModifier('colonist_placement_chance', ['settler chance', 'colonist chance']),
        MultiplicativeModifier('core_creation', ['core-creation cost', 'core creation cost']),
        MultiplicativeModifier('culture_conversion_cost', ['culture conversion cost']),
        MultiplicativeModifier('defensiveness', ['fort defense']),
        MultiplicativeModifier('dip_tech_cost_modifier', ['dip tech cost']),
        MultiplicativeModifier('diplomatic_annexation_cost', ['diplomatic annexation cost']),
        AdditiveModifier('diplomatic_reputation', ['diplomatic reputation']),
        AdditiveModifier('diplomatic_upkeep', ['diplomatic relations', 'diplomatic upkeep']),
        AdditiveModifier('diplomats', ['diplomats']),
        MultiplicativeModifier('discipline', ['discipline']),
        MultiplicativeModifier('embargo_efficiency', ['embargo efficiency']),
        MultiplicativeModifier('enemy_core_creation', ['hostile core-creation cost on us', 'enemy core creation']),
        MultiplicativeModifier('envoy_travel_time', ['envoy travel time']),
        MultiplicativeModifier('fabricate_claims_cost', ['cost to fabricate claims']),
        AdditiveModifier('free_leader_pool', ['leader(s) without upkeep', 'free leader pool']),
        MultiplicativeModifier('galley_cost', ['galley cost']),
        MultiplicativeModifier('galley_power', ['galley combat ability', 'galley power']),
        AdditiveModifier('global_colonial_growth', ['global settler increase']),
        MultiplicativeModifier('global_foreign_trade_power', ['trade power abroad', 'foreign trade power']),
        MultiplicativeModifier('global_garrison_growth', ['national garrison growth', 'global garrison growth']),
        MultiplicativeModifier('global_heretic_missionary_strength', ['missionary strength vs heretics', 'global heretic missionary strength']),
        MultiplicativeModifier('global_manpower_modifier', ['national manpower modifier', 'global manpower modifier']),
        MultiplicativeModifier('global_missionary_strength', ['missionary strength', 'global missionary strength']),
        MultiplicativeModifier('global_own_trade_power', ['domestic trade power']),
        MultiplicativeModifier('global_prov_trade_power_modifier', ['provincial trade power modifier', 'global prov trade power modifier']),
        MultiplicativeModifier('global_regiment_cost', ['regiment cost']),
        MultiplicativeModifier('global_regiment_recruit_speed', ['recruitment time', 'global regiment recruit speed']),
        AdditiveModifier('global_unrest', ['national unrest', 'global unrest']),
        MultiplicativeModifier('global_ship_cost', ['ship cost']),
        MultiplicativeModifier('global_ship_recruit_speed', ['shipbuilding time', 'global ship recruit speed']),
        MultiplicativeModifier('global_ship_repair', ['global ship repair']),
        MultiplicativeModifier('global_spy_defence', ['foreign spy detection']),
        MultiplicativeModifier('global_tariffs', ['global tariffs']),
        MultiplicativeModifier('global_tax_modifier', ['national tax modifier', 'global tax modifier']),
        MultiplicativeModifier('global_trade_goods_size_modifier', ['goods produced modifier']),
        MultiplicativeModifier('global_trade_power', ['global trade power']),
        MultiplicativeModifier('heavy_ship_cost', ['heavy ship cost']),
        MultiplicativeModifier('heavy_ship_power', ['heavy ship combat ability', 'heavy ship power']),
        MultiplicativeModifier('heir_chance', ['chance of new heir', 'heir chance']),
        AdditiveModifier('hostile_attrition', ['attrition for enemies', 'hostile attrition']),
        MultiplicativeModifier('idea_cost', ['idea cost']),
        MultiplicativeModifier('imperial_authority', ['imperial authority growth modifier']),
        AdditiveModifier('imperial_authority_value', ['imperial authority modifier']),
        MultiplicativeModifier('improve_relation_modifier', ['improve relations', 'improve relation modifier']),
        MultiplicativeModifier('infantry_cost', ['inf cost', 'infantry cost']),
        MultiplicativeModifier('infantry_power', ['inf power', 'infantry combat ability', 'infantry power']),
        AdditiveModifier('inflation_reduction', ['inflation reduction']),
        AdditiveModifier('interest', ['interest per annum', 'interest']),
        MultiplicativeModifier('justify_trade_conflict_cost', ['cost to justify trade conflict', 'justify trade conflict cost']),
        MultiplicativeModifier('land_attrition', ['land attrition']),
        MultiplicativeModifier('land_forcelimit_modifier', ['land force limit modifier', 'land forcelimit modifier']),
        MultiplicativeModifier('land_maintenance_modifier', ['land maintenance modifier']),
        MultiplicativeModifier('land_morale', ['morale of armies', 'land morale']),
        AdditiveModifier('leader_land_fire', ['land leader fire']),
        AdditiveModifier('leader_land_manuever', ['land leader maneuver']),
        AdditiveModifier('leader_land_shock', ['land leader shock']),
        AdditiveModifier('leader_naval_fire', ['naval leader fire']),
        AdditiveModifier('leader_naval_manuever', ['naval leader maneuver']),
        AdditiveModifier('leader_naval_shock', ['naval leader shock']),
        AdditiveModifier('leader_siege', ['leader siege']),
        AdditiveModifier('legitimacy', ['legitimacy', 'yearly legitimacy']),
        MultiplicativeModifier('light_ship_cost', ['light ship cost']),
        MultiplicativeModifier('light_ship_power', ['light ship combat ability', 'light ship power']),
        MultiplicativeModifier('manpower_recovery_speed', ['manpower recovery speed']),
        ConstantModifier('may_explore', ['may explore']),
        ConstantModifier('may_perform_slave_raid', ['may raid coasts']),
        MultiplicativeModifier('merc_maintenance_modifier', ['mercenary maintenance', 'merc maintenance modifier']),
        MultiplicativeModifier('mercenary_cost', ['mercenary cost']),
        MultiplicativeModifier('caravan_power', ['caravan power']),
        AdditiveModifier('merchants', ['merchants']),
        MultiplicativeModifier('mil_tech_cost_modifier', ['mil tech cost']),
        MultiplicativeModifier('migration_cooldown', ['migration cooldown']),
        AdditiveModifier('missionaries', ['missionaries']),
        AdditiveModifier('monthly_fervor_increase', ['monthly fervor', 'monthly fervor increase']),
        MultiplicativeModifier('naval_attrition', ['naval attrition']),
        MultiplicativeModifier('naval_forcelimit_modifier', ['naval force limit modifier', 'naval forcelimit modifier']),
        MultiplicativeModifier('naval_maintenance_modifier', ['naval maintenance modifier']),
        MultiplicativeModifier('naval_morale', ['morale of navies', 'naval morale']),
        AdditiveModifier('navy_tradition', ['navy tradition', 'yearly navy tradition']),
        MultiplicativeModifier('navy_tradition_decay', ['navy tradition decay']),
        ConstantModifier('no_religion_penalty', ['no religion penalty']),
        AdditiveModifier('papal_influence', ['papal influence']),
        MultiplicativeModifier('mercenary_manpower', ['mercenary manpower']),
        AdditiveModifier('prestige', ['prestige']),
        MultiplicativeModifier('prestige_decay', ['prestige decay']),
        MultiplicativeModifier('prestige_from_land', ['prestige from land']),
        MultiplicativeModifier('privateer_efficiency', ['privateer efficiency']),
        MultiplicativeModifier('production_efficiency', ['production efficiency']),
        MultiplicativeModifier('range', ['colonial range']),
        MultiplicativeModifier('rebel_support_efficiency', ['rebel support efficiency']),
        MultiplicativeModifier('recover_army_morale_speed', ['land morale recovery', 'recover army morale speed']),
        MultiplicativeModifier('recover_navy_morale_speed', ['naval morale recovery', 'recover navy morale speed']),
        MultiplicativeModifier('native_assimilation', ['native assimilation']),
        MultiplicativeModifier('native_uprising_chance', ['native uprising chance']),
        MultiplicativeModifier('reinforce_speed', ['reinforce speed']),
        MultiplicativeModifier('religious_unity', ['religious unity']),
        AdditiveModifier('republican_tradition', ['republican tradition', 'yearly republican tradition']),
        MultiplicativeModifier('ship_durability', ['ship durability']),
        MultiplicativeModifier('siege_ability', ['siege ability']),
        MultiplicativeModifier('spy_offence', ['spy network construction']),
        MultiplicativeModifier('stability_cost_modifier', ['stability cost modifier']),
        MultiplicativeModifier('technology_cost', ['technology cost']),
        AdditiveModifier('tolerance_heathen', ['tolerance of heathens', 'tolerance heathen']),
        AdditiveModifier('tolerance_heretic', ['tolerance of heretics', 'tolerance heretic']),
        AdditiveModifier('tolerance_own', ['tolerance of the true faith', 'tolerance own']),
        MultiplicativeModifier('trade_efficiency', ['trade efficiency']),
        MultiplicativeModifier('trade_range_modifier', ['trade range']),
        MultiplicativeModifier('trade_steering', ['trade steering']),
        MultiplicativeModifier('unjustified_demands', ['unjustified demands']),
        MultiplicativeModifier('vassal_forcelimit_bonus', ['vassal force limit contribution', 'vassal forcelimit bonus']),
        MultiplicativeModifier('vassal_income', ['income from vassals', 'vassal income']),
        AdditiveModifier('war_exhaustion', ['monthly war exhaustion', 'war exhaustion decrease']),
        MultiplicativeModifier('war_exhaustion_cost', ['war exhaustion cost']),
        AdditiveModifier('years_of_nationalism', ['years of separatism']),
        AdditiveModifier('global_autonomy', ['autonomy', 'national autonomy']),
        MultiplicativeModifier('province_warscore_cost', ['province warscore cost', 'province war score cost']),
        AdditiveModifier('devotion', ['devotion', 'yearly devotion']),
        MultiplicativeModifier('church_power_modifier', ['church power', 'church power modifier']),
        MultiplicativeModifier('garrison_size', ['garrison size']),
        MultiplicativeModifier('fort_maintenance_modifier', ['fort maintenance', 'fort maintenance modifier']),
        MultiplicativeModifier('loot_amount', ['looting speed']),
        AdditiveModifier('horde_unity', ['horde unity', 'yearly horde unity']),
        MultiplicativeModifier('global_sailors_modifier', ['national sailors modifier']),
        MultiplicativeModifier('sailors_recovery_speed', ['sailor recovery speed']),
        MultiplicativeModifier('state_maintenance_modifier', ['state maintenance']),
        LibertyDesireModifier('reduced_liberty_desire', ['liberty desire in subjects']),
        AdditiveModifier('yearly_corruption', ['corruption']),
        MultiplicativeModifier('global_institution_spread', ['institution spread']),
        MultiplicativeModifier('embracement_cost', ['institution embracement cost']),
        MultiplicativeModifier('movement_speed', ['movement speed']),
        MultiplicativeModifier('shock_damage_received', ['shock damage received']),
        MultiplicativeModifier('army_tradition_from_battle', ['army tradition from battles']),
        MultiplicativeModifier('naval_tradition_from_battle', ['naval tradition from battles']),
        MultiplicativeModifier('cavalry_flanking', ['cavalry flanking ability']),
        MultiplicativeModifier('fire_damage', ['land fire damage']),
        MultiplicativeModifier('capture_ship_chance', ['capture ship chance', 'chance to capture enemy ships']),
        MultiplicativeModifier('sunk_ship_morale_hit_recieved', ['morale hit when losing a ship']),
        MultiplicativeModifier('transport_cost', ['transport cost']),
        AdditiveModifier('yearly_harmony', ['harmony increase', 'yearly harmony increase']),
        AdditiveModifier('yearly_absolutism', ['yearly absolutism', 'absolutism']),
        MultiplicativeModifier('cav_to_inf_ratio', ['cavalry to infantry ratio']),
        MultiplicativeModifier('amount_of_banners', ['amount of banners', 'possible manchu banners']),
        MultiplicativeModifier('reinforce_cost_modifier', ['reinforce cost']),
        MultiplicativeModifier('shock_damage', ['shock damage']),
        MultiplicativeModifier('sailor_maintenance_modifer', ['sailor maintenance']),
        MultiplicativeModifier('administrative_efficiency', ['administrative efficiency']),
        MultiplicativeModifier('global_naval_engagement_modifier', ['global naval engagement']),
        MultiplicativeModifier('mercenary_discipline', ['mercenary discipline']),
        MultiplicativeModifier('fire_damage_received', ['fire damage received']),
        MultiplicativeModifier('monthly_piety', ['monthly piety']),
        AdditiveModifier('yearly_tribal_allegiance', ['yearly tribal allegiance']),
        MultiplicativeModifier('same_culture_advisor_cost', ['cost of adv wrc']),
        AdditiveModifier('meritocracy', ['meritocracy']),
        MultiplicativeModifier('harsh_treatment_cost', ['harsh treatment cost']),
        MultiplicativeModifier('global_ship_trade_power', ['ship trade power']),
        MultiplicativeModifier('build_time', ['construction time']),
        AdditiveModifier('possible_policy', ['possible policies']),
        MultiplicativeModifier('reform_progress_growth', ['reform progress growth']),
        AdditiveModifier('free_adm_policy', ['administrative free policies']),
        AdditiveModifier('free_dip_policy', ['diplomatic free policies']),
        AdditiveModifier('free_mil_policy', ['military free policies']),
        AdditiveModifier('possible_dip_policy', ['diplomatic possible policies']),
        AdditiveModifier('possible_mil_policy', ['military possible policies']),
        MultiplicativeModifier('power_projection_from_insults', ['power projection from insults']),
        MultiplicativeModifier('innovativeness_gain', ['innovativeness gain']),
        MultiplicativeModifier('missionary_maintenance_cost', ['missionary maintenance', 'missionary maintenance cost']),
        MultiplicativeModifier('expel_minorities_cost', ['expel minorities cost']),
        MultiplicativeModifier('naval_tradition_from_trade', ['naval tradition from trade', 'naval tradition from protecting trade']),
        MultiplicativeModifier('admiral_cost', ['admiral cost']),
        MultiplicativeModifier('center_of_trade_upgrade_cost', ['center of trade upgrade cost']),
        MultiplicativeModifier('rival_border_fort_maintenance', ['fort maintenance on border with rival']),
        AdditiveModifier('own_coast_naval_combat_bonus', ['naval combat bonus off owned coast']),
        AdditiveModifier('artillery_fire', ['artillery fire']),
        MultiplicativeModifier('autonomy_change_time', ['autonomy change cooldown']),
        MultiplicativeModifier('backrow_artillery_damage', ['artillery damage from back row']),
        AdditiveModifier('placed_merchant_power', ['merchant trade power']),
        MultiplicativeModifier('liberty_desire_from_subject_development', ['liberty desire from subjects development']),
        MultiplicativeModifier('reelection_cost', ['reelection cost']),
        MultiplicativeModifier('female_advisor_chance', ['female advisor chance']),
        AdditiveModifier('siege_blockade_progress', ['blockade impact on siege']),
        AdditiveModifier('imperial_mandate', ['mandate growth modifier']),
        MultiplicativeModifier('nobles_loyalty_modifier', ['nobility loyalty']),
        MultiplicativeModifier('burghers_influence_modifier', ['burghers influence']),
        MultiplicativeModifier('burghers_loyalty_modifier', ['burghers loyalty']),
        MultiplicativeModifier('vaisyas_loyalty_modifier', ['vaishyas loyalty']),
        MultiplicativeModifier('brahmins_muslim_loyalty_modifier', ['brahmins muslim loyalty']),
        MultiplicativeModifier('brahmins_hindu_loyalty_modifier', ['brahmins hindu loyalty']),
        MultiplicativeModifier('brahmins_other_loyalty_modifier', ['brahmins other loyalty']),
        MultiplicativeModifier('church_loyalty_modifier', ['clergy loyalty']),
        MultiplicativeModifier('dhimmi_loyalty_modifier', ['dhimmi loyalty']),
        MultiplicativeModifier('min_autonomy_in_territories', ['minimum autonomy in territories']),
        MultiplicativeModifier('governing_capacity_modifier', ['governing capacity modifier']),
        MultiplicativeModifier('allowed_marine_fraction', ['marines force limit']),
        MultiplicativeModifier('disengagement_chance', ['ship disengagement chance']),
        MultiplicativeModifier('flagship_cost', ['flagship cost']),
        AdditiveModifier('monarch_diplomatic_power', ['monarch diplomatic skill']),
        AdditiveModifier('monarch_military_power', ['monarch military skill']),
        AdditiveModifier('max_revolutionary_zeal', ['max revolutionary zeal', 'maximum revolutionary zeal']),
        MultiplicativeModifier('general_cost', ['general cost']),
        ConstantModifier('may_recruit_female_generals', ['may recruit female generals']),
        MultiplicativeModifier('trade_company_investment_cost', ['trade company investment cost']),
        MultiplicativeModifier('drill_gain_modifier', ['army drill gain modifier']),
        MultiplicativeModifier('enforce_religion_cost', ['cost of enforcing religion through war']),
        MultiplicativeModifier('leader_cost', ['leader cost']),
        ConstantModifier('auto_explore_adjacent_to_colony', ['auto explore adjacent to colony']),
        ConstantModifier('cb_on_primitives', ['cb on primitives']),
        ConstantModifier('cb_on_religious_enemies', ['cb on religious enemies']),
        ConstantModifier('idea_claim_colonies', ['idea claim colonies']),
        ConstantModifier('reduced_stab_impacts', ['reduced stab impacts']),
        ConstantModifier('sea_repair', ['sea repair']),
        MultiplicativeModifier('global_supply_limit_modifier', ['national supply limit modifier']),
        ConstantModifier('may_perform_slave_raid_on_same_religion', ['May raid coasts including coasts of countries with same religion']),
        AdditiveModifier('tribal_development_growth', ['tribal development growth']),
        MultiplicativeModifier('monthly_reform_progress_modifier', ['monthly reform progress modifier']),
    ]

class BonusTableGenerator():

    header = '''<includeonly>{{SVersion|''' + eu4_major_version() + '''|table}}
{{{!}} class="mildtable plainlist mw-collapsible {{#ifeq: {{lc:{{{collapse|}}}}}|yes|mw-collapsed|}}"
! style="width:30px" {{!}} {{icon|{{{1}}}|24px}}
! style="min-width:120px" {{!}} Traditions
! style="min-width:240px" {{!}} Ideas
! style="min-width:120px" {{!}} Bonuses
! style="min-width:240px" {{!}} Policies
{{#switch:{{lc:{{{1}}}}}'''

    footer = '''| national revolt risk
| global revolt risk = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“national revolt risk”'' was removed/renamed with patch 1.8.</span>[[Category:Bonus table outdated]]
| merchant steering towards inland
| merchant steering to inland = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“merchant steering towards inland”'' was removed with patch 1.10.</span>[[Category:Bonus table outdated]]
| building power cost
| build power cost = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“building power cost”'' was removed with patch 1.12.</span>[[Category:Bonus table outdated]]
| goods produced nationally
| global trade goods size = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“goods produced nationally”'' was renamed with patch 1.12.</span>[[Category:Bonus table outdated]]
| national trade income modifier
| global trade income modifier = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“national trade income modifier”'' was removed with patch 1.13.</span>[[Category:Bonus table outdated]]
| time to fabricate claims
| fabricate claims time = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“time to fabricate claims”'' was renamed with patch 1.16.</span>[[Category:Bonus table outdated]]
| time to justify trade conflict
| justify trade conflict time = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“time to justify trade conflict”'' was renamed with patch 1.16.</span>[[Category:Bonus table outdated]]
| national spy defense
| global spy defense = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“national spy defense”'' was renamed with patch 1.16.</span>[[Category:Bonus table outdated]]
| spy offense = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“spy offense”'' was renamed with patch 1.16.</span>[[Category:Bonus table outdated]]
| covert action relation impact
| discovered relations impact = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“covert action relation impact”'' is no more used since patch 1.17.</span>[[Category:Bonus table outdated]]
| accepted culture threshold = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“accepted culture threshold”'' was removed with patch 1.18.</span>[[Category:Bonus table outdated]]
| better relations over time = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“better relations over time”'' was merged with ''“improve_relation_modifier”'' with patch 1.19.</span>[[Category:Bonus table outdated]]
| build cost = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“build cost”'' was renamed to ''“construction cost”'' patch 1.19.</span>[[Category:Bonus table outdated]]
| reduce inflation cost
| inflation reduction cost ={{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">Since patch 1.28 no ideas and policies have the modifier ''“reduce inflation cost”''.</span>[[Category:Bonus table outdated]]
| prestige from naval =
{{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">Since patch 1.28 no ideas and policies have the modifier ''“prestige from naval”''.</span>[[Category:Bonus table outdated]]
| transport power
| transport combat ability =
{{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">Since patch 1.26 no ideas and policies have the modifier ''“transport combat ability”''.</span>[[Category:Bonus table outdated]]
| number of states =
{{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“number of states”'' was removed with patch 1.30.</span>[[Category:Bonus table outdated]]
| available mercenaries =
{{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“available mercenaries”'' was replaced by ''“mercenary manpower”'' with patch 1.30.</span>[[Category:Bonus table outdated]]

| #default = {{!}}-
{{!}}colspan="5"{{!}}<span style="color: red;">(invalid bonus type “{{lc:{{{1}}}}}” for [[Template:Bonus table]])</span>
}}
{{!}}}</includeonly><noinclude>[[Category:Templates]]{{template doc}}</noinclude>'''

    def __init__(self):
        self.eu4parser = Eu4Parser()
        self.parser = self.eu4parser.parser

    def run(self):
        lines = [self.header]
        processed_modifier_names = set()
        for modifier in all_modifiers:
            lines.append('| {} ='.format("\n| ".join(modifier.icons)))
            if modifier.name not in self.eu4parser.ideas_and_policies_by_modifier:
                lines.append('{{!}}-{{!}}colspan="5"{{!}} <span style="color: red;">no ideas and policies have the modifier \'\'“' + modifier.icons[0] + '”\'\'</span>[[Category:Bonus table outdated]]')
                continue
            all_values_for_modifier = self.eu4parser.ideas_and_policies_by_modifier[modifier.name].keys()
            for value in sorted(self.eu4parser.ideas_and_policies_by_modifier[modifier.name].keys(), key=lambda x: x if isinstance(x, str) else abs(x)*(-1) ):
                ideas = self.eu4parser.ideas_and_policies_by_modifier[modifier.name][value]
                template_params = {'t': [], 'i': [], 'b': [], 'p': []}
                for idea in self.sort_ideas(ideas):
                    if isinstance(idea, Policy):
                        template_params['p'].append(idea.formatted_name())
                    else:
                        if idea.idea_group.is_basic_idea():
                            formatted_name = '{{grey-bd|' + idea.formatted_name() + '}}'
                        else:
                            formatted_name = idea.formatted_name()
                        if idea.is_bonus():
                            template_params['b'].append(formatted_name)
                        elif idea.is_tradition():
                            template_params['t'].append(formatted_name)
                        else:
                            template_params['i'].append(formatted_name)

                lines.append('{{BTRow|' + modifier.format_value(value, all_values_for_modifier))
                for param, ideas in template_params.items():
                    if len(ideas) > 0:
                        lines.append("\t|{}= *{}".format(param, "\n*".join(ideas)))
                lines.append('}}')
            processed_modifier_names.add(modifier.name)
        unprocessed_modifier_names = set(self.eu4parser.ideas_and_policies_by_modifier.keys()) - processed_modifier_names
        if unprocessed_modifier_names:
            print('Some idea and policy modifiers are missing from all_modifiers:', file=sys.stderr)
            for modifier in unprocessed_modifier_names:
                print('{}: {}'.format(modifier, [
                    idea.formatted_name() for idea_list in self.eu4parser.ideas_and_policies_by_modifier[modifier].values()
                    for idea in idea_list
                    ]), file=sys.stderr)
        lines.append(self.footer)
        self.writeFile('bonus_tables', "\n".join(lines))

    def sort_ideas_key_function(self, idea):
        key = idea.formatted_name()
        if isinstance(idea, Idea) and idea.idea_group.is_basic_idea():
            key = '0' + key # make sure basic ideas get sorted first
        return key

    def sort_ideas(self, ideas):
        return sorted(ideas, key = self.sort_ideas_key_function)

    def writeFile(self, name, content):
        output_file = eu4outpath / '{}.txt'.format(name)
        with output_file.open('w') as f:
            f.write(content)

if __name__ == '__main__':
    generator = BonusTableGenerator()
    generator.run()


