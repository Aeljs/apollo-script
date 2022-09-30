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
import atomics
import shutil

from latency import getLatency, getLatencyDir
from latencyAWS import getLatencyAws, generateLatency, generateQuorum, computeTheoreticalLatencyWithQFile
from graph import createGraph

def getTheLogFile(name):
	if client_clone[client.index(name)] != 0 :
		save_clone = savefiles + "c-" + name + "/"
		os.makedirs(save_clone)
		subprocess.run(["rsync -r " + username + "@" + name + ":" + clone_filename + " " + save_clone], shell=True, stdout=subprocess.PIPE)
		subprocess.run([f"ssh {username}@{name} rm {clone_filename}*"], shell=True, stdout=subprocess.PIPE)


def launchOnServer(filename, name, role):
	f = open(filename, 'a')
	opt = ""
	if role != "master" :
		opt = " -maddr " + master
	if role == "client":
		if request_time != "":
			opt += " -t " + request_time
		else :
			opt += " -q %s " % request_number
		opt += " -v " + "-server " + servers[client.index(name) % len(servers)] + " -c %s -w %s " % (conflict_percentage, writing_percentage)
		if client_clone[client.index(name)] != 0 :
			opt += "-clone %s " % client_clone[client.index(name)]
			opt += "-logf " + clone_filename + "c "
		opt += (" ".join(client_option[protocol])).replace("<nb-servers>", str(len(servers)))
		print(opt)
	elif role == "server":
		opt += " -port %s " % (7070 + servers.index(name)) + "-addr " + name + " " + " ".join(server_option[protocol])
		if quorum_file != "":
			opt += " -qfile " + quorum_file
		print(opt)
	elif role == "master":
		opt += " -N %s" % len(servers)
		print(opt)

	c = open(savefiles + "config", 'a')
	command = f"\"./{directory_name}/bin/{exec_prefix}-{role}" + opt + '\"'
	c.write(command + "\n")
	c.close()

	completed = subprocess.run([f"ssh {username}@{name} " + command], shell=True, stdout=f, stderr=f)
	if role == "client":
		getTheLogFile(name)
		if latency:
			if client_clone[client.index(name)] != 0 :
				getLatencyDir(savefiles + "c-" + name + "/")
			else:
				getLatency(filename)
		else:
			print("Client %s has finished" % name)

		count.inc()
		if count.load() == len(client) :
			stopAllProcess()
			#os.kill(os.getpid(), signal.SIGINT)

