"""
tests for jinja2 templates
"""

from pkg_resources import DefaultProvider, ResourceManager, get_provider
import re
import mock
import datetime
import pytz
import pytest
from copy import deepcopy
from jinja2 import Environment, PackageLoader, Template
from jinja2.loaders import split_template_path

from pypuppetdb_daily_report import pypuppetdb_daily_report as pdr

# fixtures
from . import test_data

strip_whitespace_re = re.compile(r'\s+')


def get_html(tmpl_name, src_mock, data, dates, hostname, start_date, end_date):
    with mock.patch('jinja2.loaders.PackageLoader.get_source', src_mock):
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.RUNS_PER_DAY', 9):
            env = Environment(loader=PackageLoader('pypuppetdb_daily_report', 'templates'))
            env.filters['reportmetricname'] = pdr.filter_report_metric_name
            env.filters['reportmetricformat'] = pdr.filter_report_metric_format
            template = env.get_template(tmpl_name)
            html = template.render(data=data,
                                   dates=dates,
                                   hostname=hostname,
                                   start=start_date,
                                   end=end_date,
                                   )
    stripped = strip_whitespace_re.sub('', html)
    return (html, stripped)


class SourceGetter:

    allowed_template = ''
    package_name = 'pypuppetdb_daily_report'
    package_path = 'templates'

    def __init__(self, allowed_template):
        self.allowed_template = allowed_template
        self.provider = get_provider(self.package_name)
        self.manager = ResourceManager()
        self.src_mock = mock.MagicMock(spec='jinja2.loaders.PackageLoader.get_source', autospec=True)
        self.src_mock.side_effect = self.template_source

    def template_source(self, environment, template):
        if template != self.allowed_template:
            return ('={t}='.format(t=template), template, True)
        pieces = split_template_path(template)
        p = '/'.join((self.package_path,) + tuple(pieces))
        filename = self.provider.get_resource_filename(self.manager, p)
        source = self.provider.get_resource_string(self.manager, p)
        return (source.decode('utf-8'), filename, True)

    def get_mock(self):
        return self.src_mock


class Test_template_base:
    """ test base.html template """

    dates = deepcopy(test_data.FINAL_DATES)
    data = deepcopy(test_data.FINAL_DATA)
    template_name = 'base.html'

    def test_one(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        hostname = 'foo.example.com'
        dates = self.dates
        data = deepcopy(test_data.NODE_SUMMARY_DATA)
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date)

        assert '<h1>daily puppet(db) run summary on foo.example.com for Tue Jun 03, 2014 to Tue Jun 10</h1>' in html
        assert stripped == '<html><head></head><body><h1>dailypuppet(db)runsummaryonfoo.example.comforTueJun03,2014toTueJun10</h1>=metrics.html==facts.html==reports.html==nodes.html=</body></html>'


class Test_template_metrics:
    """ test metrics.html template """

    dates = deepcopy(test_data.FINAL_DATES)
    data = deepcopy(test_data.FINAL_DATA)
    template_name = 'metrics.html'

    def test_metrics(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        hostname = 'foo.example.com'
        dates = self.dates
        data = self.data
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date)

        assert '<tr><th>Metric</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html
        assert '<tr><th>bar</th><td>' in stripped
        assert '<tr><th>baz</th><td>' in stripped
        assert '<tr><th>foo</th><td>foo1</td><td>foo2</td><td>foo3</td><td>foo4</td><td>foo5</td><td>foo6</td><td>&nbsp;</td></tr>' in stripped


class Test_template_facts:
    """ test facts.html template """

    dates = deepcopy(test_data.FINAL_DATES)
    data = deepcopy(test_data.FINAL_DATA)
    template_name = 'facts.html'

    def test_facts(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        hostname = 'foo.example.com'
        dates = self.dates
        data = self.data
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date)

        assert '<h2>Fact Values</h2>' in html
        assert '<tr><th>Fact</th><th>Value</th><th>Count</th></tr>' in html
        assert '<tr><throwspan="2">facterversion</th><td>1.7.2</td><td>1</td></tr><tr><td>2.0.0</td><td>102</td></tr><tr><throwspan="3">puppetversion' in stripped


class Test_template_reports:
    """ test reports.html template """

    dates = deepcopy(test_data.FINAL_DATES)
    data = deepcopy(test_data.FINAL_DATA)
    template_name = 'reports.html'

    def test_reports(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        hostname = 'foo.example.com'
        dates = self.dates
        data = self.data
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date)

        assert '<h2>Report Overview</h2>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html
        assert '<tr><th>TotalReports</th><td>9</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>WithFailures</th><td>8(89%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>WithChanges</th><td>4(44%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>WithSkippedResources</th><td>3(33%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>AverageRuntime</th><td>4m5s</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>MaximumRuntime</th><td>16m40s</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped

    def test_no_runs(self):
        """ test a node with no runs """
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        hostname = 'foo.example.com'
        dates = self.dates
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)
        data = deepcopy(test_data.FINAL_DATA)
        foo = data['Tue 06/10']['nodes']['node5.example.com']
        data['Tue 06/10']['nodes'] = {'node5.example.com': foo}
        data['Tue 06/10']['aggregate']['reports'] = {'run_count': 0,
                                                     'with_failures': 0,
                                                     'with_changes': 0,
                                                     'with_skips': 0,
                                                     'run_time_total': datetime.timedelta(),
                                                     'run_time_max': datetime.timedelta()
                                                     }

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date)

        assert '<h2>Report Overview</h2>' in html


class Test_template_nodes:
    """ test nodes.html template """

    dates = deepcopy(test_data.FINAL_DATES)
    data = deepcopy(test_data.FINAL_DATA)
    template_name = 'nodes.html'

    def test_run_node_counts(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        hostname = 'foo.example.com'
        dates = self.dates
        data = self.data
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date)
        s = stripped.replace('</tr>', "</tr>\n")
        assert '<h2>Node Summary</h2>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html
        assert '<tr><th>NodesWith100%FailedRuns</th><td>4(67%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>NodesWith50-100%FailedRuns</th><td>1(17%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>NodesWithNoReport</th><td>1(17%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>NodesWith<9Runs</th><td>4(67%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
