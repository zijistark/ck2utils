import re


class Eu4Date:
    """subtracting two dates results in an int which is their difference in days"""

    month_names = [None, 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

    def __init__(self, datestring):
        matches = re.fullmatch(r'(1[0-9]{3})\.([0-9]{1,2})\.([0-9]{1,2})', datestring)
        if matches:
            self.year = int(matches.group(1))
            self.month = int(matches.group(2))
            self.day = int(matches.group(3))
        else:
            matches = re.fullmatch('([0-9]{1,2}) ?([A-Z][a-z]{2,8}) ?(1[0-9]{3})', datestring)

            if matches and matches.group(2) in self.month_names:
                self.year = int(matches.group(3))
                self.month = self.month_names.index(matches.group(2))
                self.day = int(matches.group(1))
            else:
                raise Exception('Invalid date ' + datestring)

    def get_iso_date(self):
        return '{}-{:02}-{:02}'.format(self.year, self.month, self.day)

    def get_eu4_date(self):
        return '{}.{}.{}'.format(self.year, self.month, self.day)

    def get_days_in_year(self):
        days_in_month = [None, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        days_in_year = 0
        for month in range(1, self.month):
            days_in_year += days_in_month[month]
        days_in_year += self.day
        return days_in_year

    def get_days_since_year_zero(self):
        return 365 * self.year + self.get_days_in_year()

    def __sub__(self, other_date):
        return self.get_days_since_year_zero() - other_date.get_days_since_year_zero()