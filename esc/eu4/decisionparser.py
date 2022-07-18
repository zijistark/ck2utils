from eu4.parser import Eu4Parser
from eu4.eu4lib import Decision
from eu4.cache import cached_property


class Eu4DecisionParser(Eu4Parser):

    @cached_property
    def all_decisions(self):
        decisions = {}
        for decisionfile, tree in self.parser.parse_files('decisions/*'):
            if 'country_decisions' in tree.dictionary:
                for n, v in tree['country_decisions']:
                    decision_id = n.val
                    attributes = {}
                    for n2, v2 in v:
                        attributes[n2.val] = v2
                    decision = Decision(self, decision_id, attributes)
                    if decision.id in decisions:
                        raise Exception('duplicate decision id "{}"'.format(decision.id))
                    decisions[decision.id] = decision
            else:
                print('Warning: Cant parse decisionfile "{}"'.format(decisionfile))
        return decisions

    @cached_property
    def decisions_by_title(self):
        decisions_by_title = {}
        for decision in self.all_decisions.values():
            if decision.title in decisions_by_title:
                #                 print('duplicate decision title "{}"'.format(decision.title))
                if not isinstance(decisions_by_title[decision.title], list):
                    decisions_by_title[decision.title] = [decisions_by_title[decision.title]]
                decisions_by_title[decision.title].append(decision)
            else:
                decisions_by_title[decision.title] = decision
        return decisions_by_title
