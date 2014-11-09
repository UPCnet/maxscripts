"""MAX loadtester

Usage:
    max.loadtest utalk <maxserver>

Options:
"""

from docopt import docopt
from gevent.event import AsyncResult
from utalkpythonclient.testclient import UTalkTestClient
from maxclient.rest import MaxClient

import gevent
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
    def __init__(self, maxserver):
        self.maxserver = maxserver
        self.max = MaxClient(maxserver)
        self.login()

    def create_users(self, basename, count, index=0):
        created = []
        for i in range(index, count):
            username = '{}_{:0>4}'.format(basename, i)
            self.max.people[username].post()
            created.append(username)
        return created

    def create_conversation(self, displayname, users):
        creator = users[0]
        client = MaxClient(self.maxserver, actor=creator)
        conversation = client.conversations.post(
            object_content='First Message',
            contexts={
                "objectType": "conversation",
                "participants": users,
                "displayName": displayname
            })
        return conversation.id

    def delete_conversation_and_users(self, conversation):
        client = MaxClient(self.maxserver, actor=conversation['creator'])
        users = conversation['participants']
        client.conversations[conversation['id']].delete()

        for user in users:
            self.max.people[user['username']].delete()


class LoadTestScenario(object):

    def __init__(self, maxserver):
        self.maxserver = maxserver
        self.maxhelper = MaxHelper(self.maxserver)

    def setup(self, num_conversations, users_per_conversation, messages_per_user):
        self.num_conversations = num_conversations
        self.users_per_conversation = users_per_conversation
        self.messages_per_user

        self.total_users = num_conversations * users_per_conversation

        self.conversations = []
        self.clients = []

        os.system('clear')

        print '=================================='
        print " Seting up users and conversations"
        print '=================================='

        user_index = 0

        for conversation_index in range(self.num_conversations):
            conversation_name = 'conversation_{:0>4}'.format(self.num_conversations)
            users = self.maxhelper.createUsers('user', self.users_per_conversation, user_index)
            new_conversation = self.maxhelper.createConversation(conversation_name, users)
            self.conversations.append(new_conversation)
            user_index += len(users)

        print
        print '============================='
        print " Creating {} Test Clients".format(self.total_users)
        print '============================='
        print

        # Syncronization primitives
        self.wait_for_others = AsyncResult()
        self.counter = ReadyCounter(self.wait_for_others)

        for conversation in self.conversations:
            for user in conversation['participants']:
                utalk_client = UTalkTestClient(
                    self.maxserver,
                    user['username'],
                    'password_not_needed',
                    quiet=True,
                    use_gevent=True
                )
                self.counter.add()
                utalk_client.setup(
                    conversation['id'],
                    self.messages_per_user,
                    self.messages_per_user * len(conversation['participants'] - 1),
                    self.counter
                )

                self.clients.append(utalk_client)

    def teardown(self):
        for client in self.clients:
            client.teardown()

        for conversation in self.conversations:
            self.maxhelper.delete_conversation_and_users(conversation)

    def run(self):
        try:
            self.test()
        except:
            pass

    def test(self):
        greenlets = [gevent.spawn(client.connect) for client in self.clients]
        gevent.joinall(greenlets, timeout=120, raise_error=True)
        success = None not in [g.value for g in greenlets]

        if success:
            print 'Load Test succeded'
        else:
            print 'Load Test failed'


def main(argv=sys.argv):
    arguments = docopt(__doc__, version='MAX loadtester 1.0')

    maxserver = arguments.get('maxserver')
    num_conversations = 1
    users_per_conversation = 2
    messages_per_user = 3

    test = LoadTestScenario(maxserver)

    test.setup(num_conversations, users_per_conversation, messages_per_user)
    test.run()
    test.teardown()
