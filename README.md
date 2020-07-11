# sql-to-room-utility

A utility for converting an sql(ite) schema into Java classes for use with RoomDB.
A successful run of this utility will create the entity classes, simple data access repository classes, a RoomDatabase class and a corresponding data access interface file for each entity.

## Usage
###NB: Tested on Python3 only
Example:
* python create_room_from_schema.py -d sample_app_db.sql -p com.example.cache -c AppDatabase -f app_cache.db
Run the program on the command line with the following arguments:
*  -d DIR, --dir DIR     The directory of the sql schema
*  -p PACKAGE, --package PACKAGE
                        The package name of for the Java files
*  -f DBFILE, --dbfile DBFILE
                        The database file name
*  -c DBCLASS, --dbclass DBCLASS
                        The database class name, without the java extension

## To-Do
* Add unique constraints and indexing
* Add or improve regular expressions

## Known Issues
* Unable to parse non-constant default values for a column; eg. DEFAULT (strftime('%s', now))
* Non primitive data types are assumed to be strings
