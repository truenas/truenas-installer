# API Specification

This API uses JSON-RPC 2.0: https://www.jsonrpc.org/specification

# Server methods

## adopt

“Adopt” the system. It will return an access key that must be used to authenticate on this system when
re-connecting.

### Result jsonschema

    {
      "type": "string"
    }

## authenticate

Authenticate the connection on the “adopted” system.

### Parameter jsonschema

    {
      "type": "string"
    }

## install

Performs system installation.

### Parameter jsonschema

    {
      "type": "object",
      "required": [
        "disks",
        "create_swap",
        "set_pmbr",
        "authentication"
      ],
      "additionalProperties": false,
      "properties": {
        "disks": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "create_swap": {
          "type": "boolean"
        },
        "set_pmbr": {
          "type": "boolean"
        },
        "authentication": {
          "type": [
            "object",
            "null"
          ],
          "required": [
            "username",
            "password"
          ],
          "additionalProperties": false,
          "properties": {
            "username": {
              "type": "string",
              "enum": [
                "admin",
                "root"
              ]
            },
            "password": {
              "type": "string",
              "minLength": 6
            }
          }
        },
        "post_install": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "network_interfaces": {
              "type": "array",
              "items": {
                "type": "object",
                "required": [
                  "name"
                ],
                "additionalProperties": false,
                "properties": {
                  "name": {
                    "type": "string"
                  },
                  "aliases": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "required": [
                        "type",
                        "address",
                        "netmask"
                      ],
                      "additionalProperties": false,
                      "properties": {
                        "type": {
                          "type": "string"
                        },
                        "address": {
                          "type": "string"
                        },
                        "netmask": {
                          "type": "integer"
                        }
                      }
                    }
                  },
                  "ipv4_dhcp": {
                    "type": "boolean"
                  },
                  "ipv6_auto": {
                    "type": "boolean"
                  }
                }
              }
            }
          }
        }
      }
    }

## is_adopted

Returns `true` if the system in question is “adopted”, false otherwise.

The system is “adopted” when the adopt method is called. Subsequent connections to the system must call the
`authenticate` method before trying to do anything else.

### Result jsonschema

    {
      "type": "boolean"
    }

## list_disks

Provides list of available disks.

### Result jsonschema

    {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          },
          "size": {
            "type": "number"
          },
          "model": {
            "type": "string"
          },
          "label": {
            "type": "string"
          },
          "removable": {
            "type": "boolean"
          }
        }
      }
    }

## list_network_interfaces

Provides list of available network interfaces.

### Result jsonschema

    {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          }
        }
      }
    }

## reboot

Performs system reboot.

## shutdown

Performs system shutdown.

## system_info

Provides auxiliary system information.

### Result jsonschema

    {
      "type": "object",
      "properties": {
        "installation_running": {
          "type": "boolean"
        },
        "version": {
          "type": "string"
        },
        "efi": {
          "type": "boolean"
        }
      }
    }

# Client methods

## installation_progress

Server calls this method on the client to report installation progress. This method will only be called 
after the client initiates system installation and before the server reports its result.

### Parameter jsonschema

    {
      "type": "object",
      "properties": {
        "progress": {
          "type": "number"
        },
        "message": {
          "type": "text"
        }
      }
    }

