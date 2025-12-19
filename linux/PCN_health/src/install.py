# MIT license copyright 2024,25 Jim Dodgen
# this configures and installs software
# it replaces the cfg.py file each time it runs
# Y N defaults are designed for rapid deployment during development
# usage is: "python3 install.py 
# this reads a toml configuration file see https://toml.io/
# this file is used by install.py to generate device cfg.py files (to push to the server)

import os
from pathlib import Path
import datetime
import tomllib
import sys

###### modify these as needed ######
## i use shared source librararys
all_lib_offset="../../../library/" # both linux and micropython

username = os.environ.get('SUDO_USER')

if username:
    # Use Path.home() might still point to /root when run under sudo.
    # The reliable way is using os.path.expanduser with the username.
    home_dir = Path(f'~{username}').expanduser()
    print(f"Original user's home directory: {home_dir}")
else:
    # Path.home() gets the current effective user's home (which would be /root if run as root)
    home_dir = Path.home()
    print(f"Current effective user's home directory: {home_dir}")

cluster_lib = f"{home_dir}/Dropbox/wip/pcn_clusters"


# to have  imports from libraries we need to do this:
# Get the absolute path of the current script's directory
# Add the parent directory to sys.path
# In this example, if main.py is in 'project/', this adds 'project/'
current_dir = os.path.dirname(os.path.abspath(__file__))
print ("current_dir", current_dir)
sys.path.append(os.path.join(current_dir, all_lib_offset))
import feature_power # located in all_lib_offset
###### end of stuff that needs modification ######

def load_cluster(cluster_file_name):
    if len(cluster_file_name) > 1:
        cluster_toml = cluster_lib+"/"+cluster_file_name
    else:
        print("testing from current directory")
        cluster_toml = "cluster-example.toml"  # test cluster
    print("using:", cluster_toml)
    try:
        with open(cluster_toml, 'rb') as toml_file:
            print("cluster_toml opened")
            try:
                cluster = tomllib.load(toml_file)
            except tomllib.TOMLDecodeError as e:
                print(e)
                sys.exit()
            print(cluster)
            return cluster
    except FileNotFoundError:
        print("Error: ",cluster_toml," File not found")
        sys.exit()
    except tomllib.TOMLDecodeError as e:
        print("Error: Invalid TOML format in {file_path}: {e}")
        sys.exit()
    except Exception as e:
        print("cluster_toml open failed", e)
 


class create_cfg:
    def __init__(self, cluster):
        self.cluster = cluster
        self.name = cluster["name"]
        self.our_feature = feature_power.feature(self.make_topic(self.name), publish=True)   # publisher
        self.write_cfg()

    def make_topic(self, key):
        print("make_topic", key)
        print("cluster_id",self.cluster["cluster_id"])
        desc = ""
        if desc == '':
            name =  self.cluster["cluster_id"]+"/"+key
        else:
            name =  self.cluster["cluster_id"]+"/"+key+" "+desc
        return name

# this is the cfg.py template uses % to pass in stuff
    def write_cfg(self):
        cfg_template = """# simple_emailer
# MIT license copyright 2024, 2025 Jim Dodgen
# this cfg.py was created by: install.py
# Date: %s
# MAKE YOUR CHANGES IN install.py
#
number_of_seconds_to_wait=30  # all sensors publish "power" messages every 30 seconds
#
broker = '%s'
ssl = %s # true or false
user = '%s'
password = '%s'
#
publish = "%s"
"""
        now = datetime.datetime.now()
        cfg_text =  cfg_template % (now.strftime("%Y-%m-%d %H:%M:%S"),
            self.cluster["mqtt_broker"]["broker"],
            self.cluster["mqtt_broker"]["ssl"],
            self.cluster["mqtt_broker"]["user"],
            self.cluster["mqtt_broker"]["password"],
            self.our_feature.topic(),
            )
        with open('cfg.py', 'w') as f:
            f.write(cfg_text)
        print("created cfg.py")

def main():
    while True:
        try:
            cluster_name = "cluster_jimdod_test_simple_emailer.toml"  #sys.argv[1]
        except:
            print("Input cluster toml file name:")
            cluster_name = input()
        try:
            cluster = load_cluster(cluster_name)
            break
        except:
            print("Try again")
            sys.exit()
    #print("request = ", name)
    create_cfg(cluster) # drops cfg.py file
    print("\ninstall as a service? (y,N)")
    ans = input()
    if (ans.upper() == "Y"):
        import service_tool
        service_tool.install()
    else:
        os.system("python3 pcn_health.py")

# os.system("python3 send_emails.py")

if __name__ == "__main__":
    main()
