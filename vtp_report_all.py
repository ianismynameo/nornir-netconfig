from nornir import InitNornir
from nornir_netmiko.tasks import netmiko_send_command
from nornir_utils.plugins.functions import print_result
import csv, re, os
from nornir.core.filter import F

"""
The function vtp_info will run subtasks nxos_vtp to retrieve VTP mode from Nexus switches.
If unable to retrieve VTP mode, nxos_feature_search subtask will check if the VTP feature is enabled or disabled
"""


def vtp_info_nx(task):
    sep_line = "#" * 60 + "\n"
    nxos_vtp = task.run(
        netmiko_send_command, command_string="show vtp status", use_genie=True
    )
    task.host[0] = nxos_vtp.result
    output = task.host[0]
    vtp_mode = ""
    vtp_mode_regex = re.compile(r"(VTP\sOperating\sMode\s+:\s+)(\w+)")
    vtp_mode_match = vtp_mode_regex.search(output)
    if vtp_mode_match is not None:
        if vtp_mode_match.group(2) == "Transparent":
            vtp_mode = "transparent"
        elif vtp_mode_match.group(2) == "Client":
            vtp_mode = "client"
        elif vtp_mode_match.group(2) == "Server":
            vtp_mode = "server"
        elif vtp_mode_match.group(2) == "Off":
            vtp_mode = "off"
        print("vtp_mode: " + vtp_mode)

    else:
        print("Unable to retrieve VTP mode.")
        print(
            f"{task.host} : Unable to retrieve VTP mode. Checking if VTP feature is disabled.."
        )
        print(sep_line)
        nxos_feature_search = task.run(
            netmiko_send_command, command_string="show feature | grep vtp"
        )
        task.host[0] = nxos_feature_search.result
        feature_output = task.host[0]
        vtp_feature_regex = re.compile(r"(vtp\s+)\d\s+(\w+)")
        vtp_feature_match = vtp_feature_regex.search(feature_output)
        if vtp_feature_match.group(2) == "disabled":
            vtp_mode = "NXOS - VTP feature is disabled."
        elif vtp_feature_match.group(2) == "enabled":
            vtp_mode = (
                "VTP feature is enabled, but unable to retrieve VTP Operating Mode."
            )
        else:
            print("Unable to retrieve VTP feature information..")

    print(sep_line)
    vtp_file = "vtp_report_all.csv"
    with open(vtp_file, "a") as csvfile:

        writer = csv.writer(csvfile)
        csvdata = (task.host, task.host.hostname, vtp_mode)
        file_exists = os.path.isfile(vtp_file)
        header = ["HOSTNAME", "IP ADDR", "VTP MODE"]
        if not file_exists:
            writer.writerow(header)
        writer.writerow(csvdata)


"""
The function vtp_info_ios will run subtasks ios_vtp to retrieve VTP mode from IOS switches.

"""


def vtp_info_ios(task):
    sep_line = "#" * 60 + "\n"
    ios_vtp = task.run(
        netmiko_send_command, command_string="show vtp status", use_genie=True
    )
    task.host[0] = ios_vtp.result
    output = task.host[0]["vtp"]["operating_mode"]
    if output is not None:
        vtp_mode = output
    else:
        vtp_mode = "Unable to retrieve VTP mode."
    print(sep_line)
    vtp_file = "vtp_report_xyz.csv"
    with open(vtp_file, "a") as csvfile:

        writer = csv.writer(csvfile)
        csvdata = (task.host, task.host.hostname, vtp_mode)
        file_exists = os.path.isfile(vtp_file)
        header = ["HOSTNAME", "IP ADDR", "VTP MODE"]
        if not file_exists:
            writer.writerow(header)
        writer.writerow(csvdata)


def main():
    # Filter inventory by Cisco OS type and run appropriate function

    nr = InitNornir(config_file="config.yaml")
    # nr.inventory.defaults.username = ''
    '''
    Filter Examples

        nr = nr.filter(switch_router="switch")
        nr = nr.filter(site="SiteXYZ")
        
    '''        
    
    nxos_targets = nr.filter(F(has_parent_group="cisco_nxos"))
    print(len(nxos_targets.inventory.hosts))
    result = nxos_targets.run(task=vtp_info_nx)
    print_result(result)

    ios_targets = nr.filter(F(has_parent_group="cisco_ios"))
    result = ios_targets.run(task=vtp_info_ios)
    print(len(ios_targets.inventory.hosts))
    print_result(result)


if __name__ == "__main__":
    main()
