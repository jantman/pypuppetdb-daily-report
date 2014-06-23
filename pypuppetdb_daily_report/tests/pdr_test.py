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
import mock
import logging
import datetime
from freezegun import freeze_time
from freezegun.api import FakeDatetime
from requests.exceptions import HTTPError
import pypuppetdb
from jinja2 import Environment, PackageLoader, Template
import pytz
from copy import deepcopy
from collections import OrderedDict

from pypuppetdb_daily_report import pypuppetdb_daily_report as pdr
from pypuppetdb_daily_report import VERSION

# fixtures
from . import test_data


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
        self.to = None
        self.to_str = None


class FactObject(object):
    """ object to mock a Fact """
    def __init__(self, value):
        self.value = value


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

    def test_to(self):
        """
        Test the parse_args option parsing method with to address specified
        """
        argv = ['pypuppetdb_daily_report', '-t', 'foo@example.com']
        x = pdr.parse_args(argv)
        assert x.to == ['foo@example.com']

    def test_to_multiple(self):
        """
        Test the parse_args option parsing method with multiple to addresses specified
        """
        argv = ['pypuppetdb_daily_report', '-t', 'foo@example.com,bar@example.com,baz@example.com']
        x = pdr.parse_args(argv)
        assert x.to == ['foo@example.com', 'bar@example.com', 'baz@example.com']


