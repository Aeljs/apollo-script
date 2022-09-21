import glob
import matplotlib.pyplot as plt

def getLatency(filename):
	config = filename + "/config"
	try:
		f = open(config, "r")
	except:
		return 0,0,0
	prot = f.readline()
	#Get the protocol name
	protName = prot[:-1]

	lines = f.readlines()

	#Get the conflict rate
	c = lines[-1]
	c = c[c.find(" -w"):]
	conflict = c[4:c.find(" ", 4)]
	print(conflict)

	#get all the latency previously calculated
	latency = []
	for d in glob.glob(filename + "/c*"):
		for f in glob.glob(d + "/*_latency"):
			fi = open(f, "r")
			line = fi.readline()
			avg = line[0:-1]
			avg = avg[avg.rfind(" ") + 1:-1]
			latency += [float(avg)]
	name = filename[filename.rfind("/") + 1:]
	print(name)

	#Average for all the client in the same run
	count = 0
	for l in latency:
		count += l

	average = 0
	if len(latency) != 0:
		average = count / len(latency)
	print(protName)
	return protName, average, conflict


def createGraph(directory):
	print(directory)
	name = "res.txt"
	fi = open(name, "w")

	res = []
	for f in glob.glob(directory + "/*"):
		(prot, a, c) = getLatency(f)
		if a != 0:
			res += [prot + " " + c + " " + str(a) +"\n"]

	#sort the array to have all the protocol grouped by name
	#but also to have the latency ranked to have easily the lowest and the highest
	res.sort()

	dict = {}
	prot = ""
	conflict = ""
	for line in res:
		line = line.split(" ")
		if line[0] != prot:
			prot = line[0]
			dict[prot] = {}
			conflict = ""
		if conflict != line[1] :
			conflict = line[1]
			dict[prot][conflict] = []
		dict[prot][line[1]] += [float(line[2])]

	print(dict)

	fi.write("".join(res))

	#Create the graph associated

	#ytikcs = [k for k in range(10,21)]
	xtikcs = [k for k in range(0,101,20)]

	colors = {}
	lstColor = ['red', 'blue', 'green', 'purple']
	subplot = 0
	for prot, conflict in dict.items():
		subplot += 1
		if colors.get(prot) == None :
			colors[prot] = lstColor[len(colors)]
		for c, latency in conflict.items():
			plt.subplot(1, len(dict), subplot)

			#plt.plot([int(c)], sum(latency) / len(latency), "o")
			plt.bar(int(c), latency[-1]-latency[0], 1.5, bottom=latency[0], color=colors[prot])
			plt.title(prot)
		#	plt.yticks(ytikcs)
			plt.xticks(xtikcs)

	plt.savefig(directory + "graph.pdf", bbox_inches='tight')


def main():
	directory = "result/"
	createGraph(directory)


if __name__ == '__main__':
	main()
