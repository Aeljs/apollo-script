import glob
import matplotlib.pyplot as plt

class Result:
	def __init__(self, file, protocolName, conflictRate, clients, theoretical):
		self.file = file[file.rfind("/") + 1 :]
		self.protocolName = protocolName
		self.conflictRate = conflictRate
		self.clients = clients
		self.fastPath = {}
		self.slowPath = {}
		for client, latency in theoretical.items():
			self.fastPath[client] = latency[0]
			self.slowPath[client] = latency[1]

	def __str__(self):
		return f"{self.protocolName}[{self.file}] {self.conflictRate} -> {self.clients}({self.fastPath})({self.slowPath})"

def getLatency(filename):
	config = filename + "/config"
	try:
		f = open(config, "r")
	except:
		return 0,{},0,{}
	prot = f.readline()
	#Get the protocol name
	protName = prot[:-1]

	lines = f.readlines()

	#Get the conflict rate
	c = lines[-1]
	c = c[c.find(" -w"):]
	conflict = c[4:c.find(" ", 4)]
	print(conflict)

	#get all the latency previously calculated for each client
	average = {}
	for d in glob.glob(filename + "/c*"):
		latency = []
		client = d[d.rfind("-")+1:]
		for f in glob.glob(d + "/*_latency"):
			fi = open(f, "r")
			line = fi.readline()
			avg = line[0:-1]
			avg = avg[avg.rfind(" ") + 1:-1]
			latency += [float(avg)]
		if len(latency) != 0:
			#compute the average of each clone of one client and add it in a dictionary
			average[client] = sum(latency) / len(latency)
	name = filename[filename.rfind("/") + 1:]
	print(name)

	try:
		f = open(filename + "/theoretical", "r")
	except:
		return protName, average, conflict,{}

	theoretical = {}
	#get the theoretical value for the fast and slow path
	for l in f.readlines():
		tmp = l.split(" ")
		theoretical[tmp[0]] = [float(tmp[1]), float(tmp[2])]

	print(protName)
	return protName, average, conflict, theoretical


def createGraph(directory):
	print(directory)
	result = []
	for f in glob.glob(directory + "/*"):
		(prot, a, c, t) = getLatency(f)
		#Create an array of each result
		if len(a) != 0:
			result += [Result(f, prot, c, a, t)]

	print(result[0])
	print(result)

	for r in result:
		plt.xticks(rotation=45, ha='right')
		plt.title("Latency for " + r.protocolName + " (conflict rate = " + r.conflictRate + ")")
		plt.xlabel("Clients")
		plt.ylabel("Latency (ms)")
		#plot the result in ms for each client
		plt.plot(r.clients.keys(), r.clients.values(), "o", color="blue", label="practical")
		if len(r.fastPath) != 0:
			#If we have the theoretical value we're supposed to have, we plot it
			plt.plot(r.fastPath.keys(), r.fastPath.values(), "o", color="purple", label="fastPath")
			plt.plot(r.slowPath.keys(), r.slowPath.values(), "o", color="green", label="slowPath")

		plt.legend(loc="upper left")
		plt.savefig(directory + "graph_" + r.file + ".pdf", bbox_inches='tight')
		plt.clf()

	exit(0)


def main():
	directory = "result/"
	createGraph(directory)


if __name__ == '__main__':
	main()