class Test_console_entry_point:
    """ test console_entry_point """

    def test_defaults(self):
        """ with default values """
        parse_args_mock = mock.MagicMock()
        opts_o = OptionsObject()
        opts_o.host = 'foobar'
        opts_o.to = ['foo@example.com']
        parse_args_mock.return_value = opts_o

        main_mock = mock.MagicMock()

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.parse_args', parse_args_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.main', main_mock):
            pdr.console_entry_point()
        assert parse_args_mock.call_count == 1
        assert main_mock.call_count == 1
        assert main_mock.call_args == mock.call('foobar',
                                                to=['foo@example.com'],
                                                num_days=7,
                                                dry_run=False,
                                                cache_dir='/tmp/.pypuppetdb_daily_report')

    def test_nohost(self):
        """ without a host specified """
        parse_args_mock = mock.MagicMock()
        opts_o = OptionsObject()
        opts_o.to = ['foo@example.com']
        parse_args_mock.return_value = opts_o
        main_mock = mock.MagicMock()

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.parse_args', parse_args_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.main', main_mock), \
                pytest.raises(SystemExit) as excinfo:
            pdr.console_entry_point()
        assert parse_args_mock.call_count == 1
        assert main_mock.call_count == 0
        assert excinfo.value.__str__() == "ERROR: you must specify the PuppetDB hostname with -p|--puppetdb"

    def test_verbose(self):
        """ with -v """
        parse_args_mock = mock.MagicMock()
        opts_o = OptionsObject()
        opts_o.host = 'foobar'
        opts_o.verbose = 1
        opts_o.to = ['foo@example.com']
        parse_args_mock.return_value = opts_o
        logger_mock = mock.MagicMock()
        main_mock = mock.MagicMock()

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.parse_args', parse_args_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.main', main_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
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
        opts_o.to = ['foo@example.com']
        parse_args_mock.return_value = opts_o
        logger_mock = mock.MagicMock()
        main_mock = mock.MagicMock()

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.parse_args', parse_args_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.main', main_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
            pdr.console_entry_point()
        assert parse_args_mock.call_count == 1
        assert main_mock.call_count == 1
        assert logger_mock.setLevel.call_count == 1
        assert logger_mock.setLevel.call_args == mock.call(logging.DEBUG)

    def test_no_to(self):
        """ without dry-run or a to address """
        parse_args_mock = mock.MagicMock()
        opts_o = OptionsObject()
        opts_o.host = 'foobar'
        parse_args_mock.return_value = opts_o
        main_mock = mock.MagicMock()

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.parse_args', parse_args_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.main', main_mock), \
                pytest.raises(SystemExit) as excinfo:
            pdr.console_entry_point()
        assert parse_args_mock.call_count == 1
        assert main_mock.call_count == 0
        assert excinfo.value.__str__() == "ERROR: you must either run with --dry-run or specify to address(es) with --to"


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
            pdr.get_dashboard_metrics(pdb_mock)
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
        pickle_mock = mock.MagicMock()
        pickle_mock.return_value = {'foo': 123}

        raw = "(dp1\nS'foo'\np2\nI123\ns."
        mock_open = mock.mock_open(read_data=raw)
        if sys.version_info[0] == 3:
            mock_target = 'builtins.open'
        else:
            mock_target = '__builtin__.open'

        with mock.patch('os.path.exists', path_exists_mock), \
                mock.patch(mock_target, mock_open, create=True), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.query_data_for_timespan', query_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock), \
                mock.patch('pickle.loads', pickle_mock):
            result = pdr.get_data_for_timespan('foobar',
                                               None,
                                               datetime.datetime(2014, 6, 10, hour=0, minute=0, second=0),
                                               datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59),
                                               cache_dir='/tmp/cache')
        assert path_exists_mock.call_count == 2
        assert path_exists_mock.call_args_list == [mock.call('/tmp/cache'),
                                                   mock.call('/tmp/cache/data_foobar_2014-06-10_00-00-00_2014-06-10_23-59-59.pickle')
                                                   ]
        assert mock_open.call_count == 1
        fh = mock_open.return_value.__enter__.return_value
        assert fh.read.call_count == 1
        assert result == {'foo': 123}
        assert fh.write.call_count == 0
        assert query_mock.call_count == 0
        assert logger_mock.debug.call_count == 3
        assert logger_mock.info.call_count == 1
        assert pickle_mock.call_count == 1
        assert pickle_mock.call_args == mock.call(raw)

    def test_no_cachedir(self):
        """cache_dir doesn't exist, it gets created """
        def path_join(*args):
            return os.path.join(*args)
        os_mock = mock.MagicMock()
        os_mock.path.exists.return_value = False
        os_mock.makedirs.return_value = True
        os_mock.path.join.side_effect = path_join
        query_mock = mock.MagicMock()
        query_mock.return_value = {"foo": 123}
        logger_mock = mock.MagicMock()
        pickle_mock = mock.MagicMock()
        pickle_mock.return_value = "(dp1\nS'foo'\np2\nI123\ns."

        mock_open = mock.mock_open()
        if sys.version_info[0] == 3:
            mock_target = 'builtins.open'
        else:
            mock_target = '__builtin__.open'

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.os', os_mock), \
                mock.patch(mock_target, mock_open, create=True), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.query_data_for_timespan', query_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock), \
                mock.patch('pickle.dumps', pickle_mock):
            pdr.get_data_for_timespan('foobar',
                                      None,
                                      datetime.datetime(2014, 6, 10, hour=0, minute=0, second=0),
                                      datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59),
                                      cache_dir='/tmp/cache')
        assert os_mock.path.exists.call_count == 2
        assert os_mock.path.exists.call_args_list == [mock.call('/tmp/cache'),
                                                      mock.call('/tmp/cache/data_foobar_2014-06-10_00-00-00_2014-06-10_23-59-59.pickle')
                                                      ]
        assert os_mock.makedirs.call_count == 1
        assert os_mock.makedirs.call_args == mock.call('/tmp/cache')
        assert mock_open.call_count == 1
        fh = mock_open.return_value.__enter__.return_value
        assert fh.read.call_count == 0
        assert fh.write.call_count == 1
        assert fh.write.call_args == mock.call("(dp1\nS'foo'\np2\nI123\ns.")
        assert query_mock.call_count == 1
        assert query_mock.call_args == mock.call(None,
                                                 datetime.datetime(2014, 6, 10, hour=0, minute=0, second=0),
                                                 datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59)
                                                 )
        assert logger_mock.debug.call_count == 3
        assert logger_mock.info.call_count == 1
        assert pickle_mock.call_count == 1
        assert pickle_mock.call_args == mock.call({"foo": 123})

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
        pickle_mock = mock.MagicMock()
        pickle_mock.return_value = "(dp1\nS'foo'\np2\nI123\ns."

        mock_open = mock.mock_open()
        if sys.version_info[0] == 3:
            mock_target = 'builtins.open'
        else:
            mock_target = '__builtin__.open'

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.os', os_mock), \
                mock.patch(mock_target, mock_open, create=True), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.query_data_for_timespan', query_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock), \
                mock.patch('pickle.dumps', pickle_mock):
            pdr.get_data_for_timespan('foobar',
                                      None,
                                      datetime.datetime(2014, 6, 10, hour=0, minute=0, second=0),
                                      datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59),
                                      cache_dir='/tmp/cache')
        assert os_mock.path.exists.call_count == 2
        assert os_mock.path.exists.call_args_list == [mock.call('/tmp/cache'),
                                                      mock.call('/tmp/cache/data_foobar_2014-06-10_00-00-00_2014-06-10_23-59-59.pickle')
                                                      ]
        assert mock_open.call_count == 1
        fh = mock_open.return_value.__enter__.return_value
        assert fh.read.call_count == 0
        assert fh.write.call_count == 1
        assert fh.write.call_args == mock.call("(dp1\nS'foo'\np2\nI123\ns.")
        assert query_mock.call_count == 1
        assert query_mock.call_args == mock.call(None,
                                                 datetime.datetime(2014, 6, 10, hour=0, minute=0, second=0),
                                                 datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59)
                                                 )
        assert logger_mock.debug.call_count == 3
        assert logger_mock.info.call_count == 1
        assert pickle_mock.call_count == 1
        assert pickle_mock.call_args == mock.call({"foo": 123})

    def test_no_cache(self):
        """ caching disabled """
        path_exists_mock = mock.MagicMock()
        path_exists_mock.return_value = False
        query_mock = mock.MagicMock()
        query_mock.return_value = {"foo": 123}
        logger_mock = mock.MagicMock()
        pickle_mock = mock.MagicMock()

        mock_open = mock.mock_open()
        if sys.version_info[0] == 3:
            mock_target = 'builtins.open'
        else:
            mock_target = '__builtin__.open'

        with mock.patch('os.path.exists', path_exists_mock), \
                mock.patch(mock_target, mock_open, create=True), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.query_data_for_timespan', query_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock), \
                mock.patch('pickle.dumps', pickle_mock):
            pdr.get_data_for_timespan('foobar',
                                      None,
                                      datetime.datetime(2014, 6, 10, hour=0, minute=0, second=0),
                                      datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59),
                                      cache_dir=None)
        assert path_exists_mock.call_count == 0
        assert mock_open.call_count == 0
        fh = mock_open.return_value.__enter__.return_value
        assert fh.read.call_count == 0
        assert fh.write.call_count == 0
        assert query_mock.call_count == 1
        assert query_mock.call_args == mock.call(None,
                                                 datetime.datetime(2014, 6, 10, hour=0, minute=0, second=0),
                                                 datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59)
                                                 )
        assert logger_mock.debug.call_count == 1
        assert logger_mock.info.call_count == 0
        assert pickle_mock.call_count == 0


