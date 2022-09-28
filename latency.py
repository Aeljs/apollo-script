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
		return
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
	#print(directory)
	for f in glob.glob(directory + "/*"):
		if os.path.isfile(f) :
			getLatency(f)
		else :
			getLatencyDir(f)

def main():
	if len(sys.argv) <= 1 :
		print("You need to give the directory name by arguments")
		exit(0)
	directory = sys.argv[1]
	getLatencyDir(directory)

if __name__ == '__main__':
	main()
