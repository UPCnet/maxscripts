from maxclient import MaxClient

import argparse
import ConfigParser

import sys


class AddNewMaxInstance(object):  # pragma: no cover

    def __init__(self, options, quiet=False):
        self.quiet = quiet
        self.options = options

        self.common = ConfigParser.ConfigParser()
        self.common.read(self.options.commonfile)

        self.instances = ConfigParser.ConfigParser()
        self.instances.read(self.options.instancesfile)

        try:
            self.maxserver_names = [maxserver.split('_')[-1] for maxserver in self.instances.sections() if maxserver.startswith('max_')]

        except:
            print('You must provide a valid configuration .ini file.')
            sys.exit()

    def run(self):

        print("")
        print(" Welcome, You're about to add a new max instance to {}.".format(self.options.instancesfile))
        print(" Please tell me:")
        print("")

        valid_new_section = False
        max_name = None
        while not valid_new_section:
            if max_name is not None:
                max_name = raw_input("  > Ooops!, there is already an instance with this name, try again:")
            else:
                max_name = raw_input("  > The name of the max instance (without max_ prefix): ")
            new_section_name = 'max_{}'.format(max_name)
            valid_new_section = not self.instances.has_section(new_section_name)

        max_server = raw_input("  > The base url of the max server [{}/{{name}}]: ".format(self.common.get('max', 'server')))
        if not max_server:
            max_server = '{}/{}'.format(self.common.get('max', 'server'), max_name)

        max_oauth_server = raw_input("  > The base url of the oauth server [{}/{{name}}]: ".format(self.common.get('oauth', 'server')))
        if not max_oauth_server:
            max_oauth_server = '{}/{}'.format(self.common.get('oauth', 'server'), max_name)

        max_hashtag = raw_input("  > The hashtag to track on twitter (without #): ")
        max_user = raw_input("  > The restricted user: ")

        max_client = MaxClient(url=max_server, oauth_server=max_oauth_server)
        sys.stdout.write("  > ")
        sys.stdout.flush()
        max_token = max_client.login(max_user)

        self.instances.add_section(new_section_name)
        self.instances.set(new_section_name, 'hashtag', max_hashtag)
        self.instances.set(new_section_name, 'server', max_server)
        self.instances.set(new_section_name, 'oauth_server', max_oauth_server)
        self.instances.set(new_section_name, 'restricted_user', max_user)
        self.instances.set(new_section_name, 'restricted_user_token', max_token)

        self.instances.write(open(self.options.instancesfile, 'w'))

        print("")
        print(" Changes written to {}".format(self.options.instancesfile))
        print("")


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

    command = AddNewMaxInstance(options, quiet)
    return command.run()

