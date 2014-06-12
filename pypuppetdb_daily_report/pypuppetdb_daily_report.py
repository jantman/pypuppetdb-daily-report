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
import anyjson
import os
from math import floor, ceil
from jinja2 import Environment, PackageLoader

FORMAT = "[%(levelname)s %(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.ERROR, format=FORMAT)
logger = logging.getLogger(__name__)

# these will probably be made configurable in the future
TOP_MODULES_COUNT = 10
TOP_RESOURCES_COUNT = 10


def main(hostname, num_days=7, cache_dir=None, dry_run=False):
    """
    main entry point

    :param hostname: PuppetDB hostname
    :type hostname: string
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
    start_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(seconds=1)
    end_date = start_date - datetime.timedelta(days=num_days)
    dates = []
    for query_date in (start_date - datetime.timedelta(n) for n in range(num_days)):
        end = query_date
        start = query_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_s = query_date.strftime('%a %m/%d')
        date_data[date_s] = get_data_for_timespan(pdb, start, end, cache_dir=cache_dir)
        dates.append(date_s)
    html = format_html(hostname, dates, date_data, start_date, end_date)
    send_mail(html, dry_run=dry_run)
    return True


def format_html(hostname, dates, date_data, start_date, end_date):
    """
    format the HTML report using the raw per-date dicts

    :param hostname: PuppetDB hostname
    :type hostname: string
    :param dates: ordered list of dates to display, left-to-right
    :type dates: list
    :param date_data: dict of each date to its data
    :type date_data: dict
    """
    env = Environment(loader=PackageLoader('pypuppetdb_daily_report', 'templates'))
    template = env.get_template('base.html')
    html = template.render(data=date_data,
                           dates=dates,
                           hostname=hostname,
                           start=start_date,
                           end=end_date
                           )
    return html


def get_data_for_timespan(pdb, start, end, cache_dir=None):
    """
    Get the data for a specified timespan, from cache (if possible) or else
    from PuppetDB directly.

    :param pdb: object representing a connected pypuppetdb instance
    :type pdb: one of the pypuppetdb.API classes
    :param cache_dir: absolute path to where to cache data from PuppetDB
    :type cache_dir: string
    """
    logger.debug("getting data for timespan: {start} to {end} (cache_dir={cache_dir})".format(cache_dir=cache_dir,
                                                                                              start=start.strftime('%Y-%m-%d_%H-%M-%S'),
                                                                                              end=end.strftime('%Y-%m-%d_%H-%M-%S'),
                                                                                              ))
    if cache_dir is not None:
        cache_filename = "data_{start}_{end}.json".format(start=start.strftime('%Y-%m-%d_%H-%M-%S'),
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
            data = anyjson.deserialize(raw)
            logger.info("returning cached data for timespan: {start} to {end}".format(start=start.strftime('%Y-%m-%d_%H-%M-%S'),
                                                                                      end=end.strftime('%Y-%m-%d_%H-%M-%S'),
                                                                                      ))
            return data
    data = query_data_for_timespan(pdb, start, end)
    if cache_dir is None:
        return data
    with open(cache_fpath, 'w') as fh:
        logger.debug("writing data to cache")
        fh.write(anyjson.serialize(data))
    return data


def query_data_for_timespan(pdb, start, end):
    """
    Retrieve all desired data for one day, from PuppetDB

    :param pdb: object representing a connected pypuppetdb instance
    :type pdb: one of the pypuppetdb.API classes
    """
    logger.info("querying data for timespan: {start} to {end}".format(start=start.strftime('%Y-%m-%d_%H-%M-%S'),
                                                                      end=end.strftime('%Y-%m-%d_%H-%M-%S'),
                                                                      ))
    res = {}
    logger.debug("querying nodes")
    nodes = pdb.nodes()
    res['nodes'] = [n.name for n in nodes]
    logger.debug("got {num} nodes".format(num=len(res['nodes'])))

    # if we're getting for yesterday, also snapshot dashboard metrics
    if end >= datetime.datetime.now() - datetime.timedelta(days=1):
        logger.debug("requested yesterday, getting dashboard metrics")
        res['metrics'] = get_dashboard_metrics(pdb)

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
        return "{:,f} ({:d})".format(m['MeanRate'], m['Count'])
    if 'MeanRate' in m:
        return "{:,f}".format(m['MeanRate'])
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


def send_mail(html, dry_run=False):
    """
    Send the message

    :param html: HTML to make up the body of the message
    :type html: string
    :param dry_run: whether to actually send, or just print what would be sent
    :type dry_run: boolean
    """
    if dry_run:
        logger.info("would have sent: {body}".format(body=html))
        with open('debug.html', 'w') as fh:
            fh.write(html)
        print("DEBUG - wrote to debug.html")
    else:
        logger.debug("sending mail")
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

    options, args = p.parse_args(argv)

    return options


def console_entry_point():
    """setuptools entry point"""
    opts = parse_args(sys.argv[1:])

    if opts.verbose > 1:
        logger.setLevel(logging.DEBUG)
    elif opts.verbose > 0:
        logger.setLevel(logging.INFO)

    if not opts.host:
        raise SystemExit("ERROR: you must specify the PuppetDB hostname with -p|--puppetdb")
    main(opts.host, num_days=opts.num_days, dry_run=opts.dry_run, cache_dir=opts.cache_dir)


if __name__ == "__main__":
    console_entry_point()
