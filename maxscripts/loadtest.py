"""MAX loadtester

Usage:
    max.loadtest utalk <maxserver> [options]

Options:
    -r <username>, --username <username>            Username of the max restricted user
    -p <password>, --password <password>            Password for the max restricted user
    -s <utalkserver>, --utalkserver <utalkserver>   Url of the sockjs endpoint
    -t <transport>, --transport                     Transport used, can be websocket, xhr, xhr_streaming [default: websocket]
    -c <num_conv>, --conversations <num_conv>       Number of conversations to start [default: 1]
    -u <num_users>, --users <num_users>             Number of users per conversation [default: 2]
    -m <num_msg>, --messages <num_mg>               Number of messages each user will send [default: 3]
    -a <rate>, --rate <rate>                        maximum messages/second rate [default: 0]
"""

from docopt import docopt
from gevent.event import AsyncResult
from utalkpythonclient.testclient import UTalkTestClient
from maxclient.rest import MaxClient

import gevent
import json
import os
import sys


class ReadyCounter(object):
    def __init__(self, event):
        self.count = 0
        self.event = event

    def add(self):
        self.count += 1

    def ready(self):
        self.count -= 1
        if self.count == 0:
            self.event.set()


class MaxHelper(object):
    def __init__(self, maxserver, username=None, password=None):
        self.maxserver = maxserver
        self.max = MaxClient(maxserver)
        self.max.login(username, password)

    def create_users(self, basename, count, index=0):
        created = []
        for i in xrange(index, index + count):
            username = '{}_{:0>4}'.format(basename, i)
            self.max.people[username].post()
            created.append(username)
            sys.stdout.write('.')
            sys.stdout.flush()
        return created

    def create_conversation(self, displayname, users):
        creator = users[0]
        client = MaxClient(self.maxserver, actor=creator)
        conversation = client.conversations.post(
            object_content='First Message',
            contexts=[{
                "objectType": "conversation",
                "participants": users,
                "displayName": displayname
            }])
        return client.conversations[conversation['contexts'][0]['id']].get()

    def delete_conversation_and_users(self, conversation):
        client = MaxClient(self.maxserver, actor=conversation['creator'])
        users = conversation['participants']
        client.conversations[conversation['id']].delete()

        #for user in users:
        #    self.max.people[user['username']].delete()


