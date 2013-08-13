from maxclient import MaxClient

import argparse
import ConfigParser
import json
import os
import sys


class InitRestrictedSecuritySecret(object):  # pragma: no cover

    def __init__(self, options, quiet=False):
        self.quiet = quiet
        self.options = options

        self.config = ConfigParser.ConfigParser()
        self.config.read(self.options.configfile)

        try:
            self.oauth_server = self.config.get('app:main', 'max.oauth_server')
            self.maxserver = self.config.get('app:main', 'max.server')
            self.config_dir = self.config.get('app:main', 'config_directory')
        except:
            print('You must provide a valid configuration .ini file.')
            sys.exit()

    def run(self):
        # Check if the restricted user and token is set
        settings_file = '{}/.max_restricted'.format(self.config_dir)
        if os.path.exists(settings_file):
            settings = json.loads(open(settings_file).read())
        else:
            settings = {}

        if 'token' not in settings or 'username' not in settings:
            maxclient = MaxClient(url=self.maxserver, oauth_server=self.oauth_server)
            settings['token'] = maxclient.login()
            settings['username'] = maxclient.getActor()

            open(settings_file, 'w').write(json.dumps(settings, indent=4, sort_keys=True))

        print("Initialized restricted security settings.")


def main(argv=sys.argv, quiet=False):  # pragma: no cover
    description = "Initialize restricted security settings."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-c', '--config',
                      dest='configfile',
                      type=str,
                      required=True,
                      help=("Configuration file (e.g max.ini)"))
    options = parser.parse_args()

    command = InitRestrictedSecuritySecret(options, quiet)
    return command.run()
