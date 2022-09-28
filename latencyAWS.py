import requests
import sys
import json
import itertools

url = "https://www.cloudping.co/grid/p_90/timeframe/1Y#"

def getLatencyAws():
	r = requests.get(url)
	text = r.text
	text = text[text.find("<table"):text.rfind("</table")]

	latency = {}

	#Get all the region
	region = []
	index = 0
	for _ in range(text.count('<th scope="col"')):
		index = text.find('<th scope="col"', index + 1)
		r = text[text.find("em>", index) + 3:text.find("</", index)]
		region += [r]

	print(region)

	text = text[text.find("tbody"):]

	index = 0
	end = len(text)
	#Loop on the html array et get each value
	for _ in range(text.count('<tr>')):
		index = text.find('<tr', index + 1)
		end = text.find("</tr>", index)
		t = text[index:end]
		reg = t[t.find("em>") + 3:t.find("</em")]
		latency[reg] = {}
		i = t.find("</em")
		for r in region:
			i = t.find('">', i + 1)
			e = t.find("</td", i + 1)
			latency[reg][r] = float(t[i + 2:e])

	return latency

def getRegion(servers, clients, region):
	servRegion = {}
	clientRegion = {}
	for i, s in enumerate(servers):
		servRegion[s] = region[i % len(region)]
	for i, s in enumerate(clients):
		clientRegion[s] = region[i % len(region)]

	return servRegion, clientRegion


def generateLatency(servers, clients, region, latency):
	f = open("latency.conf", "w")

	servRegion, clientRegion = getRegion(servers, clients, region)
	for src in servers:
		for dst in servers:
			f.write(src + " " + dst + " " + str(latency[servRegion[src]][servRegion[dst]]) + "ms\n")
		for dst in clients:
			f.write(src + " " + dst + " " + str(latency[servRegion[src]][clientRegion[dst]]) + "ms\n")
	for src in clients:
		for dst in servers:
			f.write(src + " " + dst + " " + str(latency[clientRegion[src]][servRegion[dst]]) + "ms\n")

	print(servRegion)

def getServerClient(file):
	#Load the config file
	with open(file, 'r') as f:
		config = json.load(f)
	prefix = config["server-prefix"]
	servers = [prefix + s for s in config["server"] if s != ""]
	clients = [prefix + s for s in config["client"] if s != ""]
	region = config["conf_latency"]
	return servers, clients, region

def generate(file, latency):
	servers, clients, region = getServerClient(file)
	if len(region) != 0:
		generateLatency(servers, clients, region, latency)

def max(a, b):
	if a > b:
		return a
	return b

def min(a, b):
	if a < b:
		return a
	return b

def computeTheoreticalLatency(server, client, origin, latency, region, fQuorum, leader):
	servRegion, clientRegion = getRegion(server, client, region)

	#We get compute each latency going from the leader to the server
	leaderServers = {}
	for s in server:
		leaderServers[s] = latency[servRegion[leader]][servRegion[s]] / 2

	#We get compute each latency going from the origin to the server
	originServers = {}
	#and the latency going from the server to the origin
	serversOrigin = {}
	for s in server:
		originServers[s] = latency[clientRegion[origin]][servRegion[s]] / 2
		serversOrigin[s] = latency[servRegion[s]][clientRegion[origin]] / 2

	#We get the maximal latency for getting a response from the quorum
	fastPath = 0
	for s in fQuorum:
		#We send the broadcast and we receive the propose
		maxFast = originServers[s] + serversOrigin[s]
		fastPath = max(fastPath, maxFast)

	slowArray = []
	for s in server:
		if s == leader or s == origin :
			continue
		#we get the maximal between receiving something from the leader (origin to leader + leader to server)
		#and receiving the broadcast (origin to server)
		#to that we add the response (server to origin)
		maxSlow = max(originServers[leader] + leaderServers[s], originServers[s]) + serversOrigin[s]
		slowArray += [maxSlow]

	slowArray.sort()
	originLeader = originServers[leader] + serversOrigin[leader]
	# we need to keep the servers where the latency is minimal
	# we need to have the maximum of theses servers (everything arrived before it)
	# the numbers of servers must be the size of a slow quorum, minus the leader
	maxQuorum = len(server) // 2
	slowPath = max(slowArray[maxQuorum], originLeader)

	return fastPath, slowPath

def computeTheoreticalLatencyWithQFile(server, client, origin, latency, region):
	fQuorum, leader = getQuorum("quorum.json")
	return computeTheoreticalLatency(server, client, origin, latency, region, fQuorum, leader)

#file = quorum file
def getQuorum(file):
	#Load the config file
	with open(file, 'r') as f:
		config = json.load(f)
	print(config)
	print(config["addr"][0])
	return config["addr"][0], config["leadersAddr"][0]


def findsubsets(servers, size):
    return list(itertools.combinations(servers, size))

def generateQuorum(file, latency):
	servers, clients, region = getServerClient(file)

	subset = findsubsets(servers, 3)

	bestLatency = -1
	bestQuorum = []
	bestLeader = ""
	for s in subset:
		for leader in s:
			lat = []
			for origin in clients:
				fp, sp = computeTheoreticalLatency(servers, clients, origin, latency, region, s, leader)
				lat += [min(fp, sp)]
			tmp = sum(lat) / len(lat)
			if bestLatency == -1 or bestLatency > tmp:
				bestLatency = tmp
				bestQuorum = s
				bestLeader = leader

	j = {"nbQuorums": 0, "addr":[bestQuorum], "leadersAddr":[bestLeader]}

	with open("quorum.json", "w") as outfile:
		json.dump(j, outfile, ensure_ascii=False, indent=4)


if __name__ == '__main__':
	latency = getLatencyAws()
	if len(sys.argv) <= 1 :
		print("You need to give the configuration file by arguments")
		exit(0)
	else:
		generate(sys.argv[1], latency)
		generateQuorum(sys.argv[1], latency)
