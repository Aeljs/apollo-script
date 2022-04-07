# Script for the Apollo cluster

## Configuration file
[Example file](config_template.json)

The configuration file is a json file, you need to specify :
- The name of the server where the master, the servers and the clients will run. You can add the `server-prefix` to have less to change. You can leave empty string, it will not harm the script. The label `client` is a dictionary with the number of clone you want to launch, it doesn't count the primary client in it.
- The number of request of each client
- The protocol name you want to run, and the options for it. Even if you don't have any other options to add you must add it to `server_option` and to `client_option`
- `clone_filename` is if you clone a client where the result should be store ON the cluster. The files will be download at the end of the execution in the directory you gave for the label `file_name`
- The `file_name` is where you want to keep the results of the run. Each launch will be separate in a sub-directory with the date.
- `gitAndCompile` is if you want to git clone/git pull and compile each time you launch, needed to be true if you use servers you never used before
