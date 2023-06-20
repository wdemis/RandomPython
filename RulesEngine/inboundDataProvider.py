#############################################################################################################
# Project               : Data Transformation Solution: Rules Engine Application
# Description           : This python code is used in conjunction with the rules engine.
#                           This code represents a stream of ingested JSON records for the
#                           rules engine to process. The data is an abbreviated version of a real
#                           data model, and represents employee data for a brand with multiple stores.
#
# Created By            : Willy Demis
# Created Date          : 2022-02-16
# Version               : 1.0
#############################################################################################################

import json

def generateInboundData():
    json_inbound_data = \
    """
    {
      "employees": [
        {
          "employee": {
            "id": "0001",
            "storeLocation": "Chicago",
            "storeId": "1111",
            "startDate": "20220207",
            "endDate": "20200309",
            "first": "Jane",
            "last": "Doe",
            "zipcode": "60131"
          }
        },
        {
          "employee": {
            "id": "0002",
            "storeLocation": "Chicago",
            "storeId": "1111",
            "startDate": "20220210",
            "first": "Jimmy",
            "last": "Dean",
            "zipcode": "60602"
          }
        },
        {
          "employee": {
            "id": "0004",
            "storeLocation": "Chicago",
            "storeId": "1111",
            "startDate": "20220310",
            "first": "Gene",
            "last": "Simmons",
            "zipcode": "60615"
          }
        },
        {
          "employee": {
            "id": "0003",
            "storeLocation": "Indianapolis",
            "storeId": "2222",
            "startDate": "20220315",
            "first": "Billy",
            "last": "Joel",
            "zipcode": "46268",
            "sales": [
              {
                "sale": {
                  "id": "1"
                }
              }
            ]
          }
        }
      ]
    }
    """
    inboundData = json.loads(json_inbound_data)
    return inboundData