from maxcarrot import RabbitClient

import ConfigParser
import argparse
import pymongo
import re
import sys
import time

from haigha.connection import Connection


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
            self.cluster = self.common.get('mongodb', 'cluster')
            self.standaloneserver = self.common.get('mongodb', 'url')
            self.clustermembers = self.common.get('mongodb', 'hosts')
            self.replicaset = self.common.get('mongodb', 'replica_set')
            self.rabbitmq_url = self.common.get('rabbitmq', 'server')
            self.rabbitmq_manage_url = self.common.get('rabbitmq', 'manage')
            self.maxserver_names = [maxserver for maxserver in self.instances.sections() if maxserver.startswith('max_')]
        except:
            print('You must provide a valid configuration .ini file.')
            sys.exit()

    def run(self):

        # Create client without declaring anything
        server = RabbitClient(self.rabbitmq_url)

        # Clear all non-native exchanges and queues
        print 'Cleaning up rabbitmq'
        server.management.cleanup(delete_all=True)

        # Create all exchanges and queues defined in spec
        server.declare()

        # Refresh
        server.management.load_exchanges()
        server.management.load_queues()

        # Connect to MongoDB
        if not self.cluster in ['true', 'True', '1', 1]:
            db_uri = self.standaloneserver
            conn = pymongo.MongoClient(db_uri)
        else:
            hosts = self.clustermembers
            replica_set = self.replicaset
            conn = pymongo.MongoReplicaSetClient(hosts, replicaSet=replica_set)

        for dbname in self.maxserver_names:
            print('')
            print('Initializing exchanges and bindings for users in "{}" max instance'.format(dbname.split('_')[-1]))
            print('')
            db = conn[dbname]

            print "Getting users list from database"
            # Get all users to create their rabbit exchange and bindings
            users = db.users.find({}, {'_id': 0, 'username': 1, 'talkingIn': 1, 'subscribedTo': 1})

            #unpack lazy results
            users = [a for a in users]
            start = time.time()

            print "Creating exchanges and bindings"

            for user in users:

                if server.user_publish_exchange(user['username']) not in server.management.exchanges_by_name or \
                   server.user_subscribe_exchange(user['username']) not in server.management.exchanges_by_name:

                    server.create_user(user['username'])
                    print 'Created exchanges for {}'.format(user['username'])

                conversations = user.get('talkingIn', [])
                # Create bindings between user read/write exchanges and conversations exchange
                for conversation in conversations:
                    server.conversations.bind_user(conversation['id'], user['username'])

                print 'Created {} conversation bindings for user {}'.format(len(conversations), user['username'])
                # Create bindings between user read exchange and activity exchange

                subscriptions = user.get('subscribedTo', [])
                created = 0
                for subscription in subscriptions:
                    context = db.contexts.find_one({'hash': subscription['hash']}, {'_id': 0, 'hash': 1, 'notifications': 1})
                    if context.get('notifications', False):
                        created += 1
                        server.activity.bind_user(context['hash'], user['username'])

                print 'Created {} context bindings for user {}'.format(created, user['username'])
            end = time.time()
            total_seconds = end - start

            print 'Total users: ', len(users)
            print 'Total seconds: ', total_seconds
            print 'Users/second: ', len(users) / total_seconds

        server.disconnect()


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
    options = parser.parse_args()

    command = InitAndPurgeRabbitServer(options, quiet)
    return command.run()
