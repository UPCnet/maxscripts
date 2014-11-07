"""MAX loadtester

Usage:
    max.loadtest utalk <maxserver>

Options:
"""

from docopt import docopt
from gevent.event import AsyncResult
from utalkpythonclient.testclient import UTalkTestClient
from maxclient.rest import MaxClient

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


def main(argv=sys.argv):
    arguments = docopt(__doc__, version='MAX loadtester 1.0')

    num_conversations = 1
    users_per_conversation = 2

    total_users = num_conversations * users_per_conversation

    maxserver = arguments.get('maxserver')
    maxhelper = MaxHelper(maxserver)

    os.system('clear')

    print '=================================='
    print " Seting up users and conversations"
    print '=================================='

    user_index = 0

    conversations = []

    for conversation_index in range(num_conversations):
        conversation_name = 'conversation_{:0>4}'.format(num_conversations)
        users = maxhelper.createUsers('user', users_per_conversation, user_index)
        new_conversation = maxhelper.createConversation(conversation_name, users)
        conversations.append(new_conversation)
        user_index += len(users)

    print
    print '============================='
    print " Creating {} Test Clients".format(total_users)
    print '============================='
    print

    utalk_clients = []

    # Syncronization primitives
    wait_for_others = AsyncResult()
    counter = ReadyCounter(wait_for_others)

    for conversation in conversations:
        for user in conversation['participants']:
            utalk_clients.append(UTalkTestClient(
                maxserver,
                user['username'],
                'password_not_needed',
                quiet=True,
                use_gevent=True
            ))
            counter.add()