class Test_main:
    """ tests for main() function """

    # TODO: refactor this test
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

        date_list = [FakeDatetime(2014, 6, 11, hour=3, minute=59, second=59, tzinfo=pytz.utc),
                     FakeDatetime(2014, 6, 10, hour=3, minute=59, second=59, tzinfo=pytz.utc),
                     FakeDatetime(2014, 6, 9, hour=3, minute=59, second=59, tzinfo=pytz.utc),
                     FakeDatetime(2014, 6, 8, hour=3, minute=59, second=59, tzinfo=pytz.utc),
                     FakeDatetime(2014, 6, 7, hour=3, minute=59, second=59, tzinfo=pytz.utc),
                     FakeDatetime(2014, 6, 6, hour=3, minute=59, second=59, tzinfo=pytz.utc),
                     FakeDatetime(2014, 6, 5, hour=3, minute=59, second=59, tzinfo=pytz.utc),
                     ]

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
        logger_mock = mock.MagicMock()
        date_list_mock = mock.MagicMock(return_value=date_list)
        localzone_mock = mock.MagicMock()
        localzone_mock.return_value = pytz.timezone('US/Eastern')

        dft_mock = mock.MagicMock()
        dft_mock.return_value = {'foo': 'bar'}
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.get_date_list', date_list_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.connect', connect_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.get_data_for_timespan', dft_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.format_html', format_html_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.send_mail', send_mail_mock), \
                mock.patch('tzlocal.get_localzone', localzone_mock):
            pdr.main('foobar', to=['foo@example.com'])
        assert connect_mock.call_count == 1
        assert connect_mock.call_args == mock.call(host='foobar')

        assert dft_mock.call_count == 7
        dft_expected = [
            mock.call('foobar', pdb_mock, FakeDatetime(2014, 6, 10, hour=4, minute=0, second=0, tzinfo=pytz.utc), FakeDatetime(2014, 6, 11, hour=3, minute=59, second=59, tzinfo=pytz.utc), cache_dir=None),
            mock.call('foobar', pdb_mock, FakeDatetime(2014, 6, 9, hour=4, minute=0, second=0, tzinfo=pytz.utc), FakeDatetime(2014, 6, 10, hour=3, minute=59, second=59, tzinfo=pytz.utc), cache_dir=None),
            mock.call('foobar', pdb_mock, FakeDatetime(2014, 6, 8, hour=4, minute=0, second=0, tzinfo=pytz.utc), FakeDatetime(2014, 6, 9, hour=3, minute=59, second=59, tzinfo=pytz.utc), cache_dir=None),
            mock.call('foobar', pdb_mock, FakeDatetime(2014, 6, 7, hour=4, minute=0, second=0, tzinfo=pytz.utc), FakeDatetime(2014, 6, 8, hour=3, minute=59, second=59, tzinfo=pytz.utc), cache_dir=None),
            mock.call('foobar', pdb_mock, FakeDatetime(2014, 6, 6, hour=4, minute=0, second=0, tzinfo=pytz.utc), FakeDatetime(2014, 6, 7, hour=3, minute=59, second=59, tzinfo=pytz.utc), cache_dir=None),
            mock.call('foobar', pdb_mock, FakeDatetime(2014, 6, 5, hour=4, minute=0, second=0, tzinfo=pytz.utc), FakeDatetime(2014, 6, 6, hour=3, minute=59, second=59, tzinfo=pytz.utc), cache_dir=None),
            mock.call('foobar', pdb_mock, FakeDatetime(2014, 6, 4, hour=4, minute=0, second=0, tzinfo=pytz.utc), FakeDatetime(2014, 6, 5, hour=3, minute=59, second=59, tzinfo=pytz.utc), cache_dir=None),
        ]
        assert dft_mock.mock_calls == dft_expected

        assert format_html_mock.call_count == 1
        r = mock.call('foobar',
                      dates,
                      data,
                      FakeDatetime(2014, 6, 11, 3, 59, 59, tzinfo=pytz.utc),
                      FakeDatetime(2014, 6, 4, 4, 0, 0, tzinfo=pytz.utc)
                      )
        assert format_html_mock.call_args == r
        assert send_mail_mock.call_count == 1
        assert send_mail_mock.call_args == mock.call(['foo@example.com'], 'daily puppet(db) run summary for foobar', 'foo bar baz', dry_run=False)


class Test_get_date_list:
    """ tests for get_date_list() function """

    def test_simple(self):
        """ as default as possible, one test """
        logger_mock = mock.MagicMock()
        localzone_mock = mock.MagicMock()
        localzone_mock.return_value = pytz.timezone('US/Eastern')

        with freeze_time("2014-06-11 08:15:43", tz_offset=-4), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock), \
                mock.patch('tzlocal.get_localzone', localzone_mock):
            pdr.get_date_list(7)

        assert logger_mock.debug.call_args_list == [mock.call('local_start_date=2014-06-10 23:59:59-0400 EDT'),
                                                    mock.call('start_date=2014-06-11 03:59:59+0000 UTC'),
                                                    mock.call('end_date=2014-06-04 04:00:00+0000 UTC')
                                                    ]


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
        assert result == '1,234,567.891235/s (1234)'

    def test_meanrate(self):
        result = pdr.metric_value({'MeanRate': 1234567.89123456789})
        assert result == '1,234,567.891235/s'

    def test_AverageEnqueueTime(self):
        result = pdr.metric_value({'AverageEnqueueTime': 1234567.89123456789})
        assert result == '1,234,567.891235/s'

    def test_other(self):
        result = pdr.metric_value({'Foo': 'bar'})
        assert result == {'Foo': 'bar'}


