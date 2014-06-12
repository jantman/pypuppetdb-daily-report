"""
tests for pypuppetdb_daily_report

The latest version of this package is available at:
<https://github.com/jantman/pypuppetdb-daily-report>

It is highly recommended that you install this via `pip`.

##################################################################################
Copyright 2013 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of pypuppetdb-daily-report.

    pypuppetdb-puppet-report is licensed under the Apache License version 2.0.
    please see LICENSE file for full text.
##################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/pypuppetdb-daily-report> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
##################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

"""

import pytest
import sys
import os
import shutil
import mock
import logging
import datetime
import re
from freezegun import freeze_time
from freezegun.api import FakeDatetime
from requests.exceptions import HTTPError
import pypuppetdb
from jinja2 import Environment, PackageLoader, Template

from pypuppetdb_daily_report import pypuppetdb_daily_report as pdr


class OptionsObject(object):
    """
    object to mock optparse return object
    """

    def __init__(self):
        """
        preseed with default values
        """
        self.dry_run = False
        self.verbose = 0
        self.host = None
        self.num_days = 7
        self.cache_dir = '/tmp/.pypuppetdb_daily_report'


class Test_parse_args:
    """
    Tests the CLI option/argument handling
    """

    def test_defaults(self):
        """
        Test the parse_args option parsing method with default / no arguments
        """
        argv = ['pypuppetdb_daily_report']
        path_mock = mock.MagicMock()
        path_mock.return_value = '/foobar/.pypuppetdb_daily_report'
        with mock.patch('os.path.expanduser', path_mock):
            x = pdr.parse_args(argv)
        assert x.dry_run == False
        assert x.verbose == 0
        assert x.cache_dir == '/foobar/.pypuppetdb_daily_report'

    def test_cache_dir(self):
        """
        Test the parse_args option parsing method with cache-dir specified
        """
        argv = ['pypuppetdb_daily_report', '-c', '/tmp/foobar']
        path_mock = mock.MagicMock()
        path_mock.return_value = '/foobar/.pypuppetdb_daily_report'
        with mock.patch('os.path.expanduser', path_mock):
            x = pdr.parse_args(argv)
        assert x.dry_run == False
        assert x.verbose == 0
        assert x.cache_dir == '/tmp/foobar'

    def test_dryrun(self):
        """
        Test the parse_args option parsing method with dry-run specified
        """
        argv = ['pypuppetdb_daily_report', '-d']
        x = pdr.parse_args(argv)
        assert x.dry_run == True
        argv = ['pypuppetdb_daily_report', '--dry-run']
        x = pdr.parse_args(argv)
        assert x.dry_run == True

    def test_verbose(self):
        """
        Test the parse_args option parsing method with verbose specified
        """
        argv = ['pypuppetdb_daily_report', '-v']
        x = pdr.parse_args(argv)
        assert x.verbose == 1

    def test_debug(self):
        """
        Test the parse_args option parsing method with debug specified
        """
        argv = ['pypuppetdb_daily_report', '-vv']
        x = pdr.parse_args(argv)
        assert x.verbose == 2

    def test_host(self):
        """
        Test the parse_args option parsing method with a PuppetDB URL
        """
        argv = ['pypuppetdb_daily_report', '-p', 'foobar']
        x = pdr.parse_args(argv)
        assert x.host == 'foobar'
        argv = ['pypuppetdb_daily_report', '--puppetdb', 'foobar']
        x = pdr.parse_args(argv)
        assert x.host == 'foobar'

    def test_num_days(self):
        """
        Test the parse_args option parsing method with number of days specified
        """
        argv = ['pypuppetdb_daily_report', '-n', '14']
        x = pdr.parse_args(argv)
        assert x.num_days == 14


