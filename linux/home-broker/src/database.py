# database.py
import sqlite3
# from paho.mqtt.client import Client
import const
# import os
import json
import logging
import time
from textwrap import wrap
#
# conditional print
import os 
my_name = os.path.basename(__file__).split(".")[0]
xprint = print # copy print
def print(*args, **kwargs): # replace print
    return
    xprint("["+my_name+"]", *args, **kwargs) # the copied real print
#
#
class database:
    def __init__(self):
        self.con = sqlite3.connect(const.db_name, timeout=const.db_timeout)
        # print("working directory[%s]" % os.getcwd())
        cur = self.con.cursor()
        try:  # see if  db exists
            cur.execute("select rowid from mqtt_device")
            cur.close()
        except:
            cur.close()
            self.initialize()

    def __del__(self):
        self.con.commit()
        self.con.close()

    def replace_password(self, pw):
        if pw == "":
            return False
        cur = self.con.cursor()
        status = True
        try:
            cur.execute("""
            insert or replace into password (password) values (?)""", 
                (pw,))
        except:
            status = False
        cur.close()
        self.con.commit()
        return status
    
    def get_devices_for_wemo(self):
        cur = self.con.cursor()
        cur.execute("""
        select distinct
            mqtt_feature.rowid,
            mqtt_device.friendly_name,  
            mqtt_device.description, 
            mqtt_feature.property,
            mqtt_feature.description,
            mqtt_feature.topic,
            mqtt_feature.true_value,
            mqtt_feature.false_value
            from mqtt_feature
            join mqtt_device on mqtt_feature.friendly_name = mqtt_device.friendly_name
            where mqtt_feature.access = "sub" and (type = 'binary' or type = 'momentary')
            order by mqtt_feature.friendly_name, mqtt_feature.property desc
        """)
        all = cur.fetchall()
        cur.close()
        return all
    
    def get_fauxmo_devices(self):
        cur = self.con.cursor()
        where = ''
        cur.execute("""
        select
            wemo_port,
            wemo_name,
            mqtt_feature.topic,
            mqtt_feature.true_value,
            mqtt_feature.false_value,
            qos,
            retain
        from wemo
        left join mqtt_feature on wemo.friendly_name = mqtt_feature.friendly_name
            and mqtt_feature.property = wemo.property
            and mqtt_feature.topic = wemo.topic
        where mqtt_feature.access = "sub"
        """)
        all = cur.fetchall()
        cur.close()
        return all
    
    def get_all_features(self):
        cur = self.con.cursor()
        query = """
        select
            friendly_name,
            property,
            description, 
            type,
            access, 
            topic,
            true_value,  
            false_value
        from mqtt_feature
        order by friendly_name, property
        """
        cur.execute(query)
        all = cur.fetchall()
        print(all)
        cur.close()
        return all

    def get_all_devices_features(self, source=None):
        where = ''
        if source in ("manIP", "IP", "ZB"):
            where = "where source = '%s'" %  (source,)
        else:
            return None

        cur = self.con.cursor()
        query = """
        select
            mqtt_feature.rowid,
            mqtt_device.friendly_name,
            mqtt_device.description,
            mqtt_device.date,
            mqtt_feature.property,
            mqtt_feature.description,
            mqtt_feature.type,
            mqtt_feature.access,
            mqtt_feature.topic, 
            mqtt_feature.true_value,
            mqtt_feature.false_value
        from mqtt_device
        left join mqtt_feature on mqtt_feature.friendly_name = mqtt_device.friendly_name
        %s
        order by mqtt_feature.friendly_name, mqtt_feature.access desc
        """ % (where,)
        print(query)
        cur.execute(query)
        all = cur.fetchall()
        print(all)
        cur.close()
        return all
    
    def cook_devices_features_for_html(self, source=None):
        all = self.get_all_devices_features(source=source)
        last_friendly_name = ""
        new_all = []
        for d in all:
            access = d[7]
            new = list(d)
            if d[1] == last_friendly_name:
                new[1] = ''
                new[2] = ''
                new[3] = ''
                cooked_address=""
            else:
                try:
                    new[3] = time.strftime("%d %b %H:%M", time.localtime(float(new[3])))
                    #'Thu, 28 Jun 2001 14:17:15 +0000
                except:
                    new[3] = ''
                cooked_address = " ".join(wrap(d[1],width=9)) 
            last_friendly_name = d[1]
            print("access [%s]" % (access,))
            new.append(True if access == "sub" else False)
            #   new.append(True)
            # else:
            #   new.append(False)
            for x in d:
                print(x)
            new.append(cooked_address)
            new_all.append(tuple(new))
        print(new_all)
        return new_all
    
    def get_manIP_device(self, rowid):
        if rowid == None:
            return None
        cur = self.con.cursor()
        cur.execute("""
        select
            mqtt_feature.rowid, 
            mqtt_device.friendly_name,  
            mqtt_feature.property,
            mqtt_feature.type,
            mqtt_feature.topic,  
            mqtt_feature.true_value,  
            mqtt_feature.false_value,
            mqtt_feature.access
            from mqtt_device
            left join mqtt_feature on mqtt_feature.friendly_name = mqtt_device.friendly_name
            where mqtt_feature.rowid = ?
        """, (rowid,))
        rec = cur.fetchone()
        print(all)
        cur.close()
        return rec  
    
    def update_manIP_feature(self,   
            value_type,
            access,
            topic,
            true_value,  
            false_value,
            rowid, 
            ):
        cur=self.get_cursor()
        print("database: topic", type(topic))
        cur.execute("""update mqtt_feature 
            set type    = ?,
            access      = ?, 
            topic   = ?,  
            true_value  = ?,  
            false_value = ?
            where rowid = ?
            """,(value_type,
                access,
                topic,
                true_value,  
                false_value, 
                rowid,  
            ))
        cur.close()
        self.con.commit()

    def get_wemo(self, row_id):
        cur = self.con.cursor()
        cur.execute("""
        select wemo.rowid, 
            wemo_name,
            wemo_port, 
            mqtt_feature.rowid,
            mqtt_device.friendly_name,
            mqtt_feature.property,
            qos,
            retain
        from wemo
        left join mqtt_device on mqtt_device.friendly_name = wemo.friendly_name
        left join mqtt_feature on mqtt_device.friendly_name = mqtt_feature.friendly_name
            and mqtt_feature.property = wemo.property
            and mqtt_feature.topic = wemo.topic
        where wemo.rowid = ?
            """, (row_id,))
        rec = cur.fetchone()
        cur.close()
        return rec
    
    def delete_all_zb_devices(self):
        cur=self.get_cursor()
        try:
            cur.execute("""delete from mqtt_feature where mqtt_feature.friendly_name in
                            (select mqtt_device.friendly_name from mqtt_device where source = \"ZB\")""")
            cur.execute("delete from mqtt_device where source = \"ZB\"")        
        except:
            print("delete_all_zb_devices failed")
        cur.close()
        self.con.commit()

    def delete_device(self, name):
        print("delete_device [%s]"% (name,))
        cur=self.get_cursor()
        try:
            cur.execute("delete from mqtt_feature where friendly_name = ?", (name,))
            cur.execute("delete from mqtt_device where friendly_name = ?", (name,))
        except:
            print("problem deleting?")
        cur.close()
        self.con.commit()

    def upsert_device(self, description, name, source):
        # first check to see if we have a major change
        # notifiers may need this to reduce MQTT traffic
        #   
        cur = self.con.cursor()
        cur.execute("""
            select
                description, 
                friendly_name 
            from mqtt_device 
            where friendly_name = ?
            and description = ?
        """, (name, description))
        r =  True if cur.fetchone() else False   ## one found nothing important minor
        cur.close()
        #
        # we always update atleast for date
        #
        now = str(int(time.time())) # standard unix time in a string
        cur=self.get_cursor()
        cur.execute(
            """
            insert or replace into mqtt_device 
                (description, 
                friendly_name, 
                source,
                date) 
            values (?,?,?,?)
            """, 
                (description, name, source, now))
        cur.close()
        self.con.commit()
        return r

    def get_all_devices(self):
        cur = self.con.cursor()
        cur.execute("""
        select  distinct
            friendly_name, 
            description, 
            source,
            date
        from mqtt_device 
        """)
        all = cur.fetchall()
        print(all)
        cur.close()
        return all
    
    def decode_access(self,access):
        published = True if (access & 1) else False
        set         = True if (access & 2) else False
        get         = True if (access & 4) else False
        return (published, set, get)

    def get_cursor(self):
        #try:
        cur = self.con.cursor()
        #except:
        #   self.con = sqlite3.connect(const.db_name)
        #   cur = self.con.cursor()
        return cur
    
    def upsert_feature(self,
            friendly_name, 
            property,  
            description, 
            type,
            access, 
            topic,  
            true_value,  
            false_value
            ):
        # first check to see if we have a change
        # notifiers may need this to reduce MQTT traffic
        #  
        cur = self.con.cursor()
        cur.execute("""
            select
            friendly_name
            from mqtt_feature 
            where friendly_name = ?
            and property = ?
            and description = ?
            and type = ?
            and access = ?
            and topic = ?
            and true_value = ?
            and false_value  = ?
        """, (friendly_name, property, description, type, access, topic, true_value, false_value))
        exists = True if cur.fetchone() else False
        cur.close()
        if exists:
            return True
        cur=self.get_cursor()
        try:
            cur.execute("""insert or replace into mqtt_feature 
                (friendly_name, 
                property,  
                description, 
                type,
                access, 
                topic,  
                true_value,  
                false_value
                )
                values (?,?,?,?,?,?,?,?)""", 
                (friendly_name,
                property,  
                description, 
                type,
                access, 
                topic,  
                true_value,  
                false_value,))
        except:
            pass
        cur.close()
        self.con.commit()

    def get_feature(self, friendly_name, property, topic):
        cur = self.con.cursor()
        cur.execute("""
        select 
            mqtt_device.rowid,
            mqtt_device.friendly_name,
            mqtt_device.description,
            mqtt_device.source,  
            mqtt_feature.rowid, 
            mqtt_feature.property,
            mqtt_feature.description,
            mqtt_feature.type, 
            mqtt_feature.access, 
            mqtt_feature.topic, 
            mqtt_feature.true_value, 
            mqtt_feature.false_value, 
            from mqtt_feature
            join mqtt_device on mqtt_device.friendly_name = mqtt_feature.friendly_name
            where mqtt_feature.friendly_name = ? 
            AND   mqtt_feature.property = ?
            AND   mqtt_feature.topic = ?
        """, (friendly_name, property, topic))
        rec = cur.fetchone()
        cur.close()
        print("get_feature returned [%s]" % (rec,))
        return rec

    def get_feature_mqtt(self, rowid):
        cur = self.con.cursor()
        cur.execute("""
        select 
            access, 
            topic, 
            true_value, 
            false_value 
            from mqtt_feature
            where rowid = ?
        """, (rowid,))
        rec = cur.fetchone()
        cur.close()
        print("get_feature_mqtt returned [%s]" % (rec,))
        return rec

    def delete_wemo(self, row_id):
        cur = self.con.cursor()
        cur.execute("""
        delete from wemo where rowid = ?
        """, (row_id,))
        cur.close()
        self.con.commit()

    def create_wemo(self, wemo_name, wemo_port, feature_row_id):
        if wemo_name == "":
            return False
        cur = self.con.cursor()
        if not wemo_port:
            cur.execute("""
            select COALESCE(max(wemo_port),0)home_MQTT_devices
                from wemo
            """)
            largest_wemo_port = cur.fetchone()[0]
            cur.close()
            print("current largest_wemo_port[%s]" % largest_wemo_port)
            if  largest_wemo_port == 0:
                wemo_port = const.base_faxmo_port
            else:
                wemo_port = int(largest_wemo_port) + 1
            cur = self.con.cursor()
        status = True
        try:
            cur.execute("""
            insert or replace into wemo (
               wemo_name, 
               wemo_port,
               friendly_name,
               property,
               topic
               ) 
                select 
                ?,
                ?,
                mqtt_device.friendly_name, 
                mqtt_feature.property,
                mqtt_feature.topic
                from mqtt_feature
                join  mqtt_device on mqtt_device.friendly_name = mqtt_feature.friendly_name
                where mqtt_feature.rowid = ? """, (wemo_name,  wemo_port, feature_row_id,))
        except Exception as e:
            print("create_wemo failed,", e)
            status = False
        cur.close()
        self.con.commit()
        return status

    def get_all_wemo(self):
        cur = self.con.cursor()
        cur.execute("""
        select  
                wemo.rowid,
                wemo_name,
                wemo_port,
                mqtt_device.friendly_name,
                mqtt_feature.property, 
                mqtt_feature.topic,
                mqtt_feature.true_value,
                mqtt_feature.false_value
            from wemo
            left join mqtt_device  on mqtt_device.friendly_name = wemo.friendly_name 
            left join mqtt_feature on mqtt_device.friendly_name = mqtt_feature.friendly_name
                    and mqtt_feature.property = wemo.property
                    and mqtt_feature.topic = wemo.topic
            where mqtt_feature.access = "sub"
            order by wemo_name;
        """)
        all = cur.fetchall()
        cur.close()
        return all

    def get_all_manual_device_names(self):
        cur = self.con.cursor()
        cur.execute("""
        select 
            mqtt_device.friendly_name,
            mqtt_device.description
            from mqtt_device
            where mqtt_device.source = "manIP"
            order by mqtt_device.friendly_name
        """)
        all = cur.fetchall()
        cur.close()
        #for e in all:
        #   print(e)
        return all
    
    def initialize(self, create_test_data=False):
        create="""
        drop table if exists wemo;
        create table wemo
        (
            wemo_name unique,
            wemo_port unique,
            friendly_name,
            property,
            topic,
            qos default 0,
            retain default 0,
            PRIMARY KEY (wemo_name, wemo_port)
        );
        drop table if exists mqtt_device;
        create table mqtt_device
        (
            friendly_name,
            description,
            source, -- "zigbee", or "IP" others in future
                    -- zigbee2mqtt forces unique "friendly_name"s zigbee2mqtt
                    -- our IP devices CAN share the same name to support MQTT multicast
                    -- IEEE is stored but not use. For IP devices it will be the last one reporting in
                    -- if the devices sharing friendly names have different features 
                    -- the one that gets published in devices_to_json() will be a collection 
                    -- of unique property features
            date, 
            PRIMARY KEY (friendly_name)
        );

        drop table if exists device_ieee;
        create table device_ieee
        (
            ieee_addr text,
            friendly_name,
            date,
            PRIMARY KEY (ieee_addr)
        );

        drop table if exists mqtt_feature;
        create table mqtt_feature
        (   mqtt_feature_id integer auto increment,
            friendly_name NOT NULL,
            property NOT NULL,  -- unique within a device same as zigbee name
            description, 
            type NOT NULL, -- like "binary", lots of others things like battery etc.
            access NOT NULL,   -- sub or pub 
            topic NOT NULL,
            true_value,    -- usually the "on" value or result from a pub only device
            false_value,   -- off value 
            PRIMARY KEY (friendly_name, property, topic, access, type)
            -- PRIMARY KEY (friendly_name, property, type, access, topic, true_value, false_value)
        );
        drop table if exists timers;
        create table timers
        (
            friendly_name,
            topic,  -- topic usualy a "set" for zigbee
            payload,  -- some form of on or off
            sunset,  -- true or false
            sunrise, -- true or false
            offset,  -- +/- offset time for sunrise/set
            time -- start time 
        );
        """
        self.con.executescript(create)  # drop and create the tables

        if create_test_data:
            #
            # this is a dummy device mostly for testing
            #
            #b [mqtt_hello] [send_hello] topic[home/70a8d3dd39f1/hello] payload[
            
            name = "friendly_example"
            self.upsert_device("test description", name, "manIP")
            self.upsert_feature(name,
                        "state",
                        "relay1",
                        "binary", 
                        "sub", 
                        "/home/"+name+"/valve", 
                        "ON",
                        "OFF",
                        )
            feature_row_id = 1 # fresh table so first insert is 1
            db.create_wemo("wemo name", "54321", feature_row_id)
            self.con.commit()
        pass

    # def void_make_wifi_tail(self,off, on, set,get, get_payload):
    #   tail =  """{"payload_off": "%s", 
    #               "payload_on": "%s", 
    #               "topic_set": "%s",
    #               "topic_get": "%s",
    #               "get_payload": "%s", 
    #               }""" %  (off, on, set, get, get_payload)
    #   try:
    #       work = json.loads(tail)
    #   except:
    #       work ='{"error": "not valid json"}'
    #       print("did not like work")
    #   print("work", work)
    #   new_tail = json.dumps(work)
        
    #   return new_tail

    
