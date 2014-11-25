from maxscripts.loadtest.utils import MaxHelper
from requests import ConnectionError

import sys
import time
from gevent.monkey import patch_all
import gevent


class LoadTestScenario(object):

    stats_template = ""

    def log(self, msg):
        if not self.quiet:
            print msg

    def __init__(self, maxserver, username, password, mode='rest', quiet=False):
        self.maxserver = maxserver
        self.quiet = quiet

        try:
            self.maxhelper = MaxHelper(self.maxserver, mode, username, password)
        except ConnectionError:
            self.log('Could not connect to {}. Check url is correct and server is running'.format(self.maxserver))
            sys.exit(1)

    def setup(self):
        """
        """
        pass

    def teardown(self):
        """
        """
        pass

    def harvest_stats(self):
        """
        """
        pass

    def run(self):
        try:
            return self.test()
        except Exception as exc:
            print exc
            print exc.message

    def stats(self):

        self.log(' > Preparing stats')
        stats = self.harvest_stats()

        results = self.stats_template.format(**stats)

        self.log(results)
        return stats


class RateLoadTest(LoadTestScenario):

    stats_template = """
  RESULTS
-------------------------------------
  Sent requests: {requests_count}

  Rates
-------------------------------------
  AVERAGE     : {average_rate:.4f} req/second
  MEDIAN      : {median_rate:.4f} req/second
  FASTEST     : {fastest_rate:.4f} req/second
  SLOWEST     : {slowest_rate:.4f} req/second

        """

    def setup(self, count):
        self.count = count
        self.response_times = []

    def test(self):
        for i in xrange(self.count):
            start = time.time()
            self.request()
            end = time.time()
            elapsed = end - start
            self.response_times.append(elapsed)
        return True

    def harvest_stats(self):

        return {
            "requests_count": self.count,
            "average_rate": 1.0 / (sum(self.response_times) / self.count),
            "median_rate": 1.0 / self.response_times[len(self.response_times) / 2],
            "slowest_rate": 1.0 / max(self.response_times),
            "fastest_rate": 1.0 / min(self.response_times)
        }


class GeventRateLoadTest(RateLoadTest):
    stats_template = """
  RESULTS
-------------------------------------
  Sent requests: {requests_count}

  Rates
-------------------------------------
  AVERAGE     : {average_rate:.4f} req/second

        """

    def test(self):
        patch_all()
        greenlets = []
        start = time.time()
        for i in xrange(self.count):
            greenlets.append(gevent.spawn(self.request))

        gevent.joinall(greenlets, raise_error=True)
        end = time.time()
        elapsed = end - start
        self.elapsed = elapsed
        return True

    def harvest_stats(self):

        return {
            "requests_count": self.count,
            "average_rate": 1.0 / (self.elapsed / self.count),
        }
