import os
import re
import glob
import sys
import json

def getLatency(filename):
	f = open(filename, "r")
	name = filename[filename.rfind("/") + 1:]
	lines = f.readlines()
	r = re.compile(".*latency *")
	newlist = list(filter(r.match, lines))
	latency = []
	if len(newlist) == 0:
		exit(0)
	for v in newlist:
		res = v[0:-1]
		res = res[res.rfind(" ") + 1:]
		latency += [float(res)]
	count = 0
	for l in latency:
		count += l
	average = count / len(latency)
	print("AVERAGE ", name, " ", average)
	f = open(filename + "_latency", "w")
	f.write("AVERAGE " + str(average))
	f.write("\n")
	f.write("\n".join(map(str, latency)))

def getLatencyDir(directory):
	print(directory)
	for f in glob.glob(directory + "/c*"):
		getLatency(f)

def main():
	if len(sys.argv) <= 1 :
		print("You need to give the directory name by arguments")
		exit(0)
	directory = sys.argv[1]
	getLatencyDir(directory)

def generateLatency():
	#get the log file by args
	if len(sys.argv) <= 1 :
		print("You need to give the configuration file by arguments")
		exit(0)
	config_file = sys.argv[1]
	#Load the config file
	with open(config_file, 'r') as f:
		config = json.load(f)

	prefix = config["server-prefix"]
	servers = [prefix + s for s in config["server"] if s != ""]
	print(servers)
	f = open("latency.conf", "w")
	for i in range(len(servers)):
		for j in range(len(servers)):
			f.write(servers[i] + " " + servers[j] + " 10ms\n")


#generateLatency()
