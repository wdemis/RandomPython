#############################################################################################################
# Project               : Data Transformation Solution: Rules Engine Application
# Description           : This python code is used in conjunction with the rules engine.
#                           This code represents a stream of current "known" JSON records
#                           that would have been supplied to the rules engine through an
#                           ORM model. Assume this data would be the JSON serialized version
#                           of the DB record's current state. This dataset represents a very
#                           simple employee registry for a brand with multiple stores.
#
#                           In the event that the rules engine asks for an unknown record,
#                           a blank representation would be returned.
#
# Created By            : Willy Demis
# Created Date          : 2022-02-16
# Version               : 1.0
#############################################################################################################

import json

def getCurrentStateData(employeeId, storeId):
    json_empty_data = \
    """
    {
      "employees": [
        {
          "employee": {
            "id": "",
            "storeLocation": "",
            "storeId": "",
            "startDate": "",
            "first": "",
            "last": "",
            "zipcode": ""
          }
        }
      ]
    }
    """
    
    json_current_data = \
    """
    {
      "employees": [
        {
          "employee": {
            "id": "0001",
            "storeLocation": "Chicago",
            "storeId": "1111",
            "startDate": "20220207",
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
            "first": "James",
            "last": "Dean",
            "zipcode": "60602"
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
            "zipcode": "46268"
          }
        }
      ]
    }
    """
    currentData = json.loads(json_current_data)
    for employee in currentData['employees']:
        dataSourceEmployeeId = employee["employee"]["id"]
        dataSourceStoreId = employee["employee"]["storeId"]
        if (dataSourceEmployeeId == employeeId and dataSourceStoreId == storeId):
            return employee
    
    emptyData = json.loads(json_empty_data)
    return emptyData["employees"][0]