#############################################################################################################
# Project               : Data Transformation Solution: Rules Engine Application
# Description           : This python code uses the "durable_rules" framework for evaluating
#                           ingested JSON elements against known JSON elements. The known
#                           JSON elements could be ORM data objects serialized to JSON. Using
#                           the rules engine, decisions can be made based on two rulesets:
#                               1) RuleSet1
#                                   a) Determine hiring event
#                                   b) Determine firing event
#                                   c) Determine name change event
#                               2) RuleSet2
#                                   a) Determine first sales event\
#
#                           Of course the rules are arbitrary and contrived for this example.
#                           In the real world, rulesets would be in their own files and likely
#                           very complicated. This example ultimately just shows durable_rules
#                           in action.
#
#                           The durable_rules engine documentation can be found here:
#                               https://github.com/jruizgit/rules/blob/master/docs/py/reference.md
#
# Created By            : Willy Demis
# Created Date          : 2022-02-16
# Version               : 1.0
#############################################################################################################

from durable.lang import *
from inboundDataProvider import generateInboundData
from currentStateDataProvider import getCurrentStateData
from jsondiff import diff
import json

#This would be a serivce level call to update the DB with the incoming data
def storeEventToDB(jsonObj):
    print('Store employee {0} to DB'.format(jsonObj["employee"]["id"]))

#This shows the ability to have rulesets per store since some stores might want to track different metrics for employees
with ruleset('Chicago'):
    
    #When the "<<" operator is used, then "passes" through the ruleset will match each line represented by the operator.
    # The engine uses "forward occurance" to store state about the fact (labeled below as "current") and compare it to the 
    # next event to pass through the ruleset (labeled below as "ingest"). So the ruleset is comparing the current rule definition
    # to the ingest rule definition in order to make a decision if the overall "when_all" rule criteria can be applied
    @when_all(c.current << (-m.employee.endDate) & (+m.employee.startDate) & (m.employee.startDate != ''),
              c.ingest << (+m.employee.endDate) & (m.employee.id == c.current.employee.id))
    def releaseEvent(c):
        print('Current state: \t{0}\nIngest state: \t{1}\nDecision: {2} was fired from store {3}'.format(c.current, c.ingest, c.ingest.employee.first + " " + c.ingest.employee.last, c.ingest.employee.storeId))
        storeEventToDB(c.ingest)
        c.retract_fact(c.current)

    @when_all(c.current << (m.employee.startDate == ''), 
              c.ingest << (m.employee.startDate != '') & (-m.employee.endDate))
    def hireEvent(c):
        print('Current state: \t{0}\nIngest state: \t{1}\nDecision: {2} was hired at store {3}'.format(c.current, c.ingest, c.ingest.employee.first + " " + c.ingest.employee.last, c.ingest.employee.storeId))
        storeEventToDB(c.ingest)
        c.retract_fact(c.current)

    @when_any(all(c.current << (+m.employee.first), 
                  c.ingest << (+m.employee.first) & (m.employee.first != c.current.employee.first) & (m.employee.id == c.current.employee.id)),
              all(c.current << (+m.employee.last), 
                  c.ingest << (+m.employee.last) & (m.employee.last != c.current.employee.last) & (m.employee.id == c.current.employee.id)))
    def nameChangeEvent(c):
        print('Decision: Employee {0} had name change event\nCurrent state: \t{1}\nIngest state: \t{2}\nJSON Diff: \t{3}'.format(c.ingest.employee.id, c.current, c.ingest, diff(c.current, c.ingest)))
        storeEventToDB(c.ingest)
        c.retract_fact(c.current)

#This shows a different rule set with different logic for another store
with ruleset('Indianapolis'):
    @when_all(c.current << (-m.empoyee.sales),
              c.ingest << (+m.employee.sales) & (m.employee.id == c.current.employee.id))
    def firstSalesEvent(c):
        print('Current state: \t{0}\nIngest state: \t{1}\nDecision: {2} had first sales event at store {3}'.format(c.current, c.ingest, c.ingest.employee.first + " " + c.ingest.employee.last, c.ingest.employee.storeId))
        storeEventToDB(c.ingest)
        c.retract_fact(c.current)


#Simulate getting json data from event grid location
inboundData = generateInboundData()
print('')

for employee in inboundData['employees']:
    employeeId = employee["employee"]["id"]
    storeId = employee["employee"]["storeId"]
    district = employee["employee"]["storeLocation"]

    #The durable_rules engine needs to get the current state as a 'fact'
    # After the current state is sent, then the ingest state needs to be sent as an 'event'
    # Fact/Event, Fact/Event, etc... this logical ordering is very important for it to work properly
    
    #This simulates going to a DB to get the current state data for comparison. This submits the data as an Event to the rules engine
    print('Sending current DB state fact to processor for district {0} on employee id: {1} and store id: {2}'.format(district, employeeId, storeId))
    assert_fact(district, getCurrentStateData(employeeId, storeId))

    #This presents the inbound data as a fact to the rules engine. A Fact can be compared against a subesquent Event
    print('Sending inbound event to processor for employee id: {0}'.format(employeeId))
    post(district, employee)
    print('')