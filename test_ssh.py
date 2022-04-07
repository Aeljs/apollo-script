import subprocess
import sys
import threading
import os
import time
import signal
import datetime
import paramiko
import json
import re
import random


config_file = "config"
username = "theo.dupuy"
ssh_key = "/home/theodupuy/.ssh/"

def launchOnServer(filename, name, role):
    f = open(filename, 'w')
    opt = ""
    if role != "master" :
        opt = " -maddr " + master
    if role == "client":
        opt += " -v " + " -server " + random.choice(servers) + " " + " ".join(client_option[protocol])
        print(opt)
    elif role == "server":
        opt += " -port %s " % (7070 + servers.index(name)) + "-addr " + name + " " + " ".join(server_option[protocol])
        print(opt)
    elif role == "master":
        opt += " -N %s" % len(servers)
        print(opt)
    subprocess.run([f"ssh {username}@{name} ./shreplic/bin/shr-{role}" + opt], shell=True, stdout=f, stderr=f)


def stopAllProcess(sig, frame):
    #Load the config file
    with open(config_file, 'r') as f:
        config = json.load(f)

    prefix = config["server-prefix"]
    master = prefix + config["master"]
    servers = [prefix + s for s in config["server"] if s != ""]
    client = [prefix + s for s in config["client"] if s != ""]

    cluster = {"master" : [master], "server": servers, "client" : client}
    path = config["path"]

    print("kill the process on the cluster")
    for k, t in cluster.items():
        for v in t :
            res = subprocess.run([f"ssh {username}@{v} ps -C shr-{k} -o pid="], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                pid = res.stdout
                subprocess.run([f"ssh {username}@{v} kill -9 {int(pid)}"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception as e:
                print(pid)

    sys.exit(0)


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
    path = config["path"]

    if config["gitAndCompile"] :
        print("clone and compile the file on the cluster")
        for k, t in cluster.items():
            for v in t :
                #Get the ssh key and copy them to the server
                subprocess.run(["rsync", "-r", ssh_key, username + "@" + v + ":" + "~/.ssh/"], stdout=subprocess.PIPE)

                #Start a ssh session
                ssh_client = paramiko.client.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(v, username=username)
                _stdin, _stdout,_stderr = ssh_client.exec_command("cd shreplic")
                #check if there already a directory
                if _stdout.channel.recv_exit_status() == 1 :
                    #clone if not
                    _stdin, _stdout,_stderr = ssh_client.exec_command("git clone git@github.com:vonaka/shreplic.git")
                    print(v + " : " + _stdout.read().decode())
                else :
                    #pull
                    _stdin, _stdout,_stderr = ssh_client.exec_command("cd shreplic && git pull")
                    print(v + " : " + _stdout.read().decode())
                #Compile the programm
                _stdin, _stdout,_stderr = ssh_client.exec_command("cd shreplic && make")
                print(v + " : " + _stdout.read().decode())

                ssh_client.close()
    else :
        print("Clone and compile : Skip")

    print("Launch")

    for k, t in cluster.items():
        for v in t :
            if k != "client":
                threading.Thread(target=launchOnServer, name=f"{k}_{v}", args=(savefiles + k + '-' + v, v, k)).start()
            if k == "master":
                time.sleep(2)

    print("Waiting for the servers to connect")
    signal.signal(signal.SIGINT, stopAllProcess)

    time.sleep(1)
    while True:
        f = open(savefiles + "server-" + servers[0], "r")
        lines = f.readlines()
        r = re.compile(".*Waiting for client connections*")
        newlist = list(filter(r.match, lines))
        if len(newlist) != 0 :
            print("Server settle")
            break;
        time.sleep(1)

    #Launch clients
    print("Launch clients")
    for v in client :
        threading.Thread(target=launchOnServer, name=f"client_{v}", args=(savefiles + "client-" + v, v, "client")).start()

    print("Main thread done")

main()