class Test_send_mail:

    def test_dry_run(self):
        logger_mock = mock.MagicMock()
        mock_open = mock.mock_open()

        if sys.version_info[0] == 3:
            mock_target = 'builtins.open'
        else:
            mock_target = '__builtin__.open'

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock), \
                mock.patch(mock_target, mock_open, create=True):
            result = pdr.send_mail(None, 'foo bar baz', '<html></html>', dry_run=True)

        assert result == True
        assert logger_mock.warning.call_count == 1
        assert logger_mock.warning.call_args == mock.call("DRY RUN - not sending mail; wrote body to ./output.html")
        assert mock_open.call_count == 1
        assert mock_open.call_args == mock.call('output.html', 'w')
        fh = mock_open.return_value.__enter__.return_value
        assert fh.write.call_count == 1
        assert fh.write.call_args == mock.call('<html></html>')

    def test_send(self):
        logger_mock = mock.MagicMock()
        mimemultipart_mock = mock.MagicMock()
        mimetext_mock = mock.MagicMock()
        smtp_mock = mock.MagicMock()
        smtp_mock_res = mock.MagicMock()
        smtp_mock.return_value = smtp_mock_res
        node_mock = mock.MagicMock(return_value='nodename')
        getuser_mock = mock.MagicMock(return_value='username')

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.MIMEMultipart', mimemultipart_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.MIMEText', mimetext_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.platform_node', node_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.getuser', getuser_mock), \
                mock.patch('smtplib.SMTP', smtp_mock):
            result = pdr.send_mail(['foo@example.com', 'bar@example.com'], 'foo bar baz', '<html></html>')

        assert result == True
        assert logger_mock.debug.call_count == 1
        assert logger_mock.debug.call_args == mock.call('sending mail')
        assert mock.call('alternative') in mimemultipart_mock.mock_calls
        assert mock.call().__setitem__('subject', 'foo bar baz') in mimemultipart_mock.mock_calls
        assert mock.call().__setitem__('To', 'foo@example.com,bar@example.com') in mimemultipart_mock.mock_calls
        assert mock.call().__setitem__('From', 'username@nodename') in mimemultipart_mock.mock_calls
        assert mimetext_mock.call_count == 1
        assert mimetext_mock.call_args == mock.call('<html></html>', 'html')
        assert smtp_mock.call_count == 1
        assert smtp_mock_res.sendmail.call_count == 1


class Test_query_data_for_timespan:

    # TODO: refactor this test
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
        query_node_mock = mock.MagicMock()
        query_node_mock.return_value = {'reports': {'foo': 'bar'}}
        get_facts_mock = mock.MagicMock()
        agg_mock = mock.MagicMock(return_value={})

        start = datetime.datetime(2014, 6, 10, hour=4, minute=0, second=0, tzinfo=pytz.utc)
        end = datetime.datetime(2014, 6, 11, hour=3, minute=59, second=59, tzinfo=pytz.utc)

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.get_dashboard_metrics', get_metrics_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.get_facts', get_facts_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.query_data_for_node', query_node_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.aggregate_data_for_timespan', agg_mock), \
                freeze_time("2014-06-11 08:15:43"):
            foo = pdr.query_data_for_timespan(pdb_mock,
                                              start,
                                              end
                                              )
        # assert 1 == "todo - mock pdb.facts()"
        assert pdb_mock.nodes.call_count == 1
        assert foo['nodes'] == {'node1': {'reports': {'foo': 'bar'}},
                                'node2': {'reports': {'foo': 'bar'}},
                                'node3': {'reports': {'foo': 'bar'}}
                                }
        assert logger_mock.debug.call_count == 7
        assert logger_mock.info.call_count == 1
        assert get_metrics_mock.call_count == 1
        assert get_metrics_mock.call_args == mock.call(pdb_mock)
        assert get_facts_mock.call_count == 1
        assert get_facts_mock.call_args == mock.call(pdb_mock)
        assert query_node_mock.call_count == 3
        assert query_node_mock.call_args_list == [mock.call(pdb_mock, node1, start, end),
                                                  mock.call(pdb_mock, node2, start, end),
                                                  mock.call(pdb_mock, node3, start, end)
                                                  ]
        assert agg_mock.call_count == 1
        agg_arg = foo
        agg_arg.pop('aggregate')
        assert agg_mock.call_args == mock.call(agg_arg)

    # TODO: refactor this test
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
        get_facts_mock = mock.MagicMock()
        query_node_mock = mock.MagicMock()
        query_node_mock.return_value = {'reports': {'foo': 'bar'}}
        agg_mock = mock.MagicMock(return_value={})

        start = datetime.datetime(2014, 6, 7, hour=4, minute=0, second=0, tzinfo=pytz.utc)
        end = datetime.datetime(2014, 6, 8, hour=3, minute=59, second=59, tzinfo=pytz.utc)

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.get_dashboard_metrics', get_metrics_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.get_facts', get_facts_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.query_data_for_node', query_node_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.aggregate_data_for_timespan', agg_mock), \
                freeze_time("2014-06-11 08:15:43"):
            foo = pdr.query_data_for_timespan(pdb_mock,
                                              start,
                                              end
                                              )
        assert pdb_mock.nodes.call_count == 1
        assert foo['nodes'] == {'node1': {'reports': {'foo': 'bar'}},
                                'node2': {'reports': {'foo': 'bar'}},
                                'node3': {'reports': {'foo': 'bar'}}
                                }
        assert logger_mock.debug.call_count == 6
        assert logger_mock.info.call_count == 1
        assert get_metrics_mock.call_count == 0
        assert get_facts_mock.call_count == 0
        assert query_node_mock.call_count == 3
        assert query_node_mock.call_args_list == [mock.call(pdb_mock, node1, start, end),
                                                  mock.call(pdb_mock, node2, start, end),
                                                  mock.call(pdb_mock, node3, start, end)
                                                  ]
        assert agg_mock.call_count == 1
        agg_arg = foo
        agg_arg.pop('aggregate')
        assert agg_mock.call_args == mock.call(agg_arg)


