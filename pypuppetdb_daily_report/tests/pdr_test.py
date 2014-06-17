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
import pytz
import pprint
from copy import deepcopy

from pypuppetdb_daily_report import pypuppetdb_daily_report as pdr

# fixtures
import test_data


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


class Test_console_entry_point:
    """ test console_entry_point """

    def test_defaults(self):
        """ with default values """
        parse_args_mock = mock.MagicMock()
        opts_o = OptionsObject()
        opts_o.host = 'foobar'
        parse_args_mock.return_value = opts_o

        main_mock = mock.MagicMock()

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.parse_args', parse_args_mock), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.main', main_mock):
            pdr.console_entry_point()
        assert parse_args_mock.call_count == 1
        assert main_mock.call_count == 1

    def test_nohost(self):
        """ without a host specified """
        parse_args_mock = mock.MagicMock()
        opts_o = OptionsObject()
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
            result = pdr.get_data_for_timespan(None,
                                               datetime.datetime(2014, 6, 10, hour=0, minute=0, second=0),
                                               datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59),
                                               cache_dir='/tmp/cache')
        assert path_exists_mock.call_count == 2
        assert path_exists_mock.call_args_list == [mock.call('/tmp/cache'),
                                                   mock.call('/tmp/cache/data_2014-06-10_00-00-00_2014-06-10_23-59-59.pickle')
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
            result = pdr.get_data_for_timespan(None,
                                               datetime.datetime(2014, 6, 10, hour=0, minute=0, second=0),
                                               datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59),
                                               cache_dir='/tmp/cache')
        assert os_mock.path.exists.call_count == 2
        assert os_mock.path.exists.call_args_list == [mock.call('/tmp/cache'),
                                                      mock.call('/tmp/cache/data_2014-06-10_00-00-00_2014-06-10_23-59-59.pickle')
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
            result = pdr.get_data_for_timespan(None,
                                               datetime.datetime(2014, 6, 10, hour=0, minute=0, second=0),
                                               datetime.datetime(2014, 6, 10, hour=23, minute=59, second=59),
                                               cache_dir='/tmp/cache')
        assert os_mock.path.exists.call_count == 2
        assert os_mock.path.exists.call_args_list == [mock.call('/tmp/cache'),
                                                      mock.call('/tmp/cache/data_2014-06-10_00-00-00_2014-06-10_23-59-59.pickle')
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
            result = pdr.get_data_for_timespan(None,
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
            pdr.main('foobar')
        assert connect_mock.call_count == 1
        assert connect_mock.call_args == mock.call(host='foobar')

        assert dft_mock.call_count == 7
        dft_expected = [
            mock.call(pdb_mock, FakeDatetime(2014, 6, 10, hour=4, minute=0, second=0, tzinfo=pytz.utc), FakeDatetime(2014, 6, 11, hour=3, minute=59, second=59, tzinfo=pytz.utc), cache_dir=None),
            mock.call(pdb_mock, FakeDatetime(2014, 6, 9, hour=4, minute=0, second=0, tzinfo=pytz.utc), FakeDatetime(2014, 6, 10, hour=3, minute=59, second=59, tzinfo=pytz.utc), cache_dir=None),
            mock.call(pdb_mock, FakeDatetime(2014, 6, 8, hour=4, minute=0, second=0, tzinfo=pytz.utc), FakeDatetime(2014, 6, 9, hour=3, minute=59, second=59, tzinfo=pytz.utc), cache_dir=None),
            mock.call(pdb_mock, FakeDatetime(2014, 6, 7, hour=4, minute=0, second=0, tzinfo=pytz.utc), FakeDatetime(2014, 6, 8, hour=3, minute=59, second=59, tzinfo=pytz.utc), cache_dir=None),
            mock.call(pdb_mock, FakeDatetime(2014, 6, 6, hour=4, minute=0, second=0, tzinfo=pytz.utc), FakeDatetime(2014, 6, 7, hour=3, minute=59, second=59, tzinfo=pytz.utc), cache_dir=None),
            mock.call(pdb_mock, FakeDatetime(2014, 6, 5, hour=4, minute=0, second=0, tzinfo=pytz.utc), FakeDatetime(2014, 6, 6, hour=3, minute=59, second=59, tzinfo=pytz.utc), cache_dir=None),
            mock.call(pdb_mock, FakeDatetime(2014, 6, 4, hour=4, minute=0, second=0, tzinfo=pytz.utc), FakeDatetime(2014, 6, 5, hour=3, minute=59, second=59, tzinfo=pytz.utc), cache_dir=None),
        ]
        assert dft_mock.mock_calls == dft_expected

        assert format_html_mock.call_count == 1
        r = mock.call('foobar',
                      dates,
                      data,
                      FakeDatetime(2014, 6, 11, 3, 59, 59, tzinfo=pytz.utc),
                      FakeDatetime(2014, 6, 4, 4, 0, 0, tzinfo=pytz.utc)
                      )
        pprint.pprint(r)
        pprint.pprint(format_html_mock.call_args)
        assert format_html_mock.call_args == r
        assert send_mail_mock.call_count == 1
        assert send_mail_mock.call_args == mock.call('foo bar baz', dry_run=False)


class Test_get_date_list:
    """ tests for main() function """

    def test_simple(self):
        """ as default as possible, one test """
        logger_mock = mock.MagicMock()
        localzone_mock = mock.MagicMock()
        localzone_mock.return_value = pytz.timezone('US/Eastern')

        with freeze_time("2014-06-11 08:15:43", tz_offset=-4), \
                mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.logger', logger_mock), \
                mock.patch('tzlocal.get_localzone', localzone_mock):
            dates = pdr.get_date_list(7)

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
        assert foo['reports']['run_count'] == 4
        assert foo['reports']['run_time_total'] == datetime.timedelta(seconds=1111)
        assert foo['reports']['run_time_max'] == datetime.timedelta(seconds=1000)
        assert pdb_mock.event_counts.call_args_list == [mock.call('["=", "report", "hash3"]', summarize_by='certname'),
                                                        mock.call('["=", "report", "hash4"]', summarize_by='certname'),
                                                        mock.call('["=", "report", "hash5"]', summarize_by='certname'),
                                                        mock.call('["=", "report", "hash6"]', summarize_by='certname')
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
        node_mock.reports.return_value = [r1, r2]
        pdb_mock.event_counts.return_value = [{u'noops': 4,
                                               u'skips': 3,
                                               u'successes': 1,
                                               u'subject-type': u'certname',
                                               u'failures': 2,
                                               u'subject': {u'title': u'node1.example.com'}}
                                              ]

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
        assert foo['reports']['run_count'] == 2
        assert foo['reports']['run_time_total'] == datetime.timedelta(seconds=1010)
        assert foo['reports']['run_time_max'] == datetime.timedelta(seconds=1000)
        assert pdb_mock.event_counts.call_count == 2
        assert pdb_mock.event_counts.call_args_list == [mock.call('["=", "report", "hash1"]', summarize_by='certname'),
                                                        mock.call('["=", "report", "hash2"]', summarize_by='certname'),
                                                        ]
        print(logger_mock.debug.call_args_list)
        assert foo['reports']['with_failures'] == 2
        assert foo['reports']['with_changes'] == 2
        assert foo['reports']['with_skips'] == 2


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


class Test_filter_report_metric_name:

    def test_aggregate(self):
        assert pdr.filter_report_metric_name('with_skips') == 'With Skipped Resources'
        assert pdr.filter_report_metric_name('run_time_max') == 'Maximum Runtime'
        assert pdr.filter_report_metric_name('with_failures') == 'With Failures'
        assert pdr.filter_report_metric_name('with_changes') == 'With Changes'
        assert pdr.filter_report_metric_name('run_count') == 'Total Reports'
        assert pdr.filter_report_metric_name('run_time_avg') == 'Average Runtime'
        assert pdr.filter_report_metric_name('nodes_with_no_report') == 'Nodes With No Report'


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


class Test_aggregate_data_for_timespan:

    def test_report_counts(self):
        data = deepcopy(test_data.FINAL_DATA['Tue 06/10'])
        data.pop('aggregate', None)
        result = pdr.aggregate_data_for_timespan(data)
        assert result['reports']['run_count'] == 9
        assert result['reports']['run_time_total'] == datetime.timedelta(seconds=2210)
        assert result['reports']['run_time_max'] == datetime.timedelta(seconds=1000)
        assert result['reports']['with_failures'] == 8
        assert result['reports']['with_changes'] == 4
        assert result['reports']['with_skips'] == 3
        assert result['reports']['run_time_avg'].days == 0
        assert result['reports']['run_time_avg'].seconds == 245
        assert result['reports']['nodes_with_no_report'] == 1

    def test_report_counts_divzero(self):
        data = {
            'metrics': {'foo': {'formatted': 'foo1'}, 'bar': {'formatted': 'bar1'}, 'baz': {'formatted': 'baz1'}},
            'facts': {'puppetversion': {'3.4.1': 2, '3.4.2': 1, '3.6.1': 100}, 'facterversion': {'2.0.0': 102, '1.7.2': 1}},
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
        result = pdr.aggregate_data_for_timespan(data)
        assert result['reports']['run_count'] == 0
        assert result['reports']['run_time_total'] == datetime.timedelta()
        assert result['reports']['run_time_max'] == datetime.timedelta()
        assert result['reports']['with_failures'] == 0
        assert result['reports']['with_changes'] == 0
        assert result['reports']['with_skips'] == 0
        assert result['reports']['run_time_avg'] == datetime.timedelta()
        assert result['reports']['nodes_with_no_report'] == 1
