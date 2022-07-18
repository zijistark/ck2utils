from eu4.parser import Eu4Parser
from eu4.eu4lib import Event
from eu4.cache import cached_property


class Eu4EventParser(Eu4Parser):

    @cached_property
    def all_events(self):
        events = {}
        mandatory_attributes = ['id', 'title', 'desc']
        for eventfile, tree in self.parser.parse_files('events/*'):
            namespace = ''
            for n, v in tree:
                if n.val == 'namespace':
                    namespace = v.val
                elif n.val == 'normal_or_historical_nations':
                    pass  # ignore
                elif n.val == 'country_event' or n.val == 'province_event':
                    attributes = {}
                    eventid = None
                    for n2, v2 in v:
                        attributes[n2.val] = v2
                    missing_attributes = [a for a in mandatory_attributes if a not in attributes]
                    if len(missing_attributes) > 0:
                        raise Exception('Event is missing attributes {}'.format(', '.join(missing_attributes)))
                    event = Event(self, attributes)
                    if event.id in events:
                        raise Exception('duplicate event id "{}"'.format(event.id))
                    events[event.id] = event
                else:
                    raise Exception('unknown key "{}" in file "{}"'.format(n.val, eventfile))
        return events

    @cached_property
    def events_by_title(self):
        events_by_title = {}
        for event in self.all_events.values():
            if event.title in events_by_title:
                # print('duplicate event title "{}"'.format(event.title))
                if not isinstance(events_by_title[event.title], list):
                    events_by_title[event.title] = [events_by_title[event.title]]
                events_by_title[event.title].append(event)
            else:
                events_by_title[event.title] = event
        return events_by_title