class Test_query_data_for_node:

    # pypuppetdb datetimes are tz-aware, and appear to always be UTC
    r1 = mock.MagicMock()
    r1.start = datetime.datetime(2014, 6, 11, hour=5, minute=50, second=0, tzinfo=pytz.utc)
    r1.run_time = datetime.timedelta(seconds=4000)
    r1.hash_ = 'hash1'
    r2 = mock.MagicMock()
    r2.start = datetime.datetime(2014, 6, 11, hour=5, minute=9, second=0, tzinfo=pytz.utc)
    r2.run_time = datetime.timedelta(seconds=100)
    r2.hash_ = 'hash2'
    # start what should return
    r3 = mock.MagicMock()
    r3.start = datetime.datetime(2014, 6, 11, hour=3, minute=55, second=0, tzinfo=pytz.utc)
    r3.run_time = datetime.timedelta(seconds=1)
    r3.hash_ = 'hash3'
    r4 = mock.MagicMock()
    r4.start = datetime.datetime(2014, 6, 10, hour=17, minute=0, second=0, tzinfo=pytz.utc)
    r4.run_time = datetime.timedelta(seconds=100)
    r4.hash_ = 'hash4'
    r5 = mock.MagicMock()
    r5.start = datetime.datetime(2014, 6, 10, hour=5, minute=0, second=2, tzinfo=pytz.utc)
    r5.run_time = datetime.timedelta(seconds=1000)
    r5.hash_ = 'hash5'
    r6 = mock.MagicMock()
    r6.start = datetime.datetime(2014, 6, 10, hour=4, minute=59, second=55, tzinfo=pytz.utc)
    r6.run_time = datetime.timedelta(seconds=10)
    r6.hash_ = 'hash6'
    # end what should return
    r7 = mock.MagicMock()
    r7.start = datetime.datetime(2014, 6, 9, hour=17, minute=50, second=0, tzinfo=pytz.utc)
    r7.run_time = datetime.timedelta(seconds=2000)
    r7.hash_ = 'hash7'
    reports = [r1, r2, r3, r4, r5, r6, r7]

    def test_iterate_reports(self):
        """ simple test of default code path """
        pdb_mock = mock.MagicMock(spec=pypuppetdb.api.v3.API, autospec=True)
        node_mock = mock.MagicMock(spec=pypuppetdb.types.Node, autospec=True)
        node_mock.name = 'node1.example.com'
        logger_mock = mock.MagicMock()
        node_mock.reports.return_value = self.reports

        start = datetime.datetime(2014, 6, 10, hour=4, minute=0, second=0, tzinfo=pytz.utc)
        end = datetime.datetime(2014, 6, 11, hour=3, minute=59, second=59, tzinfo=pytz.utc)

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
            foo = pdr.query_data_for_node(pdb_mock,
                                          node_mock,
                                          start,
                                          end
                                          )
        assert node_mock.reports.call_count == 1
        assert logger_mock.debug.call_count == 3
        assert logger_mock.debug.call_args_list == [mock.call('querying node node1.example.com for timespan: 2014-06-10 04-00-00+0000 to 2014-06-11 03-59-59+0000'),
                                                    mock.call('found first report before time period - start time is 2014-06-09 17:50:00+00:00'),
                                                    mock.call('got 4 reports for node'),
                                                    ]
        assert foo['reports']['run_count'] == 4
        assert foo['reports']['run_time_total'] == datetime.timedelta(seconds=1111)
        assert foo['reports']['run_time_max'] == datetime.timedelta(seconds=1000)
        assert pdb_mock.events.call_args_list == [mock.call('["=", "report", "hash3"]'),
                                                  mock.call('["=", "report", "hash4"]'),
                                                  mock.call('["=", "report", "hash5"]'),
                                                  mock.call('["=", "report", "hash6"]')
                                                  ]

    def test_iterate_events(self):
        """ test iterating over events """
        pdb_mock = mock.MagicMock(spec=pypuppetdb.api.v3.API, autospec=True)
        logger_mock = mock.MagicMock()
        node_mock = mock.MagicMock(spec=pypuppetdb.types.Node, autospec=True)
        node_mock.name = 'node1.example.com'
        r1 = mock.MagicMock()
        r1.start = datetime.datetime(2014, 6, 10, hour=5, minute=0, second=2, tzinfo=pytz.utc)
        r1.run_time = datetime.timedelta(seconds=1000)
        r1.hash_ = 'hash1'
        r2 = mock.MagicMock()
        r2.start = datetime.datetime(2014, 6, 10, hour=5, minute=10, second=2, tzinfo=pytz.utc)
        r2.run_time = datetime.timedelta(seconds=10)
        r2.hash_ = 'hash2'
        r3 = mock.MagicMock()
        r3.start = datetime.datetime(2014, 6, 10, hour=5, minute=11, second=2, tzinfo=pytz.utc)
        r3.run_time = datetime.timedelta(seconds=10)
        r3.hash_ = 'hash3'
        r4 = mock.MagicMock()
        r4.start = datetime.datetime(2014, 6, 10, hour=5, minute=12, second=2, tzinfo=pytz.utc)
        r4.run_time = datetime.timedelta(seconds=10)
        r4.hash_ = 'hash4'
        node_mock.reports.return_value = [r1, r2, r3, r4]

        event_data = deepcopy(test_data.EVENT_DATA)

        def event_se(query):
            return event_data.get(query, [])
        pdb_mock.events.side_effect = event_se

        start = datetime.datetime(2014, 6, 10, hour=4, minute=0, second=0, tzinfo=pytz.utc)
        end = datetime.datetime(2014, 6, 11, hour=3, minute=59, second=59, tzinfo=pytz.utc)

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock):
            foo = pdr.query_data_for_node(pdb_mock,
                                          node_mock,
                                          start,
                                          end
                                          )
        assert node_mock.reports.call_count == 1
        assert logger_mock.debug.call_count == 2
        assert pdb_mock.event_counts.call_count == 0
        assert pdb_mock.events.call_count == 4
        assert pdb_mock.events.call_args_list == [mock.call('["=", "report", "hash1"]'),
                                                  mock.call('["=", "report", "hash2"]'),
                                                  mock.call('["=", "report", "hash3"]'),
                                                  mock.call('["=", "report", "hash4"]'),
                                                  ]
        assert foo['reports']['run_count'] == 4
        assert foo['reports']['run_time_total'] == datetime.timedelta(seconds=1030)
        assert foo['reports']['run_time_max'] == datetime.timedelta(seconds=1000)
        assert foo['reports']['with_failures'] == 2
        assert foo['reports']['with_changes'] == 2
        assert foo['reports']['with_skips'] == 1
        assert foo['resources']['failed'][('Package', 'srvadmin-idrac7')] == 2
        assert foo['resources']['skipped'][('Service', 'dataeng')] == 1
        assert foo['resources']['failed'][('Package', 'libsmbios')] == 1
        assert foo['resources']['skipped'][('Augeas', 'disable dell yum plugin once OM is installed')] == 1
        assert foo['resources']['changed'][('Exec', 'zookeeper ensemble check')] == 1
        assert foo['resources']['changed'][('Service', 'winbind')] == 1
        assert foo['resources']['changed'][('Service', 'zookeeper-server')] == 2


