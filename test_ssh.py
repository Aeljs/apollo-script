import subprocess
import sys
import threading
import os
import time
import signal
import datetime
import paramiko
import json



config_file = "config"
username = "theo.dupuy"

def launchOnServer(filename, name, role):
    f = open(filename, 'w')
    opt = ""
    if role != "master" :
        opt = " -maddr " + master
    if role == "client":
        opt += " -v " + " -server " + servers[0] + " " + " ".join(client_option[protocol])
    elif role == "server":
        opt += " -port %s " % (7070 + servers.index(name)) + "-addr " + name + " ".join(server_option[protocol])
        print(opt)
    subprocess.run([f"ssh {username}@{name} ./shreplic/bin/shr-{role}" + opt], shell=True, stdout=f, stderr=f)

def main():
    #Load the config file
    with open(config_file, 'r') as f:
        config = json.load(f)
    print(config)

    #result files
    savefiles = config["file_name"] + datetime.datetime.now().strftime("%d-%m-%y;%X") + "/"
    try:
        os.makedirs(savefiles)
    except FileExistsError as e:
        for f in os.listdir(savefiles):
            os.remove(savefiles + f)

    #verify the protocol is correct
    global protocol
    global server_option
    global client_option
    server_option = config["server_option"]
    client_option = config["client_option"]
    protocol = config["protocol"]
    if not protocol in server_option:
        print('Wrong protocole name')
        exit(0)

    #Verify that all names are unique
    for s in config["server"]:
        if s != "" and (s in config["client"] or s == config["master"]):
            print("Servers, master and clients can't be on the same server")
            exit(0)

    prefix = config["server-prefix"]
    global master
    global servers
    master = prefix + config["master"]
    servers = [prefix + s for s in config["server"] if s != ""]
    client = [prefix + s for s in config["client"] if s != ""]


    cluster = {"master" : [master], "server": servers, "client" : client}
    cluster_ssh = {}
    #username = "theo.dupuy"
    path = config["path"]

    print("Build the project...")
    compile = subprocess.run(["make"], stdout=subprocess.PIPE, cwd=path)
    #print((compile.stdout).decode("utf-8"))

    print("rsync the file on the cluster")
    for k, t in cluster.items():
        for v in t :
            subprocess.Popen(f"ssh {username}@{v} mkdir -p shreplic", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            subprocess.run(["rsync", "-r", path + "bin/", username + "@" + v + ":" + config["path_server"]], stdout=subprocess.PIPE)


    for k, t in cluster.items():
        for v in t :
            threading.Thread(target=launchOnServer, name=f"{k}_{v}", args=(savefiles + k + '-' + v, v, k)).start()

    print("launch")



main()
