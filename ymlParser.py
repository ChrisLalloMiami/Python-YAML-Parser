def tryDownConversion(value: str):
    '''Attempts to down-convert the given string value to an int, float, or boolean'''
    if value[0] == '"' and value[len(value) - 1] == '"' or value[0] == "'" and value[len(value) - 1] == "'":
        return value[1:len(value) - 1]
    elif value.lower() == "false":
        return False
    elif value.lower() == "true":
        return True
    else:
        try:
            temp = float(value)
            if round(temp) == temp:
                return int(temp)
            else:
                return temp
        except ValueError:
            return value
 
def clearComments(line: str):
    '''Clears the comments from a given line'''
    commentLocation = line.find("#")
    if commentLocation != -1:
        return line[:commentLocation].rstrip()
    else:
        return line
    
def parseInline(value: str, containerType: str):
    '''Parses an individual value when encountering inline dictionaries or lists, returning either list entries or key-value pairs'''
    keys = []
    values = []
 
    if containerType == "{}": # If parsing a dictionary
        innerSep = 0
        while (innerSep != -1):
            innerSep = value.find(":")
            if innerSep != -1:
                innerKey = value[1:innerSep]
                nextDelimiter = value.find(",") # Search for next pair by comma, or go to end of dictionary
 
                if nextDelimiter == -1:
                    nextDelimiter = value.find("}")
 
                innerValue = value[innerSep + 2:nextDelimiter]
                value = value[nextDelimiter + 1:]
                keys.append(innerKey)
                values.append(innerValue)
        return [keys, values]
    else: # If parsing a list
        nextDelimiter = 0
        while nextDelimiter != -1:
            nextDelimiter = value.find(",")
            if nextDelimiter != -1:
                nextValue = value[1:nextDelimiter]
                value = value[nextDelimiter+1:]
                values.append(nextValue)
            else:
                nextDelimiter = value.find("]")
                nextValue = value[1:nextDelimiter]
                values.append(nextValue)
                break
        return values
    
 
def parseYml(filePath: str):
    '''Parses the yml file referenced by filePath, returning its contents in a dictionary'''
    with open(filePath, "r") as file:
        lastIndentationLvl = 0
        fileMap = {}
        currentPath = []
        isList = False
 
        contents = file.read()
        lines = contents.split("\n")
        index = 0
 
        # Remove comments/newlines/trailing whitespace
        while index != len(lines):
            line = clearComments(lines[index])
            lines[index] = line
            
            # Remove those lines from list
            if len(line) == 0 or line == "" or line[0] == "#":
                del lines[index]
                index = index - 1 if index > 0 else 0
                continue
            
            dash = line.find("-")
            sep = line.find(":")
            key = line[:sep].strip()
            value = line[sep + 1:].strip()
            thisIndentationLvl = int((len(line) - len(line.lstrip())) / 2) # Assumes 2 spaces per tab in yml file
 
            if len(key) != 0 or dash != -1: # Covers new/empty lines
                if thisIndentationLvl < lastIndentationLvl:
                    isList = False
                    diff = lastIndentationLvl - thisIndentationLvl
                    for x in range(diff):
                        currentPath.pop()
 
                if isList: # When handling lists instead of dictionaries
                    value = line[dash + 1:].strip()
 
                if len(value) != 0 and thisIndentationLvl == 0: # If an entry has a value and is top-level (has no parents)
                    # Check for inline dictionaries or lists
                    if value[0] == "{":
                        fileMap[key] = {}
                        kvs = parseInline(value, "{}")
                        for x in range(len(kvs[0])):
                            fileMap[key][tryDownConversion(kvs[0][x].strip())] = tryDownConversion(kvs[1][x])
                    elif value[0] == "[":
                        fileMap[key] = []
                        vals = parseInline(value, "[]")
                        for val in vals:
                            fileMap[key].append(tryDownConversion(val))
                    # No inline dictionaries or lists. Just one key-value pair
                    else:
                        fileMap[key] = tryDownConversion(value)
                elif len(value) != 0 and thisIndentationLvl != 0: # If an entry has a value and is not top-level (has parents)
                    # Check for inline dictionaries or lists
                    if value[0] == "{":
                        currentPath[len(currentPath) - 1][key] = {}
                        kvs = parseInline(value, "{}")
                        for x in range(len(kvs[0])):
                            currentPath[len(currentPath) - 1][key][tryDownConversion(kvs[0][x].strip())] = tryDownConversion(kvs[1][x])
                        index += 1
                        continue
                    elif value[0] == "[":
                        currentPath[len(currentPath) - 1][key] = []
                        vals = parseInline(value, "[]")
                        for val in vals:
                            currentPath[len(currentPath) - 1][key].append(tryDownConversion(val))
                        index += 1
                        continue
                        
                    # No inline dictionaries or lists. Just one key-value pair or list member
                    if not isList:
                        currentPath[len(currentPath) - 1][key] = tryDownConversion(value)
                    else:
                        currentPath[len(currentPath) - 1].append(tryDownConversion(value))
                elif len(value) == 0: # If an entry does not have a value (a parent dictionary)
                    if len(currentPath) == 0: # When this will be a top-level dictionary
                        if index + 1 < len(lines):
                            nextLine = clearComments(lines[index + 1]) # Check if next line will start a list or a dictionary
                            nextSep = nextLine.find(":")
                            if nextSep != -1:
                                isList = False
                                fileMap[key] = {}
                                currentPath.append(fileMap[key])
                            else:
                                isList = True
                                fileMap[key] = []
                                currentPath.append(fileMap[key])
                    else: # When this is a sub-dictionary
                        if index + 1 < len(lines):
                            nextLine = clearComments(lines[index + 1]) # Check if next line will start a list or a dictionary
                            nextSep = nextLine.find(":")
                            if nextSep != -1:
                                isList = False
                                currentPath[len(currentPath) - 1][key] = {}
                                currentPath.append(currentPath[len(currentPath) - 1][key])
                            else:
                                isList = True
                                currentPath[len(currentPath) - 1][key] = []
                                currentPath.append(currentPath[len(currentPath) - 1][key])
                lastIndentationLvl = thisIndentationLvl # Does not apply when scanning newlines/whitespace/comment lines
                index += 1
        return fileMap