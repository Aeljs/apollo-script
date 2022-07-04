import os
import re
import glob
import sys

def getLatency(filename):
	f = open(filename, "r")
	name = filename[filename.rfind("/") + 1:]
	lines = f.readlines()
	r = re.compile(".*latency *")
	newlist = list(filter(r.match, lines))
	latency = []
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


def main():
	if len(sys.argv) <= 1 :
		print("You need to give the directory name by arguments")
		exit(0)
	directory = sys.argv[1]
	print(directory)
	for f in glob.glob(directory + "/client*"):
		getLatency(f)

main()
