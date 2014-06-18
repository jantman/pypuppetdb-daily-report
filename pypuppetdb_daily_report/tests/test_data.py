"""
Test fixtures

Since we have objects (specifically datetime.timedelta) in here, we can't
really use JSON for this. The alternative is to pickle, but that makes it
a pain to work with.

"""
import datetime
from pytz import utc

FINAL_DATA = {
    'Tue 06/10': {
        'metrics': {'foo': {'formatted': 'foo1'}, 'bar': {'formatted': 'bar1'}, 'baz': {'formatted': 'baz1'}},
        'facts': {'puppetversion': {'3.4.1': 2, '3.4.2': 1, '3.6.1': 100}, 'facterversion': {'2.0.0': 102, '1.7.2': 1}},
        'nodes': {
            'node1.example.com': {
                'reports': {
                    'run_count': 2,
                    'run_time_total': datetime.timedelta(seconds=1010),
                    'run_time_max': datetime.timedelta(seconds=1000),
                    'with_failures': 2,
                    'with_changes': 2,
                    'with_skips': 2,
                },
            },
            'node2.example.com': {
                'reports': {
                    'run_count': 1,
                    'run_time_total': datetime.timedelta(seconds=100),
                    'run_time_max': datetime.timedelta(seconds=100),
                    'with_failures': 1,
                    'with_changes': 1,
                    'with_skips': 1,
                },
            },
            'node3.example.com': {
                'reports': {
                    'run_count': 1,
                    'run_time_total': datetime.timedelta(seconds=500),
                    'run_time_max': datetime.timedelta(seconds=500),
                    'with_failures': 0,
                    'with_changes': 1,
                    'with_skips': 0,
                },
            },
            'node4.example.com': {
                'reports': {
                    'run_count': 5,
                    'run_time_total': datetime.timedelta(seconds=600),
                    'run_time_max': datetime.timedelta(seconds=500),
                    'with_failures': 5,
                    'with_changes': 0,
                    'with_skips': 0,
                },
            },
            'node5.example.com': {
                'reports': {
                    'run_count': 0,
                    'run_time_total': datetime.timedelta(),
                    'run_time_max': datetime.timedelta(),
                    'with_failures': 0,
                    'with_changes': 0,
                    'with_skips': 0,
                },
            },
            'node6.example.com': {
                'reports': {
                    'run_count': 10,
                    'run_time_total': datetime.timedelta(seconds=100),
                    'run_time_max': datetime.timedelta(seconds=90),
                    'with_failures': 7,
                    'with_changes': 2,
                    'with_skips': 7,
                },
            },
        },
        'aggregate': {
            'reports': {
                'with_skips': 3,
                'run_time_max': datetime.timedelta(0, 1000),
                'with_failures': 8,
                'with_changes': 4,
                'run_count': 9,
                'run_time_total': datetime.timedelta(0, 2210),
                'run_time_avg': datetime.timedelta(0, 245, 555555),
                'nodes_with_no_report': 1,
                'nodes_no_successful_runs': 4,
                'nodes_50+_failed': 1,
            },
        },
    },
    'Mon 06/09': {'metrics': {'foo': {'formatted': 'foo2'}, 'bar': {'formatted': 'bar2'}, 'baz': {'formatted': 'baz2'}}},
    'Sun 06/08': {'metrics': {'foo': {'formatted': 'foo3'}, 'bar': {'formatted': 'bar3'}, 'baz': {'formatted': 'baz3'}}},
    'Sat 06/07': {'metrics': {'foo': {'formatted': 'foo4'}, 'bar': {'formatted': 'bar4'}, 'baz': {'formatted': 'baz4'}}},
    'Fri 06/06': {'metrics': {'foo': {'formatted': 'foo5'}, 'bar': {'formatted': 'bar5'}, 'baz': {'formatted': 'baz5'}}},
    'Thu 06/05': {'metrics': {'foo': {'formatted': 'foo6'}, 'bar': {'formatted': 'bar6'}, 'baz': {'formatted': 'baz6'}}},
    'Wed 06/04': {'foo': 'bar'},
}

FINAL_DATES = ['Tue 06/10',
               'Mon 06/09',
               'Sun 06/08',
               'Sat 06/07',
               'Fri 06/06',
               'Thu 06/05',
               'Wed 06/04'
               ]

