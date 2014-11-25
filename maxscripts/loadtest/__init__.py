"""MAX loadtester

Usage:
    max.loadtest utalk <maxserver> [options]
    max.loadtest utalk-rate <maxserver> [options]
    max.loadtest max messages <maxserver> [options]
    max.loadtest max timeline <maxserver> [options]

Options:
    -r <username>, --username <username>            Username of the max restricted user
    -p <password>, --password <password>            Password for the max restricted user
    -s <utalkserver>, --utalkserver <utalkserver>   Url of the sockjs endpoint
    -t <transport>, --transport                     Transport used, can be websocket, xhr, xhr_streaming [default: websocket]
    -c <num_conv>, --conversations <num_conv>       Number of conversations to start [default: 1]
    -u <num_users>, --users <num_users>             Number of users per conversation [default: 2]
    -m <num_msg>, --messages <num_mg>               Number of messages each user will send [default: 3]
    -a <rate>, --rate <rate>                        maximum messages/second rate [default: 0]
    -e <mode>, --maxclient <mode>                   Type of maxclient to use, rest, or wsgi [default: rest]
"""

from docopt import docopt

import sys
import time

from maxscripts.loadtest.utalk import UtalkLoadTest
from maxscripts.loadtest.max import MaxMessagesLoadTest
from maxscripts.loadtest.max import MaxTimelineLoadTest


def main(argv=sys.argv):
    arguments = docopt(__doc__, version='MAX loadtester 1.0')

    maxserver = arguments.get('<maxserver>')

    max_user = arguments.get('--username')
    max_user_password = arguments.get('--password')

    num_conversations = int(arguments.get('--conversations'))
    users_per_conversation = int(arguments.get('--users'))
    messages_per_user = int(arguments.get('--messages'))
    message_rate = float(arguments.get('--rate'))
    maxclient_mode = arguments.get('--maxclient')

    if arguments.get('utalk'):
        test = UtalkLoadTest(maxserver, max_user, max_user_password, mode=maxclient_mode)
        test.setup(num_conversations, users_per_conversation, messages_per_user, message_rate)
        success = test.run()
        test.teardown()
        if success:
            test.stats()

    if arguments.get('utalk-rates'):
        # Test results modifing message_rate
        rates = [10, 25, 50, 100, 150, 200, 300, 500, 750, 1000, 1250, 1500, 1750, 2000, 2500, 3000, 4000, 5000]

        print " USERS   RATE   RECV   ACKD"
        for rate in rates:
            test = UtalkLoadTest(maxserver, max_user, max_user_password, mode=maxclient_mode, quiet=True)
            test.setup(num_conversations, users_per_conversation, messages_per_user, rate)
            test.run()
            stats = test.stats()
            print "{total_users:>6} {effective_rate:>6.2f} {average_recv_time:>6.2f} {average_ackd_time:>6.2f}".format(**stats)
            time.sleep(20)

    # Max loadtests
    if arguments.get('max'):
        if arguments.get('messages'):
            test = MaxMessagesLoadTest(maxserver, max_user, max_user_password, mode=maxclient_mode)
            test.setup(messages_per_user)
            success = test.run()
            if success:
                test.stats()

        if arguments.get('timeline'):
            test = MaxTimelineLoadTest(maxserver, max_user, max_user_password, mode=maxclient_mode)
            test.setup(messages_per_user)
            success = test.run()
            if success:
                test.stats()