# test stuff  not running when imported 
if __name__ == "__main__":
    db=database()
    # print(db.cook_devices_features_for_html())
    # print(db.delete_device(13))
    # rc = db.upsert_device("no addr test", "foobar", "IP")
    # print(rc)

    # rc = database.upsert_feature(
    #   "foobar",
    #   "state",
    #   "relay1",
    #   "binary", 
    #   "sub", 
    #   "/home/foobar/thing", 
    #   "ON",
    #   "OFF")  
    # print(rc)
    # print(db.delete_device(13))

    #db.get_all_manual_devices()
    # print("database  opened")
    #js =db.make_wifi_tail("OFF","ON", "/dodod/set","/dodod/get")
    #print(js)
    #print("initialize?")
    #input()
    #db.initialize(create_test_data=True)
    #print(db.get_all_wemo())
    # db.upsert_device("water")
    # db.create_broker([server1])
    # row = [0,"server", "server.local","", "", "" ]
    # db.update_broker(row)
    # row = [0,"another server", "server.local","", "", "" ]
    # db.update_broker(row)
    # brokers = db.get_all_brokers()
    # print (brokers)

    # """rowid,device_name, topic, payload_on, payload_off,payload_state,
    #       broker_name, client_id """
    
    # db.upsert_device("a foo device", "foo", "IP")
    
    # db.upsert_device(row)
    # devices = db.get_all_devices()    
    # for row in devices:
    #   print(row)
    #   #for col in row:
    #       #print(col)
    # row = db.get_device(4)

    # if row == None:
    #   print("not found")
    # print(row)
    #d = db.get_fauxmo_devices()
    #print(d)




    