NODE_SUMMARY_DATA = {
    'Tue 06/10': {
        'metrics': {'foo': {'formatted': 'foo1'}, 'bar': {'formatted': 'bar1'}, 'baz': {'formatted': 'baz1'}},
        'facts': {'puppetversion': {'3.4.1': 2, '3.4.2': 1, '3.6.1': 100}, 'facterversion': {'2.0.0': 102, '1.7.2': 1}},
        'nodes': {
            'node1.example.com': {
                'reports': {
                    'run_count': 2,
                    'run_time_total': datetime.timedelta(seconds=1010),
                    'run_time_max': datetime.timedelta(seconds=1000),
                    'with_failures': 2,
                    'with_changes': 2,
                    'with_skips': 2,
                },
            },
        },
        'aggregate': {
            'reports': {
                'with_skips': 3,
                'run_time_max': datetime.timedelta(0, 1000),
                'with_failures': 8,
                'with_changes': 4,
                'run_count': 9,
                'run_time_total': datetime.timedelta(0, 2210),
                'run_time_avg': datetime.timedelta(0, 245, 555555),
                'nodes_with_no_report': 1,
            },
            'nodes': {
                'count': 10,
                'all_failed': 1,
                'half_failed': 4,
                'any_failed': 2,
                'less_than_X_reports': 1,
                'with_changes': 5,
            },
        },
    },
    'Mon 06/09': {
        'metrics': {'foo': {'formatted': 'foo1'}, 'bar': {'formatted': 'bar1'}, 'baz': {'formatted': 'baz1'}},
        'facts': {'puppetversion': {'3.4.1': 2, '3.4.2': 1, '3.6.1': 100}, 'facterversion': {'2.0.0': 102, '1.7.2': 1}},
        'nodes': {
            'node1.example.com': {
                'reports': {
                    'run_count': 2,
                    'run_time_total': datetime.timedelta(seconds=1010),
                    'run_time_max': datetime.timedelta(seconds=1000),
                    'with_failures': 2,
                    'with_changes': 2,
                    'with_skips': 2,
                },
            },
        },
        'aggregate': {
            'reports': {
                'with_skips': 3,
                'run_time_max': datetime.timedelta(0, 1000),
                'with_failures': 8,
                'with_changes': 4,
                'run_count': 9,
                'run_time_total': datetime.timedelta(0, 2210),
                'run_time_avg': datetime.timedelta(0, 245, 555555),
                'nodes_with_no_report': 1,
            },
            'nodes': {
                'count': 8,
                'all_failed': 4,
                'half_failed': 0,
                'any_failed': 2,
                'less_than_X_reports': 0,
                'with_changes': 6,
            },
        },
    },
    'Sun 06/08': {'metrics': {'foo': {'formatted': 'foo3'}, 'bar': {'formatted': 'bar3'}, 'baz': {'formatted': 'baz3'}}},
    'Sat 06/07': {'metrics': {'foo': {'formatted': 'foo4'}, 'bar': {'formatted': 'bar4'}, 'baz': {'formatted': 'baz4'}}},
    'Fri 06/06': {'metrics': {'foo': {'formatted': 'foo5'}, 'bar': {'formatted': 'bar5'}, 'baz': {'formatted': 'baz5'}}},
    'Thu 06/05': {'metrics': {'foo': {'formatted': 'foo6'}, 'bar': {'formatted': 'bar6'}, 'baz': {'formatted': 'baz6'}}},
    'Wed 06/04': {'foo': 'bar'},
}

NODE_AGGR_NODES = {
    'node1.example.com': {
        'reports': {
            'run_count': 1,
            'run_time_total': datetime.timedelta(seconds=100),
            'run_time_max': datetime.timedelta(seconds=100),
            'with_failures': 1,
            'with_changes': 1,
            'with_skips': 1,
        },
    },
    # TODO - left off here
    'node2.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node3.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node4.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node5.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node6.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node7.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node8.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node9.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node10.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
}

