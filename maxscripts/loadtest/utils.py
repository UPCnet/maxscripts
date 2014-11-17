from gevent.event import AsyncResult
from maxclient.rest import MaxClient as RestMaxClient
from maxclient.wsgi import MaxClient as WsgiMaxClient

import sys


class ReadyCounter(object):
    def __init__(self):
        self.count = 0
        self.event = AsyncResult()

    def add(self):
        self.count += 1

    def ready(self):
        self.count -= 1
        if self.count == 0:
            self.event.set()


class MaxHelper(object):
    def __init__(self, maxserver, mode, username=None, password=None):
        self.MaxClient = WsgiMaxClient if mode == 'wsgi' else RestMaxClient
        self.maxserver = maxserver
        self.max = self.MaxClient(maxserver)
        self.max.login(username, password)

    def get_client_as(self, actor):
        client = self.MaxClient(self.maxserver, actor=actor)
        client.setToken('xxx')
        return client

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
        client = self.get_client_as(creator)
        conversation = client.conversations.post(
            object_content='First Message',
            contexts=[{
                "objectType": "conversation",
                "participants": users,
                "displayName": displayname
            }])
        return client.conversations[conversation['contexts'][0]['id']].get()

    def delete_conversation_and_users(self, conversation):
        client = self.get_client_as(conversation['creator'])
        users = conversation['participants']
        client.conversations[conversation['id']].delete()

        #for user in users:
        #    self.max.people[user['username']].delete()