class Test_console_entry_point:
    """ test console_entry_point """

    def test_defaults(self):
        """ with default values """
        parse_args_mock = mock.MagicMock()
        opts_o = OptionsObject()
        opts_o.host = 'foobar'
        parse_args_mock.return_value = opts_o

        main_mock = mock.MagicMock()

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.parse_args', parse_args_mock):
            with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.main', main_mock):
                pdr.console_entry_point()
        assert parse_args_mock.call_count == 1
        assert main_mock.call_count == 1

    def test_nohost(self):
        """ without a host specified """
        parse_args_mock = mock.MagicMock()
        opts_o = OptionsObject()
        parse_args_mock.return_value = opts_o
        main_mock = mock.MagicMock()

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.parse_args', parse_args_mock):
            with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.main', main_mock):
                with pytest.raises(SystemExit) as excinfo:
                    pdr.console_entry_point()
        assert parse_args_mock.call_count == 1
        assert main_mock.call_count == 0
        assert excinfo.value.message == "ERROR: you must specify the PuppetDB hostname with -p|--puppetdb"

    def test_verbose(self):
        """ with -v """
        parse_args_mock = mock.MagicMock()
        opts_o = OptionsObject()
        opts_o.host = 'foobar'
        opts_o.verbose = 1
        parse_args_mock.return_value = opts_o

        logger_mock = mock.MagicMock()

        main_mock = mock.MagicMock()

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.parse_args', parse_args_mock):
            with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.main', main_mock):
                with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
                    pdr.console_entry_point()
        assert parse_args_mock.call_count == 1
        assert main_mock.call_count == 1
        assert logger_mock.setLevel.call_count == 1
        assert logger_mock.setLevel.call_args == mock.call(logging.INFO)

    def test_debug(self):
        """ with -v """
        parse_args_mock = mock.MagicMock()
        opts_o = OptionsObject()
        opts_o.host = 'foobar'
        opts_o.verbose = 2
        parse_args_mock.return_value = opts_o

        logger_mock = mock.MagicMock()

        main_mock = mock.MagicMock()

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.parse_args', parse_args_mock):
            with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.main', main_mock):
                with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
                    pdr.console_entry_point()
        assert parse_args_mock.call_count == 1
        assert main_mock.call_count == 1
        assert logger_mock.setLevel.call_count == 1
        assert logger_mock.setLevel.call_args == mock.call(logging.DEBUG)


class Test_get_dashboard_metrics:

    def test_get(self):
        """ defaults """
        pdb_mock = mock.MagicMock()
        val_mock = mock.MagicMock()
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.metric_value', val_mock):
            foo = pdr.get_dashboard_metrics(pdb_mock)
        assert pdb_mock.metric.call_count == 17
        assert val_mock.call_count == 17
        assert isinstance(foo, dict)

    def test_exception(self):
        """ throws a HTTP exception """
        pdb_mock = mock.MagicMock()

        def side_effect(*args, **kwargs):
            raise HTTPError('foo')

        pdb_mock.metric.side_effect = side_effect
        logger_mock = mock.MagicMock()
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
            foo = pdr.get_dashboard_metrics(pdb_mock)
        assert pdb_mock.metric.call_count == 17
        assert mock.call("unable to get value for metric: Catalog duplication") in logger_mock.debug.call_args_list


