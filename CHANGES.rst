Changelog
=========

5.0.9 (unreleased)
------------------

- Nothing changed yet.


5.0.8 (2022-09-14)
------------------

* Try except error delete binding [Pilar Marinas]

5.0.7 (2022-05-24)
------------------

* Try except error delete binding [Pilar Marinas]

5.0.6 (2022-04-29)
------------------

* setuptools and ipdb [Pilar Marinas]

5.0.5 (2022-03-18)
------------------

* Cambios para que funcione la nueva version de mongo [Pilar Marinas]

5.0.4 (2016-07-26)
------------------

* Solucionar get token restricted nou osirisjwt [Pilar Marinas]
* Don't assume default security exists [Carles Bruguera]

5.0.3 (2015-07-01)
------------------

* Improve script to allow sparse indexes, update and cleanup [Carles Bruguera]
* Change script name [Carles Bruguera]
* Refactor security script [Carles Bruguera]
* New max initializer script [Carles Bruguera]

5.0.2 (2015-06-19)
------------------

* Fix newinstance script [Carles Bruguera]
* Remove unused variables [Carles Bruguera]
* Allow multikey indexes on mongodb [Carles Bruguera]

5.0.1 (2015-05-19)
------------------

* Release fix


5.0 (2015-05-19)
----------------

* Fix dependencies and hubcli [Carles Bruguera]
* Avatar loadtest [Carles Bruguera]
* Add maxcli and maxhub cli wrappers [Carles Bruguera]
* Don't initialize cloudapis on tests database [Carles Bruguera]
* Add aglio documentation generator [Carles Bruguera]

4.0.12 (2015-01-29)
-------------------

* Use maxutils.mongodb to acces mongo [Carles Bruguera]
* Last changes, fix things [Victor Fernandez de Alba]
* Added new script for changing the URL of a selected contexts given its starting string [Victor Fernandez de Alba]

4.0.10 (2014-12-01)
-------------------

* Delete unknown exchange bindings [Carles Bruguera]

4.0.9 (2014-12-01)
------------------

* BUG: context bindings were created on conversations [Carles Bruguera]

4.0.8 (2014-12-01)
------------------



4.0.7 (2014-12-01)
------------------

* Log detail of loaded items [Carles Bruguera]

4.0.6 (2014-12-01)
------------------

* Depend on maxutils [Carles Bruguera]

4.0.5 (2014-12-01)
------------------

* Improve rabbitmq script [Carles Bruguera]
* Check existance of bindings before declaring [Carles Bruguera]
* Generalize batch processing [Carles Bruguera]
* Do not use gevent when tasks == 1 [Carles Bruguera]
* Improvements to rabbitmq script [Carles Bruguera]
* Do not start gevent when only one task [Carles Bruguera]
* Check existance of exchange/bindings before declaring [Carles Bruguera]
* Generalize batch process [Carles Bruguera]
* Reduce verbosity to speedup processing [Carles Bruguera]
* Update script to use auth on mongo [Carles Bruguera]

4.0.4 (2014-11-26)
------------------

* Make mongodb initializer auth-enabled [Carles Bruguera]

4.0.3 (2014-11-25)
------------------

* Add timeline loadtest [Carles Bruguera]
* Enable operation with a single user [Carles Bruguera]
* Option to choose between rest and wsgi maxclients [Carles Bruguera]
* New generic rate test scenario [Carles Bruguera]
* test max messages rates scenraio [Carles Bruguera]
* Organize loatest code [Carles Bruguera]
* Move file [Carles Bruguera]
* Fix typo [Carles Bruguera]
* Separate stats building from printing [Carles Bruguera]
* Quiet log mode [Carles Bruguera]
* Dynamic variable testing [Carles Bruguera]
* Option to rate-limiting requests [Carles Bruguera]
* Don't create and destroy eveything in each test [Carles Bruguera]
* Calculate effective rate [Carles Bruguera]
* Finished loadtest [Carles Bruguera]
* WIP: Finish basic test, wrapped in a scenario class [Carles Bruguera]
* WIP: Refactor max load tests on maxscripts package [Carles Bruguera]
* Gevent enabled rabbit populator [Carles Bruguera]
* Move utalkclient to new package [Carles Bruguera]
* Add websocket utalk client [Carles Bruguera]

4.0.2 (2014-06-02)
------------------

* Fix bigmax dependency [Carles Bruguera]

4.0.1 (2014-05-08)
------------------

* Add a parameter to disable selective purge [Carles Bruguera]
* Declare everythin always [Carles Bruguera]
* Don't delete all [Carles Bruguera]
* Adapt to new maxcarrot [Carles Bruguera]

4.0.0 (2014-04-15)
------------------

* Clean all exchanges [Carles Bruguera]
* Declare exchanges [Carles Bruguera]
* Refactor scripts to adapt to new architecture [Carles Bruguera]
* Show more information when a mismatched user found [Carles Bruguera]
* Don't report twice [Carles Bruguera]
* Don't miss N*view_config statements on a method [Carles Bruguera]
* allow custom oauth server [Carles Bruguera]

1.3.3 (2014-02-20)
------------------

* Add mongoindexes script [Carles Bruguera]

1.3.2 (2014-01-21)
------------------

* Fix get_directory_path [Victor Fernandez de Alba]

1.3.1 (unreleased)
------------------

* Disable delete orphaned exchanges [Victor Fernandez de Alba]

1.3 (2013-10-03)
----------------

 * Add mod operations to user and context [Carles Bruguera]
 * Remove setrestricted script [Carles Bruguera]
 * Added script to generate entries in config/instances.ini Removed deprecated setrestricted script [Carles Bruguera]
 * Put sensible defaults to scripts Make rabbitmq init script N-able based on instances.ini [Carles Bruguera]
 * Update to use separated ini files Autocreate also the tests cloudapis info in the database [Carles Bruguera]
 * Missing part in manage url [Carles Bruguera]
 * Change rabbitmq connection url format [Carles Bruguera]
 * Enable use of custom rabbitmq manage port [Carles Bruguera]
 * Fix variable name [Carles Bruguera]
 * Make use of rabbitmq buildout ports [Carles Bruguera]
 * Scripts cleanup [Carles Bruguera]
 * Bump version [Carles Bruguera]
 * Fix stomp endpoint name [Carles Bruguera]
 * Updated cloudapis to match maxbunny.ini [Victor Fernandez de Alba]
 * New script for setting the max restricted user [Victor Fernandez de Alba]
 * make queues durable [Victor Fernandez de Alba]
 * Added restart tweety rule [Victor Fernandez de Alba]
 * Add the default exchange and queue for twitter task processing [Victor Fernandez de Alba]
 * Added maxclient as dependency, added new initialization for maxpush/rabbit [Victor Fernandez de Alba]
 * Updated the initialization of the push queue [Victor Fernandez de Alba]
 * Unified extensions for README and CHANGES. Updated MANIFEST.in [Victor Fernandez de Alba]
 * Initializer for RabbitMQ [Victor Fernandez de Alba]

1.2 (2013-08-05)
----------------

- Updated cloudapis to match maxbunny.ini
- New script for setting the max restricted user
- make queues durable
- Added restart tweety rule
- Add the default exchange and queue for twitter task processing
- Added maxclient as dependency, added new initialization for maxpush/rabbit
- Updated the initialization of the push queue
- Initializer for RabbitMQ


1.1 (2013-06-26)
----------------

- New script for adding and updating the cloudapis settings to the MAXDB.


1.0 (2013-06-13)
----------------

-  Initial version
