{
    "Alarm_button": {
        "date": "1724353764",
        "description": "visual and \"audio\" notifier with push button",
        "features": {
            "alert": {
                "access": "sub",
                "description": "visual and/or sound emitter",
                "false_value": "off",
                "topic": "home/hot_water_controller/alert",
                "true_value": "on",
                "type": "binary"
            },
            "button": {
                "access": "pub",
                "description": "simple momentary event",
                "false_value": null,
                "topic": "home/Alarm_button/button",
                "true_value": "pressed",
                "type": "momentary"
            }
        },
        "source": "IP"
    },
    "corded_leak": {
        "date": "1724174257",
        "description": "Water leak sensor",
        "features": {
            "battery_low": {
                "access": "pub",
                "description": "Indicates if the battery of this device is almost empty",
                "false_value": "{\"battery_low\": \"False\"}",
                "topic": "zigbee2mqtt/corded_leak",
                "true_value": "{\"battery_low\": \"True\"}",
                "type": "binary"
            },
            "linkquality": {
                "access": "pub",
                "description": "Link quality (signal strength)",
                "false_value": null,
                "topic": "zigbee2mqtt/corded_leak",
                "true_value": "{\"linkquality\": \"number\"}",
                "type": "numeric"
            },
            "water_leak": {
                "access": "pub",
                "description": "Indicates whether the device detected a water leak",
                "false_value": "{\"water_leak\": \"False\"}",
                "topic": "zigbee2mqtt/corded_leak",
                "true_value": "{\"water_leak\": \"True\"}",
                "type": "binary"
            }
        },
        "source": "ZB"
    },
    "dave": {
        "date": "1724174257",
        "description": "Zigbee smart switch changed",
        "features": {
            "power_on_behavior": {
                "access": "sub",
                "description": "Controls the behavior when the device is powered on after power loss. If you get an `UNSUPPORTED_ATTRIBUTE` error, the device does not support it.",
                "false_value": "{\"power_on_behavior\": \"off\"}",
                "topic": "zigbee2mqtt/dave/set",
                "true_value": "{\"power_on_behavior\": \"on\"}",
                "type": "enum"
            },
            "state": {
                "access": "sub",
                "description": "On/off state of the switch",
                "false_value": "{\"state\": \"OFF\"}",
                "topic": "zigbee2mqtt/dave/set",
                "true_value": "{\"state\": \"ON\"}",
                "type": "binary"
            }
        },
        "source": "ZB"
    },
    "demo_wall_switch": {
        "date": "1724174262",
        "description": "Zigbee in-wall smart switch",
        "features": {
            "power_on_behavior": {
                "access": "sub",
                "description": "Controls the behavior when the device is powered on after power loss. If you get an `UNSUPPORTED_ATTRIBUTE` error, the device does not support it.",
                "false_value": "{\"power_on_behavior changed\": \"off\"}",
                "topic": "zigbee2mqtt/demo_wall_switch/set",
                "true_value": "{\"power_on_behavior\": \"on\"}",
                "type": "enum"
            },
            "state": {
                "access": "sub",
                "description": "On/off state of the switch",
                "false_value": "{\"state\": \"OFF\"}",
                "topic": "zigbee2mqtt/demo_wall_switch/set",
                "true_value": "{\"state\": \"ON\"}",
                "type": "binary"
            }
        },
        "source": "ZB"
    },
    "door_bell": {
        "date": "1723405303",
        "description": "Four different chimes and a button",
        "features": {
            "ding_ding": {
                "access": "sub",
                "description": "Ding ding chime",
                "false_value": null,
                "topic": "home/door_bell/ding_ding",
                "true_value": "pressed",
                "type": "momentary"
            },
            "ding_dong": {
                "access": "sub",
                "description": "Ding dong chime",
                "false_value": null,
                "topic": "home/door_bell/ding_dong",
                "true_value": "pressed",
                "type": "momentary"
            },
            "three_chimes": {
                "access": "sub",
                "description": "westminster_abby, ding ding and ding dong chimes",
                "false_value": null,
                "topic": "home/door_bell/three_chimes",
                "true_value": "pressed",
                "type": "momentary"
            },
            "westminster_abby": {
                "access": "sub",
                "description": "Westminster abby chime",
                "false_value": null,
                "topic": "home/door_bell/westminster_abby",
                "true_value": "pressed",
                "type": "momentary"
            }
        },
        "source": "IP"
    },
    "hot_water_controller": {
        "date": "1724353653",
        "description": "tankless water heater recirc controller",
        "features": {
            "button": {
                "access": "sub",
                "description": "simple momentary event",
                "false_value": null,
                "topic": "home/Alarm_button/button",
                "true_value": "pressed",
                "type": "momentary"
            }
        },
        "source": "IP"
    },
    "inline": {
        "date": "1724174257",
        "description": "Zigbee on/off controller",
        "features": {
            "state": {
                "access": "sub",
                "description": "On/off state of the switch",
                "false_value": "{\"state\": \"OFF\"}",
                "topic": "zigbee2mqtt/inline/set",
                "true_value": "{\"state\": \"ON\"}",
                "type": "binary"
            }
        },
        "source": "ZB"
    },
    "mag_switch": {
        "date": "1724174256",
        "description": "Door sensor",
        "features": {
            "battery_low": {
                "access": "pub",
                "description": "Indicates if the battery of this device is almost empty",
                "false_value": "{\"battery_low\": \"False\"}",
                "topic": "zigbee2mqtt/mag_switch",
                "true_value": "{\"battery_low\": \"True\"}",
                "type": "binary"
            },
            "contact": {
                "access": "pub",
                "description": "Indicates if the contact is closed (= true) or open (= false)",
                "false_value": "{\"contact\": \"True\"}",
                "topic": "zigbee2mqtt/mag_switch",
                "true_value": "{\"contact\": \"False\"}",
                "type": "binary"
            },
            "linkquality": {
                "access": "pub",
                "description": "Link quality (signal strength)",
                "false_value": null,
                "topic": "zigbee2mqtt/mag_switch",
                "true_value": "{\"linkquality\": \"number\"}",
                "type": "numeric"
            },
            "tamper": {
                "access": "pub",
                "description": "Indicates whether the device is tampered",
                "false_value": "{\"tamper\": \"False\"}",
                "topic": "zigbee2mqtt/mag_switch",
                "true_value": "{\"tamper\": \"True\"}",
                "type": "binary"
            },
            "voltage": {
                "access": "pub",
                "description": "Voltage of the battery in millivolts",
                "false_value": null,
                "topic": "zigbee2mqtt/mag_switch",
                "true_value": "{\"voltage\": \"number\"}",
                "type": "numeric"
            }
        },
        "source": "ZB"
    },
    "main_valve": {
        "date": "1722796861",
        "description": "motor valve controller, with feedback",
        "features": {
            "state": {
                "access": "pub",
                "description": "current state on, off or unknown",
                "false_value": "off",
                "topic": "home/main_valve/state",
                "true_value": "on",
                "type": "binary"
            },
            "toggle": {
                "access": "sub",
                "description": "supports on and off",
                "false_value": "off",
                "topic": "home/main_valve/toggle",
                "true_value": "on",
                "type": "binary"
            }
        },
        "source": "IP"
    },
    "motion1": {
        "date": "1724174259",
        "description": "Motion sensor with scene switch",
        "features": {
            "battery": {
                "access": "pub",
                "description": "Remaining battery in %, can take up to 24 hours before reported",
                "false_value": null,
                "topic": "zigbee2mqtt/motion1",
                "true_value": "{\"battery\": \"number\"}",
                "type": "numeric"
            },
            "light": {
                "access": "pub",
                "description": null,
                "false_value": "{\"light\": \"off\"}",
                "topic": "zigbee2mqtt/motion1",
                "true_value": "{\"light\": \"on\"}",
                "type": "enum"
            },
            "linkquality": {
                "access": "pub",
                "description": "Link quality (signal strength)",
                "false_value": null,
                "topic": "zigbee2mqtt/motion1",
                "true_value": "{\"linkquality\": \"number\"}",
                "type": "numeric"
            },
            "occupancy": {
                "access": "pub",
                "description": "Indicates whether the device detected occupancy",
                "false_value": "{\"occupancy\": \"False\"}",
                "topic": "zigbee2mqtt/motion1",
                "true_value": "{\"occupancy\": \"True\"}",
                "type": "binary"
            },
            "voltage": {
                "access": "pub",
                "description": "Voltage of the battery in millivolts",
                "false_value": null,
                "topic": "zigbee2mqtt/motion1",
                "true_value": "{\"voltage\": \"number\"}",
                "type": "numeric"
            }
        },
        "source": "ZB"
    },
    "office_bath_wall_switch": {
        "date": "1724174261",
        "description": "In-wall smart switch",
        "features": {
            "linkquality": {
                "access": "pub",
                "description": "Link quality (signal strength)",
                "false_value": null,
                "topic": "zigbee2mqtt/office_bath_wall_switch",
                "true_value": "{\"linkquality\": \"number\"}",
                "type": "numeric"
            },
            "power": {
                "access": "pub",
                "description": "Instantaneous measured power",
                "false_value": null,
                "topic": "zigbee2mqtt/office_bath_wall_switch",
                "true_value": "{\"power\": \"number\"}",
                "type": "numeric"
            },
            "state": {
                "access": "sub",
                "description": "On/off state of the switch",
                "false_value": "{\"state\": \"OFF\"}",
                "topic": "zigbee2mqtt/office_bath_wall_switch/set",
                "true_value": "{\"state\": \"ON\"}",
                "type": "binary"
            }
        },
        "source": "ZB"
    },
    "round_leak": {
        "date": "1724174257",
        "description": "Water leak detector",
        "features": {
            "battery_low": {
                "access": "pub",
                "description": "Indicates if the battery of this device is almost empty",
                "false_value": "{\"battery_low\": \"False\"}",
                "topic": "zigbee2mqtt/round_leak",
                "true_value": "{\"battery_low\": \"True\"}",
                "type": "binary"
            },
            "linkquality": {
                "access": "pub",
                "description": "Link quality (signal strength)",
                "false_value": null,
                "topic": "zigbee2mqtt/round_leak",
                "true_value": "{\"linkquality\": \"number\"}",
                "type": "numeric"
            },
            "tamper": {
                "access": "pub",
                "description": "Indicates whether the device is tampered",
                "false_value": "{\"tamper\": \"False\"}",
                "topic": "zigbee2mqtt/round_leak",
                "true_value": "{\"tamper\": \"True\"}",
                "type": "binary"
            },
            "water_leak": {
                "access": "pub",
                "description": "Indicates whether the device detected a water leak",
                "false_value": "{\"water_leak\": \"False\"}",
                "topic": "zigbee2mqtt/round_leak",
                "true_value": "{\"water_leak\": \"True\"}",
                "type": "binary"
            }
        },
        "source": "ZB"
    },
    "sam": {
        "date": "1724174256",
        "description": "Zigbee smart switch",
        "features": {
            "power_on_behavior": {
                "access": "sub",
                "description": "Controls the behavior when the device is powered on after power loss. If you get an `UNSUPPORTED_ATTRIBUTE` error, the device does not support it.",
                "false_value": "{\"power_on_behavior\": \"off\"}",
                "topic": "zigbee2mqtt/sam/set",
                "true_value": "{\"power_on_behavior\": \"on\"}",
                "type": "enum"
            },
            "state": {
                "access": "sub",
                "description": "On/off state of the switch",
                "false_value": "{\"state\": \"OFF\"}",
                "topic": "zigbee2mqtt/sam/set",
                "true_value": "{\"state\": \"ON\"}",
                "type": "binary"
            }
        },
        "source": "ZB"
    },
    "ss1": {
        "date": "1724174257",
        "description": "1 gang switch",
        "features": {
            "power_on_behavior": {
                "access": "sub",
                "description": "Controls the behavior when the device is powered on after power loss. If you get an `UNSUPPORTED_ATTRIBUTE` error, the device does not support it.",
                "false_value": "{\"power_on_behavior\": \"off\"}",
                "topic": "zigbee2mqtt/ss1/set",
                "true_value": "{\"power_on_behavior\": \"on\"}",
                "type": "enum"
            },
            "state": {
                "access": "sub",
                "description": "On/off state of the switch",
                "false_value": "{\"state\": \"OFF\"}",
                "topic": "zigbee2mqtt/ss1/set",
                "true_value": "{\"state\": \"ON\"}",
                "type": "binary"
            }
        },
        "source": "ZB"
    },
    "ss2": {
        "date": "1724174263",
        "description": "1 gang switch",
        "features": {
            "power_on_behavior": {
                "access": "sub",
                "description": "Controls the behavior when the device is powered on after power loss. If you get an `UNSUPPORTED_ATTRIBUTE` error, the device does not support it.",
                "false_value": "{\"power_on_behavior\": \"off\"}",
                "topic": "zigbee2mqtt/ss2/set",
                "true_value": "{\"power_on_behavior\": \"on\"}",
                "type": "enum"
            },
            "state": {
                "access": "sub",
                "description": "On/off state of the switch",
                "false_value": "{\"state\": \"OFF\"}",
                "topic": "zigbee2mqtt/ss2/set",
                "true_value": "{\"state\": \"ON\"}",
                "type": "binary"
            }
        },
        "source": "ZB"
    },
    "ss_quad_1": {
        "date": "1724174260",
        "description": "4 channel relay",
        "features": {
            "backlight_mode": {
                "access": "sub",
                "description": "Mode of the backlight",
                "false_value": "{\"backlight_mode\": \"OFF\"}",
                "topic": "zigbee2mqtt/ss_quad_1/set",
                "true_value": "{\"backlight_mode\": \"ON\"}",
                "type": "binary"
            },
            "linkquality": {
                "access": "pub",
                "description": "Link quality (signal strength)",
                "false_value": null,
                "topic": "zigbee2mqtt/ss_quad_1",
                "true_value": "{\"linkquality\": \"number\"}",
                "type": "numeric"
            },
            "power_on_behavior_l1": {
                "access": "sub",
                "description": "Controls the behavior when the device is powered on after power loss. If you get an `UNSUPPORTED_ATTRIBUTE` error, the device does not support it.",
                "false_value": "{\"power_on_behavior_l1\": \"off\"}",
                "topic": "zigbee2mqtt/ss_quad_1/set",
                "true_value": "{\"power_on_behavior_l1\": \"on\"}",
                "type": "enum"
            },
            "power_on_behavior_l2": {
                "access": "sub",
                "description": "Controls the behavior when the device is powered on after power loss. If you get an `UNSUPPORTED_ATTRIBUTE` error, the device does not support it.",
                "false_value": "{\"power_on_behavior_l2\": \"off\"}",
                "topic": "zigbee2mqtt/ss_quad_1/set",
                "true_value": "{\"power_on_behavior_l2\": \"on\"}",
                "type": "enum"
            },
            "power_on_behavior_l3": {
                "access": "sub",
                "description": "Controls the behavior when the device is powered on after power loss. If you get an `UNSUPPORTED_ATTRIBUTE` error, the device does not support it.",
                "false_value": "{\"power_on_behavior_l3\": \"off\"}",
                "topic": "zigbee2mqtt/ss_quad_1/set",
                "true_value": "{\"power_on_behavior_l3\": \"on\"}",
                "type": "enum"
            },
            "power_on_behavior_l4": {
                "access": "sub",
                "description": "Controls the behavior when the device is powered on after power loss. If you get an `UNSUPPORTED_ATTRIBUTE` error, the device does not support it.",
                "false_value": "{\"power_on_behavior_l4\": \"off\"}",
                "topic": "zigbee2mqtt/ss_quad_1/set",
                "true_value": "{\"power_on_behavior_l4\": \"on\"}",
                "type": "enum"
            },
            "state_l1": {
                "access": "sub",
                "description": "On/off state of the switch",
                "false_value": "{\"state_l1\": \"OFF\"}",
                "topic": "zigbee2mqtt/ss_quad_1/set",
                "true_value": "{\"state_l1\": \"ON\"}",
                "type": "binary"
            },
            "state_l2": {
                "access": "sub",
                "description": "On/off state of the switch",
                "false_value": "{\"state_l2\": \"OFF\"}",
                "topic": "zigbee2mqtt/ss_quad_1/set",
                "true_value": "{\"state_l2\": \"ON\"}",
                "type": "binary"
            },
            "state_l3": {
                "access": "sub",
                "description": "On/off state of the switch",
                "false_value": "{\"state_l3\": \"OFF\"}",
                "topic": "zigbee2mqtt/ss_quad_1/set",
                "true_value": "{\"state_l3\": \"ON\"}",
                "type": "binary"
            },
            "state_l4": {
                "access": "sub",
                "description": "On/off state of the switch",
                "false_value": "{\"state_l4\": \"OFF\"}",
                "topic": "zigbee2mqtt/ss_quad_1/set",
                "true_value": "{\"state_l4\": \"ON\"}",
                "type": "binary"
            }
        },
        "source": "ZB"
    },
    "temp1": {
        "date": "1724174260",
        "description": "Temperature and humidity sensor",
        "features": {
            "humidity": {
                "access": "pub",
                "description": "Measured relative humidity",
                "false_value": null,
                "topic": "zigbee2mqtt/temp1",
                "true_value": "{\"humidity\": \"number\"}",
                "type": "numeric"
            },
            "linkquality": {
                "access": "pub",
                "description": "Link quality (signal strength)",
                "false_value": null,
                "topic": "zigbee2mqtt/temp1",
                "true_value": "{\"linkquality\": \"number\"}",
                "type": "numeric"
            },
            "temperature": {
                "access": "pub",
                "description": "Measured temperature value",
                "false_value": null,
                "topic": "zigbee2mqtt/temp1",
                "true_value": "{\"temperature\": \"number\"}",
                "type": "numeric"
            },
            "voltage": {
                "access": "pub",
                "description": "Voltage of the battery in millivolts",
                "false_value": null,
                "topic": "zigbee2mqtt/temp1",
                "true_value": "{\"voltage\": \"number\"}",
                "type": "numeric"
            }
        },
        "source": "ZB"
    },
    "test_valve": {
        "date": "1722472406",
        "description": "motor valve controller, with feedback",
        "source": "IP"
    }
}