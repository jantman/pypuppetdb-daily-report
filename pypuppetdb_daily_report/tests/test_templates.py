"""
tests for jinja2 templates
"""

from pkg_resources import ResourceManager, get_provider
import re
import mock
import datetime
import pytz
from copy import deepcopy
from jinja2 import Environment, PackageLoader
from jinja2.loaders import split_template_path
import inspect  # write_debug()

from pypuppetdb_daily_report import pypuppetdb_daily_report as pdr

# fixtures
from . import test_data

strip_whitespace_re = re.compile(r'\s+')


def get_html(tmpl_name, src_mock, data, dates, hostname, start_date, end_date, config={}, run_info={}):
    if 'num_rows' not in config:
        config['num_rows'] = 10
    config['start'] = start_date
    config['end'] = end_date

    with mock.patch('jinja2.loaders.PackageLoader.get_source', src_mock):
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.RUNS_PER_DAY', 9):
            env = Environment(loader=PackageLoader('pypuppetdb_daily_report', 'templates'), extensions=['jinja2.ext.loopcontrols'])
            env.filters['reportmetricname'] = pdr.filter_report_metric_name
            env.filters['reportmetricformat'] = pdr.filter_report_metric_format
            env.filters['resourcedictsort'] = pdr.filter_resource_dict_sort
            template = env.get_template(tmpl_name)
            html = template.render(data=data,
                                   dates=dates,
                                   hostname=hostname,
                                   config=config,
                                   run_info=run_info,
                                   )
    stripped = strip_whitespace_re.sub('', html)
    return (html, stripped)


def write_debug(html, stripped):
    frm = inspect.stack()[1]
    name = "{func}_{line}".format(func=frm[3], line=frm[2])
    with open("{name}.html".format(name=name), 'w') as fh:
        fh.write(html)
    print("html written to {name}.html".format(name=name))
    with open("{name}.stripped".format(name=name), 'w') as fh:
        fh.write(stripped)
    print("stripped written to {name}.stripped".format(name=name))


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

        run_info = {
            'version': '1.2.3',
            'host': 'foobar',
            'user': 'baz',
            'date_s': '1234',
        }

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date, run_info=run_info)

        assert '<h1>daily puppet(db) run summary on foo.example.com for Tue Jun 10, 2014</h1>' in html
        expected = '<html><head></head><body><h1>dailypuppet(db)runsummaryonfoo.example.comforTueJun10,2014</h1>'
        expected += '=metrics.html==facts.html==reports.html==report_resources.html==nodes.html==node_resources.html='
        expected += '<br/><br/><p>Generatedbypypuppetdb_daily_reportv1.2.3onfoobarasbazat1234.</p>'
        expected += '</body></html>'
        assert stripped == expected


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
        assert '<tr><th>TotalReports</th><td>19</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>WithFailures</th><td>15(79%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>WithChanges</th><td>6(32%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>WithSkippedResources</th><td>10(53%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>AverageRuntime</th><td>2m1s</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
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
        assert '<h2>Node Summary</h2>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html
        assert '<tr><th>Count</th><td>6</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>With100%FailedRuns</th><td>4(67%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>With50-100%FailedRuns</th><td>1(17%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>WithNoReport</th><td>1(17%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>With<9Runsin24h</th><td>4(67%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>WithChanges</th><td>4(67%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped
        assert '<tr><th>WithSkippedResources</th><td>3(50%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' in stripped


