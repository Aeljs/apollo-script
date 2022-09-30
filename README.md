# Script for the Apollo cluster

    python3 test_ssh.py config_file

## Configuration file
[Example file](config_template.json)

[Example gbroadcast file](example/gbroadcast.json)

[Example shreplic file](example/shreplic.json)

The configuration file is a json file, you need to specify :
- The name of the server where the master, the servers and the clients will run. You can add the `server-prefix` to have less to change. You can leave empty string, it will not harm the script. The label `client` is a dictionary with the number of clone you want to launch, it doesn't count the primary client in it.
- The array `conf_latency` specify if you want to use specific latency with specific AWS region. The region code are [here](https://www.cloudping.co/grid/p_90/timeframe/1Y) and you can have more precision and launch it by hand with the script [latency AWS](latencyAWS.py)
- The number of request of each client, or the time during the client would send commands (leave `request_time` empty if you want to use the number of request)
- The conflict and writing percentage
- `quorum_file` is where the quorum file is to pass it by argument. Do not copy a quorum file to the servers
- `quorum_conf` allow you to copy a quorum conf file to the server if true, if false, fetch the quorum file we need to use to compute the theoretical latency.
- The protocol name you want to run, and the options for it. Even if you don't have any other options to add you must add it to `server_option` and to `client_option`
- `conf_file` where you want to have your latency.conf
- `directory_name` is the name of the directory where the code will end up
- `exec_prefix` will help to launch and kill all the process (for example for shreplic it will be shr, gbr for gbroadcast...)
- `git` will be true if you want to use the git to be sure to have a stable version, if it's false you will synchronize the files from your computer
- `git_name` will help to git clone, will only be used if git is true
- `path_directory` is where to code is on your computer, will only be needed if git is false
- `clone_filename` is if you clone a client where the result should be store ON the cluster. The files will be download at the end of the execution in the directory you gave for the label `file_name`
- The `file_name` is where you want to keep the results of the run. Each launch will be separate in a sub-directory with the date.
- The username of the server for the connection through ssh
- The directory where you have a ssh key to git clone/git pull
- `getAndCompile` is if you want to git clone/git pull and compile each time you launch, needed to be true if you use servers you never used before
- The option `latency` will compute and save the average latency each client experimented (you can do it by hand after with the script [latency](latency.py))

## Quorum & Latency conf
To generate the quorum conf file and the latency conf file you can launch [latencyAWS](latencyAWS.py) with the [config file](config_template.json)

## Compute results latency
Launch [latency](latency.py) with the directory you want to have the latency result. Using `file_name` will compute the average latency for all your result. The average latency will be compute for each clone and will be store in a file named `c*_latency`.

## Draw a beautiful graph
Launch [graph](graph.py) to create a graph for each result's directory you have. By default it will search a directory name `result/`.
