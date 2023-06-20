import collections
import requests
import pprint
import getpass
import getopt
import urllib
import sys

from colorama import init
from termcolor import colored
init()

##### Used as a global variable to determine what the 'develop' branch should
#####   be compared to for GitFlow in release branch creation
developBranch = 'development'

##### Used as a global variable to determine what the jira host
#####   This is set as a global for convenience in changing to run against other domains
host = 'https://jira.mydomain.com'



class Session:
    def __init__(self, username, password, host):
        self.username = username
        self.password = password
        self.host = host
        self.jiraSession = requests.Session()
        self.jiraSession.auth = (username, password)
        self.auth = self.jiraSession.post(host)

    def performGet(self, url):
        return self.jiraSession.get(self.host + url)


class Sprint:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class Ticket:
    def __init__(self, id, key, fixVersion, component, labels, activityType):
        self.id = id
        self.key = key
        self.fixVersion = fixVersion
        self.component = component
        self.labels = labels
        self.activityType = activityType


class PullRequest:
    def __init__(self, repo, branch, status, author, reviewers, ticket):
        self.repo = repo
        self.branch = branch
        self.status = status
        self.author = author
        self.reviewers = reviewers
        self.ticket = ticket


class Reviewer:
    def __init__(self, name, didApprove):
        self.name = name
        self.didApprove = didApprove



def getBoardId(session, jiraBoard):
    encodedName = urllib.parse.quote(jiraBoard)
    response = session.performGet('/rest/agile/latest/board?name=' + encodedName)
    if len(response.json()['values']) > 0:
        boardId = response.json()['values'][0]['id']
        print("\tFound board id: " + str(boardId))
        return boardId
    else:
        print("\t" + colored("No board found named: ", 'red', attrs=[]) \
            + colored("'" + jiraBoard + "'", 'yellow', attrs=['bold']) \
            + colored(" Exiting script.", 'red', attrs=[]))
        sys.exit(2)


def getSprintsWithName(session, boardId, releaseNumber):
    response = session.performGet('/rest/agile/latest/board/' + str(boardId) + '/sprint')

    sprints = []
    for value in response.json()['values']:
        if value['name'].find(str(releaseNumber)) != -1:
            name = value['name']
            id = value['id']
            sprints.append(Sprint(id, name))
            print("\tFound sprint: " + colored(name, 'yellow', attrs=[]) + " with id: " + str(id))
    return sprints


def getTicketsForSprint(session, boardId, sprint, releaseCreation):
    response = session.performGet('/rest/greenhopper/1.0/rapid/charts/scopechangeburndownchart?rapidViewId=' + str(boardId) + '&sprintId=' + str(sprint.id))
    print("\tFound " + colored(str(len(response.json()['issueToSummary'])), 'yellow', attrs=['bold']) + " tickets in sprint " + colored(sprint.name, 'magenta', attrs=[]))
    
    tickets = []
    for issueKey in response.json()['issueToSummary'].keys():
        issueResponse = session.performGet('/rest/agile/latest/issue/' + str(issueKey))
        issue = issueResponse.json()
        ticket = Ticket(issue['id'], issue['key'], getFixVersionForTicket(issue), getComponentForTicket(issue), getLabelsForTicket(issue), getActivityTypeForTicket(issue))
        tickets.append(ticket)
        if releaseCreation == False:
            print('\t\t{:<40s}{:<40s}{:<40s}{:<40s}{:<40s}'.format("Found ticket: " \
                + colored(ticket.key, 'cyan', attrs=[]), "with Fix Version: " \
                + colored(ticket.fixVersion, 'cyan', attrs=[]), "for Component: " \
                + colored(ticket.component, 'cyan', attrs=[]), "with Labels:" \
                + colored(ticket.labels, 'cyan', attrs=[]), "with ActivityType: " \
                + colored(ticket.activityType, 'cyan', attrs=[])))
    return tickets


def getFixVersionForTicket(issue):
    if "fixVersions" in issue['fields']:
        if len(issue['fields']['fixVersions']) > 0:
            return issue['fields']['fixVersions'][0]['name']
    return '<null>'


def getComponentForTicket(issue):
    if "components" in issue['fields']:
        if len(issue['fields']['components']) > 0:
            return issue['fields']['components'][0]['name']
    return '<null>'


def getActivityTypeForTicket(issue):
    if "customfield_12112" in issue['fields']:
        if issue['fields']['customfield_12112'] is None:
            return '<null>'
        else:
            return issue['fields']['customfield_12112']['value']
    else:
        return '<null>'


def getLabelsForTicket(issue):
    if "labels" in issue['fields']:
        if len(issue['fields']['labels']) > 0:
            labels = ""
            for label in issue['fields']['labels']:
                if not labels:
                    labels = label
                else:
                    labels = labels + "," + label
            return labels
    return '<null>'


