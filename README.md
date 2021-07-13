# dbdoky.py

This Python script generates a browsable HTML representation of an SQL-Server database. It also pushes those files into a git repository, thus tracking all changes in the database. Just run this script every night.

This script was made to be run on a linux server. 

To get git functionality, you should install git packages and add an SSH key from your account on github or gitlab. If you dont, the script will still work, just without git functionality.
You should create your git-repo before running this script for the first time, as it only accesses already existing repos, but does not create them.

This script uses the following packages, install any that are missing:
* sys
* os
* pyodbc
* codecs
* shutil
* datetime
* git
* re
