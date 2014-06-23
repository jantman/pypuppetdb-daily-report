#!/usr/bin/env python
"""
pypuppetdb-daily-report.py
Script to print or email a daily Puppet run summary report using data from
a PuppetDB instance, accessed via nedap's pypuppetdb.

See README.rst for further information.

Requirements:
- pypuppetdb

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

import sys
import optparse
import logging
from . import VERSION
from pypuppetdb import connect
import requests
import datetime
import os
from math import floor, ceil
from jinja2 import Environment, PackageLoader
import pytz
import tzlocal
from ago import delta2dict
from collections import defaultdict, OrderedDict
from platform import node as platform_node
from getpass import getuser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

import pickle

FORMAT = "[%(levelname)s %(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.ERROR, format=FORMAT)
logger = logging.getLogger(__name__)

# these will probably be made configurable in the future
NUM_RESULT_ROWS = 10
RUNS_PER_DAY = 40
FACTS = ['puppetversion', 'facterversion', 'lsbdistdescription']


def main(hostname, to=None, num_days=7, cache_dir=None, dry_run=False):
    """
    main entry point

    :param hostname: PuppetDB hostname
    :type hostname: string
    :param to: list of addresses to send mail to
    :type to: list
    :param num_days: the number of days to report on, default 7
    :type num_days: int
    :param cache_dir: absolute path to where to cache data from PuppetDB
    :type cache_dir: string
    :param dry_run: whether to actually send, or just print what would be sent
    :type dry_run: boolean
    """
    pdb = connect(host=hostname)

    # essentially figure out all these for yesterday, build the tables, serialize the result as JSON somewhere. then just keep the last ~7 days json files
    date_data = {}
    dates = []  # ordered
    date_list = get_date_list(num_days)
    localtz = tzlocal.get_localzone()
    start_date = date_list[0]
    end_date = date_list[-1] - datetime.timedelta(hours=23, minutes=59, seconds=59)
    for query_date in date_list:
        end = query_date
        start = query_date - datetime.timedelta(days=1) + datetime.timedelta(seconds=1)
        date_s = (query_date - datetime.timedelta(hours=1)).astimezone(localtz).strftime('%a %m/%d')
        date_data[date_s] = get_data_for_timespan(hostname, pdb, start, end, cache_dir=cache_dir)
        dates.append(date_s)
    html = format_html(hostname, dates, date_data, start_date, end_date)
    subject = 'daily puppet(db) run summary for {host}'.format(host=hostname)
    send_mail(to, subject, html, dry_run=dry_run)
    return True


def get_date_list(num_days):
    """
    For an integer number of days (num_days), get an ordered list of
    DateTime objects to report on.
    """
    local_tz = tzlocal.get_localzone()
    local_start_date = local_tz.localize(datetime.datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(seconds=1)
    logger.debug("local_start_date={d}".format(d=local_start_date.strftime("%Y-%m-%d %H:%M:%S%z %Z")))
    start_date = local_start_date.astimezone(pytz.utc)
    logger.debug("start_date={d}".format(d=start_date.strftime("%Y-%m-%d %H:%M:%S%z %Z")))
    end_date = (start_date - datetime.timedelta(days=num_days)) + datetime.timedelta(seconds=1)
    logger.debug("end_date={d}".format(d=end_date.strftime("%Y-%m-%d %H:%M:%S%z %Z")))
    dates = [start_date - datetime.timedelta(n) for n in range(num_days)]
    return dates


def format_html(hostname, dates, date_data, start_date, end_date):
    """
    format the HTML report using the raw per-date dicts

    :param hostname: PuppetDB hostname
    :type hostname: string
    :param dates: ordered list of dates to display, left-to-right
    :type dates: list
    :param date_data: dict of each date to its data
    :type date_data: dict
    :param start_date: beginning of time period that data is for
    :type start_date: Datetime
    :param end_date: end of time period that data is for
    :type end_date: Datetime
    """
    env = Environment(loader=PackageLoader('pypuppetdb_daily_report', 'templates'), extensions=['jinja2.ext.loopcontrols'])
    env.filters['reportmetricname'] = filter_report_metric_name
    env.filters['reportmetricformat'] = filter_report_metric_format
    env.filters['resourcedictsort'] = filter_resource_dict_sort
    template = env.get_template('base.html')

    run_info = {
        'version': VERSION,
        'date_s': datetime.datetime.now(pytz.utc).astimezone(tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S%z %Z'),
        'host': platform_node(),
        'user': getuser(),
    }

    config = {
        'start': start_date,
        'end': end_date,
        'num_rows': NUM_RESULT_ROWS,
    }

    html = template.render(data=date_data,
                           dates=dates,
                           hostname=hostname,
                           config=config,
                           run_info=run_info,
                           )
    return html


def filter_resource_dict_sort(d):
    """
    Used to sort a dictionary of resources, tuple-of-strings key and int value,
    sorted reverse by value and alphabetically by key within each value set.
    """
    items = list(d.items())
    keyfunc = lambda x: tuple([-x[1]] + list(x[0]))
    return OrderedDict(sorted(items, key=keyfunc))


def filter_report_metric_name(s):
    """
    jinja2 filter to return the metric name for a given metric key
    """
    metric_names = {'with_skips': 'With Skipped Resources',
                    'run_time_max': 'Maximum Runtime',
                    'with_failures': 'With Failures',
                    'with_changes': 'With Changes',
                    'run_count': 'Total Reports',
                    'run_time_total': 'Total Runtime',
                    'run_time_avg': 'Average Runtime',
                    'with_no_report': 'With No Report',
                    'with_no_successful_runs': 'With 100% Failed Runs',
                    'with_50+%_failed': 'With 50-100% Failed Runs',
                    'with_too_few_runs': 'With <{n} Runs in 24h'.format(n=RUNS_PER_DAY),
                    }
    return metric_names.get(s, s)


def filter_report_metric_format(o):
    """
    jinja2 filter to return a formatted metric string for the given metric value
    """
    if isinstance(o, str):
        return o
    if isinstance(o, int):
        return '{o}'.format(o=o)
    if isinstance(o, datetime.timedelta):
        d = delta2dict(o)
        s = ''
        for i in ['day', 'hour', 'minute', 'second']:
            if d[i] > 0:
                s += '{i}{suffix} '.format(i=d[i], suffix=i[0])
        s = s.strip()
        return s
    return str(o)


def get_data_for_timespan(hostname, pdb, start, end, cache_dir=None):
    """
    Get the data for a specified timespan, from cache (if possible) or else
    from PuppetDB directly.

    :param hostname: name of the puppetdb host we're connected to
    :type hostname: string
    :param pdb: object representing a connected pypuppetdb instance
    :type pdb: one of the pypuppetdb.API classes
    :param start: beginning of time period to get data for
    :type start: Datetime
    :param end: end of time period to get data for
    :type end: Datetime
    :param cache_dir: absolute path to where to cache data from PuppetDB
    :type cache_dir: string
    """
    logger.debug("getting data for timespan: {start} to {end} (cache_dir={cache_dir})".format(cache_dir=cache_dir,
                                                                                              start=start.strftime('%Y-%m-%d_%H-%M-%S'),
                                                                                              end=end.strftime('%Y-%m-%d_%H-%M-%S'),
                                                                                              ))
    if cache_dir is not None:
        cache_filename = "data_{host}_{start}_{end}.pickle".format(host=hostname,
                                                                   start=start.strftime('%Y-%m-%d_%H-%M-%S'),
                                                                   end=end.strftime('%Y-%m-%d_%H-%M-%S'))
        cache_fpath = os.path.join(cache_dir, cache_filename)
        logger.debug("cache file: {fpath}".format(fpath=cache_fpath))
        if not os.path.exists(cache_dir):
            logger.info("creating dir: {cache_dir}".format(cache_dir=cache_dir))
            os.makedirs(cache_dir)
        if os.path.exists(cache_fpath):
            with open(cache_fpath, 'r') as fh:
                logger.debug("reading cache file")
                raw = fh.read()
            data = pickle.loads(raw)
            logger.info("returning cached data for timespan: {start} to {end}".format(start=start.strftime('%Y-%m-%d_%H-%M-%S'),
                                                                                      end=end.strftime('%Y-%m-%d_%H-%M-%S'),
                                                                                      ))
            return data
    data = query_data_for_timespan(pdb, start, end)
    if cache_dir is None:
        return data
    with open(cache_fpath, 'w') as fh:
        logger.debug("writing data to cache")
        fh.write(pickle.dumps(data))
    return data


def query_data_for_timespan(pdb, start, end):
    """
    Retrieve all desired data for one day, from PuppetDB

    :param pdb: object representing a connected pypuppetdb instance
    :type pdb: one of the pypuppetdb.API classes
    :param start: beginning of time period to get data for
    :type start: Datetime
    :param end: end of time period to get data for
    :type end: Datetime
    """
    logger.info("querying data for timespan: {start} to {end}".format(start=start.strftime('%Y-%m-%d_%H-%M-%S'),
                                                                      end=end.strftime('%Y-%m-%d_%H-%M-%S'),
                                                                      ))
    res = {}

    # if we're getting for yesterday, also snapshot dashboard metrics
    if end >= pytz.utc.localize(datetime.datetime.now()) - datetime.timedelta(days=1):
        logger.debug("requested yesterday, getting dashboard metrics")
        res['metrics'] = get_dashboard_metrics(pdb)
        res['facts'] = get_facts(pdb)

    logger.debug("querying nodes")
    nodes = pdb.nodes()
    res['nodes'] = {}
    for node in nodes:
        logger.debug("working node {node}".format(node=node.name))
        node_data = query_data_for_node(pdb, node, start, end)
        res['nodes'][node.name] = node_data

    logger.debug("got {num} nodes".format(num=len(res['nodes'])))

    logger.debug("aggregating data")
    res['aggregate'] = aggregate_data_for_timespan(res)

    return res


def aggregate_data_for_timespan(data):
    """
    Calculate aggregate values for all data in a given timespan

    :param data: dict of result data from query_data_for_timespan()
    :type data: dict
    """
    res = {}
    res['reports'] = {'run_count': 0,
                      'run_time_total': datetime.timedelta(),
                      'run_time_max': datetime.timedelta(),
                      'run_time_avg': datetime.timedelta(),
                      'with_failures': 0,
                      'with_changes': 0,
                      'with_skips': 0,
                      'resources': {'failed': defaultdict(int), 'changed': defaultdict(int), 'skipped': defaultdict(int)},
                      }
    res['nodes'] = {'with_failures': 0,
                    'with_changes': 0,
                    'with_skips': 0,
                    'with_no_report': 0,
                    'with_no_successful_runs': 0,
                    'with_50+%_failed': 0,
                    'with_too_few_runs': 0,
                    'resources': {'failed': defaultdict(int), 'changed': defaultdict(int), 'skipped': defaultdict(int), 'flapping': defaultdict(int)},
                    }

    for node in data['nodes']:
        if 'reports' not in data['nodes'][node]:
            res['nodes']['with_no_report'] += 1
            res['nodes']['with_no_successful_runs'] += 1
            continue
        if 'run_count' not in data['nodes'][node]['reports']:
            res['nodes']['with_no_report'] += 1
            res['nodes']['with_no_successful_runs'] += 1
            continue

        failpct = 0
        if data['nodes'][node]['reports']['run_count'] > 0:
            failpct = float(data['nodes'][node]['reports']['with_failures']) / float(data['nodes'][node]['reports']['run_count'])

        if data['nodes'][node]['reports']['run_count'] < RUNS_PER_DAY:
            res['nodes']['with_too_few_runs'] += 1

        if data['nodes'][node]['reports']['run_count'] == 0:
            res['nodes']['with_no_report'] += 1
            res['nodes']['with_no_successful_runs'] += 1
        elif data['nodes'][node]['reports']['with_failures'] == data['nodes'][node]['reports']['run_count']:
            res['nodes']['with_no_successful_runs'] += 1
        elif failpct >= 0.5 and failpct < 1.0:
            res['nodes']['with_50+%_failed'] += 1

        for key in ['run_count', 'with_failures', 'with_changes', 'with_skips']:
            if key in data['nodes'][node]['reports']:
                res['reports'][key] += data['nodes'][node]['reports'][key]
            if key in data['nodes'][node]['reports'] and key in res['nodes'] and data['nodes'][node]['reports'][key] > 0:
                res['nodes'][key] += 1

        if 'run_time_total' in data['nodes'][node]['reports']:
            res['reports']['run_time_total'] = res['reports']['run_time_total'] + data['nodes'][node]['reports']['run_time_total']
        if 'run_time_max' in data['nodes'][node]['reports'] and data['nodes'][node]['reports']['run_time_max'] > res['reports']['run_time_max']:
            res['reports']['run_time_max'] = data['nodes'][node]['reports']['run_time_max']

        # resource counts across all nodes
        if 'resources' in data['nodes'][node]:
            for key in ['failed', 'changed', 'skipped']:
                if key in data['nodes'][node]['resources']:
                    for tup in data['nodes'][node]['resources'][key]:
                        res['nodes']['resources'][key][tup] += 1
                        res['reports']['resources'][key][tup] += data['nodes'][node]['resources'][key][tup]
                        # flapping resources, count of nodes
                        if key == 'changed' and (float(data['nodes'][node]['resources'][key][tup]) >= (data['nodes'][node]['reports']['run_count'] * 0.45)):
                            res['nodes']['resources']['flapping'][tup] += 1

    # flatten defaultdicts for serialization
    for key in res['nodes']['resources']:
        res['nodes']['resources'][key] = dict(res['nodes']['resources'][key])
    for key in res['reports']['resources']:
        res['reports']['resources'][key] = dict(res['reports']['resources'][key])

    if res['reports']['run_count'] != 0:
        res['reports']['run_time_avg'] = res['reports']['run_time_total'] / res['reports']['run_count']
    logger.debug("aggregation done, returning result")
    return res


def get_facts(pdb):
    """
    return a dict of the values of the facts in FACTS and the counts of each value

    :param pdb: object representing a connected pypuppetdb instance
    :type pdb: one of the pypuppetdb.API classes
    """
    logger.debug("querying facts")
    res = {}
    for fact in FACTS:
        res[fact] = {}
        fact_vals = pdb.facts(fact)
        for val in fact_vals:
            if val.value not in res[fact]:
                res[fact][val.value] = 0
            res[fact][val.value] += 1
    logger.debug("done with facts")
    return res


def query_data_for_node(pdb, node, start, end):
    """
    Retrieve all desired data for a given node in a given time period

    :param pdb: object representing a connected pypuppetdb instance
    :type pdb: one of the pypuppetdb.API classes
    :param node: the node to query for
    :type node: pypuppetdb.types.Node
    :param start: beginning of time period to get data for
    :type start: Datetime
    :param end: end of time period to get data for
    :type end: Datetime
    """
    logger.debug("querying node {name} for timespan: {start} to {end}".format(start=start.strftime('%Y-%m-%d %H-%M-%S%z'),
                                                                              end=end.strftime('%Y-%m-%d %H-%M-%S%z'),
                                                                              name=node.name,
                                                                              ))
    res = {}

    res['reports'] = {'run_count': 0,
                      'with_failures': 0,
                      'with_changes': 0,
                      'with_skips': 0,
                      'run_time_total': datetime.timedelta(),
                      'run_time_max': datetime.timedelta()
                      }
    res['resources'] = {'failed': defaultdict(int),
                        'changed': defaultdict(int),
                        'skipped': defaultdict(int),
                        }
    for rep in node.reports():
        if rep.start > end:
            continue
        if rep.start < start:
            # reports are returned sorted desc by completion time of run
            logger.debug("found first report before time period - start time is {s}".format(s=rep.start))
            break
        res['reports']['run_count'] += 1
        res['reports']['run_time_total'] = res['reports']['run_time_total'] + rep.run_time
        if rep.run_time > res['reports']['run_time_max']:
            res['reports']['run_time_max'] = rep.run_time
        query_s = '["=", "report", "{hash_}"]'.format(hash_=rep.hash_)
        events = pdb.events(query_s)
        # increment per-report counters
        skips = 0
        successes = 0
        failures = 0
        for e in events:
            if e.status == 'skipped':
                skips += 1
                res['resources']['skipped'][(e.item['type'], e.item['title'])] += 1
            elif e.status == 'success':
                successes += 1
                res['resources']['changed'][(e.item['type'], e.item['title'])] += 1
            elif e.status == 'failure':
                failures += 1
                res['resources']['failed'][(e.item['type'], e.item['title'])] += 1
        # increment per-node counters for this report
        if skips > 0:
            res['reports']['with_skips'] += 1
        if successes > 0:
            res['reports']['with_changes'] += 1
        if failures > 0:
            res['reports']['with_failures'] += 1

    # flatten defaultdicts for serialization
    for key in res['resources']:
        res['resources'][key] = dict(res['resources'][key])

    logger.debug("got {num} reports for node".format(num=res['reports']['run_count']))

    return res


def get_dashboard_metrics(pdb):
    """
    return a dict of the metrics displayed on the PuppetDB dashboard

    :param pdb: object representing a connected pypuppetdb instance
    :type pdb: one of the pypuppetdb.API classes
    """
    logger.debug("getting dashboard metrics...")
    metrics = {}
    metrics['Nodes'] = {'path': 'com.puppetlabs.puppetdb.query.population:type=default,name=num-nodes', 'order': 2, 'formatted': None}
    metrics['Resources'] = {'path': 'com.puppetlabs.puppetdb.query.population:type=default,name=num-resources', 'order': 3, 'formatted': None}
    metrics['Resource Duplication'] = {'path': 'com.puppetlabs.puppetdb.query.population:type=default,name=pct-resource-dupes', 'order': 4, 'formatted': None}
    metrics['Catalog duplication'] = {'path': 'com.puppetlabs.puppetdb.scf.storage:type=default,name=duplicate-pct', 'order': 5, 'formatted': None}
    metrics['Command Queue'] = {'path': 'org.apache.activemq:BrokerName=localhost,Type=Queue,Destination=com.puppetlabs.puppetdb.commands', 'order': 6, 'formatted': None}
    metrics['Command Processing Time'] = {'path': 'com.puppetlabs.puppetdb.command:type=global,name=processing-time', 'order': 7, 'formatted': None}
    metrics['Command Processing'] = {'path': 'com.puppetlabs.puppetdb.command:type=global,name=processed', 'order': 8, 'formatted': None}
    metrics['Processed'] = {'path': 'com.puppetlabs.puppetdb.command:type=global,name=processed', 'order': 9, 'formatted': None}
    metrics['Retired'] = {'path': 'com.puppetlabs.puppetdb.command:type=global,name=retried', 'order': 10, 'formatted': None}
    metrics['Discarded'] = {'path': 'com.puppetlabs.puppetdb.command:type=global,name=discarded', 'order': 11, 'formatted': None}
    metrics['Rejected'] = {'path': 'com.puppetlabs.puppetdb.command:type=global,name=fatal', 'order': 12, 'formatted': None}
    metrics['Enqueueing'] = {'path': 'com.puppetlabs.puppetdb.http.server:type=/v2/commands,name=service-time', 'order': 13, 'formatted': None}
    metrics['Collection Queries'] = {'path': 'com.puppetlabs.puppetdb.http.server:type=/v2/resources,name=service-time', 'order': 14, 'formatted': None}
    metrics['DB Compaction'] = {'path': 'com.puppetlabs.puppetdb.scf.storage:type=default,name=gc-time', 'order': 15, 'formatted': None}
    metrics['DLO Compression'] = {'path': 'com.puppetlabs.puppetdb.command.dlo:type=global,name=compression', 'order': 16, 'formatted': None}
    metrics['DLO Size on Disk'] = {'path': 'com.puppetlabs.puppetdb.command.dlo:type=global,name=filesize', 'order': 17, 'formatted': None}
    metrics['Discarded Messages'] = {'path': 'com.puppetlabs.puppetdb.command.dlo:type=global,name=messages', 'order': 18, 'formatted': None}

    for metric in metrics:
        logger.debug("getting metric: %s" % metric)
        try:
            metrics[metric]['api_response'] = pdb.metric(metrics[metric]['path'])
            metrics[metric]['formatted'] = metric_value(metrics[metric]['api_response'])
            logger.debug("got raw value: %s" % metrics[metric]['formatted'])
        except requests.exceptions.HTTPError:
            logger.debug("unable to get value for metric: %s" % metric)
    logger.info("got dashboard metrics")

    return metrics


def metric_value(m):
    """
    Takes a dict returned by the metric() API endpoint, returns the formatted value we want to track.
    """
    if 'Value' in m:
        if m['Value'] == 0.0:
            return "0"
        if ceil(m['Value']) == floor(m['Value']):
            return int(m['Value'])
        return "{:,f}".format(m['Value'])
    if 'MeanRate' in m and 'Count' in m:
        return "{:,f}/s ({:d})".format(m['MeanRate'], m['Count'])
    if 'MeanRate' in m:
        return "{:,f}/s".format(m['MeanRate'])
    if 'AverageEnqueueTime' in m:
        return "{:,f}/s".format(m['AverageEnqueueTime'])
    """
    # metrics requiring special handling/formatting:
    jvmheap = pdb.metric('java.lang:type=Memory')
    logger.debug("got jvmheap metric raw value: %s" % jvmheap)
    jvmheap_s = "{:.2%} ({:d}/{:d})".format((jvmheap['HeapMemoryUsage']['used'] / jvmheap['HeapMemoryUsage']['max']),
                                            jvmheap['HeapMemoryUsage']['used'], jvmheap['HeapMemoryUsage']['max'])
    jvmnonheap_s = "{:.2%} ({:d}/{:d})".format((jvmheap['NonHeapMemoryUsage']['used'] / jvmheap['NonHeapMemoryUsage']['max']),
                                            jvmheap['NonHeapMemoryUsage']['used'], jvmheap['NonHeapMemoryUsage']['max'])
    metrics['JVM Heap Memory Usage'] = {'path': 'java.lang:type=Memory', 'order': 1, 'value': jvmheap_s}
    metrics['JVM Non-Heap Memory Usage'] = {'path': 'java.lang:type=Memory', 'order': 1, 'value': jvmnonheap_s}
    """
    return m


def send_mail(to, subject, html, dry_run=False):
    """
    Send the message

    :param html: HTML to make up the body of the message
    :type html: string
    :param dry_run: whether to actually send, or just print what would be sent
    :type dry_run: boolean
    """
    if dry_run:
        with open('output.html', 'w') as fh:
            fh.write(html)
        logger.warning("DRY RUN - not sending mail; wrote body to ./output.html")
        return True
    logger.debug("sending mail")
    msg = MIMEMultipart('alternative')
    msg['subject'] = subject
    msg['To'] = ','.join(to)
    msg['From'] = '{user}@{host}'.format(user=getuser(), host=platform_node())
    body = MIMEText(html, 'html')
    msg.attach(body)
    # send
    s = smtplib.SMTP()
    s.sendmail(msg['From'], to, msg.as_string())
    return True


def parse_args(argv):
    """ parse arguments/options """
    p = optparse.OptionParser()

    p.add_option('-p', '--puppetdb', dest='host', action='store', type='string',
                 help='PuppetDB hostname')

    p.add_option('-n', '--num-days', dest='num_days', action='store', type='int', default=7,
                 help='Number of days to report on; default 7')

    p.add_option('-d', '--dry-run', dest='dry_run', action='store_true', default=False,
                 help='dry-run - dont actually send anything')

    p.add_option('-v', '--verbose', dest='verbose', action='count', default=0,
                 help='verbose output. specify twice for debug-level output.')

    cache_dir = os.path.expanduser('~/.pypuppetdb_daily_report')
    p.add_option('-c', '--cache-dir', dest='cache_dir', action='store', type='string', default=cache_dir,
                 help='data cache directory (default: {cache_dir})'.format(cache_dir=cache_dir))

    p.add_option('-t', '--to', dest='to_str', action='store', type='string',
                 help='csv list of addresses to send mail to')

    options, args = p.parse_args(argv)

    if options.to_str and ',' in options.to_str:
        options.to = options.to_str.split(',')
    else:
        options.to = [options.to_str]

    return options


def console_entry_point():
    """setuptools entry point"""
    opts = parse_args(sys.argv[1:])

    if opts.verbose > 1:
        logger.setLevel(logging.DEBUG)
    elif opts.verbose > 0:
        logger.setLevel(logging.INFO)

    if not opts.to and not opts.dry_run:
        raise SystemExit("ERROR: you must either run with --dry-run or specify to address(es) with --to")

    if not opts.host:
        raise SystemExit("ERROR: you must specify the PuppetDB hostname with -p|--puppetdb")
    main(opts.host, to=opts.to, num_days=opts.num_days, dry_run=opts.dry_run, cache_dir=opts.cache_dir)


if __name__ == "__main__":
    console_entry_point()
