Changelog
=========

1.3.1 (unreleased)
------------------

- Nothing changed yet.


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
