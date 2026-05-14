sample_zigbee2mqtt_bridge_devices = '''
[
    {
        "definition": null,
        "disabled": false,
        "endpoints": {
            "1": {
                "bindings": [],
                "clusters": {
                    "input": [],
                    "output": []
                },
                "configured_reportings": [],
                "scenes": []
            },
            "10": {
                "bindings": [],
                "clusters": {
                    "input": [],
                    "output": []
                },
                "configured_reportings": [],
                "scenes": []
            },
            "11": {
                "bindings": [],
                "clusters": {
                    "input": [
                        "ssIasAce",
                        "genTime"
                    ],
                    "output": [
                        "ssIasZone",
                        "ssIasWd"
                    ]
                },
                "configured_reportings": [],
                "scenes": []
            },
            "110": {
                "bindings": [],
                "clusters": {
                    "input": [],
                    "output": []
                },
                "configured_reportings": [],
                "scenes": []
            },
            "12": {
                "bindings": [],
                "clusters": {
                    "input": [],
                    "output": []
                },
                "configured_reportings": [],
                "scenes": []
            },
            "13": {
                "bindings": [],
                "clusters": {
                    "input": [
                        "genOta"
                    ],
                    "output": []
                },
                "configured_reportings": [],
                "scenes": []
            },
            "2": {
                "bindings": [],
                "clusters": {
                    "input": [],
                    "output": []
                },
                "configured_reportings": [],
                "scenes": []
            },
            "242": {
                "bindings": [],
                "clusters": {
                    "input": [],
                    "output": []
                },
                "configured_reportings": [],
                "scenes": []
            },
            "3": {
                "bindings": [],
                "clusters": {
                    "input": [],
                    "output": []
                },
                "configured_reportings": [],
                "scenes": []
            },
            "4": {
                "bindings": [],
                "clusters": {
                    "input": [],
                    "output": []
                },
                "configured_reportings": [],
                "scenes": []
            },
            "47": {
                "bindings": [],
                "clusters": {
                    "input": [],
                    "output": []
                },
                "configured_reportings": [],
                "scenes": []
            },
            "5": {
                "bindings": [],
                "clusters": {
                    "input": [],
                    "output": []
                },
                "configured_reportings": [],
                "scenes": []
            },
            "6": {
                "bindings": [],
                "clusters": {
                    "input": [],
                    "output": []
                },
                "configured_reportings": [],
                "scenes": []
            },
            "8": {
                "bindings": [],
                "clusters": {
                    "input": [],
                    "output": []
                },
                "configured_reportings": [],
                "scenes": []
            }
        },
        "friendly_name": "Coordinator",
        "ieee_address": "0x00124b0024c2bb71",
        "interview_completed": true,
        "interviewing": false,
        "network_address": 0,
        "supported": false,
        "type": "Coordinator"
    },
    {
        "date_code": "20210610-BL",
        "definition": {
            "description": "Zigbee smart switch",
            "exposes": [
                {
                    "features": [
                        {
                            "access": 7,
                            "description": "On/off state of the switch",
                            "name": "state",
                            "property": "state",
                            "type": "binary",
                            "value_off": "OFF",
                            "value_on": "ON",
                            "value_toggle": "TOGGLE"
                        }
                    ],
                    "type": "switch"
                },
                {
                    "access": 7,
                    "description": "Controls the behavior when the device is powered on after power loss",
                    "name": "power_on_behavior",
                    "property": "power_on_behavior",
                    "type": "enum",
                    "values": [
                        "off",
                        "on",
                        "toggle",
                        "previous"
                    ]
                },
                {
                    "access": 1,
                    "description": "Link quality (signal strength)",
                    "name": "linkquality",
                    "property": "linkquality",
                    "type": "numeric",
                    "unit": "lqi",
                    "value_max": 255,
                    "value_min": 0
                }
            ],
            "model": "SWITCH-ZR03-1",
            "options": [
                {
                    "access": 2,
                    "description": "State actions will also be published as 'action' when true (default false).",
                    "name": "state_action",
                    "property": "state_action",
                    "type": "binary",
                    "value_off": false,
                    "value_on": true
                }
            ],
            "supports_ota": false,
            "vendor": "eWeLink"
        },
        "disabled": false,
        "endpoints": {
            "1": {
                "bindings": [
                    {
                        "cluster": "genOnOff",
                        "target": {
                            "endpoint": 242,
                            "ieee_address": "0x00124b0024c2bb71",
                            "type": "endpoint"
                        }
                    },
                    {
                        "cluster": "genOnOff",
                        "target": {
                            "endpoint": 1,
                            "ieee_address": "0x00124b0024c2bb71",
                            "type": "endpoint"
                        }
                    }
                ],
                "clusters": {
                    "input": [
                        "genBasic",
                        "genIdentify",
                        "genGroups",
                        "genScenes",
                        "genOnOff",
                        "touchlink",
                        "64599",
                        "64529"
                    ],
                    "output": [
                        "genOta"
                    ]
                },
                "configured_reportings": [],
                "scenes": []
            },
            "242": {
                "bindings": [],
                "clusters": {
                    "input": [],
                    "output": [
                        "greenPower"
                    ]
                },
                "configured_reportings": [],
                "scenes": []
            }
        },
        "friendly_name": "",
        "ieee_address": "0x7cb94c6322c30000_bob",
        "interview_completed": true,
        "interviewing": false,
        "manufacturer": "eWeLink",
        "model_id": "SWITCH-ZR03-1",
        "network_address": 21793,
        "power_source": "Unknown",
        "software_build_id": "1.1.0",
        "supported": true,
        "type": "Router"
    },
    {
        "date_code": "20210610-BL",
        "definition": {
            "description": "Zigbee smart switch",
            "exposes": [
                {
                    "features": [
                        {
                            "access": 7,
                            "description": "On/off state of the switch",
                            "name": "state",
                            "property": "state",
                            "type": "binary",
                            "value_off": "OFF",
                            "value_on": "ON",
                            "value_toggle": "TOGGLE"
                        }
                    ],
                    "type": "switch"
                },
                {
                    "access": 7,
                    "description": "Controls the behavior when the device is powered on after power loss",
                    "name": "power_on_behavior",
                    "property": "power_on_behavior",
                    "type": "enum",
                    "values": [
                        "off",
                        "on",
                        "toggle",
                        "previous"
                    ]
                },
                {
                    "access": 1,
                    "description": "Link quality (signal strength)",
                    "name": "linkquality",
                    "property": "linkquality",
                    "type": "numeric",
                    "unit": "lqi",
                    "value_max": 255,
                    "value_min": 0
                }
            ],
            "model": "SWITCH-ZR03-1",
            "options": [
                {
                    "access": 2,
                    "description": "State actions will also be published as 'action' when true (default false).",
                    "name": "state_action",
                    "property": "state_action",
                    "type": "binary",
                    "value_off": false,
                    "value_on": true
                }
            ],
            "supports_ota": false,
            "vendor": "eWeLink"
        },
        "disabled": false,
        "endpoints": {
            "1": {
                "bindings": [
                    {
                        "cluster": "genOnOff",
                        "target": {
                            "endpoint": 242,
                            "ieee_address": "0x00124b0024c2bb71",
                            "type": "endpoint"
                        }
                    }
                ],
                "clusters": {
                    "input": [
                        "genBasic",
                        "genIdentify",
                        "genGroups",
                        "genScenes",
                        "genOnOff",
                        "touchlink",
                        "64599",
                        "64529"
                    ],
                    "output": [
                        "genOta"
                    ]
                },
                "configured_reportings": [],
                "scenes": []
            },
            "242": {
                "bindings": [],
                "clusters": {
                    "input": [],
                    "output": [
                        "greenPower"
                    ]
                },
                "configured_reportings": [],
                "scenes": []
            }
        },
        "friendly_name": "sam",
        "ieee_address": "0x7cb94c6354b20000",
        "interview_completed": true,
        "interviewing": false,
        "manufacturer": "eWeLink",
        "model_id": "SWITCH-ZR03-1",
        "network_address": 47126,
        "power_source": "Unknown",
        "software_build_id": "1.1.0",
        "supported": true,
        "type": "Router"
    },
    {
        "date_code": "",
        "definition": {
            "description": "Water leak detector",
            "exposes": [
                {
                    "access": 1,
                    "description": "Indicates whether the device detected a water leak",
                    "name": "water_leak",
                    "property": "water_leak",
                    "type": "binary",
                    "value_off": false,
                    "value_on": true
                },
                {
                    "access": 1,
                    "description": "Indicates if the battery of this device is almost empty",
                    "name": "battery_low",
                    "property": "battery_low",
                    "type": "binary",
                    "value_off": false,
                    "value_on": true
                },
                {
                    "access": 1,
                    "description": "Remaining battery in %, can take up to 24 hours before reported.",
                    "name": "battery",
                    "property": "battery",
                    "type": "numeric",
                    "unit": "%",
                    "value_max": 100,
                    "value_min": 0
                },
                {
                    "access": 1,
                    "description": "Link quality (signal strength)",
                    "name": "linkquality",
                    "property": "linkquality",
                    "type": "numeric",
                    "unit": "lqi",
                    "value_max": 255,
                    "value_min": 0
                }
            ],
            "model": "TS0207_water_leak_detector",
            "options": [],
            "supports_ota": false,
            "vendor": "TuYa"
        },
        "disabled": false,
        "endpoints": {
            "1": {
                "bindings": [
                    {
                        "cluster": "genPowerCfg",
                        "target": {
                            "endpoint": 242,
                            "ieee_address": "0x00124b0024c2bb71",
                            "type": "endpoint"
                        }
                    }
                ],
                "clusters": {
                    "input": [
                        "genBasic",
                        "genPowerCfg",
                        "genIdentify",
                        "ssIasZone"
                    ],
                    "output": [
                        "genOta",
                        "genTime"
                    ]
                },
                "configured_reportings": [
                    {
                        "attribute": "batteryPercentageRemaining",
                        "cluster": "genPowerCfg",
                        "maximum_report_interval": 62000,
                        "minimum_report_interval": 3600,
                        "reportable_change": 0
                    }
                ],
                "scenes": []
            }
        },
        "friendly_name": "pub leak",
        "ieee_address": "0x847127fffe17c7b9",
        "interview_completed": true,
        "interviewing": false,
        "manufacturer": "_TZ3000_jjua3lql",
        "model_id": "TS0207",
        "network_address": 64578,
        "power_source": "Battery",
        "supported": true,
        "type": "EndDevice"
    },
    {
        "date_code": "20190907-V102",
        "definition": {
            "description": "Zigbee smart plug",
            "exposes": [
                {
                    "features": [
                        {
                            "access": 7,
                            "description": "On/off state of the switch",
                            "name": "state",
                            "property": "state",
                            "type": "binary",
                            "value_off": "OFF",
                            "value_on": "ON",
                            "value_toggle": "TOGGLE"
                        }
                    ],
                    "type": "switch"
                },
                {
                    "access": 1,
                    "description": "Link quality (signal strength)",
                    "name": "linkquality",
                    "property": "linkquality",
                    "type": "numeric",
                    "unit": "lqi",
                    "value_max": 255,
                    "value_min": 0
                }
            ],
            "model": "SA-003-Zigbee",
            "options": [
                {
                    "access": 2,
                    "description": "State actions will also be published as 'action' when true (default false).",
                    "name": "state_action",
                    "property": "state_action",
                    "type": "binary",
                    "value_off": false,
                    "value_on": true
                }
            ],
            "supports_ota": false,
            "vendor": "eWeLink"
        },
        "disabled": false,
        "endpoints": {
            "1": {
                "bindings": [
                    {
                        "cluster": "genOnOff",
                        "target": {
                            "endpoint": 1,
                            "ieee_address": "0x00124b0024c2bb71",
                            "type": "endpoint"
                        }
                    }
                ],
                "clusters": {
                    "input": [
                        "genBasic",
                        "genIdentify",
                        "genGroups",
                        "genScenes",
                        "genOnOff"
                    ],
                    "output": [
                        "genBasic"
                    ]
                },
                "configured_reportings": [],
                "scenes": []
            }
        },
        "friendly_name": "jake",
        "ieee_address": "0x00124b001b7c000e",
        "interview_completed": true,
        "interviewing": false,
        "manufacturer": "eWeLink",
        "model_id": "SA-003-Zigbee",
        "network_address": 25656,
        "power_source": "Mains (single phase)",
        "supported": true,
        "type": "Router"
    },
    {
        "date_code": "20190907-V102",
        "definition": {
            "description": "Zigbee smart plug",
            "exposes": [
                {
                    "features": [
                        {
                            "access": 7,
                            "description": "On/off state of the switch",
                            "name": "state",
                            "property": "state",
                            "type": "binary",
                            "value_off": "OFF",
                            "value_on": "ON",
                            "value_toggle": "TOGGLE"
                        }
                    ],
                    "type": "switch"
                },
                {
                    "access": 1,
                    "description": "Link quality (signal strength)",
                    "name": "linkquality",
                    "property": "linkquality",
                    "type": "numeric",
                    "unit": "lqi",
                    "value_max": 255,
                    "value_min": 0
                }
            ],
            "model": "SA-003-Zigbee",
            "options": [
                {
                    "access": 2,
                    "description": "State actions will also be published as 'action' when true (default false).",
                    "name": "state_action",
                    "property": "state_action",
                    "type": "binary",
                    "value_off": false,
                    "value_on": true
                }
            ],
            "supports_ota": false,
            "vendor": "eWeLink"
        },
        "disabled": false,
        "endpoints": {
            "1": {
                "bindings": [
                    {
                        "cluster": "genOnOff",
                        "target": {
                            "endpoint": 1,
                            "ieee_address": "0x00124b0024c2bb71",
                            "type": "endpoint"
                        }
                    }
                ],
                "clusters": {
                    "input": [
                        "genBasic",
                        "genIdentify",
                        "genGroups",
                        "genScenes",
                        "genOnOff"
                    ],
                    "output": [
                        "genBasic"
                    ]
                },
                "configured_reportings": [],
                "scenes": []
            }
        },
        "friendly_name": "joe",
        "ieee_address": "0x00124b001cd51f43",
        "interview_completed": true,
        "interviewing": false,
        "manufacturer": "eWeLink",
        "model_id": "SA-003-Zigbee",
        "network_address": 25795,
        "power_source": "Mains (single phase)",
        "supported": true,
        "type": "Router"
    },
    {
        "date_code": "",
        "definition": {
            "description": "Temperature & humidity sensor with display",
            "exposes": [
                {
                    "access": 1,
                    "description": "Remaining battery in %, can take up to 24 hours before reported.",
                    "name": "battery",
                    "property": "battery",
                    "type": "numeric",
                    "unit": "%",
                    "value_max": 100,
                    "value_min": 0
                },
                {
                    "access": 1,
                    "description": "Measured temperature value",
                    "name": "temperature",
                    "property": "temperature",
                    "type": "numeric",
                    "unit": "°C"
                },
                {
                    "access": 1,
                    "description": "Measured relative humidity",
                    "name": "humidity",
                    "property": "humidity",
                    "type": "numeric",
                    "unit": "%"
                },
                {
                    "access": 1,
                    "description": "Voltage of the battery in millivolts",
                    "name": "voltage",
                    "property": "voltage",
                    "type": "numeric",
                    "unit": "mV"
                },
                {
                    "access": 1,
                    "description": "Link quality (signal strength)",
                    "name": "linkquality",
                    "property": "linkquality",
                    "type": "numeric",
                    "unit": "lqi",
                    "value_max": 255,
                    "value_min": 0
                }
            ],
            "model": "TS0201",
            "options": [
                {
                    "access": 2,
                    "description": "Number of digits after decimal point for temperature, takes into effect on next report of device.",
                    "name": "temperature_precision",
                    "property": "temperature_precision",
                    "type": "numeric",
                    "value_max": 3,
                    "value_min": 0
                },
                {
                    "access": 2,
                    "description": "Calibrates the temperature value (absolute offset), takes into effect on next report of device.",
                    "name": "temperature_calibration",
                    "property": "temperature_calibration",
                    "type": "numeric"
                },
                {
                    "access": 2,
                    "description": "Number of digits after decimal point for humidity, takes into effect on next report of device.",
                    "name": "humidity_precision",
                    "property": "humidity_precision",
                    "type": "numeric",
                    "value_max": 3,
                    "value_min": 0
                },
                {
                    "access": 2,
                    "description": "Calibrates the humidity value (absolute offset), takes into effect on next report of device.",
                    "name": "humidity_calibration",
                    "property": "humidity_calibration",
                    "type": "numeric"
                }
            ],
            "supports_ota": false,
            "vendor": "TuYa"
        },
        "disabled": false,
        "endpoints": {
            "1": {
                "bindings": [],
                "clusters": {
                    "input": [
                        "genPowerCfg",
                        "genIdentify",
                        "msTemperatureMeasurement",
                        "msRelativeHumidity",
                        "genBasic"
                    ],
                    "output": [
                        "genIdentify",
                        "genOta",
                        "genTime"
                    ]
                },
                "configured_reportings": [],
                "scenes": []
            }
        },
        "friendly_name": "Temp and Humid 1",
        "ieee_address": "0xa4c13853dd247061",
        "interview_completed": true,
        "interviewing": false,
        "manufacturer": "_TZ3000_0s1izerx",
        "model_id": "TS0201",
        "network_address": 49320,
        "power_source": "Battery",
        "supported": true,
        "type": "EndDevice"
    },
    {
        "date_code": "",
        "definition": {
            "description": "Door sensor",
            "exposes": [
                {
                    "access": 1,
                    "description": "Indicates if the contact is closed (= true) or open (= false)",
                    "name": "contact",
                    "property": "contact",
                    "type": "binary",
                    "value_off": true,
                    "value_on": false
                },
                {
                    "access": 1,
                    "description": "Indicates if the battery of this device is almost empty",
                    "name": "battery_low",
                    "property": "battery_low",
                    "type": "binary",
                    "value_off": false,
                    "value_on": true
                },
                {
                    "access": 1,
                    "description": "Indicates whether the device is tampered",
                    "name": "tamper",
                    "property": "tamper",
                    "type": "binary",
                    "value_off": false,
                    "value_on": true
                },
                {
                    "access": 1,
                    "description": "Remaining battery in %, can take up to 24 hours before reported.",
                    "name": "battery",
                    "property": "battery",
                    "type": "numeric",
                    "unit": "%",
                    "value_max": 100,
                    "value_min": 0
                },
                {
                    "access": 1,
                    "description": "Voltage of the battery in millivolts",
                    "name": "voltage",
                    "property": "voltage",
                    "type": "numeric",
                    "unit": "mV"
                },
                {
                    "access": 1,
                    "description": "Link quality (signal strength)",
                    "name": "linkquality",
                    "property": "linkquality",
                    "type": "numeric",
                    "unit": "lqi",
                    "value_max": 255,
                    "value_min": 0
                }
            ],
            "model": "TS0203",
            "options": [],
            "supports_ota": false,
            "vendor": "TuYa"
        },
        "disabled": false,
        "endpoints": {
            "1": {
                "bindings": [],
                "clusters": {
                    "input": [
                        "genPowerCfg",
                        "genIdentify",
                        "ssIasZone",
                        "genBasic"
                    ],
                    "output": [
                        "genIdentify",
                        "genGroups",
                        "genScenes",
                        "genOnOff",
                        "genLevelCtrl",
                        "touchlink",
                        "genOta",
                        "genTime"
                    ]
                },
                "configured_reportings": [],
                "scenes": []
            }
        },
        "friendly_name": "door sensor",
        "ieee_address": "0xa4c13839f388d8ec",
        "interview_completed": true,
        "interviewing": false,
        "manufacturer": "_TZ3000_26fmupbb",
        "model_id": "TS0203",
        "network_address": 61969,
        "power_source": "Battery",
        "supported": true,
        "type": "EndDevice"
    }
]
'''