class Test_get_data_for_timespan:

    def test_is_cached(self):
        """ data is cached """
        path_exists_mock = mock.MagicMock()
        path_exists_mock.return_value = True
        query_mock = mock.MagicMock()
        query_mock.return_value = {}
        logger_mock = mock.MagicMock()

        raw_json = '{"foo": 123}'
        mock_open = mock.mock_open(read_data=raw_json)
        if sys.version_info[0] == 3:
            mock_target = 'builtins.open'
        else:
            mock_target = '__builtin__.open'

        with mock.patch('os.path.exists', path_exists_mock):
            with mock.patch(mock_target, mock_open, create=True):
                with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.query_data_for_timespan', query_mock):
                    with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
                        result = pdr.get_data_for_timespan(None,
                                                           datetime.datetime(2014, 06, 10, hour=0, minute=0, second=0),
                                                           datetime.datetime(2014, 06, 10, hour=23, minute=59, second=59),
                                                           cache_dir='/tmp/cache')
        assert path_exists_mock.call_count == 2
        assert path_exists_mock.call_args_list == [mock.call('/tmp/cache'),
                                                   mock.call('/tmp/cache/data_2014-06-10_00-00-00_2014-06-10_23-59-59.json')
                                                   ]
        assert mock_open.call_count == 1
        fh = mock_open.return_value.__enter__.return_value
        assert fh.read.call_count == 1
        assert result == {'foo': 123}
        assert fh.write.call_count == 0
        assert query_mock.call_count == 0
        assert logger_mock.debug.call_count == 3
        assert logger_mock.info.call_count == 1

    def test_no_cachedir(self):
        """cache_dir doesn't exist """
        def path_join(*args):
            return os.path.join(*args)
        os_mock = mock.MagicMock()
        os_mock.path.exists.return_value = False
        os_mock.makedirs.return_value = True
        os_mock.path.join.side_effect = path_join
        query_mock = mock.MagicMock()
        query_mock.return_value = {"foo": 123}
        logger_mock = mock.MagicMock()

        mock_open = mock.mock_open()
        if sys.version_info[0] == 3:
            mock_target = 'builtins.open'
        else:
            mock_target = '__builtin__.open'

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.os', os_mock):
            with mock.patch(mock_target, mock_open, create=True):
                with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.query_data_for_timespan', query_mock):
                    with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
                        result = pdr.get_data_for_timespan(None,
                                                           datetime.datetime(2014, 06, 10, hour=0, minute=0, second=0),
                                                           datetime.datetime(2014, 06, 10, hour=23, minute=59, second=59),
                                                           cache_dir='/tmp/cache')
        assert os_mock.path.exists.call_count == 2
        assert os_mock.path.exists.call_args_list == [mock.call('/tmp/cache'),
                                                      mock.call('/tmp/cache/data_2014-06-10_00-00-00_2014-06-10_23-59-59.json')
                                                      ]
        assert os_mock.makedirs.call_count == 1
        assert os_mock.makedirs.call_args == mock.call('/tmp/cache')
        assert mock_open.call_count == 1
        fh = mock_open.return_value.__enter__.return_value
        assert fh.read.call_count == 0
        assert fh.write.call_count == 1
        assert fh.write.call_args == mock.call('{"foo": 123}')
        assert query_mock.call_count == 1
        assert query_mock.call_args == mock.call(None,
                                                 datetime.datetime(2014, 06, 10, hour=0, minute=0, second=0),
                                                 datetime.datetime(2014, 06, 10, hour=23, minute=59, second=59)
                                                 )
        assert logger_mock.debug.call_count == 3
        assert logger_mock.info.call_count == 1

    def test_not_cached(self):
        """ data not cached """
        def path_join(*args):
            return os.path.join(*args)
        os_mock = mock.MagicMock()
        os_mock.path.exists.return_value = False
        os_mock.makedirs.return_value = True
        os_mock.path.join.side_effect = path_join
        query_mock = mock.MagicMock()
        query_mock.return_value = {"foo": 123}
        logger_mock = mock.MagicMock()

        mock_open = mock.mock_open()
        if sys.version_info[0] == 3:
            mock_target = 'builtins.open'
        else:
            mock_target = '__builtin__.open'

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.os', os_mock):
            with mock.patch(mock_target, mock_open, create=True):
                with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.query_data_for_timespan', query_mock):
                    with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
                        result = pdr.get_data_for_timespan(None,
                                                           datetime.datetime(2014, 06, 10, hour=0, minute=0, second=0),
                                                           datetime.datetime(2014, 06, 10, hour=23, minute=59, second=59),
                                                           cache_dir='/tmp/cache')
        assert os_mock.path.exists.call_count == 2
        assert os_mock.path.exists.call_args_list == [mock.call('/tmp/cache'),
                                                      mock.call('/tmp/cache/data_2014-06-10_00-00-00_2014-06-10_23-59-59.json')
                                                      ]
        assert mock_open.call_count == 1
        fh = mock_open.return_value.__enter__.return_value
        assert fh.read.call_count == 0
        assert fh.write.call_count == 1
        assert fh.write.call_args == mock.call('{"foo": 123}')
        assert query_mock.call_count == 1
        assert query_mock.call_args == mock.call(None,
                                                 datetime.datetime(2014, 06, 10, hour=0, minute=0, second=0),
                                                 datetime.datetime(2014, 06, 10, hour=23, minute=59, second=59)
                                                 )
        assert logger_mock.debug.call_count == 3
        assert logger_mock.info.call_count == 1

    def test_no_cache(self):
        """ caching disabled """
        path_exists_mock = mock.MagicMock()
        path_exists_mock.return_value = False
        query_mock = mock.MagicMock()
        query_mock.return_value = {"foo": 123}
        logger_mock = mock.MagicMock()

        mock_open = mock.mock_open()
        if sys.version_info[0] == 3:
            mock_target = 'builtins.open'
        else:
            mock_target = '__builtin__.open'

        with mock.patch('os.path.exists', path_exists_mock):
            with mock.patch(mock_target, mock_open, create=True):
                with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.query_data_for_timespan', query_mock):
                    with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
                        result = pdr.get_data_for_timespan(None,
                                                           datetime.datetime(2014, 06, 10, hour=0, minute=0, second=0),
                                                           datetime.datetime(2014, 06, 10, hour=23, minute=59, second=59),
                                                           cache_dir=None)
        assert path_exists_mock.call_count == 0
        assert mock_open.call_count == 0
        fh = mock_open.return_value.__enter__.return_value
        assert fh.read.call_count == 0
        assert fh.write.call_count == 0
        assert query_mock.call_count == 1
        assert query_mock.call_args == mock.call(None,
                                                 datetime.datetime(2014, 06, 10, hour=0, minute=0, second=0),
                                                 datetime.datetime(2014, 06, 10, hour=23, minute=59, second=59)
                                                 )
        assert logger_mock.debug.call_count == 1
        assert logger_mock.info.call_count == 0


