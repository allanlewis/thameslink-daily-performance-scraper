import calendar
import json
import re
import urllib2
from ast import literal_eval
from ConfigParser import ConfigParser
from datetime import datetime
from pprint import pprint

from bs4 import BeautifulSoup, SoupStrainer

# CONSTANTS
DATE_FORMAT = '%A %d %B %Y'
PERCENTAGE_PATTERN = '\d+(\.\d+)?%'
DATE_STRING_PATTERN = \
    '(%(days)s) (?P<day>\d+) (?P<month>%(months)s) (?P<year>\d{4})'
FILENAME_DATE_FORMAT = '%Y.%m.%d'
FILENAME_FORMAT = 'data.%s.json'

# Parse config file
config = ConfigParser()
config.read('config.ini')
assert config.has_section('thameslink')

config = dict(config.items('thameslink'))
required_config = {'report_url', 'content_attrs', 'table_attrs'}
assert required_config.issubset(set(config.keys()))

report_url = config['report_url']
content_attrs = literal_eval(config['content_attrs'])
table_attrs = literal_eval(config['table_attrs'])

# Get page
page = urllib2.urlopen(report_url)

# Extract relevant content
strainer = SoupStrainer(attrs=content_attrs)
content = BeautifulSoup(page, parse_only=strainer)

# Determine date of report
days = '|'.join(calendar.day_name)
months = '|'.join(calendar.month_name[1:])  # Element 0 is empty
date_pattern = re.compile(
    DATE_STRING_PATTERN % {'days': days, 'months': months})
date_string = content.find(text=date_pattern)
report_date = datetime.strptime(date_string, DATE_FORMAT).date()

# Parse data
data = {}
route = None
for tr in content \
        .find('table', attrs=table_attrs) \
        .find('tbody') \
        .find_all('tr'):
    for i, td in enumerate(tr.find_all('td')):
        if i == 0:
            route = str(td.string)
            data[route] = {}
        else:
            assert re.match(PERCENTAGE_PATTERN, td.string)
            percentage = float(td.string.replace(r'%', ''))
            if i == 1:
                data[route]['PPM'] = percentage
            elif i == 2:
                data[route]['Right Time'] = percentage
            else:
                raise Exception("Unexpected data: %s" % td.string)
pretty_data = json.dumps(data, sort_keys=True, indent=4)
print pretty_data
file_name = FILENAME_FORMAT % report_date.strftime(FILENAME_DATE_FORMAT)
with open(file_name, 'w') as file_:
    file_.write(pretty_data)
