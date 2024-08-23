import json
import const
import database

def devices_to_json():
    db = database.database()
    devices_dict = {}
    devices = db.get_all_devices()
    for dev in devices:
        (friendly_name, description, source,date) = dev
        devices_dict[friendly_name] = {
            "description": description,
            "source": source,
            "date": date,
            }
    features = db.get_all_features()
    features_dictionary = {}
    current_friendly_name = None
    for feat in features:
        (friendly_name, 
			property,  
			description, 
			type,
			access, 
			topic,
			true_value,  
			false_value,
			) = feat
        print(feat)
        if current_friendly_name == None:
            current_friendly_name = friendly_name       
        if current_friendly_name == friendly_name:
            features_dictionary[property] = {
                "description": description,
                "type": type,
                "access": access,
                "topic": topic,
                "true_value": true_value,
                "false_value": false_value,
                }
        else:
            devices_dict[current_friendly_name]["features"] = features_dictionary
            print(json.dumps( devices_dict, sort_keys=True, indent=4) )
            features_dictionary = {}
        current_friendly_name = friendly_name
        # print(feat)
    devices_dict[current_friendly_name]["features"] = features_dictionary
    as_json = json.dumps( devices_dict, sort_keys=True, indent=4) 
    #foo = json.loads(as_json) 
    #print(foo)
    return as_json

if __name__ == "__main__":
    js = devices_to_json()
    print(js)
    f = open("mqtt_json.js", "w")
    f.write(js)
    f.close()
