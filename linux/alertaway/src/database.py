# database.py
import sqlite3
# from paho.mqtt.client import Client
# import const
# import os
import json
import logging
import time
from textwrap import wrap
import http_common as const
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
'''        
cursor.execute("SELECT * FROM users JOIN posts ON users.id = posts.user_id")
row = cursor.fetchone()

# Let's inspect the keys now:
print(row.keys())  
# Outputs: ['users.id', 'users.name', 'posts.id', 'posts.user_id', 'posts.title']

# 3. ACCESS BOTH EXPEDITIOUSLY WITHOUT NAME COLLISIONS:
print(row['users.id'])  # Outputs: 1
print(row['posts.id'])  # Outputs: 99
'''
class database:
    def __init__(self, row_factory=False):
        print(const.DB_NAME)
        self.con = sqlite3.connect(const.DB_NAME, timeout=const.DB_TIMEOUT)
        self.con.execute("PRAGMA foreign_keys = ON;")
        #self.con.execute("PRAGMA full_column_names = 1;")
        print("working directory[%s]" % os.getcwd())
        if row_factory:
            self.con.row_factory=sqlite3.Row
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

    def close(self):
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
            -- where mqtt_feature.access = "sub" and (type = 'binary' or type = 'momentary')
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
            port,
            voice_name,
            mqtt_feature.topic,
            mqtt_feature.true_value,
            mqtt_feature.false_value,
            qos,
            retain
        from voice_device
        join mqtt_feature on mqtt_feature.topic = voice_device.topic
            and mqtt_feature.true_value = voice_device.true_value
        where voice_device.handler = "wemo"
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
        #print(query)
        cur.execute(query)
        all = cur.fetchall()
        #print(all)
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
                    new[3] = time.strftime("%d %b %H:%M %Y", time.localtime(float(new[3])))
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
            voice_name,
            port,
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
        #
        # we always update atleast for date
        #
        print("upsert_device:", description, name, source)
        now = str(int(time.time())) # standard unix time in a string
        cur=self.get_cursor()
        cur.execute(
            """
            insert or ignore into mqtt_device
                (description,
                friendly_name,
                source,
                date)
            values (?,?,?,?)
            """,
                (description, name, source, now))
        cur.close()
        self.con.commit()
        return

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
        #   self.con = sqlite3.connect(const.DB_NAME)
        #   cur = self.con.cursor()
        return cur

    def upsert_feature(self, data_list):
    # data_list should be a list of tuples or dictionaries
        cur = self.con.cursor()
        query = """
            INSERT or REPLACE INTO mqtt_feature (
                friendly_name, property, description, type,
                access, topic, true_value, false_value
            ) VALUES (
                :friendly_name, :property, :description, :type,
                :access, :topic, :true_value, :false_value
            )
        """
    # Use executemany for bulk performance
        cur.execute(query, data_list)
        if cur.rowcount > 0:
            print(f"upsert_feature Success! Inserted row with ID: {cur.lastrowid}")
        else:
            print("upsert_feature Failure: No rows were inserted.")
        self.con.commit()

    def old_upsert_feature(self,
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
        #print("get_feature_mqtt returned [%s]" % (rec,))
        return rec

    def delete_wemo(self, row_id):
        cur = self.con.cursor()
        cur.execute("""
        delete from wemo where rowid = ?
        """, (row_id,))
        cur.close()
        self.con.commit()

    def create_voice(self, voice_name, port, feature_row_id):
        if voice_name == "":
            return False
        cur = self.con.cursor()
        if not port:
            cur.execute("""
            select COALESCE(max(port),0)home_MQTT_devices
                from wemo
            """)
            largest_port = cur.fetchone()[0]
            cur.close()
            print("current largest_port[%s]" % largest_port)
            if  largest_port == 0:
                port = const.BASE_FAXMO_PORT
            else:
                port = int(largest_port) + 1
            cur = self.con.cursor()
        status = True
        try:
            cur.execute("""
            insert or replace into wemo (
               voice_name,
               port,
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
                where mqtt_feature.rowid = ? """, (voice_name,  port, feature_row_id,))
        except Exception as e:
            print("create_voice failed,", e)
            status = False
        cur.close()
        self.con.commit()
        return status

    def get_all_wemo(self):
        cur = self.con.cursor()
        cur.execute("""
        select
                voice.rowid,
                voice_name,
                port,
                mqtt_device.friendly_name,
                mqtt_device.description,
                mqtt_feature.topic,
                mqtt_feature.true_value,
                mqtt_feature.false_value
            from voice_device
            left join mqtt_device  on mqtt_device.friendly_name = wemo.friendly_name
            left join mqtt_feature on mqtt_device.friendly_name = mqtt_feature.friendly_name
                    and mqtt_feature.true_value = voice.true_value
                    and mqtt_feature.topic = wemo.topic
            --where mqtt_feature.access = "sub"
            order by voice_name;
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

    def get_publish_devices(self):
        cur = self.con.cursor()
        cur.execute("""
        select distinct
            mqtt_feature_id,
            -- source,
            topic,
            type,
            property,
            true_value,
            false_value

        from mqtt_feature
        left join mqtt_device on mqtt_feature.friendly_name = mqtt_device.friendly_name
        where (type = "binary" and source = "ZB" and property like "state%" and topic like "%set")
            or source = "IP" or source = "manIP"
        order by topic desc
        """)
        all = cur.fetchall()
        cur.close()
        tuple_rows = [tuple(row) for row in all]
        xprint(tuple_rows)
        return all

    def get_subscribe_devices(self):
        cur = self.con.cursor()
        cur.execute("""
        select distinct
            mqtt_feature.rowid,
            -- source,
            topic,
            type,
            property,
            true_value,
            false_value
        from mqtt_feature
        left join mqtt_device on mqtt_feature.friendly_name = mqtt_device.friendly_name
        where (type = "binary" and source = "ZB" and property like "state%" and topic like "%get")
            or source = "IP" or source = "manIP"
        order by topic desc
        """)
        all = cur.fetchall()
        cur.close()
        return all

    def get_all_timers(self):
        cur = self.con.cursor()
        cur.execute("""
        select
            rowid,
            topic,
            days,
            start_type,
            start_hour,
            start_minute,
            start_offset,
            stop_type,
            stop_hour,
            stop_minute,
            stop_offset
            from timers
            order by topic
        """)
        all = cur.fetchall()
        cur.close()
        return all

    def get_all_triggers(self):
        cur = self.con.cursor()
        cur.execute("""
        select
            rowid,
            pub_topic,
            pub_payload,
            sub_topic,
            sub_payload
            from triggers
            order by pub_topic
        """)
        all = cur.fetchall()
        cur.close()
        return all

    def get_device_info(self, rowid):
        cur = self.con.cursor()
        cur.execute("""
        select
            topic,
            true_value,
            false_value

        from mqtt_device
        join mqtt_feature on mqtt_feature.friendly_name = mqtt_device.friendly_name
        where
            mqtt_feature.rowid = ?
        """, (rowid,))
        rec = cur.fetchone()
        cur.close()
        print("get_feature_mqtt returned [%s]" % (rec,))
        return rec

    def get_timers_for_today(self):
        print("get_timers_for_today")
        cur = self.con.cursor()
        cur.execute("""
        select
            *
            from timers

            WHERE days LIKE strftime('%%%w%%','now' ,'localtime')
        """)
        all = cur.fetchall()
        return all
        
    def process_sql(self,sql_text):
        # 1. Split into individual lines to strip inline comments safely
        lines_raw = sql_text.split('\n')
        clean_lines = []
        
        for line in lines_raw:
            # Split by comment marker and take the left side (the actual SQL code)
            code_part = line.split('--')[0]
            # Only keep it if it contains actual characters
            if code_part.strip():
                clean_lines.append(code_part.strip())
                
        # 2. Join the cleaned lines back together with a space
        #    This safely flattens internal newlines into a single line
        flattened_sql = " ".join(clean_lines)
        
        # 3. Now it is safe to split into distinct statements by semicolon
        statements = [stmt.strip() for stmt in flattened_sql.split(';') if stmt.strip()]
        
        return statements
       
    def test_data(self):
        inserts = """
INSERT INTO "mqtt_device" ("friendly_name","description","source","date") 
    VALUES ('big thing','its a nice thing','manIP','1778015702');
INSERT INTO "mqtt_device" ("friendly_name","description","source","date") 
    VALUES ('small thing','small huh','manIP','1778015745');
INSERT INTO "mqtt_device" ("friendly_name","description","source","date") 
    VALUES ('door','just a door','manIP','1778015745');
INSERT INTO "mqtt_device" ("friendly_name","description","source","date") 
    VALUES ('water leak','leak detector','manIP','1778015745');
INSERT INTO "mqtt_device" ("friendly_name","description","source","date") 
    VALUES ('door bell','ringgy thinggy','manIP','1778015745');
INSERT INTO "mqtt_device" ("friendly_name","description","source","date") 
    VALUES ('door closed','door sensor','manIP','1778015745');

INSERT INTO "mqtt_feature" ("mqtt_feature_id","friendly_name","property","description","type","access","topic","true_value","false_value") 
    VALUES (NULL,'big thing','manual','its a nice thing','binary',NULL,'home/big_thing/state','yes','no');
INSERT INTO "mqtt_feature" ("mqtt_feature_id","friendly_name","property","description","type","access","topic","true_value","false_value") 
    VALUES (NULL,'small thing','manual','small huh','binary',NULL,'home/small_thing/state','1','0');
INSERT INTO "mqtt_feature" ("mqtt_feature_id","friendly_name","property","description","type","access","topic","true_value","false_value") 
    VALUES (NULL,'door','manual','small huh','binary',NULL,'home/door/state','open','closed');
INSERT INTO "mqtt_feature" ("mqtt_feature_id","friendly_name","property","description","type","access","topic","true_value","false_value") 
    VALUES (NULL,'water leak','manual','small huh','binary',NULL,'home/water/status','leaking',NULL);
INSERT INTO "mqtt_feature" ("mqtt_feature_id","friendly_name","property","description","type","access","topic","true_value","false_value") 
    VALUES (NULL,'door bell','manual','small huh','binary',NULL,'home/doorbell/button','',NULL);

INSERT INTO "voice_device" ("mqtt_feature_id","voice_name","port","topic","true_value", "handler") 
    VALUES (2, "beadroom light", '55555','home/small_thing/state',"1","wemo");

INSERT INTO "cameras" ("camera_name","url","user","password","rotate") VALUES ('Driveway','http://192.168.0.4/cgi-bin/snapshot.cgi?channel=1','admin','alert.Away','');
INSERT INTO "cameras" ("camera_name","url","user","password","rotate") VALUES ('Front door','http://192.168.0.3/cgi-bin/snapshot.cgi?channel=4','admin','dr0wssap!','90');
INSERT INTO "cameras" ("camera_name","url","user","password","rotate") VALUES ('Side door','http://192.168.0.3/cgi-bin/snapshot.cgi?channel=4','admin','dr0wssap!','90');

INSERT INTO "emailaddr" ("emailaddr_name","email_address") VALUES ('bill','bill@foo.com');
INSERT INTO "emailaddr" ("emailaddr_name","email_address") VALUES ('don','don@foo.com');
INSERT INTO "emailaddr" ("emailaddr_name","email_address") VALUES ('Jim','jim@dodgen.us');

INSERT INTO "timers" ("mqtt_feature_id", "topic","true_value","false_value","days","start_type","start_hour","start_minute","start_offset","stop_type","stop_hour","stop_minute","stop_offset","time_to_stop","time_to_start","seconds_from_midnight","state") 
VALUES (2,'home/small_thing/state','1','0','0,1,2,3,4,5,6','Sunrise',0,0,'0','Sunrise',0,0,'30',NULL,NULL,NULL,NULL);

INSERT INTO "triggers" ("sub_mqtt_feature_id", "sub_topic","sub_true_value", "sub_payload","pub_mqtt_feature_id", "pub_topic","pub_true_value", "pub_payload") 
    VALUES (2, 'home/small_thing/state','1','1',   1, 'home/big_thing/state','yes','no');

INSERT INTO "events" ("mqtt_feature_id","events_name","mqtt_topic","matching_payload","only_on_change_of_payload","subject","body") 
    VALUES (3, 'door open','home/door/state','open',0,'door is open','Me thinks a knave has left the hatch open');
INSERT INTO "events" ("mqtt_feature_id","events_name","mqtt_topic","matching_payload","only_on_change_of_payload","subject","body") 
    VALUES (4,'bad thing','home/water/status','leaking',0,'water leak from heater','turn the valve next to the door off.
if you had ball_valve_controller you could use triggers to turn it off automatically');
INSERT INTO "events" ("mqtt_feature_id","events_name","mqtt_topic","matching_payload","only_on_change_of_payload","subject","body") 
    VALUES (5,'door bell','home/doorbell/button','',0,'door bell pressed','What do you see');
INSERT INTO "events" ("mqtt_feature_id","events_name","mqtt_topic","matching_payload","only_on_change_of_payload","subject","body") 
    VALUES (3,'door closed','home/door/state','closed',0,'closed now','yes it is');

-- test set for simple_emailer 
INSERT INTO "cameras_in_events" ("events_name","camera_name") VALUES ('bad thing','Side door');
INSERT INTO "cameras_in_events" ("events_name","camera_name") VALUES ('bad thing','Front door');
INSERT INTO "cameras_in_events" ("events_name","camera_name") VALUES ('door open','Front door');
INSERT INTO "cameras_in_events" ("events_name","camera_name") VALUES ('door open','Driveway');
INSERT INTO "cameras_in_events" ("events_name","camera_name") VALUES ('door bell','Front door');
INSERT INTO "cameras_in_events" ("events_name","camera_name") VALUES ('door closed','Side door');

INSERT INTO "emailaddr_in_events" ("events_name","emailaddr_name") VALUES ('bad thing','Jim');
INSERT INTO "emailaddr_in_events" ("events_name","emailaddr_name") VALUES ('bad thing','don');
INSERT INTO "emailaddr_in_events" ("events_name","emailaddr_name") VALUES ('door open','bill');
INSERT INTO "emailaddr_in_events" ("events_name","emailaddr_name") VALUES ('door bell','Jim');
INSERT INTO "emailaddr_in_events" ("events_name","emailaddr_name") VALUES ('door closed','Jim');
INSERT INTO "emailaddr_in_events" ("events_name","emailaddr_name") VALUES ('door closed','bill');
INSERT INTO "emailaddr_in_events" ("events_name","emailaddr_name") VALUES ('door closed','don');

"""
        xprint("loading test data")
        cur = self.con.cursor()
        cleaned_statements = self.process_sql(inserts)
        for stmt in cleaned_statements:
            try:
                cur.execute(stmt)
            except Exception as e:
                xprint(f"\n{stmt}\n{e}")
                exit()
        

    def initialize(self, create_test_data=False):
        create="""
PRAGMA foreign_keys = OFF;
DROP TABLE IF EXISTS mqtt_device;
CREATE TABLE mqtt_device (
    friendly_name TEXT PRIMARY KEY,
    description TEXT,
    source TEXT,                    -- "zigbee", "IP", "manual", etc.
    date TEXT
);

DROP TABLE IF EXISTS mqtt_feature;
CREATE TABLE mqtt_feature (
    mqtt_feature_id INTEGER PRIMARY KEY,  
    friendly_name TEXT NOT NULL,
    property TEXT,                  
    description TEXT,
    type TEXT,                      
    access TEXT,   
    topic TEXT NOT NULL,
    true_value TEXT,  --  NOT NULL,       
    false_value TEXT,
    -- UNIQUE (topic, true_value),
    -- UNIQUE (friendly_name, topic),  
    FOREIGN KEY (friendly_name) 
        REFERENCES mqtt_device (friendly_name)
        ON DELETE CASCADE
);

DROP TABLE IF EXISTS timers;
CREATE TABLE timers (
    timer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mqtt_feature_id INTEGER NOT NULL,
    topic TEXT NOT NULL,
    true_value TEXT NOT NULL,  
       
    false_value TEXT,    
    days TEXT,                    
    start_type TEXT,              
    start_hour INTEGER,           
    start_minute INTEGER,         
    start_offset INTEGER,         
    stop_type TEXT,               
    stop_hour INTEGER,            
    stop_minute INTEGER,          
    stop_offset INTEGER,          
    time_to_stop TEXT,            
    time_to_start TEXT,           
    seconds_from_midnight INTEGER, 
    state INTEGER DEFAULT 0,
    FOREIGN KEY (mqtt_feature_id) 
        REFERENCES mqtt_feature (mqtt_feature_id) 
        ON DELETE CASCADE
);

DROP TABLE IF EXISTS triggers;
CREATE TABLE triggers (
    sub_mqtt_feature_id INTEGER,
    sub_topic TEXT NOT NULL,   -- trigger_daemon subscribes to this
    sub_true_value TEXT NOT NULL,
    sub_payload TEXT NOT NULL, -- if it matches this true_value...
    pub_mqtt_feature_id INTEGER,
    pub_topic TEXT NOT NULL,   -- ...it publishes to this topic
    pub_true_value TEXT NOT NULL,
    pub_payload TEXT NOT NULL, -- ...with this true_value payload
    PRIMARY KEY (sub_topic, sub_payload, pub_topic, pub_payload)
    FOREIGN KEY (sub_mqtt_feature_id) 
        REFERENCES mqtt_feature (id) 
        ON DELETE CASCADE,
    FOREIGN KEY (pub_mqtt_feature_id) 
        REFERENCES mqtt_feature (mqtt_feature_id) 
        ON DELETE CASCADE
);

DROP TABLE IF EXISTS voice_device;
CREATE TABLE voice_device ( -- was wemo (
    id INTEGER PRIMARY KEY,
    mqtt_feature_id INTEGER,  
    voice_name TEXT UNIQUE, 
    port INTEGER UNIQUE,   
    -- friendly_name TEXT,          
    -- property TEXT,
    topic TEXT,
    true_value,
    handler,   -- "wemo" or "hue" 
    qos INTEGER DEFAULT 0,
    retain INTEGER DEFAULT 0,
    FOREIGN KEY (mqtt_feature_id) 
        REFERENCES mqtt_feature (mqtt_feature_id) 
        ON DELETE CASCADE
);

DROP TABLE IF EXISTS cameras;
CREATE TABLE cameras (
    camera_name TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    user TEXT,
    password TEXT,
    rotate INTEGER DEFAULT 0
);

DROP TABLE IF EXISTS emailaddr;
CREATE TABLE emailaddr (
    emailaddr_name TEXT PRIMARY KEY, 
    email_address TEXT NOT NULL      
);

DROP TABLE IF EXISTS events;
CREATE TABLE events (
    mqtt_feature_id INTEGER, 
    events_name TEXT,                 
    mqtt_topic TEXT NOT NULL,   
    -- true_value,              
    matching_payload TEXT NOT NULL,
    only_on_change_of_payload INTEGER DEFAULT 1, 
    subject TEXT,                    
    body TEXT,                    
    PRIMARY KEY (events_name, matching_payload),
    UNIQUE (events_name), -- Required so junction tables can bind to event name alone
    FOREIGN KEY (mqtt_feature_id) 
        REFERENCES mqtt_feature (mqtt_feature_id) 
        ON DELETE CASCADE
);

DROP TABLE IF EXISTS cameras_in_events;
CREATE TABLE cameras_in_events (
    events_name TEXT,
    camera_name TEXT,
    PRIMARY KEY (events_name, camera_name),
    FOREIGN KEY (events_name) 
        REFERENCES events (events_name) 
        ON DELETE CASCADE,
    FOREIGN KEY (camera_name) 
        REFERENCES cameras (camera_name) 
        ON DELETE CASCADE
);

DROP TABLE IF EXISTS emailaddr_in_events;
CREATE TABLE emailaddr_in_events (
    events_name TEXT,
    emailaddr_name TEXT,
    PRIMARY KEY (events_name, emailaddr_name),
    FOREIGN KEY (events_name) 
        REFERENCES events (events_name) 
        ON DELETE CASCADE,
    FOREIGN KEY (emailaddr_name) 
        REFERENCES emailaddr (emailaddr_name) 
        ON DELETE CASCADE
);

        drop table if exists config;
        CREATE TABLE IF NOT EXISTS config ( -- this is a singleton
            id INTEGER PRIMARY KEY CHECK (id = 0),
            alive_interval INTEGER DEFAULT 30,
            publish  TEXT DEFAULT "home/alertaway/power",
            -- zigbee_refresh_seconds INTEGER default 30,
            -- local broker mosquitto
            local_broker_ip TEXT DEFAULT '127.0.0.1',
            local_broker_port INTEGER default 1883,
            local_broker_ssl   INTEGER DEFAULT FALSE,
            local_broker_user  TEXT DEFAULT NULL,
            local_broker_password TEXT DEFAULT NULL,
            local_broker_sleep_seconds INTEGER default 1000,
            local_broker_mqtt_keepalive INTEGER default 120,
            -- cloud broker (optional)
            cloud_broker_ip TEXT  DEFAULT NULL,
            cloud_broker_port INTEGER DEFAULT 1883,
            cloud_broker_ssl  INTEGER DEFAULT FALSE,
            cloud_broker_user TEXT DEFAULT NULL,
            cloud_broker_password TEXT DEFAULT NULL,
            cloud_broker_sleep_seconds INTEGER default 1000,
            cloud_broker_mqtt_keepalive INTEGER default 120,
            --- 
            gmail_password  TEXT DEFAULT NULL,
            gmail_user  TEXT DEFAULT NULL
        );
        INSERT or ignore INTO config (id) VALUES (0);  -- this is a singleton
        PRAGMA foreign_keys = ON;
"""
        cur = self.con.cursor()
        cleaned_statements = self.process_sql(create)
        for stmt in cleaned_statements:
            #xprint(stmt)
            try:
                cur.execute(stmt)
            except Exception as e:
                xprint(f"\n{stmt}\n{e}")
                exit()
                

# test stuff  not running when imported
if __name__ == "__main__":
    input("You are destroying devices.db")
    input("You are destroying devices.db")
    input("YOU ARE DESTROYING DEVICES.DB")
    xprint("opening database")
    db=database()
    xprint("create tables")
    db.initialize()
    xprint("load test data")
    db.test_data()
    xprint("\ninitialized and test data loaded")
    
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