EVENT_DATA = {
    '["=", "report", "hash1"]': [
    ],
    '["=", "report", "hash2"]': [
        {
            '_Event__string': u'Package[srvadmin-idrac7]/14eaf89f52496f94bae336d454b60fac6189ff1b',
            'failed': True,
            'hash_': u'14eaf89f52496f94bae336d454b60fac6189ff1b',
            'item': {
                u'message': u"failure message here",
                u'new': u'present',
                u'old': u'absent',
                u'property': u'ensure',
                u'title': u'srvadmin-idrac7',
                u'type': u'Package',
            },
            'node': u'node1.example.com',
            'status': u'failure',
            'timestamp': datetime.datetime(2014, 6, 18, 13, 2, 54, 122000, tzinfo=utc),
        },
        {
            '_Event__string': u'Service[dataeng]/14eaf89f52496f94bae336d454b60fac6189ff1b',
            'failed': False,
            'hash_': u'14eaf89f52496f94bae336d454b60fac6189ff1b',
            'item': {
                u'message': None,
                u'new': None,
                u'old': None,
                u'property': None,
                u'title': u'dataeng',
                u'type': u'Service',
            },
            'node': u'node1.example.com',
            'status': u'skipped',
            'timestamp': datetime.datetime(2014, 6, 18, 13, 3, 3, 99000, tzinfo=utc),
        },
        {
            '_Event__string': u'Package[libsmbios]/14eaf89f52496f94bae336d454b60fac6189ff1b',
            'failed': True,
            'hash_': u'14eaf89f52496f94bae336d454b60fac6189ff1b',
            'item': {
                u'message': u"failure message here",
                u'new': u'latest',
                u'old': u'2.2.26-3.el5',
                u'property': u'ensure',
                u'title': u'libsmbios',
                u'type': u'Package',
            },
            'node': u'node1.example.com',
            'status': u'failure',
            'timestamp': datetime.datetime(2014, 6, 18, 13, 3, 2, 995000, tzinfo=utc),
        },
        {
            '_Event__string': u'Augeas[disable dell yum plugin once OM is installed]/14eaf89f52496f94bae336d454b60fac6189ff1b',
            'failed': False,
            'hash_': u'14eaf89f52496f94bae336d454b60fac6189ff1b',
            'item': {
                u'message': None,
                u'new': None,
                u'old': None,
                u'property': None,
                u'title': u'disable dell yum plugin once OM is installed',
                u'type': u'Augeas',
            },
            'node': u'node1.example.com',
            'status': u'skipped',
            'timestamp': datetime.datetime(2014, 6, 18, 13, 3, 3, 100000, tzinfo=utc),
        },
    ],
    '["=", "report", "hash3"]': [
        {
            '_Event__string': u'Exec[zookeeper ensemble check]/c5a40c3068f295966541d7e51d3e6fe76e56870c',
            'failed': False,
            'hash_': u'c5a40c3068f295966541d7e51d3e6fe76e56870c',
            'item': {
                u'message': u'executed successfully',
                u'new': [u'0'],
                u'old': u'notrun',
                u'property': u'returns',
                u'title': u'zookeeper ensemble check',
                u'type': u'Exec',
            },
            'node': u'node1.example.com',
            'status': u'success',
            'timestamp': datetime.datetime(2014, 6, 18, 13, 0, 55, 300000, tzinfo=utc),
        },
        {
            '_Event__string': u'Service[winbind]/c5a40c3068f295966541d7e51d3e6fe76e56870c',
            'failed': False,
            'hash_': u'c5a40c3068f295966541d7e51d3e6fe76e56870c',
            'item': {
                u'message': u"ensure changed 'stopped' to 'running'",
                u'new': u'running',
                u'old': u'stopped',
                u'property': u'ensure',
                u'title': u'winbind',
                u'type': u'Service',
            },
            'node': u'node1.example.com',
            'status': u'success',
            'timestamp': datetime.datetime(2014, 6, 18, 13, 1, 0, 122000, tzinfo=utc),
        },
        {
            '_Event__string': u'Service[zookeeper-server]/c5a40c3068f295966541d7e51d3e6fe76e56870c',
            'failed': False,
            'hash_': u'c5a40c3068f295966541d7e51d3e6fe76e56870c',
            'item': {
                u'message': u"ensure changed 'stopped' to 'running'",
                u'new': u'running',
                u'old': u'stopped',
                u'property': u'ensure',
                u'title': u'zookeeper-server',
                u'type': u'Service',
            },
            'node': u'node1.example.com',
            'status': u'success',
            'timestamp': datetime.datetime(2014, 6, 18, 13, 0, 54, 129000, tzinfo=utc),
        },
    ],
    '["=", "report", "hash4"]': [
        {
            '_Event__string': u'Package[srvadmin-idrac7]/14eaf89f52496f94bae336d454b60fac6189ff1b',
            'failed': True,
            'hash_': u'14eaf89f52496f94bae336d454b60fac6189ff1b',
            'item': {
                u'message': u"failure message here",
                u'new': u'present',
                u'old': u'absent',
                u'property': u'ensure',
                u'title': u'srvadmin-idrac7',
                u'type': u'Package',
            },
            'node': u'node1.example.com',
            'status': u'failure',
            'timestamp': datetime.datetime(2014, 6, 18, 13, 2, 54, 122000, tzinfo=utc),
        },
        {
            '_Event__string': u'Service[zookeeper-server]/c5a40c3068f295966541d7e51d3e6fe76e56870c',
            'failed': False,
            'hash_': u'c5a40c3068f295966541d7e51d3e6fe76e56870c',
            'item': {
                u'message': u"ensure changed 'stopped' to 'running'",
                u'new': u'running',
                u'old': u'stopped',
                u'property': u'ensure',
                u'title': u'zookeeper-server',
                u'type': u'Service',
            },
            'node': u'node1.example.com',
            'status': u'success',
            'timestamp': datetime.datetime(2014, 6, 18, 13, 0, 54, 129000, tzinfo=utc),
        },
    ],
}
