from maxcarrot import RabbitServer

import ConfigParser
import argparse
import json
import pymongo
import re
import requests
import sys


class InitAndPurgeRabbitServer(object):  # pragma: no cover

    def __init__(self, options, quiet=False):
        self.quiet = quiet
        self.options = options

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

        def get_exchange_info():
            req = requests.get('{}/api/exchanges/%2F'.format(self.rabbitmq_manage_url), auth=('guest', 'guest'))
            return req.json()

        def delete_old_exchanges(exchanges):
            for exchange in exchanges:
                if re.match(r'[0-9A-Fa-f]{24}', exchange['name']):
                    print 'Deleting ancient exchange {}'.format(exchange['name'])
                    requests.delete(
                        '{}/api/exchanges/%2F/{}'.format(self.rabbitmq_manage_url, exchange['name']),
                        data=json.dumps({'vhost': '/', 'name': exchange['name']}),
                        auth=('guest', 'guest')
                    )

        # Connect to the database
        if not self.cluster in ['true', 'True', '1', 1]:
            db_uri = self.standaloneserver
            conn = pymongo.MongoClient(db_uri)
        else:
            hosts = self.clustermembers
            replica_set = self.replicaset
            conn = pymongo.MongoReplicaSetClient(hosts, replicaSet=replica_set)

        server = RabbitServer(self.rabbitmq_url, declare=True)
        delete_old_exchanges(get_exchange_info())

        for dbname in self.maxserver_names:
            print('')
            print('Initializing and purging RabbitMQ server for "{}" max instance'.format(dbname.split('_')[-1]))
            print('')

            db = conn[dbname]

            # Get all users to create their rabbit exchange and bindings
            users = db.users.find({}, {'_id': 0, 'username': 1, 'talkingIn': 1, 'subscribedTo': 1})

            for user in users:
                server.create_user(user['username'])
                print 'Created exchanges for user {}'.format(user['username'])

                # Create bindings between user read/write exchanges and conversations exchange
                for conversation in user.get('talkingIn', []):
                    server.conversations.bind_user(conversation['id'], user['username'])

                print 'Created {} conversation bindings for user {}'.format(len(user['talkingIn']), user['username'])
                # Create bindings between user read exchange and activity exchange
                created = 0
                for subscription in user.get('subscribedTo', []):
                    context = db.contexts.find_one({'hash': subscription['hash']}, {'_id': 0, 'hash': 1, 'notifications': 1})
                    if context.get('notifications', False):
                        created += 1
                        server.activity.bind_user(context['hash'], user['username'])

                print 'Created {} context bindings for user {}'.format(created, user['username'])
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
