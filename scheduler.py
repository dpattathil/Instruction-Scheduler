import sys

#easier ways to check which type of instruction we're looking at
math = set(['add', 'sub', 'mult', 'div'])
address = set(['loadAI', 'storeAI', 'outputAI'])

#dict to map instruction types to their cycle counts
cycles = {
	'loadI' : 1, 
	'loadAI' : 5, 
	'storeAI' : 5,
	'add' : 1,
	'sub' : 1,
	'mult' : 3,
	'div' : 3,
	'outputAI' : 5
}

#object to store instructions
class instr:
	def __init__(self, opcode, field1, field2, field3, cost):
		self.opcode = opcode
		self.field1 = field1
		self.field2 = field2
		self.field3 = field3
		self.cycles = cost

if len(sys.argv) != 4:
	print("You have inputted incorrect parameters for the scheduler.\n")

fileName = sys.argv[2]

f = open(fileName, 'r')

instructions = []
input_ = []
#reads all the lines of a file
for line in f:
	#removing symbols that are not opcodes or registers/mem locations
	input_.append(line)
	line = line.replace("=>", " ")
	line = line.replace(",", " ")
	line = line.split()
	if len(line) == 3:
		line.append(None)
	line.append(cycles[line[0]])
	instruction = instr(*line)
	instructions.append(instruction)

#time to build the actual dependence graph

leaves = set()
parents = {}
children = {}
for i in range(len(instructions)):
	parents[i] = set()
	children[i] = set()

#gives the parameters left of the '=>'
def leftparams(instruction):
	op = instruction.opcode
	if op == 'loadI':
		return None
	if (op in math):
		return [instruction.field1, instruction.field2]
	if (op == 'outputAI') or (op == 'loadAI'):
		return (instruction.field1, instruction.field2)
	if op == 'storeAI':
		return instruction.field1

#gives the parameters right of the '=>'
def rightparams(instruction):
	op = instruction.opcode
	if op == 'loadI':
		return instruction.field2
	if (op in math) or (op == 'outputAI') or (op == 'loadAI'):
		return instruction.field3
	if op == 'storeAI':
		return (instruction.field2, instruction.field3)

#for inst in instructions:
#	print(inst.opcode + "\t" +  inst.field1 + "\t" +  inst.field2 + "\t" +  inst.field3 + "\tcycles: " + str(inst.cycles))

for i in range(len(instructions)):
	
	inst_i = instructions[i]
	op_i = inst_i.opcode

	#sets all inst's related to loading r0 as children of this inst
	if(op_i == 'loadI') and (inst_i.field2 == 'r0'):
		for j in range(len(instructions)):
			inst_j = instructions[j]
			op_j = inst_j.opcode
			if(op_j in address):
				parents[j].add(i)
				children[i].add(j)
		leaves.add(i)
		continue
	
	#links all of the output's in order to maintain output order
	if(op_i == 'outputAI'):
		for j in range(i+1, len(instructions)):
			inst_j = instructions[j]
			op_j = inst_j.opcode
			if(op_j  == 'outputAI'):
				parents[j].add(i)
				children[i].add(j)
				break

	#iterate through the rest of the inst's and check for dependence
	for j in range(i+1, len(instructions)):
		inst_j = instructions[j]
		op_j = inst_j.opcode
		if op_j == 'loadI':
			continue
		if op_j in math:
			if rightparams(inst_i) in leftparams(inst_j):
				parents[j].add(i)
				children[i].add(j)
				break
		if rightparams(inst_i) == leftparams(inst_j):
			parents[j].add(i)
			children[i].add(j)
			break

	#iterate through previous inst's and check for anti dependence
	for j in reversed(range(0, i)):
		inst_j = instructions[j]
		op_j = inst_j.opcode
		if op_j == 'loadI':
			continue
		if op_j in math:
			if rightparams(inst_i) in leftparams(inst_j):
				parents[i].add(j)
				children[j].add(i)
				break
		if rightparams(inst_i) == leftparams(inst_j):
			parents[i].add(j)
			children[j].add(i)
			break 

	#if this item has no parents, add it to the leaves set
	if parents[i] == set():
		leaves.add(i)

#print("leaves: " + str(leaves))
#print("parents: " + str(parents))
#print("children: " + str(children))

#set values at each node to their cycle count
h = {}
for i in range(len(instructions)):
	h[i] = cycles[instructions[i].opcode]

#find the final statement in this block
for key, value in children.items():
	if value == set():
		root = key
		break

#find longest latency paths from every single node
queue = [root]
while queue != []:
	item = queue.pop(0)
	for parent in parents[item]:
		queue.append(parent)
	for child in children[item]:
		h[item] = max(h[item], h[child] + cycles[instructions[item].opcode])

#print(h)

#active set, cycle count, and output order for final schedule
active = {}
cycle = 0
output = []

#logic for heuristics
def choose_node(var):
	if var == '-a':
		max_latency = -1
		start = -1
		for leaf in leaves:
			if h[leaf] > max_latency:
				max_latency = h[leaf]
				start = leaf
		return start
	if var == '-b':
		max_latency = -1
		start = -1
		for leaf in leaves:
			count = cycles[instructions[leaf].opcode]
			if count > max_latency:
				max_latency = count
				start = leaf
		return start
	if var == '-c':
		min_latency = 100
		start = -1
		for leaf in leaves:
			count = cycles[instructions[leaf].opcode]
			if count < min_latency:
				min_latency = count
				start = leaf
		return start
	print("incorrect argument given")

#algorithm for creating a schedule out of a dependence tree
while (leaves != set()) or (len(active) > 0):
	if leaves != set():
		start = choose_node(sys.argv[1])
		leaves.remove(start)
		active[start] = cycle
		output.append(start)
	cycle += 1
	to_remove = []
	for key in active:
		if cycles[instructions[key].opcode] + active[key] <= cycle:
			to_remove.append(key)
	for key in to_remove:
		active.pop(key)
		for child in children[key]:
			parents[child].remove(key)
			if parents[child] == set():
				leaves.add(child)

#replaces the node order with actual lines from the input file
for i in range(len(output)):
	output[i] = input_[output[i]]

f = open(sys.argv[3], "w")

for i in output:
	f.write(i)

f.close()

