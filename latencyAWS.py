import requests

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
			latency[reg][r] = t[i + 2:e]

	#print(latency)
	return latency

def generateLatency(servers, clients, region, latency):
	print(servers)
	f = open("latency.conf", "w")
	servRegion = {}
	clientRegion = {}
	for i, s in enumerate(servers):
		servRegion[s] = region[i % len(region)]
	for i, s in enumerate(clients):
		clientRegion[s] = region[i % len(region)]

	for src in servers:
		for dst in servers:
			f.write(src + " " + dst + " " + latency[servRegion[src]][servRegion[dst]] + "ms\n")
		for dst in clients:
			f.write(src + " " + dst + " " + latency[servRegion[src]][clientRegion[dst]] + "ms\n")
	for src in clients:
		for dst in servers:
			f.write(src + " " + dst + " " + latency[clientRegion[src]][servRegion[dst]] + "ms\n")

	print(servRegion)

if __name__ == '__main__':
	getLatencyAws()
