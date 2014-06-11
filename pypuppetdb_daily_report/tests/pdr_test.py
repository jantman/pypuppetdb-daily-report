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


class Test_parse_args:
    """
    Tests the CLI option/argument handling
    """

    def test_defaults(self):
        """
        Test the parse_args option parsing method with default / no arguments
        """
        argv = ['pypuppetdb_daily_report']
        x = pdr.parse_args(argv)
        assert x.dry_run == False
        assert x.verbose == 0

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
        foo = pdr.get_dashboard_metrics(pdb_mock)
        assert pdb_mock.metric.call_count == 17
        assert isinstance(foo, dict)


class Test_get_data_for_timespan:

    def test_get(self):
        """ defaults """
        assert 1 == "not implemented yet"


class Test_data_for_timespan:

    def test_today(self):
        """ data for today """
        assert 1 == "not implemented yet"


class Test_main:
    """ tests for main() function """

    def test_default(self):
        """ as default as possible, one test """
        pdb_mock = mock.MagicMock()
        get_metrics_mock = mock.MagicMock()
        dt_now_mock = mock.MagicMock()
        dt_now_mock.return_value = datetime.datetime(2014, 06, 11, 08, 15, 43, 1)

        with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.connect', pdb_mock):
            with mock.patch('pypuppetdb_daily_report.pypuppetdb_daily_report.get_dashboard_metrics', get_metrics_mock):
                with mock.patch('datetime.datetime.now', dt_now_mock):
                    foo = pdr.main('foobar')
        assert pdb_mock.call_count == 1
        assert pdb_mock.call_args == mock.call(host='foobar')
        assert get_metrics_mock.call_count == 1
        assert foo == True
        assert dt_now_mock.call_count == 1