def getPRStatusForTicketId(session, ticket, releaseCreation):
    response = session.performGet('/rest/dev-status/latest/issue/summary?issueId=' + str(ticket.id))
    prCount = response.json()['summary']['pullrequest']['overall']['count']
    prState = response.json()['summary']['pullrequest']['overall']['state']
    if releaseCreation == False:
        print('\t{:<71s}{:<15s}{:<26s}{:<35s}'.format("Ticket: " + colored(str(ticket.key), 'yellow', attrs=[]) \
            + " has " + colored(str(prCount), 'yellow', attrs=[]) + " pull requests and a state of: ", \
            colored(prState, 'magenta', attrs=[]), \
            " and an activity type of: ", \
            colored(ticket.activityType, 'yellow', attrs=[])))
    return prCount


def getPRDetailsForTicketId(session, ticket, releaseCreation):
    response = session.performGet('/rest/dev-status/latest/issue/detail?issueId=' + str(ticket.id) + '&applicationType=stash&dataType=pullrequest')
    detailElement = response.json()['detail'][0]
    if len(detailElement['pullRequests']) > 0:
        pullRequests = list()
        for pr in detailElement['pullRequests']:
            repo = pr['destination']['repository']['name']
            branch = pr['destination']['branch']
            status = pr['status']
            author = pr['author']['name']
            reviewers = list()
            for r in pr['reviewers']:
                reviewers.append(Reviewer(r['name'], r['approved']))
            
            pullRequest = PullRequest(repo, branch, status, author, reviewers, ticket)
            pullRequests.append(pullRequest)
            if releaseCreation == False:
                print('\t\t{:<45s}{:<45s}{:<30s}{:<35s}{:<100s}'.format("Repository: " + colored(repo, 'cyan', attrs=[]), \
                    "Merge branch: " + colored(branch, 'cyan', attrs=[]), \
                    "Status: " + colored(status, 'cyan', attrs=[]), \
                    "Author: " + colored(author, 'cyan', attrs=[]), \
                    "Approvers: " + colored(getPRApprovers(pullRequest), 'cyan', attrs=[])))

        return pullRequests


def getPRApprovers(pullRequest):
    approvers = list()
    for reviewer in pullRequest.reviewers:
        if reviewer.didApprove:
            approvers.append(reviewer.name)

    return str(approvers) if len(approvers) > 0 else "None"


def getPRCountWithMergesToDevelop(pullRequests):
    mergeCount = 0
    for pr in pullRequests:
        if pr.status == 'MERGED' and pr.branch.lower() in developBranch:
            mergeCount += 1
    return mergeCount


def getUniqueReposForPRsToDevelop(pullRequests):
    uniqueRepos = list()
    for pullRequest in pullRequests:
        if pullRequest.repo not in uniqueRepos and pullRequest.branch.lower() in developBranch:
            uniqueRepos.append(pullRequest.repo)
    return uniqueRepos


def getTicketsForRepo(pullRequests, repo):
    ticketsForRepo = list()
    for pr in pullRequests:
        if pr.repo in repo and pr.branch.lower() in developBranch and pr.status == 'MERGED' and pr.ticket.key not in ticketsForRepo:
            ticketsForRepo.append(pr.ticket.key)

    ticketsForRepo.sort()
    if len(ticketsForRepo) > 0:
        print("\tRepository: " + repo)
        for ticket in ticketsForRepo:
            print('\t\t' + colored(ticket, 'yellow', attrs=[]))


def getTicketsWithIncorrectFixVersion(pullRequests, releaseNumber):
    ticketsForRepo = {}
    for pr in pullRequests:
        if pr.branch.lower() in developBranch and pr.status == 'MERGED' and pr.ticket.key not in ticketsForRepo and not pr.ticket.fixVersion.startswith("MR" + str(releaseNumber)):
            ticketsForRepo[pr.ticket.key] = pr.ticket.fixVersion

    ticketsForRepoOrdered = collections.OrderedDict(sorted(ticketsForRepo.items()))
    if len(ticketsForRepoOrdered) > 0:
        print('\n\t' + colored('Tickets that have a', 'cyan', attrs=[]) + ' ' + colored('suspicious fix version', 'red', attrs=[]))
        for ticket, fixVersion in ticketsForRepoOrdered.items():
            print('\t\t' + colored(ticket, 'yellow', attrs=[]) + " Fix Version: " + colored(fixVersion, 'red', attrs=[]))


def yes_or_no(question):
    while "the answer is invalid":
        reply = str(input(question+' (y/n): ')).lower().strip()
        if reply[:1] == 'y':
            return True
        if reply[:1] == 'n':
            return False


def argsNotSet(username, password, jiraBoard, releaseNumber, releaseCreation):
    if (username == ''):
        print("\t" + colored("username was not supplied", 'red', attrs=['bold']) + "\n")
        return True
    if (password == ''):
        print("\t" + colored("password was not supplied", 'red', attrs=['bold']) + "\n")
        return True
    if (jiraBoard == ''):
        print("\t" + colored("jiraBoard was not supplied", 'red', attrs=['bold']) + "\n")
        return True
    if (releaseNumber == ''):
        print("\t" + colored("releaseNumber was not supplied", 'red', attrs=['bold']) + "\n")
        return True
    if (releaseCreation == ''):
        print("\t" + colored("releaseCreation was not supplied", 'red', attrs=['bold']) + "\n")
        return True
    
    return False


