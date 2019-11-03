import re


"""
Comware VLANs are provided as VIDs or as VID range with "to" in between. 
This method creates a list of unique vlans from this string. 
"""
def vlanStringToArray(string):
    matches = re.findall('(\d+) to (\d+)', string)
    vlans = []
    for match in matches:
        vlans.extend(map(str, range(int(match[0]), int(match[1]) + 1)))

    string = re.sub('(\d+) to (\d+)', '', string)

    vlans.extend(list(map(str, string.split())))

    return vlans
"""
Comware uses multiple lines of "port trunk permit vlan" if more then 10 vlans are tagged on a port. 
This method replaces it with one line per vlan. Also normalizes the "to"-notation for vlan ranges.
"""
def preprocessor(config_text):
    interfaces = re.findall('(^interface ([A-Za-z0-9\/\-\:]+)$(.*?)^#$)+', config_text, re.MULTILINE | re.DOTALL)

    for interface in interfaces:
        vlans = []
        m = re.findall('[^undo] port trunk permit vlan ([0-9 to]+)', interface[2], re.MULTILINE | re.DOTALL)
        if len(m) > 0:
            for i in m:
                vlans.extend(vlanStringToArray(i))

        # replace multiple statements with one
        interface_new = re.sub('[^undo]( port trunk permit vlan ([0-9 to]+)\n)+', '\n port trunk permit vlan '.join(vlans) + '\n', interface[0])
        # replace interface section with modified section
        config_text = config_text.replace(interface[0], interface_new)

    return config_text