class Test_main:
    """ tests for main() function """

    def test_default(self):
        """ as default as possible, one test """
        data = {'Fri 06/06': {'foo': 'bar'},
                'Tue 06/10': {'foo': 'bar'},
                'Thu 06/05': {'foo': 'bar'},
                'Wed 06/04': {'foo': 'bar'},
                'Sun 06/08': {'foo': 'bar'},
                'Sat 06/07': {'foo': 'bar'},
                'Mon 06/09': {'foo': 'bar'}
                }

        dates = ['Tue 06/10',
                 'Mon 06/09',
                 'Sun 06/08',
                 'Sat 06/07',
                 'Fri 06/06',
                 'Thu 06/05',
                 'Wed 06/04'
                 ]

        pdb_mock = mock.MagicMock(spec='pypuppetdb.api.v3.API')
        connect_mock = mock.MagicMock()
        connect_mock.return_value = pdb_mock
        format_html_mock = mock.MagicMock()
        format_html_mock.return_value = 'foo bar baz'
        send_mail_mock = mock.MagicMock()

        dft_mock = mock.MagicMock()
        dft_mock.return_value = {'foo': 'bar'}
        with freeze_time("2014-06-11 08:15:43"):
            with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.connect', connect_mock):
                with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.get_data_for_timespan', dft_mock):
                    with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.format_html', format_html_mock):
                        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.send_mail', send_mail_mock):
                            pdr.main('foobar')
        assert connect_mock.call_count == 1
        assert connect_mock.call_args == mock.call(host='foobar')

        assert dft_mock.call_count == 7
        dft_expected = [
            mock.call(pdb_mock, FakeDatetime(2014, 06, 10, hour=0, minute=0, second=0), FakeDatetime(2014, 06, 10, hour=23, minute=59, second=59), cache_dir=None),
            mock.call(pdb_mock, FakeDatetime(2014, 06, 9, hour=0, minute=0, second=0), FakeDatetime(2014, 06, 9, hour=23, minute=59, second=59), cache_dir=None),
            mock.call(pdb_mock, FakeDatetime(2014, 06, 8, hour=0, minute=0, second=0), FakeDatetime(2014, 06, 8, hour=23, minute=59, second=59), cache_dir=None),
            mock.call(pdb_mock, FakeDatetime(2014, 06, 7, hour=0, minute=0, second=0), FakeDatetime(2014, 06, 7, hour=23, minute=59, second=59), cache_dir=None),
            mock.call(pdb_mock, FakeDatetime(2014, 06, 6, hour=0, minute=0, second=0), FakeDatetime(2014, 06, 6, hour=23, minute=59, second=59), cache_dir=None),
            mock.call(pdb_mock, FakeDatetime(2014, 06, 5, hour=0, minute=0, second=0), FakeDatetime(2014, 06, 5, hour=23, minute=59, second=59), cache_dir=None),
            mock.call(pdb_mock, FakeDatetime(2014, 06, 4, hour=0, minute=0, second=0), FakeDatetime(2014, 06, 4, hour=23, minute=59, second=59), cache_dir=None),
        ]
        assert dft_mock.mock_calls == dft_expected

        assert format_html_mock.call_count == 1
        assert format_html_mock.call_args == mock.call('foobar',
                                                       dates,
                                                       data,
                                                       FakeDatetime(2014, 6, 10, 23, 59, 59),
                                                       FakeDatetime(2014, 6, 3, 23, 59, 59)
                                                       )
        assert send_mail_mock.call_count == 1
        assert send_mail_mock.call_args == mock.call('foo bar baz', dry_run=False)