def printHelp():
    print('\t' + colored("validateRelease.py ", 'yellow', attrs=[]) \
        + colored("-u ", 'cyan', attrs=[]) + colored("<username> ", 'magenta', attrs=[]) \
        + colored("-p ", 'cyan', attrs=[]) + colored("<password> ", 'magenta', attrs=[]) \
        + colored("-b ", 'cyan', attrs=[]) + colored("<board> ", 'magenta', attrs=[]) \
        + colored("-n ", 'cyan', attrs=[]) + colored("<releasenum> ", 'magenta', attrs=[]) \
        + colored("-r ", 'cyan', attrs=[]) + colored("<releasereport> ", 'magenta', attrs=[]) \
        + "\n")


def main(argv):
    username = ''
    password = ''
    jiraBoard = ''
    releaseNumber = ''
    releaseCreation = ''
    try:
        opts, args = getopt.getopt(argv,"hu:p:b:n:r:",["username=","password=","board=","releasenum=","releasereport="])
        for opt, arg in opts:
            if opt == '-h':
                printHelp()
                sys.exit()
            elif opt in ("-u", "--username"):
                username = arg
            elif opt in ("-p", "--password"):
                password = arg
            elif opt in ("-b", "--board"):
                jiraBoard = arg
            elif opt in ("-n", "--releasenum"):
                releaseNumber = arg
            elif opt in ("-r", "--releasereport"):
                if arg.lower() == 'n' or arg.lower() == 'false':
                    releaseCreation = False
                else:
                    releaseCreation = True

        if len(opts) > 0 and argsNotSet(username, password, jiraBoard, releaseNumber, releaseCreation):
            print('\tIf using command line arguments, then all command line arguments must be specified.')
            printHelp()
            sys.exit(2)
        elif len(opts) == 0:
            username = input("Enter jira username: ")
            password = getpass.getpass("Enter jira password: ")
            jiraBoard = input("Enter jira board name: ")
            releaseNumber = input("Enter release number: ")
            releaseCreation = yes_or_no("Generate release branch creation report")

    except getopt.GetoptError:
        printHelp()
        sys.exit(2)


    print("\n")
    print("*****************************Validating Release MR" + str(releaseNumber) + "*****************************")    
    print("\nGetting id for board: " + jiraBoard)
    session = Session(username, password, host)
    boardId = getBoardId(session, jiraBoard)

    print("\nGetting sprints for release MR" + releaseNumber)
    sprints = getSprintsWithName(session, boardId, releaseNumber)

    ticketsInRelease = list()
    print("\nGetting tickets for release: MR" + releaseNumber)
    for sprint in sprints:
        ticketsInSprint = getTicketsForSprint(session, boardId, sprint, releaseCreation)
        for ticket in ticketsInSprint:
            ticketsInRelease.append(ticket)

    print("\nGetting PR Status for " + colored(str(len(ticketsInRelease)), 'yellow', attrs=[]) + " tickets in release MR" + str(releaseNumber))
    pullRequestsInTickets = list()
    for ticket in ticketsInRelease:
        prCount = getPRStatusForTicketId(session, ticket, releaseCreation)
        if int(prCount) > 0:
            pullRequestsInTicket = getPRDetailsForTicketId(session, ticket, releaseCreation)
            for pr in pullRequestsInTicket:
                pullRequestsInTickets.append(pr)

            if releaseCreation == False:
                print("\n")

    if releaseCreation == True:
        mergedPRs = getPRCountWithMergesToDevelop(pullRequestsInTickets)
        print("\tLocated " + colored(mergedPRs, 'yellow', attrs=[]) \
            + " Pull Request in " + colored('MERGED', 'cyan', attrs=[]) \
            + " status to " + colored('DEVELOPMENT', 'cyan', attrs=[]) + " branch")

        print("\nGenerating " + colored('Release Branch Creation Report', 'magenta', attrs=[]) \
            + " for PRs " + colored('MERGED', 'cyan', attrs=[]) \
            + " to the " + colored('DEVELOPMENT', 'cyan', attrs=[]) \
            + " branch for " + colored('MR' + str(releaseNumber), 'yellow', attrs=[]))

        uniqueRepos = getUniqueReposForPRsToDevelop(pullRequestsInTickets)
        for repo in uniqueRepos:
            getTicketsForRepo(pullRequestsInTickets, repo)
            
        getTicketsWithIncorrectFixVersion(pullRequestsInTickets, releaseNumber)

    print("\n*****************************Validation Complete*****************************\n")



if __name__ == "__main__":
    main(sys.argv[1:])









	
