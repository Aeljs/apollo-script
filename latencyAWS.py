import requests
import sys
import json

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

def generate(file, latency):
	#Load the config file
	with open(file, 'r') as f:
		config = json.load(f)
	prefix = config["server-prefix"]
	servers = [prefix + s for s in config["server"] if s != ""]
	client = [prefix + s for s in config["client"] if s != ""]
	region = config["conf_latency"]
	if len(region) != 0:
		generateLatency(servers, client, region, latency)


if __name__ == '__main__':
	latency = getLatencyAws()
	if len(sys.argv) <= 1 :
		print("You need to give the configuration file by arguments")
		exit(0)
	else:
		generate(sys.argv[1], latency)