class Test_metric_value:

    def test_float(self):
        result = pdr.metric_value({'Value': 1234567.89123456789})
        assert result == '1,234,567.891235'

    def test_int(self):
        result = pdr.metric_value({'Value': 123.00000})
        assert result == 123

    def test_float_zero(self):
        result = pdr.metric_value({'Value': 0.0})
        assert result == '0'

    def test_meanrate_count(self):
        result = pdr.metric_value({'MeanRate': 1234567.89123456789, 'Count': 1234})
        assert result == '1,234,567.891235 (1234)'

    def test_meanrate(self):
        result = pdr.metric_value({'MeanRate': 1234567.89123456789})
        assert result == '1,234,567.891235'

    def test_other(self):
        result = pdr.metric_value({'Foo': 'bar'})
        assert result == {'Foo': 'bar'}


class Test_send_mail:

    def test_dry_run(self):
        logger_mock = mock.MagicMock()

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
            result = pdr.send_mail('foo bar baz', dry_run=True)

        assert result == True
        assert logger_mock.debug.call_count == 0
        assert logger_mock.info.call_count == 1
        assert logger_mock.info.call_args == mock.call('would have sent: foo bar baz')

    def test_send(self):
        logger_mock = mock.MagicMock()

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
            result = pdr.send_mail('foo bar baz')

        assert result == True
        assert logger_mock.debug.call_count == 1
        assert logger_mock.debug.call_args == mock.call('sending mail')
        assert logger_mock.info.call_count == 0


