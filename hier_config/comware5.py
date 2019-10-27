import re


"""
Comware VLANs are provided as VIDs or as VID range with "to" in between. 
This method creates a list of unique vlans from this string. 
"""
def vlanStringToArray(string):
    matches = re.findall('(\d+) to (\d+)', string)
    vlans = []
    for match in matches:
        vlans.extend(range(int(match[0]), int(match[1]) + 1))

    string = re.sub('(\d+) to (\d+)', '', string)

    vlans.extend(list(map(str, string.split())))

    return vlans
"""
Comware uses multiple lines of "port trunk permit vlan" if more then 10 vlans are tagged on a port. 
This method replaces it with one line dealing with all vlans. Also normalizes the "to"-notation for vlan ranges.
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
        interface_new = re.sub('[^undo]( port trunk permit vlan ([0-9 to]+)\n)+', '\n port trunk permit vlan '+' '.join(vlans) + '\n', interface[0])

        # replace interface section with modified section
        config_text = re.sub(interface[0], interface_new, config_text)

    return config_text

"""
As multiple vlan ids are handled in the same configuration line a "undo" and "do" on all VLANs 
might impact traffic forwarding. 

This method computes the differences and a minimal change statement.
"""
def postprocess_remediation_config(remediation_config):
    for child in remediation_config.get_children('startswith', 'interface '):
        current_vlans = child.get_child('startswith', 'undo port trunk permit vlan')
        m = re.findall('port trunk permit vlan ([0-9 ]+)', current_vlans.text)

        current_vlans_list = vlanStringToArray(m[0])

        target_vlans = child.get_child('startswith', 'port trunk permit vlan')
        m = re.findall('port trunk permit vlan ([0-9 ]+)', target_vlans.text)
        target_vlans_list = vlanStringToArray(m[0])

        remove_vlans = set(current_vlans_list) - set(target_vlans_list)
        add_vlans = set(target_vlans_list) - set(current_vlans_list)
        if len(add_vlans) > 0:
            target_vlans.text = 'port trunk permit vlan '+' '.join(add_vlans)
        else:
            child.del_child(target_vlans)

        if len(remove_vlans) >0:
            current_vlans.text = 'undo port trunk permit vlan ' + ' '.join(remove_vlans)
        else:
            child.del_child(current_vlans)

    return remediation_config