class LoadTestScenario(object):

    def __init__(self, maxserver, username, password):
        self.maxserver = maxserver
        self.maxhelper = MaxHelper(self.maxserver, username, password)

    def load(self, json_file):
        if os.path.exists(json_file):
            return json.loads(open(json_file).read())
        else:
            return []

    def setup(self, num_conversations, users_per_conversation, messages_per_user, message_rate):
        self.num_conversations = num_conversations
        self.users_per_conversation = users_per_conversation
        self.messages_per_user = messages_per_user
        self.total_users = num_conversations * users_per_conversation

        self.created_conversations = self.load('conversations.json')
        self.clients = []

        os.system('clear')
        print

        print " > Creating {} users and {} conversations".format(self.total_users, self.num_conversations)

        if self.created_conversations:
            print '    --> Skipping {} existing conversations'.format(len(self.created_conversations))

        self.conversations = []

        for conversation_index in xrange(self.num_conversations):
            if conversation_index < len(self.created_conversations):
                # conversation exists
                self.conversations.append(self.created_conversations[conversation_index])
            else:
                # we need a new conversation
                sys.stdout.write("\n    --> Creating conversation #{} ".format(conversation_index))
                sys.stdout.flush()
                conversation_name = 'conversation_{:0>4}'.format(self.num_conversations)
                users = self.maxhelper.create_users('user_{:0>4}_'.format(conversation_index), self.users_per_conversation, 0)
                new_conversation = self.maxhelper.create_conversation(conversation_name, users)
                self.conversations.append(new_conversation)
                self.create_conversations.append(new_conversation)

        open('conversations.json', 'w').write(json.dumps(self.created_conversations))

        print
        print " > Creating {} Test Clients".format(self.total_users)

        # Syncronization primitives
        self.wait_for_others = AsyncResult()
        self.counter = ReadyCounter(self.wait_for_others)

        start_delay = 1.0 / message_rate if message_rate > 0 else 0
        for conversation in self.conversations:
            for user in conversation['participants'][:self.users_per_conversation]:
                utalk_client = UTalkTestClient(
                    self.maxserver,
                    user['username'],
                    token_login='password_not_needed',
                    quiet=True,
                    use_gevent=True
                )
                self.counter.add()
                utalk_client.setup(
                    conversation['id'],
                    self.messages_per_user,
                    self.messages_per_user * (self.users_per_conversation - 1),
                    self.counter,
                    start_delay=start_delay * self.counter.count,
                    message_delay=self.total_users * start_delay
                )

                self.clients.append(utalk_client)

    def teardown(self):
        print " > Test Teardown"
        # gevent.killall(self.greenlets)

        # for client in self.clients:
        #     client.teardown()

        # for conversation in self.conversations:
        #     self.maxhelper.delete_conversation_and_users(conversation)

    def run(self):
        return self.test()
        # try:
        #     return self.test()
        # except Exception as exc:
        #     print exc
        #     print exc.message
        #     return False

    def stats(self):
        print ' > Harvesting stats'
        # Collect information harvested by each client
        # connect_times = [a.value.join_time for a in messenger_threads]
        # message_times = [a.value.seconds_per_message for a in messenger_threads]

        # first_message_time = min([a.value.start_talking_time for a in messenger_threads])
        # last_message_time = min([a.value.end_talking_time for a in messenger_threads])
        # total_sending_time = last_message_time - first_message_time
        # total_sending_time = total_sending_time.total_seconds()

        all_recv_times = []
        all_ackd_times = []
        rates = {}
        all_sent_times = []

        def elapsed(t0, t1):
            message_elapsed = t1 - t0
            return message_elapsed.total_seconds()

        for client in self.clients:
            all_recv_times += [elapsed(*times) for times in client.stats['recv_times']]
            all_ackd_times += [elapsed(*times) for times in client.stats['ackd_times']]
            for sent in client.stats['send_times']:
                r_id = sent.strftime('%Y%m%d%H%M%S')
                rates.setdefault(r_id, 0)
                rates[r_id] += 1
                all_sent_times.append(sent)

        sorted_rates = sorted(rates.items(), key=lambda x: x[0])
        all_sent_times.sort()
        seconds_elapsed = all_sent_times[-1] - all_sent_times[0]
        actual_rate = len(all_sent_times) / seconds_elapsed.total_seconds()
        print 'Message rate = {} m/s'.format(actual_rate)

        for rate, value in sorted_rates:
            print value, 'm/s'

        average_recv_time = sum(all_recv_times) / len(all_recv_times)
        average_ackd_time = sum(all_ackd_times) / len(all_ackd_times)

        min_recv_time = min(all_recv_times)
        max_recv_time = max(all_recv_times)

        min_ackd_time = min(all_ackd_times)
        max_ackd_time = max(all_ackd_times)

        all_ackd_times.sort()
        all_recv_times.sort()

        median_recv_time = all_recv_times[len(all_recv_times) / 2]
        median_ackd_time = all_ackd_times[len(all_ackd_times) / 2]

        normal_user_message_time = 5
        print
        print ' RESULTS'
        print '---------'
        print
        print ' Conversations: %d' % self.num_conversations
        print ' Users per conversation: %d' % self.users_per_conversation
        print ' Total concurrent users: %d ' % self.total_users
        print ' Rate tested: %.2f' % actual_rate

        print ' Assuming users writing a message every {} seconds, with this results'.format(normal_user_message_time)
        print ' we can handle %d concurrent users ' % int(actual_rate / (1.0 / normal_user_message_time))
        print
        print 'Message reception times'
        print '------------------------------------'
        print ' AVERAGE : %.2f seconds/message' % (average_recv_time)
        print ' MEDIAN : %.2f seconds/message' % (median_recv_time)
        print ' MIN     : %.2f seconds/message' % (min_recv_time)
        print ' MAX     : %.2f seconds/message' % (max_recv_time)
        print
        print
        print 'Message acknowledge times'
        print '------------------------------------'
        print ' AVERAGE : %.2f seconds/message' % (average_ackd_time)
        print ' MEDIAN : %.2f seconds/message' % (median_ackd_time)
        print ' MIN     : %.2f seconds/message' % (min_ackd_time)
        print ' MAX     : %.2f seconds/message' % (max_ackd_time)
        print

    def test(self):

        print " > Testing: sending {} messages".format(self.total_users * self.messages_per_user)

        from gevent.monkey import patch_all
        patch_all()

        self.greenlets = [gevent.spawn(client.start) for client in self.clients]
        gevent.joinall(self.greenlets, raise_error=True)
        success = False not in [client.succeded() for client in self.clients]

        if success:
            print ' > Load Test finished, all messages received'
            return True
        else:
            print ' > Load Test failed'
            for client in self.clients:
                if not client.succeded():
                    print '{} AKCD:{}, RECV:{}'.format(client.username, client.ackd_messages, client.received_messages)
            return False


def main(argv=sys.argv):
    arguments = docopt(__doc__, version='MAX loadtester 1.0')

    maxserver = arguments.get('<maxserver>')

    max_user = arguments.get('--username')
    max_user_password = arguments.get('--password')

    num_conversations = int(arguments.get('--conversations'))
    users_per_conversation = int(arguments.get('--users'))
    messages_per_user = int(arguments.get('--messages'))
    message_rate = float(arguments.get('--rate'))

    test = LoadTestScenario(maxserver, max_user, max_user_password)

    test.setup(num_conversations, users_per_conversation, messages_per_user, message_rate)
    success = test.run()
    test.teardown()
    if success:
        test.stats()