def stopAllProcess():
	#Load the config file
	with open(config_file, 'r') as f:
		config = json.load(f)

	prefix = config["server-prefix"]
	master = prefix + config["master"]
	servers = [prefix + s for s in config["server"] if s != ""]
	client = [prefix + s for s in config["client"] if s != ""]

	cluster = {"master" : [master], "server": servers, "client" : client}

	print("kill the process on the cluster")
	for k, t in cluster.items():
		for v in t :
			res = subprocess.run([f"ssh {username}@{v} ps -C {exec_prefix}-{k} -o pid="], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			try:
				pid = res.stdout
				subprocess.run([f"ssh {username}@{v} kill -9 {int(pid)}"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			except Exception as e:
				print(pid)

def sigCatch(sig, frame):
	stopAllProcess()
	sys.exit(0)

def main():
	#get the log file by args
	if len(sys.argv) <= 1 :
		print("You need to give the configuration file by arguments")
		exit(0)
	else:
		global config_file
		config_file = sys.argv[1]
	#Load the config file
	with open(config_file, 'r') as f:
		config = json.load(f)
	print(config)


	#verify the protocol is correct
	global protocol
	global server_option
	global client_option
	global request_number
	global request_time
	global conflict_percentage
	global writing_percentage

	server_option = config["server_option"]
	client_option = config["client_option"]
	request_number = config["request_number"]
	request_time = config["request_time"]
	conflict_percentage = config["conflict_percentage"]
	writing_percentage = config["writing_percentage"]
	protocol = config["protocol"]
	if not protocol in server_option:
		print('Wrong protocole name')
		exit(0)

	#Verify that all names are unique
	for s in config["server"]:
		if s != "" and s == config["master"]:
			print("Servers and master can't be on the same server")
			exit(0)

	prefix = config["server-prefix"]
	global master
	global servers
	global client
	global client_clone
	master = prefix + config["master"]
	servers = [prefix + s for s in config["server"] if s != ""]
	client = [prefix + s for s in config["client"] if s != ""]
	client_clone = [x for s, x in config["client"].items() if s != ""]

	global quorum_file
	quorum_file = config["quorum_file"]
	global clone_filename
	clone_filename = config["clone_filename"]
	global latency
	latency = config["latency"]
	global username
	username = config["username_server"]
	ssh_key = config["ssh_dir"]
	global cluster
	cluster = {"master" : [master], "server": servers, "client" : client}
	#Get the proper name
	global directory_name
	global exec_prefix
	directory_name = config["directory_name"]
	exec_prefix = config["exec_prefix"]
	git_name = config["git_name"]

	if config["getAndCompile"] :
		if config["git"]:
			print("clone and compile the file on the cluster")
			for k, t in cluster.items():
				for v in t :
					#Get the ssh key and copy them to the server
					subprocess.run(["rsync", "-r", ssh_key, username + "@" + v + ":" + "~/.ssh/"], stdout=subprocess.PIPE)

					#Start a ssh session
					ssh_client = paramiko.client.SSHClient()
					ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
					ssh_client.connect(v, username=username)
					_stdin, _stdout,_stderr = ssh_client.exec_command("cd " + directory_name)
					#check if there already a directory
					if _stdout.channel.recv_exit_status() == 1 :
						#clone if not
						_stdin, _stdout,_stderr = ssh_client.exec_command("git clone " + git_name)
						print(v + " : " + _stdout.read().decode())
					else :
						#pull
						_stdin, _stdout,_stderr = ssh_client.exec_command("cd " + directory_name + " && git pull")
						print(v + " : " + _stdout.read().decode())
					#Compile the programm
					_stdin, _stdout,_stderr = ssh_client.exec_command("cd " + directory_name + " && make")
					print(v + " : " + _stdout.read().decode())

					if k == "client":
						#Create the directory for the clone log
						_stdin, _stdout,_stderr = ssh_client.exec_command("mkdir -p " + clone_filename)
						print(v + " : " + _stdout.read().decode())

					ssh_client.close()
		else:
			print("rsync")
			for k, t in cluster.items():
				for v in t :
					subprocess.run(["rsync -r "  + config["path_directory"] + " " + username + "@" + v + ":" + directory_name], shell=True, stdout=subprocess.PIPE)
					#Start a ssh session
					ssh_client = paramiko.client.SSHClient()
					ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
					ssh_client.connect(v, username=username)

					#Compile the programm
					_stdin, _stdout,_stderr = ssh_client.exec_command("cd " + directory_name + " && make")
					print(v + " : " + _stdout.read().decode())

					if k == "client":
						#Create the directory for the clone log
						_stdin, _stdout,_stderr = ssh_client.exec_command("rm -r " + clone_filename)
						_stdin, _stdout,_stderr = ssh_client.exec_command("mkdir -p " + clone_filename)
						print(v + " : " + _stdout.read().decode())
					ssh_client.close()

	else :
		print("Clone and compile : Skip")
	#Latency conf AWS
	conf_latency = config["conf_latency"]
	if len(conf_latency) != 0:
		print(conf_latency)

		aws = getLatencyAws()
		with open("awsRegion.json", "w") as outfile:
			json.dump(aws, outfile, ensure_ascii=False, indent=4)
		generateLatency(servers, client, conf_latency, aws)

		conf_file = config["conf_file"]
		for ser in servers :
			subprocess.run(["rsync", "-r", "latency.conf", username + "@" + ser + ":" + conf_file], stdout=subprocess.PIPE)

	quorum_suffix = quorum_file[quorum_file.rfind("/") + 1:]
	#We copy the quorum file to the server, or copy the quorum file from the server
	if config["quorum_conf"]:
		#If we have a conf latency we compute the best quorum
		if len(conf_latency) != 0:
			generateQuorum(config_file, aws)

		for ser in servers :
			subprocess.run(["rsync", "-r", quorum_suffix, username + "@" + ser + ":" + quorum_file], stdout=subprocess.PIPE)
	else:
		for ser in servers :
			subprocess.run(["rsync", "-r", username + "@" + ser + ":" + quorum_file, quorum_suffix], stdout=subprocess.PIPE)

def launch():
	#Load the config file
	with open(config_file, 'r') as f:
		config = json.load(f)
	print(config)

	#result files
	global savefiles
	global result
	result = config["file_name"]
	savefiles = config["file_name"] + datetime.datetime.now().strftime("%d-%m-%y_%X_") + config["directory_name"] + "/"
	print(savefiles)
	try:
		os.makedirs(savefiles)
	except FileExistsError as e:
		for f in os.listdir(savefiles):
			os.remove(savefiles + f)

	global count
	count = atomics.atomic(width=4, atype=atomics.INT)

	print("Launch")
	signal.signal(signal.SIGINT, sigCatch)

	c = open(savefiles + "config", 'a')
	c.write(config["protocol"] + "\n")
	c.write(" ".join(config["conf_latency"]) + "\n")
	c.close()

	shutil.copyfile("awsRegion.json", savefiles + "awsRegion.json")

	for k, t in cluster.items():
		for v in t :
			if k != "client":
				threading.Thread(target=launchOnServer, name=f"{k}_{v}", args=(savefiles + k + '-' + v, v, k)).start()
			if k == "master":
				time.sleep(2)

	print("Waiting for the servers to connect")

	time.sleep(1)
	for k, t in cluster.items():
		for v in t :
			if k == "server":
				while True:
					f = open(savefiles + "server-" + v, "r")
					lines = f.readlines()
					r = re.compile(".*Waiting for client connections*")
					newlist = list(filter(r.match, lines))
					if len(newlist) != 0 :
						print("Server settle")
						break;
					time.sleep(1)

	#Launch clients
	print("Launch clients")
	cThread = []
	for v in client :
		cThread += [threading.Thread(target=launchOnServer, name=f"client_{v}", args=(savefiles + "client-" + v, v, "client"))]

	for t in cThread:
		t.start()

	with open("awsRegion.json", 'r') as f:
		aws = json.load(f)
	c = open(savefiles + "config", 'r')
	c.readline()
	region = c.readline()[:-1].split(" ")
	print("region")
	print(region)
	c = open(savefiles + "theoretical", 'a')
	for v in client :
		fp, sp = computeTheoreticalLatencyWithQFile(servers, client, v, aws, region)
		c.write(v + " " + str(fp) + " " + str(sp) + "\n")

	c.close()


	print("Main thread done")

	for t in cThread:
		t.join()

main()
for _ in range(1):
	launch()

createGraph("result/")