class Test_get_facts:

    def test_get_facts(self):
        """ defaults """
        def fact_getter(name):
            if name == 'puppetversion':
                return [FactObject('a'),
                        FactObject('a'),
                        FactObject('a'),
                        FactObject('b'),
                        FactObject('b'),
                        FactObject('c')
                        ]
            if name == 'facterversion':
                return [FactObject('one'),
                        FactObject('two'),
                        FactObject('two')
                        ]
            if name == 'lsbdistdescription':
                return [FactObject('1'),
                        FactObject('1'),
                        FactObject('1'),
                        FactObject('1'),
                        FactObject('2'),
                        FactObject('3'),
                        FactObject('4'),
                        FactObject('5')
                        ]
            return []
        expected = {'puppetversion': {'a': 3, 'b': 2, 'c': 1},
                    'facterversion': {'one': 1, 'two': 2},
                    'lsbdistdescription': {'1': 4, '2': 1, '3': 1, '4': 1, '5': 1}
                    }

        pdb_mock = mock.MagicMock()
        pdb_mock.facts.side_effect = fact_getter
        foo = pdr.get_facts(pdb_mock)
        assert pdb_mock.facts.call_count == 3
        assert isinstance(foo, dict)
        assert foo == expected


class Test_filter_report_metric_name:

    def test_aggregate(self):
        assert pdr.filter_report_metric_name('with_skips') == 'With Skipped Resources'
        assert pdr.filter_report_metric_name('run_time_max') == 'Maximum Runtime'
        assert pdr.filter_report_metric_name('with_failures') == 'With Failures'
        assert pdr.filter_report_metric_name('with_changes') == 'With Changes'
        assert pdr.filter_report_metric_name('run_count') == 'Total Reports'
        assert pdr.filter_report_metric_name('run_time_avg') == 'Average Runtime'
        assert pdr.filter_report_metric_name('with_no_report') == 'With No Report'
        assert pdr.filter_report_metric_name('with_no_successful_runs') == 'With 100% Failed Runs'
        assert pdr.filter_report_metric_name('with_50+%_failed') == 'With 50-100% Failed Runs'
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.RUNS_PER_DAY', 9):
            assert pdr.filter_report_metric_name('with_too_few_runs') == 'With <9 Runs in 24h'


