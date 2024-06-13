import json
import const
import database

def devices_to_json():
    db = database.database()
    devices_dict = []
    devices = db.get_all_devices()
    for dev in devices:
        (friendly_name, description, source,date) = dev
        d = {
            "friendly_name": friendly_name,
            "description": description,
            "source": source,
            "date": date,
            }
        devices_dict.append(d)
    features_dict = []
    features = db.get_all_features()
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
        f = {"friendly_name": friendly_name, 
            "property": property,
            "description": description,
            "type": type,
            "access": access,
            "topic": topic,
            "true_value": true_value,
            "false_value": false_value,
            }
        features_dict.append(f)
    all = {"devices": devices_dict, "features": features_dict}
    as_json = json.dumps( all) 
    #foo = json.loads(as_json) 
    #print(foo)
    return as_json

if __name__ == "__main__":
    js = devices_to_json()
    f = open("../alertaway2/mqtt_json.js", "w")
    f.write(js)
    f.close()