class Test_query_data_for_timespan:

    def test_yesterday(self):
        """ simple test of default code path, checking for yesterday's date """
        node1 = mock.MagicMock(spec=pypuppetdb.types.Node, autospec=True)
        node1.name = u'node1'
        node2 = mock.MagicMock(spec=pypuppetdb.types.Node, autospec=True)
        node2.name = u'node2'
        node3 = mock.MagicMock(spec=pypuppetdb.types.Node, autospec=True)
        node3.name = u'node3'
        pdb_mock = mock.MagicMock(spec=pypuppetdb.api.v3.API, autospec=True)
        pdb_mock.nodes.return_value = iter([node1, node2, node3])
        logger_mock = mock.MagicMock()
        get_metrics_mock = mock.MagicMock()

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
            with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.get_dashboard_metrics', get_metrics_mock):
                with freeze_time("2014-06-11 08:15:43"):
                    foo = pdr.query_data_for_timespan(pdb_mock,
                                                      datetime.datetime(2014, 06, 10, hour=0, minute=0, second=0),
                                                      datetime.datetime(2014, 06, 10, hour=23, minute=59, second=59)
                                                      )
        # assert 1 == "todo - mock pdb.facts()"
        assert pdb_mock.nodes.call_count == 1
        assert foo['nodes'] == ['node1', 'node2', 'node3']
        assert logger_mock.debug.call_count == 8
        assert logger_mock.info.call_count == 1
        assert get_metrics_mock.call_count == 1
        assert get_metrics_mock.call_args == mock.call(pdb_mock)

    def test_before_yesterday(self):
        """ simple test of default code path, checking for yesterday's date """
        node1 = mock.MagicMock(spec=pypuppetdb.types.Node, autospec=True)
        node1.name = u'node1'
        node2 = mock.MagicMock(spec=pypuppetdb.types.Node, autospec=True)
        node2.name = u'node2'
        node3 = mock.MagicMock(spec=pypuppetdb.types.Node, autospec=True)
        node3.name = u'node3'
        pdb_mock = mock.MagicMock(spec=pypuppetdb.api.v3.API, autospec=True)
        pdb_mock.nodes.return_value = iter([node1, node2, node3])
        logger_mock = mock.MagicMock()
        get_metrics_mock = mock.MagicMock()

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
            with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.get_dashboard_metrics', get_metrics_mock):
                with freeze_time("2014-06-11 08:15:43"):
                    foo = pdr.query_data_for_timespan(pdb_mock,
                                                      datetime.datetime(2014, 06, 7, hour=0, minute=0, second=0),
                                                      datetime.datetime(2014, 06, 7, hour=23, minute=59, second=59)
                                                      )
        assert pdb_mock.nodes.call_count == 1
        assert foo['nodes'] == ['node1', 'node2', 'node3']
        assert logger_mock.debug.call_count == 7
        assert logger_mock.info.call_count == 1
        assert get_metrics_mock.call_count == 0