class Test_filter_resource_dict_sort:

    def test_dict_sort(self):
        test_dict = {
            ('aaa', 'aaa'): 1,
            ('aaa', 'aab'): 1,
            ('aab', 'aaa'): 1,
            ('aaa', 'aac'): 1,
            ('aaa', 'aa'): 3,
            ('zzz', 'aaa'): 10,
        }
        expected = OrderedDict()
        expected[('zzz', 'aaa')] = 10
        expected[('aaa', 'aa')] = 3
        expected[('aaa', 'aaa')] = 1
        expected[('aaa', 'aab')] = 1
        expected[('aaa', 'aac')] = 1
        expected[('aab', 'aaa')] = 1
        result = pdr.filter_resource_dict_sort(test_dict)
        assert result == expected


class Test_filter_report_metric_format:

    def test_string(self):
        assert pdr.filter_report_metric_format('foo') == 'foo'

    def test_int(self):
        assert pdr.filter_report_metric_format(123) == '123'

    def test_timedelta(self):
        d = datetime.timedelta(seconds=10)
        assert pdr.filter_report_metric_format(d) == '10s'
        d = datetime.timedelta(0, 245, 555555)
        assert pdr.filter_report_metric_format(d) == '4m 5s'
        d = datetime.timedelta(3, 3661)
        assert pdr.filter_report_metric_format(d) == '3d 1h 1m 1s'
        d = datetime.timedelta(0, 3600)
        assert pdr.filter_report_metric_format(d) == '1h'
        d = datetime.timedelta(0, 1000)
        assert pdr.filter_report_metric_format(d) == '16m 40s'

    def test_other(self):
        assert pdr.filter_report_metric_format(123.1) == '123.1'


class Test_aggregate_data_for_timespan:

    def test_report_counts(self):
        data = deepcopy(test_data.FINAL_DATA['Tue 06/10'])
        data.pop('aggregate', None)
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.RUNS_PER_DAY', 4):
            result = pdr.aggregate_data_for_timespan(data)
        assert result['reports']['run_count'] == 19
        assert result['reports']['run_time_total'] == datetime.timedelta(seconds=2310)
        assert result['reports']['run_time_max'] == datetime.timedelta(seconds=1000)
        assert result['reports']['with_failures'] == 15
        assert result['reports']['with_changes'] == 6
        assert result['reports']['with_skips'] == 10
        assert result['reports']['run_time_avg'].days == 0
        assert result['reports']['run_time_avg'].seconds == 121

    def test_node_counts(self):
        data = deepcopy(test_data.FINAL_DATA['Tue 06/10'])
        data.pop('aggregate', None)
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.RUNS_PER_DAY', 4):
            result = pdr.aggregate_data_for_timespan(data)
        assert result['nodes']['with_no_report'] == 1
        assert result['nodes']['with_no_successful_runs'] == 4
        assert result['nodes']['with_50+%_failed'] == 1
        assert result['nodes']['with_too_few_runs'] == 4
        assert result['nodes']['with_changes'] == 4
        assert result['nodes']['with_skips'] == 3

    def test_resource_node_counts(self):
        data = deepcopy(test_data.FINAL_DATA['Tue 06/10'])
        data.pop('aggregate', None)

        expected = {
            'changed': {
                (u'Exec', u'zookeeper ensemble check'): 1,
                (u'Service', u'winbind'): 2,
                (u'Service', u'zookeeper-server'): 2,
            },
            'failed': {
                (u'Exec', u'zookeeper ensemble check'): 1,
                (u'Package', u'libsmbios'): 2,
                (u'Package', u'srvadmin-idrac7'): 2,
            },
            'skipped': {
                (u'Augeas', u'disable dell yum plugin once OM is installed'): 2,
                (u'Exec', u'zookeeper ensemble check'): 1,
                (u'Service', u'dataeng'): 1,
            },
        }

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.RUNS_PER_DAY', 4):
            result = pdr.aggregate_data_for_timespan(data)

        result['nodes']['resources'].pop('flapping', None)  # test_node_flapping_resources()
        assert result['nodes']['resources'] == expected

    def test_missing_keys(self):
        """ to get coverage on some missed branches """
        data = deepcopy(test_data.FINAL_DATA['Tue 06/10'])
        data.pop('aggregate', None)

        # remove some keys
        for n in data['nodes']:
            data['nodes'][n]['reports'].pop('with_skips', None)
            data['nodes'][n]['reports'].pop('run_time_total', None)

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.RUNS_PER_DAY', 4):
            result = pdr.aggregate_data_for_timespan(data)
        # really just make sure it doesn't error out, and gives us a dict with some keys back
        assert isinstance(result, dict)
        assert len(result) > 1

    def test_resource_report_counts(self):
        data = deepcopy(test_data.FINAL_DATA['Tue 06/10'])
        data.pop('aggregate', None)

        expected = {
            'changed': {
                (u'Exec', u'zookeeper ensemble check'): 1,
                (u'Service', u'winbind'): 2,
                (u'Service', u'zookeeper-server'): 4,
            },
            'failed': {
                (u'Exec', u'zookeeper ensemble check'): 1,
                (u'Package', u'libsmbios'): 2,
                (u'Package', u'srvadmin-idrac7'): 4,
            },
            'skipped': {
                (u'Augeas', u'disable dell yum plugin once OM is installed'): 11,
                (u'Exec', u'zookeeper ensemble check'): 1,
                (u'Service', u'dataeng'): 1,
            },
        }

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.RUNS_PER_DAY', 4):
            result = pdr.aggregate_data_for_timespan(data)

        assert result['reports']['resources'] == expected

    def test_report_counts_divzero(self):
        data = {
            'nodes': {
                'node1.example.com': {
                    'reports': {
                        'run_count': 0,
                        'run_time_total': datetime.timedelta(),
                        'run_time_max': datetime.timedelta(),
                        'with_failures': 0,
                        'with_changes': 0,
                        'with_skips': 0,
                    },
                },
            },
        }
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.RUNS_PER_DAY', 4):
            result = pdr.aggregate_data_for_timespan(data)
        assert result['reports']['run_count'] == 0
        assert result['reports']['run_time_total'] == datetime.timedelta()
        assert result['reports']['run_time_max'] == datetime.timedelta()
        assert result['reports']['with_failures'] == 0
        assert result['reports']['with_changes'] == 0
        assert result['reports']['with_skips'] == 0
        assert result['reports']['run_time_avg'] == datetime.timedelta()

    def test_report_counts_empty_node(self):
        data = {
            'nodes': {
                'node1.example.com': {
                    'reports': {},
                },
                'node2.example.com': {},
            },
        }
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.RUNS_PER_DAY', 4):
            result = pdr.aggregate_data_for_timespan(data)
        assert result['reports']['run_count'] == 0
        assert result['reports']['run_time_total'] == datetime.timedelta()
        assert result['reports']['run_time_max'] == datetime.timedelta()
        assert result['reports']['with_failures'] == 0
        assert result['reports']['with_changes'] == 0
        assert result['reports']['with_skips'] == 0
        assert result['reports']['run_time_avg'] == datetime.timedelta()

    def test_node_counts_divzero(self):
        data = {
            'nodes': {
                'node1.example.com': {
                    'reports': {
                        'run_count': 0,
                        'run_time_total': datetime.timedelta(),
                        'run_time_max': datetime.timedelta(),
                        'with_failures': 0,
                        'with_changes': 0,
                        'with_skips': 0,
                    },
                },
            },
        }
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.RUNS_PER_DAY', 4):
            result = pdr.aggregate_data_for_timespan(data)
        assert result['nodes']['with_no_report'] == 1
        assert result['nodes']['with_no_successful_runs'] == 1
        assert result['nodes']['with_50+%_failed'] == 0
        assert result['nodes']['with_changes'] == 0
        assert result['nodes']['with_skips'] == 0
        assert result['nodes']['with_too_few_runs'] == 1

    def test_node_counts_empty_node(self):
        data = {
            'nodes': {
                'node1.example.com': {
                    'reports': {},
                },
                'node2.example.com': {},
            },
        }
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.RUNS_PER_DAY', 4):
            result = pdr.aggregate_data_for_timespan(data)
        assert result['nodes']['with_no_report'] == 2
        assert result['nodes']['with_no_successful_runs'] == 2
        assert result['nodes']['with_50+%_failed'] == 0
        assert result['nodes']['with_changes'] == 0
        assert result['nodes']['with_skips'] == 0
        assert result['nodes']['with_too_few_runs'] == 0

    def test_node_flapping_resources(self):
        """
        any resources changed in >= 45% of reports for a node
        this should be resource -> number of nodes
        """
        data = deepcopy(test_data.FLAPPING_DATA)
        data.pop('aggregate', None)

        expected = {
            (u'Augeas', u'disable dell yum plugin once OM is installed'): 1,
            (u'Exec', u'zookeeper ensemble check'): 6,
            (u'Package', u'libsmbios'): 3,
            (u'Service', u'dataeng'): 3,
            (u'Service', u'winbind'): 2,
            (u'Service', u'zookeeper-server'): 3,
        }

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.RUNS_PER_DAY', 4):
            result = pdr.aggregate_data_for_timespan(data)

        assert result['nodes']['resources']['flapping'] == expected

    def test_test_data(self):
        """
        Make sure test_data.FINAL_DATA is accurate
        """
        data = deepcopy(test_data.FINAL_DATA['Tue 06/10'])
        expected = data.pop('aggregate', None)
        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.RUNS_PER_DAY', 4):
            result = pdr.aggregate_data_for_timespan(data)
        assert result == expected