class Test_template_node_resources:
    """ test node_resources.html template """

    dates = deepcopy(test_data.FINAL_DATES)
    data = deepcopy(test_data.FINAL_DATA)
    template_name = 'node_resources.html'

    def test_changes(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        hostname = 'foo.example.com'
        dates = self.dates
        data = self.data
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date)

        assert '<h3>Top Resource Changes, by Number of Nodes with Change</h3>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html

        lines = ['<!--beginnode_resources.html-->']
        lines.append('<h3>TopResourceChanges,byNumberofNodeswithChange</h3><tableborder="1">')
        lines.append('<tr><th>&nbsp;</th><th>Tue06/10</th><th>Mon06/09</th><th>Sun06/08</th><th>Sat06/07</th><th>Fri06/06</th><th>Thu06/05</th><th>Wed06/04</th></tr>')
        lines.append('<tr><th>TotalNodes</th><td>6</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Service[winbind]</th><td>2(33%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Service[zookeeper-server]</th><td>2(33%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Exec[zookeeperensemblecheck]</th><td>1(17%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('</table>')
        all_lines = ''
        for line in lines:
            assert line in stripped
            all_lines += line
        assert all_lines in stripped

    def test_changes_limit(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        hostname = 'foo.example.com'
        dates = self.dates
        data = self.data
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date, config={'num_rows': 2})

        assert '<h3>Top Resource Changes, by Number of Nodes with Change</h3>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html

        lines = ['<!--beginnode_resources.html-->']
        lines.append('<h3>TopResourceChanges,byNumberofNodeswithChange</h3><tableborder="1">')
        lines.append('<tr><th>&nbsp;</th><th>Tue06/10</th><th>Mon06/09</th><th>Sun06/08</th><th>Sat06/07</th><th>Fri06/06</th><th>Thu06/05</th><th>Wed06/04</th></tr>')
        lines.append('<tr><th>TotalNodes</th><td>6</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Service[winbind]</th><td>2(33%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Service[zookeeper-server]</th><td>2(33%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('</table>')
        all_lines = ''
        for line in lines:
            assert line in stripped
            all_lines += line
        assert all_lines in stripped
        assert 'Exec[zookeeperensemblecheck]' not in html

    def test_failed(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        hostname = 'foo.example.com'
        dates = self.dates
        data = self.data
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date)

        assert '<h3>Top Resource Failures, by Number of Nodes with Failure</h3>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html

        lines = ['<h3>TopResourceFailures,byNumberofNodeswithFailure</h3><tableborder="1">']
        lines.append('<tr><th>&nbsp;</th><th>Tue06/10</th><th>Mon06/09</th><th>Sun06/08</th><th>Sat06/07</th><th>Fri06/06</th><th>Thu06/05</th><th>Wed06/04</th></tr>')
        lines.append('<tr><th>TotalNodes</th><td>6</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Package[libsmbios]</th><td>2(33%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Package[srvadmin-idrac7]</th><td>2(33%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Exec[zookeeperensemblecheck]</th><td>1(17%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('</table>')
        all_lines = ''
        for line in lines:
            assert line in stripped
            all_lines += line
        assert all_lines in stripped

    def test_failed_limit(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        hostname = 'foo.example.com'
        dates = self.dates
        data = self.data
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date, config={'num_rows': 2})

        assert '<h3>Top Resource Failures, by Number of Nodes with Failure</h3>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html

        lines = ['<h3>TopResourceFailures,byNumberofNodeswithFailure</h3><tableborder="1">']
        lines.append('<tr><th>&nbsp;</th><th>Tue06/10</th><th>Mon06/09</th><th>Sun06/08</th><th>Sat06/07</th><th>Fri06/06</th><th>Thu06/05</th><th>Wed06/04</th></tr>')
        lines.append('<tr><th>TotalNodes</th><td>6</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Package[libsmbios]</th><td>2(33%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Package[srvadmin-idrac7]</th><td>2(33%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('</table>')
        all_lines = ''
        for line in lines:
            assert line in stripped
            all_lines += line
        assert all_lines in stripped
        assert 'Exec[zookeeperensemblecheck]' not in html

    def test_flapping(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        flapping = {
            ('Aaa', 'zab'): 2,
            ('Aaa', 'zac'): 2,
            ('Ccc', 'zaa'): 2,
            ('Foo', 'bar'): 6,
            ('Zzz', 'zzz'): 1,
        }

        hostname = 'foo.example.com'
        dates = self.dates
        data = self.data
        data['Tue 06/10']['aggregate']['nodes']['resources']['flapping'] = flapping
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date)

        assert '<h3>Top Flapping Resources, by Number of Nodes</h3>' in html
        assert '<p>Flapping defined as a resource changed in at least 45% of runs on a node.</p>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html

        lines = ['<h3>TopFlappingResources,byNumberofNodes</h3><p>Flappingdefinedasaresourcechangedinatleast45%ofrunsonanode.</p><tableborder="1">']
        lines.append('<tr><th>&nbsp;</th><th>Tue06/10</th><th>Mon06/09</th><th>Sun06/08</th><th>Sat06/07</th><th>Fri06/06</th><th>Thu06/05</th><th>Wed06/04</th></tr>')
        lines.append('<tr><th>TotalNodes</th><td>6</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Foo[bar]</th><td>6(100%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Aaa[zab]</th><td>2(33%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Aaa[zac]</th><td>2(33%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Ccc[zaa]</th><td>2(33%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Zzz[zzz]</th><td>1(17%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('</table>')
        lines.append('<!--endnode_resources.html-->')
        all_lines = ''
        for line in lines:
            assert line in stripped
            all_lines += line
        assert all_lines in stripped

    def test_flapping_limit(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        flapping = {
            ('Aaa', 'zab'): 2,
            ('Aaa', 'zac'): 2,
            ('Ccc', 'zaa'): 2,
            ('Foo', 'bar'): 6,
            ('Zzz', 'zzz'): 1,
        }

        hostname = 'foo.example.com'
        dates = self.dates
        data = self.data
        data['Tue 06/10']['aggregate']['nodes']['resources']['flapping'] = flapping
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date, config={'num_rows': 2})

        assert '<h3>Top Flapping Resources, by Number of Nodes</h3>' in html
        assert '<p>Flapping defined as a resource changed in at least 45% of runs on a node.</p>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html

        lines = ['<h3>TopFlappingResources,byNumberofNodes</h3><p>Flappingdefinedasaresourcechangedinatleast45%ofrunsonanode.</p><tableborder="1">']
        lines.append('<tr><th>&nbsp;</th><th>Tue06/10</th><th>Mon06/09</th><th>Sun06/08</th><th>Sat06/07</th><th>Fri06/06</th><th>Thu06/05</th><th>Wed06/04</th></tr>')
        lines.append('<tr><th>TotalNodes</th><td>6</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Foo[bar]</th><td>6(100%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Aaa[zab]</th><td>2(33%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('</table>')
        lines.append('<!--endnode_resources.html-->')
        all_lines = ''
        for line in lines:
            assert line in stripped
            all_lines += line
        assert all_lines in stripped
        assert 'Aaa[zac]' not in html
        assert 'Ccc[zaa]' not in html
        assert 'Zzz[zzz]' not in html


class Test_template_report_resources:
    """ test report_resources.html template """

    dates = deepcopy(test_data.FINAL_DATES)
    data = deepcopy(test_data.FINAL_DATA)
    template_name = 'report_resources.html'

    def test_changes(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        hostname = 'foo.example.com'
        dates = self.dates
        data = self.data
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date)

        assert '<h3>Top Resource Changes, by Number of Reports with Change</h3>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html

        lines = ['<!--beginreport_resources.html-->']
        lines.append('<h3>TopResourceChanges,byNumberofReportswithChange</h3><tableborder="1">')
        lines.append('<tr><th>&nbsp;</th><th>Tue06/10</th><th>Mon06/09</th><th>Sun06/08</th><th>Sat06/07</th><th>Fri06/06</th><th>Thu06/05</th><th>Wed06/04</th></tr>')
        lines.append('<tr><th>TotalReports</th><td>19</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Service[zookeeper-server]</th><td>4(21%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Service[winbind]</th><td>2(11%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Exec[zookeeperensemblecheck]</th><td>1(5%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('</table>')
        all_lines = ''
        for line in lines:
            assert line in stripped
            all_lines += line
        assert all_lines in stripped

    def test_changes_limit(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        hostname = 'foo.example.com'
        dates = self.dates
        data = self.data
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date, config={'num_rows': 2})

        assert '<h3>Top Resource Changes, by Number of Reports with Change</h3>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html

        lines = ['<!--beginreport_resources.html-->']
        lines.append('<h3>TopResourceChanges,byNumberofReportswithChange</h3><tableborder="1">')
        lines.append('<tr><th>&nbsp;</th><th>Tue06/10</th><th>Mon06/09</th><th>Sun06/08</th><th>Sat06/07</th><th>Fri06/06</th><th>Thu06/05</th><th>Wed06/04</th></tr>')
        lines.append('<tr><th>TotalReports</th><td>19</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Service[zookeeper-server]</th><td>4(21%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Service[winbind]</th><td>2(11%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('</table>')
        all_lines = ''
        for line in lines:
            assert line in stripped
            all_lines += line
        assert all_lines in stripped
        assert 'Exec[zookeeperensemblecheck]' not in html

    def test_failed(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        hostname = 'foo.example.com'
        dates = self.dates
        data = self.data
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date)

        assert '<h3>Top Resource Failures, by Number of Reports with Failure</h3>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html

        lines = ['<h3>TopResourceFailures,byNumberofReportswithFailure</h3><tableborder="1">']
        lines.append('<tr><th>&nbsp;</th><th>Tue06/10</th><th>Mon06/09</th><th>Sun06/08</th><th>Sat06/07</th><th>Fri06/06</th><th>Thu06/05</th><th>Wed06/04</th></tr>')
        lines.append('<tr><th>TotalReports</th><td>19</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Package[srvadmin-idrac7]</th><td>4(21%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Package[libsmbios]</th><td>2(11%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Exec[zookeeperensemblecheck]</th><td>1(5%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('</table>')
        lines.append('<!--endreport_resources.html-->')
        all_lines = ''
        for line in lines:
            assert line in stripped
            all_lines += line
        assert all_lines in stripped

    def test_failed_limit(self):
        sg = SourceGetter(self.template_name)
        tmp_src_mock = sg.get_mock()

        hostname = 'foo.example.com'
        dates = self.dates
        data = self.data
        start_date = datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc)
        end_date = datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc)

        html, stripped = get_html(self.template_name, tmp_src_mock, data, dates, hostname, start_date, end_date, config={'num_rows': 2})

        assert '<h3>Top Resource Failures, by Number of Reports with Failure</h3>' in html
        assert '<tr><th>&nbsp;</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html

        lines = ['<h3>TopResourceFailures,byNumberofReportswithFailure</h3><tableborder="1">']
        lines.append('<tr><th>&nbsp;</th><th>Tue06/10</th><th>Mon06/09</th><th>Sun06/08</th><th>Sat06/07</th><th>Fri06/06</th><th>Thu06/05</th><th>Wed06/04</th></tr>')
        lines.append('<tr><th>TotalReports</th><td>19</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Package[srvadmin-idrac7]</th><td>4(21%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('<tr><th>Package[libsmbios]</th><td>2(11%)</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        lines.append('</table>')
        lines.append('<!--endreport_resources.html-->')
        all_lines = ''
        for line in lines:
            assert line in stripped
            all_lines += line
        assert all_lines in stripped
        assert 'Exec[zookeeperensemblecheck]' not in html
