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


class Test_template_base:

    strip_whitespace_re = re.compile(r'\s+')

    dates = deepcopy(test_data.FINAL_DATES)
    data = deepcopy(test_data.FINAL_DATA)

    def test_one(self):
        data = deepcopy(test_data.NODE_SUMMARY_DATA)
        template_allowed = 'base.html'

        def template_source(environment, template):
            if template != template_allowed:
                return ('={t}='.format(t=template), template, True)
            package_name = 'pypuppetdb_daily_report'
            package_path = 'templates'
            provider = get_provider(package_name)
            manager = ResourceManager()
            pieces = split_template_path(template)
            p = '/'.join((package_path,) + tuple(pieces))
            filename = provider.get_resource_filename(manager, p)
            source = provider.get_resource_string(manager, p)
            return (source.decode('utf-8'), filename, True)
        tmp_src_mock = mock.MagicMock(spec='jinja2.loaders.PackageLoader.get_source', autospec=True)
        tmp_src_mock.side_effect = template_source

        hostname = 'foo.example.com'
        dates = self.dates
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        with mock.patch('jinja2.loaders.PackageLoader.get_source', tmp_src_mock):
            env = Environment(loader=PackageLoader('pypuppetdb_daily_report', 'templates'))
            env.filters['reportmetricname'] = pdr.filter_report_metric_name
            env.filters['reportmetricformat'] = pdr.filter_report_metric_format
            template = env.get_template('base.html')
            html = template.render(data=data,
                                   dates=dates,
                                   hostname=hostname,
                                   start=start_date,
                                   end=end_date
                                   )
        stripped = self.strip_whitespace_re.sub('', html)
        assert stripped == ''


class Test_format_html:

    strip_whitespace_re = re.compile(r'\s+')

    dates = deepcopy(test_data.FINAL_DATES)
    data = deepcopy(test_data.FINAL_DATA)

    def test_basic(self):
        env_mock = mock.MagicMock(spec=Environment, autospec=True)
        env_obj_mock = mock.MagicMock(spec=Environment, autospec=True)
        tmpl_mock = mock.MagicMock(spec=Template, autospec=True)
        tmpl_mock.render.return_value = 'baz'
        env_obj_mock.get_template.return_value = tmpl_mock
        env_obj_mock.filters = {}
        env_mock.return_value = env_obj_mock
        pl_mock = mock.MagicMock(spec=PackageLoader, autospec=True)
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.Environment', env_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.PackageLoader', pl_mock):
            html = pdr.format_html('foo.example.com',
                                   self.dates,
                                   self.data,
                                   datetime.datetime(2014, 6, 3, 0, 0, 0, tzinfo=pytz.utc),
                                   datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)
                                   )
        assert env_mock.call_count == 1
        assert pl_mock.call_count == 1
        assert pl_mock.call_args == mock.call('pypuppetdb_daily_report', 'templates')
        assert env_obj_mock.get_template.call_count == 1
        assert env_obj_mock.get_template.call_args == mock.call('base.html')
        assert env_obj_mock.filters['reportmetricname'] == pdr.filter_report_metric_name
        assert env_obj_mock.filters['reportmetricformat'] == pdr.filter_report_metric_format
        assert tmpl_mock.render.call_count == 1
        assert tmpl_mock.render.call_args == mock.call(data=self.data,
                                                       dates=self.dates,
                                                       hostname='foo.example.com',
                                                       start=datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc),
                                                       end=datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)
                                                       )
        assert html == 'baz'

    def test_body(self):
        html = pdr.format_html('foo.example.com',
                               self.dates,
                               self.data,
                               datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc),
                               datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)
                               )
        assert '<html>' in html
        assert '<h1>daily puppet(db) run summary on foo.example.com for Tue Jun 03, 2014 to Tue Jun 10</h1>' in html

    def test_metrics(self):
        html = pdr.format_html('foo.example.com',
                               self.dates,
                               self.data,
                               datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc),
                               datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)
                               )
        stripped = self.strip_whitespace_re.sub('', html)
        assert '<html>' in html
        assert '<tr><th>Metric</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html
        assert '<tr><th>bar</th><td>' in stripped
        assert '<tr><th>baz</th><td>' in stripped
        assert '<tr><th>foo</th><td>foo1</td><td>foo2</td><td>foo3</td><td>foo4</td><td>foo5</td><td>foo6</td><td>&nbsp;</td></tr>' in stripped

    def test_facts(self):
        html = pdr.format_html('foo.example.com',
                               self.dates,
                               self.data,
                               datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc),
                               datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)
                               )
        stripped = self.strip_whitespace_re.sub('', html)
        assert '<html>' in html
        assert '<h2>Fact Values</h2>' in html
        assert '<tr><th>Fact</th><th>Value</th><th>Count</th></tr>' in html
        assert '<tr><throwspan="2">facterversion</th><td>1.7.2</td><td>1</td></tr><tr><td>2.0.0</td><td>102</td></tr><tr><throwspan="3">puppetversion' in stripped

    def test_run_overview(self):
        html = pdr.format_html('foo.example.com',
                               self.dates,
                               self.data,
                               datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc),
                               datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)
                               )
        stripped = self.strip_whitespace_re.sub('', html)
        assert '<html>' in html
        assert '<h2>Report Overview</h2>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html
        assert '<tr><th>TotalReports</th><td>9</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>WithFailures</th><td>8(89%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>WithChanges</th><td>4(44%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>WithSkippedResources</th><td>3(33%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>AverageRuntime</th><td>4m5s</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>MaximumRuntime</th><td>16m40s</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>NodesWithNoReport</th><td>1</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped

    def test_no_runs(self):
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
        html = pdr.format_html('foo.example.com',
                               self.dates,
                               data,
                               datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc),
                               datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)
                               )
        assert '<html>' in html

    @pytest.mark.skipif(1 == 1, reason='not implemented yet')
    def test_run_node_counts(self):
        data = deepcopy(test_data.NODE_SUMMARY_DATA)
        html = pdr.format_html('foo.example.com',
                               self.dates,
                               data,
                               datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc),
                               datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)
                               )
        stripped = self.strip_whitespace_re.sub('', html)
        assert '<html>' in html
        assert '<h2>Node Summary</h2>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html
        assert '<tr><th>TotalNodes</th><td>10</td><td>8</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>100%FailedRuns</th><td>1(10%)</td><td>4(50%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>50%+FailedRuns</th><td>4(40%)</td><td>0</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>AnyFailedRuns</th><td>2(20%)</td><td>2(25%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>LessThan40Reports</th><td>1(10%)</td><td>0</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>WithChanges</th><td>5(50%)</td><td>6(75%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
