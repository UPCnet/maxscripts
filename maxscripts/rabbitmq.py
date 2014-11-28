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

    def __init__(self, options, quiet=False):
        self.quiet = quiet
        self.options = options

        self.exchanges_by_name = {}
        self.queues_by_name = {}

        self.common = ConfigParser.ConfigParser()
        self.common.read(self.options.commonfile)

        self.instances = ConfigParser.ConfigParser()
        self.instances.read(self.options.instancesfile)

        try:
            self.cluster = asbool(self.common.get('mongodb', 'cluster'))
            self.standaloneserver = self.common.get('mongodb', 'url')
            self.clustermembers = self.common.get('mongodb', 'hosts')
            self.replicaset = self.common.get('mongodb', 'replica_set')

            self.mongo_auth = asbool(self.common.get('mongodb', 'auth'))
            self.mongo_authdb = self.common.get('mongodb', 'authdb')
            self.mongo_username = self.common.get('mongodb', 'username')
            self.mongo_password = self.common.get('mongodb', 'password')
            self.cluster = self.common.get('mongodb', 'username')
            self.rabbitmq_url = self.common.get('rabbitmq', 'server')
            self.rabbitmq_manage_url = self.common.get('rabbitmq', 'manage')
            self.maxserver_names = [maxserver for maxserver in self.instances.sections()]
        except:
            print('You must provide a valid configuration .ini file.')
            sys.exit()

    def add_users(self, users, db, server):
        print "Creating exchanges and bindings"

        for count, user in enumerate(users):
            server.create_user(user['username'])
            print '{}/{} Created exchanges for {}'.format(count, len(users), user['username'])

            count += 1

            conversations = user.get('talkingIn', [])
            # Create bindings between user read/write exchanges and conversations exchange
            for conversation in conversations:
                server.conversations.bind_user(conversation['id'], user['username'])

            if conversations:
                print 'Created {} conversation bindings for user {}'.format(len(conversations), user['username'])

            # Create bindings between user read exchange and activity exchange
            subscriptions = user.get('subscribedTo', [])
            created = 0
            for subscription in subscriptions:
                context = db.contexts.find_one({'hash': subscription['hash']}, {'_id': 0, 'hash': 1, 'notifications': 1})
                if context.get('notifications', False):
                    created += 1
                    server.activity.bind_user(context['hash'], user['username'])
                    context['hash']
            if created:
                print 'Created {} context bindings for user {}'.format(created, user['username'])

    def run(self):

        # Create client without declaring anything

        self.server = RabbitClient(self.rabbitmq_url)

        # Clear all non-native exchanges and queues
        print 'Cleaning up rabbitmq'
        self.server.management.cleanup(delete_all=self.options.deleteall)

        # Create all exchanges and queues defined in spec
        self.server.declare()

        # Refresh
        self.server.management.load_exchanges()
        self.server.management.load_queues()

        # Mongodb connection initialization
        cluster_enabled = self.cluster
        auth_enabled = self.mongo_auth
        mongodb_uri = self.clustermembers if cluster_enabled else self.standalone

        conn = mongodb.get_connection(
            mongodb_uri,
            use_greenlets=True,
            cluster=self.replicaset if cluster_enabled else None)

        # Connect to MongoDB
        if not self.cluster:
            db_uri = self.standaloneserver
            conn = pymongo.MongoClient(db_uri)
        else:
            hosts = self.clustermembers
            replica_set = self.replicaset
            conn = pymongo.MongoReplicaSetClient(hosts, replicaSet=replica_set)

        for maxname in self.maxserver_names:

            print('')
            print('Initializing exchanges and bindings for users in "{}" max instance'.format(dbname))
            print('')
            db = mongodb.get_database(
                conn,
                'max_{}'.format(maxname),
                username=self.mongo_username if auth_enabled else None,
                password=self.mongo_password if auth_enabled else None,
                authdb=self.mongo_authdb if auth_enabled else None)

            print "Getting users list from database"

            # Get all users to create their rabbit exchange and bindings
            query = {} if not self.options.usernamefilter else {'username': self.options.usernamefilter}
            all_users = db.users.find(query, {'_id': 0, 'username': 1, 'talkingIn': 1, 'subscribedTo': 1})
            #unpack lazy results
            all_users = [a for a in all_users]

            batch = []
            tasks = 15 if len(all_users) > 15 else 1
            users_per_task = len(all_users) / tasks

            for task_index in range(tasks + 1):
                start = task_index * users_per_task
                end = (task_index + 1) * users_per_task
                if start < len(all_users):
                    batch.append(all_users[start:end])

            start = time.time()

            #for users in batch:
            #    self.add_users(users, db)

            threads = [gevent.spawn(self.add_users, users, db, RabbitClient(self.rabbitmq_url)) for users in batch]
            gevent.joinall(threads)

            end = time.time()
            total_seconds = end - start
            print 'Total users: ', len(all_users)
            print 'Total seconds: ', total_seconds
            print 'Users/second: ', len(all_users) / total_seconds

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
        '-u', '--user',
        dest='usernamefilter',
        type=str,
        default=None,
        help=("Perform action only for this user"))
    options = parser.parse_args()

    command = InitAndPurgeRabbitServer(options, quiet)
    return command.run()
