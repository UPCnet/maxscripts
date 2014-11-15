from maxscripts.loadtest.utils import MaxHelper
from maxscripts.loadtest.utils import ReadyCounter
from utalkpythonclient.testclient import UTalkTestClient

import gevent
import json
import os
import sys


class UtalkLoadTest(object):

    def log(self, msg):
        if not self.quiet:
            print msg

    def __init__(self, maxserver, username, password, quiet=False):
        self.maxserver = maxserver
        self.maxhelper = MaxHelper(self.maxserver, username, password)
        self.quiet = quiet

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
        self.message_rate = message_rate

        self.created_conversations = self.load('conversations.json')
        self.clients = []

        if not self.quiet:
            os.system('clear')
        self.log('')
        self.log(" > Creating {} users and {} conversations".format(self.total_users, self.num_conversations))

        if self.created_conversations:
            self.log('    --> Skipping {} existing conversations'.format(len(self.created_conversations)))

        self.conversations = []

        for conversation_index in xrange(self.num_conversations):
            if conversation_index < len(self.created_conversations):
                # conversation exists
                self.conversations.append(self.created_conversations[conversation_index])
            else:
                # we need a new conversation
                if not self.quiet:
                    sys.stdout.write("\n    --> Creating conversation #{} ".format(conversation_index))
                    sys.stdout.flush()
                conversation_name = 'conversation_{:0>4}'.format(self.num_conversations)
                users = self.maxhelper.create_users('user_{:0>4}_'.format(conversation_index), self.users_per_conversation, 0)
                new_conversation = self.maxhelper.create_conversation(conversation_name, users)
                self.conversations.append(new_conversation)
                self.created_conversations.append(new_conversation)

        open('conversations.json', 'w').write(json.dumps(self.created_conversations))

        self.log("\n > Creating {} Test Clients".format(self.total_users))

        # Syncronization primitives
        self.counter = ReadyCounter()
        self.wait_for_others = ReadyCounter.event

        start_delay = 1.0 / self.message_rate if message_rate > 0 else 0
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
        self.log(" > Test Teardown")
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

    def harvest_stats(self):

        all_recv_times = []
        all_ackd_times = []
        rates = {}
        all_sent_times = []

        def elapsed(t0, t1):
            message_elapsed = t1 - t0
            return abs(message_elapsed.total_seconds())

        for client in self.clients:
            all_recv_times += [elapsed(*times) for times in client.stats['recv_times']]
            all_ackd_times += [elapsed(*times) for times in client.stats['ackd_times']]
            for sent in client.stats['send_times']:
                r_id = sent.strftime('%Y%m%d%H%M%S')
                rates.setdefault(r_id, 0)
                rates[r_id] += 1
                all_sent_times.append(sent)

        all_sent_times.sort()
        seconds_elapsed = all_sent_times[-1] - all_sent_times[0]
        actual_rate = len(all_sent_times) / seconds_elapsed.total_seconds()

        # sorted_rates = sorted(rates.items(), key=lambda x: x[0])
        # for rate, value in sorted_rates:
        #     print value, 'm/s'

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

        return {
            "conversations": self.num_conversations,
            "users_per_conversation": self.users_per_conversation,
            "total_users": self.total_users,
            "requested_rate": self.message_rate,
            "effective_rate": actual_rate,
            "average_recv_time": average_recv_time,
            "median_recv_time": median_recv_time,
            "min_recv_time": min_recv_time,
            "max_recv_time": max_recv_time,
            "average_ackd_time": average_ackd_time,
            "median_ackd_time": median_ackd_time,
            "min_ackd_time": min_ackd_time,
            "max_ackd_time": max_ackd_time,

        }

    def stats(self):
        self.log(' > Preparing stats')
        stats = self.harvest_stats()

        # Assuming users writing a message every {} seconds, with this results'.format(normal_user_message_time)
        # we can handle %d concurrent users ' % int(actual_rate / (1.0 / normal_user_message_time))

        results = """
  RESULTS
-------------------------------------
  Conversations: {conversations}
  Users per conversation: {users_per_conversation}
  Total concurrent users: {total_users}
  Rate requested: {requested_rate:.3f} messages/s
  Effective rate: {effective_rate:.3f} messages/s

  Message reception times
-------------------------------------
  AVERAGE : {average_recv_time:.3f} seconds/message
  MEDIAN  : {median_recv_time:.3f} seconds/message
  MIN     : {min_recv_time:.3f} seconds/message
  MAX     : {max_recv_time:.3f} seconds/message

  Message acknowledge times
-------------------------------------
  AVERAGE : {average_ackd_time:.3f} seconds/message
  MEDIAN  : {median_ackd_time:.3f} seconds/message
  MIN     : {min_ackd_time:.3f} seconds/message
  MAX     : {max_ackd_time:.3f} seconds/message
        """.format(**stats)

        self.log(results)
        return stats

    def test(self):

        self.log(" > Testing: sending {} messages".format(self.total_users * self.messages_per_user))

        from gevent.monkey import patch_all
        patch_all()

        self.greenlets = [gevent.spawn(client.start) for client in self.clients]
        gevent.joinall(self.greenlets, raise_error=True)
        success = False not in [client.succeded() for client in self.clients]

        if success:
            self.log(' > Load Test finished, all messages received')
            return True
        else:
            self.log(' > Load Test failed')
            for client in self.clients:
                if not client.succeded():
                    self.log('{} AKCD:{}, RECV:{}'.format(client.username, client.ackd_messages, client.received_messages))
            return False