class Test_format_html:

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
        node_mock = mock.MagicMock(return_value='nodename')
        getuser_mock = mock.MagicMock(return_value='username')
        localzone_mock = mock.MagicMock()
        localzone_mock.return_value = pytz.timezone('US/Eastern')

        expected_run_info = {
            'version': VERSION,
            'user': 'username',
            'host': 'nodename',
            'date_s': '2014-06-11 04:15:43-0400 EDT',
        }

        with freeze_time("2014-06-11 08:15:43"), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.Environment', env_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.PackageLoader', pl_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.platform_node', node_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.getuser', getuser_mock), \
                mock.patch('tzlocal.get_localzone', localzone_mock):

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
        assert env_obj_mock.filters == {
            'reportmetricname': pdr.filter_report_metric_name,
            'reportmetricformat': pdr.filter_report_metric_format,
            'resourcedictsort': pdr.filter_resource_dict_sort,
        }
        assert tmpl_mock.render.call_count == 1
        assert node_mock.call_count == 1
        assert getuser_mock.call_count == 1
        expected_config = {
            'start': datetime.datetime(2014, 6, 3, hour=0, minute=0, second=0, tzinfo=pytz.utc),
            'end': datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59, tzinfo=pytz.utc),
            'num_rows': 10,

        }
        assert tmpl_mock.render.call_args == mock.call(data=self.data,
                                                       dates=self.dates,
                                                       hostname='foo.example.com',
                                                       config=expected_config,
                                                       run_info=expected_run_info,
                                                       )
        assert html == 'baz'