class Test_format_html:

    strip_whitespace_re = re.compile(r'\s+')

    def test_basic(self):
        data = {'foo': 'bar'}
        dates = []

        env_mock = mock.MagicMock(spec=Environment, autospec=True)
        env_obj_mock = mock.MagicMock(spec=Environment, autospec=True)
        tmpl_mock = mock.MagicMock(spec=Template, autospec=True)
        tmpl_mock.render.return_value = 'baz'
        env_obj_mock.get_template.return_value = tmpl_mock
        env_mock.return_value = env_obj_mock
        pl_mock = mock.MagicMock(spec=PackageLoader, autospec=True)
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.Environment', env_mock):
            with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.PackageLoader', pl_mock):
                html = pdr.format_html('foo.example.com',
                                       dates,
                                       data,
                                       datetime.datetime(2014, 06, 3, 0, 0, 0),
                                       datetime.datetime(2014, 06, 10, hour=23, minute=59, second=59)
                                       )
        assert env_mock.call_count == 1
        assert pl_mock.call_count == 1
        assert pl_mock.call_args == mock.call('pypuppetdb_daily_report', 'templates')
        assert env_obj_mock.get_template.call_count == 1
        assert env_obj_mock.get_template.call_args == mock.call('base.html')
        assert tmpl_mock.render.call_count == 1
        assert tmpl_mock.render.call_args == mock.call(data={'foo': 'bar'},
                                                       dates=[],
                                                       hostname='foo.example.com',
                                                       start=datetime.datetime(2014, 06, 3, hour=0, minute=0, second=0),
                                                       end=datetime.datetime(2014, 06, 10, hour=23, minute=59, second=59)
                                                       )
        assert html == 'baz'

    def test_body(self):
        data = {'Fri 06/06': {'foo': 'bar'},
                'Tue 06/10': {'foo': 'bar'},
                'Thu 06/05': {'foo': 'bar'},
                'Wed 06/04': {'foo': 'bar'},
                'Sun 06/08': {'foo': 'bar'},
                'Sat 06/07': {'foo': 'bar'},
                'Mon 06/09': {'foo': 'bar'}
                }

        dates = ['Tue 06/10',
                 'Mon 06/09',
                 'Sun 06/08',
                 'Sat 06/07',
                 'Fri 06/06',
                 'Thu 06/05',
                 'Wed 06/04'
                 ]
        html = pdr.format_html('foo.example.com',
                               dates,
                               data,
                               datetime.datetime(2014, 06, 3, hour=0, minute=0, second=0),
                               datetime.datetime(2014, 06, 10, hour=23, minute=59, second=59)
                               )
        assert '<html>' in html
        assert '<h1>daily puppet(db) run summary on foo.example.com for Tue Jun 03, 2014 to Tue Jun 10</h1>' in html

    def test_metrics(self):
        data = {'Tue 06/10': {'metrics': {'foo': {'formatted': 'foo1'}, 'bar': {'formatted': 'bar1'}, 'baz': {'formatted': 'baz1'}}},
                'Mon 06/09': {'metrics': {'foo': {'formatted': 'foo2'}, 'bar': {'formatted': 'bar2'}, 'baz': {'formatted': 'baz2'}}},
                'Sun 06/08': {'metrics': {'foo': {'formatted': 'foo3'}, 'bar': {'formatted': 'bar3'}, 'baz': {'formatted': 'baz3'}}},
                'Sat 06/07': {'metrics': {'foo': {'formatted': 'foo4'}, 'bar': {'formatted': 'bar4'}, 'baz': {'formatted': 'baz4'}}},
                'Fri 06/06': {'metrics': {'foo': {'formatted': 'foo5'}, 'bar': {'formatted': 'bar5'}, 'baz': {'formatted': 'baz5'}}},
                'Thu 06/05': {'metrics': {'foo': {'formatted': 'foo6'}, 'bar': {'formatted': 'bar6'}, 'baz': {'formatted': 'baz6'}}},
                'Wed 06/04': {'foo': 'bar'},
                }

        dates = ['Tue 06/10',
                 'Mon 06/09',
                 'Sun 06/08',
                 'Sat 06/07',
                 'Fri 06/06',
                 'Thu 06/05',
                 'Wed 06/04'
                 ]
        html = pdr.format_html('foo.example.com',
                               dates,
                               data,
                               datetime.datetime(2014, 06, 3, hour=0, minute=0, second=0),
                               datetime.datetime(2014, 06, 10, hour=23, minute=59, second=59)
                               )
        stripped = self.strip_whitespace_re.sub('', html)
        assert '<html>' in html
        assert '<tr><th>Metric</th><th>Tue 06/10</th><th>Mon 06/09</th><th>Sun 06/08</th><th>Sat 06/07</th><th>Fri 06/06</th><th>Thu 06/05</th><th>Wed 06/04</th></tr>' in html
        assert '<tr><th>bar</th><td>' in stripped
        assert '<tr><th>baz</th><td>' in stripped
        assert '<tr><th>foo</th><td>foo1</td><td>foo2</td><td>foo3</td><td>foo4</td><td>foo5</td><td>foo6</td><td>&nbsp;</td></tr>' in stripped
