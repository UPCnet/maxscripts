import ConfigParser
import argparse
import pymongo
import sys
import time
import gevent
from gevent.monkey import patch_all

patch_all()

from maxcarrot import RabbitClient
from maxutils import mongodb


def asbool(value):
    return value in [1, True, 'true', 'True']


class InitAndPurgeRabbitServer(object):  # pragma: no cover

    def log(self, message):
        if self.verbose:
            print message

    def __init__(self, options, quiet=False):
        self.quiet = quiet
        self.options = options

        self.exchanges_by_name = {}
        self.queues_by_name = {}

        self.common = ConfigParser.ConfigParser()
        self.common.read(self.options.commonfile)

        self.instances = ConfigParser.ConfigParser()
        self.instances.read(self.options.instancesfile)

        self.workers = self.options.workers
        self.verbose = self.options.verbose

        try:
            self.cluster = asbool(self.common.get('mongodb', 'cluster'))
            self.standaloneserver = self.common.get('mongodb', 'url')
            self.clustermembers = self.common.get('mongodb', 'hosts')
            self.replicaset = self.common.get('mongodb', 'replica_set')

            self.mongo_auth = asbool(self.common.get('mongodb', 'auth'))
            self.mongo_authdb = self.common.get('mongodb', 'authdb')
            self.mongo_username = self.common.get('mongodb', 'username')
            self.mongo_password = self.common.get('mongodb', 'password')
            self.rabbitmq_url = self.common.get('rabbitmq', 'server')
            self.rabbitmq_manage_url = self.common.get('rabbitmq', 'manage')
            self.maxserver_names = [maxserver for maxserver in self.instances.sections()]
        except:
            print('You must provide a valid configuration .ini file.')
            sys.exit()

    def add_users(self, server, users):

        for count, user in enumerate(users):
            if server.user_publish_exchange(user['username']) in self.exchanges_by_name and \
               server.user_subscribe_exchange(user['username']) in self.exchanges_by_name:
                server.create_user(user['username'], create_exchanges=False)
                self.log('Created internal bindings for {}'.format(user['username']))
            else:
                self.log('Created exchanges and bindings for {}'.format(user['username']))
                server.create_user(user['username'])

    def add_conversation_bindings(self, server, conversations):
        """
        """
        for cid, members in conversations:
            for member in members:
                pub_binding_key = '{}_{}.*_conversations'.format(server.user_publish_exchange(member), cid)
                sub_binding_key = 'conversations_{}.*_{}'.format(cid, server.user_subscribe_exchange(member))
                if pub_binding_key in self.conversation_bindings and \
                   sub_binding_key in self.conversation_bindings:
                    pass
                else:
                    self.log('Create pub/sub bindings for user {} on conversation {}'.format(member, cid))
                    server.conversations.bind_user(cid, member)

    def add_context_bindings(self, server, contexts):
        """
        """
        for cid, members in contexts:
            for member in members:
                sub_binding_key = 'activity_{}_{}'.format(cid, server.user_subscribe_exchange(member))
                if sub_binding_key in self.conversation_bindings:
                    pass
                else:
                    self.log('Create pub/sub bindings for user {} on conversation {}'.format(member, cid))
                    server.conversations.bind_user(cid, member)

    def do_batch(self, method, items):
        batch = []
        tasks = self.workers if len(items) > self.workers else 1

        if tasks > 1:
            users_per_task = len(items) / tasks

            for task_index in range(tasks + 1):
                start = task_index * users_per_task
                end = (task_index + 1) * users_per_task
                if start < len(items):
                    batch.append(items[start:end])

        start = time.time()
        if tasks == 1:
            method(self.server, items)
        else:
            threads = [gevent.spawn(method, RabbitClient(self.rabbitmq_url), batch_items) for batch_items in batch]
            gevent.joinall(threads)

        end = time.time()
        total_seconds = end - start
        print
        print ' | Total items: {}'.format(len(items))
        print ' | Total seconds: {:.2f}'.format(total_seconds)
        print ' | Items/second: {:.2f}'.format(len(items) / total_seconds)
        print

    def run(self):

        # Create client without declaring anything

        self.server = RabbitClient(self.rabbitmq_url)

        # Clear all non-native exchanges and queues
        print '> Cleaning up rabbitmq'
        self.server.management.cleanup(delete_all=self.options.deleteall)

        # Create all exchanges and queues defined in spec
        print '> Creating default exchanges, queues and bindings'
        self.server.declare()

        # Refresh
        print '> Loading current exchanges and queues'
        self.server.management.load_exchanges()
        self.server.management.load_queues()
        self.exchanges_by_name = self.server.management.exchanges_by_name

        print '> Loading current conversation bindings'
        bindings = self.server.management.load_exchange_bindings('conversations')
        self.conversation_bindings = ['{source}_{routing_key}_{destination}'.format(**binding) for binding in bindings]

        print '> Loading current context bindings'
        bindings = self.context_bindings = self.server.management.load_exchange_bindings('activity')
        self.context_bindings = ['{source}_{routing_key}_{destination}'.format(**binding) for binding in bindings]

        # Mongodb connection initialization
        cluster_enabled = self.cluster
        auth_enabled = self.mongo_auth
        mongodb_uri = self.clustermembers if cluster_enabled else self.standaloneserver

        conn = mongodb.get_connection(
            mongodb_uri,
            use_greenlets=True,
            cluster=self.replicaset if cluster_enabled else None)

        for maxname in self.maxserver_names:
            print('')
            print('============================================================================')
            print(' Processing "{}" max instance'.format(maxname))
            print('============================================================================')
            print('')
            db = mongodb.get_database(
                conn,
                'max_{}'.format(maxname),
                username=self.mongo_username if auth_enabled else None,
                password=self.mongo_password if auth_enabled else None,
                authdb=self.mongo_authdb if auth_enabled else None)

            print "> Getting users list from database"

            # Get all users to create their rabbit exchange and bindings
            query = {} if not self.options.usernamefilter else {'username': self.options.usernamefilter}
            all_users = db.users.find(query, {'_id': 0, 'username': 1, 'talkingIn': 1, 'subscribedTo': 1})
            contexts_with_notifications = db.contexts.find({'notifications': {'$nin': [False], '$exists': 1}}, {'hash': 1})
            contexts_with_notifications_hashs = [a['hash'] for a in contexts_with_notifications]

            # unpack lazy results
            all_users = [a for a in all_users]
            print '> Got {} users'.format(len(all_users))
            print

            # Extract the list of conversations and context subscriptions from all users
            conversations = {}
            contexts = {}
            for user in all_users:
                for conversation in user.get('talkingIn', []):
                    conv = conversations.setdefault(conversation['id'], [])
                    conv.append(user['username'])
                for context in user.get('subscribedTo', []):
                    if context['hash'] in contexts_with_notifications_hashs:
                        ctxt = contexts.setdefault(context['hash'], [])
                        ctxt.append(user['username'])

            print '> Starting Batch: Create user exchanges and bindings'
            self.do_batch(self.add_users, all_users)

            print '> Starting Batch: Create conversation bindings'
            self.do_batch(self.add_conversation_bindings, conversations.items())

            print '> Starting Batch: Create context bindings'
            self.do_batch(self.add_context_bindings, contexts.items())

        self.server.disconnect()


def main(argv=sys.argv, quiet=False):  # pragma: no cover
    description = "Initialize and purge if needed RabbitMQ development server."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        '-i', '--instances',
        dest='instancesfile',
        type=str,
        default='config/instances.ini',
        help=("Max instances configuration file"))
    parser.add_argument(
        '-c', '--config',
        dest='commonfile',
        type=str,
        default='config/common.ini',
        help=("Common configuration file"))
    parser.add_argument(
        '-d', '--delete-all',
        dest='deleteall',
        type=bool,
        default=False,
        help=("Delete all exchanges and queues first"))
    parser.add_argument(
        '-v', '--verbose',
        dest='verbose',
        type=bool,
        default=False,
        help=("Log every action"))
    parser.add_argument(
        '-w', '--workers',
        dest='workers',
        type=int,
        default=1,
        help=("Number of gevent workers to start"))
    parser.add_argument(
        '-u', '--user',
        dest='usernamefilter',
        type=str,
        default=None,
        help=("Perform action only for this user"))
    options = parser.parse_args()

    command = InitAndPurgeRabbitServer(options, quiet)
    return command.run()
