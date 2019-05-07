import csv
import json
import time
import json

import requests
from requests.auth import HTTPBasicAuth


csv_dir = 
prod_jira_csv = 
all_jira_csv = 
url = 
username =
password =  


def create_json(jiraDict):
    json_data = {
        'fields': {
            'project': {
                'key' : jiraDict['project_key']
            },
            'summary' : jiraDict['new_title'],
            'description' : jiraDict['description'],
            'customfield_10005' : int(jiraDict['story_points']),
            'duedate' : jiraDict['due_date'],
            'issuetype' : {
                'name' : jiraDict['issuetype']
            },
            'assignee' : {
                'name' : jiraDict['assignee']
            },
            'timetracking' : {
                'originalEstimate' : jiraDict['estimated_time'],
                'remainingEstimate' : jiraDict['remaining_time']
            }
        }
    }
 
    jiraJSON = json.dumps(json_data)
 
    return jiraJSON
 

def http_request(url, username, password, data):
    headers = {'Content-Type' : 'application/json'}
    response = requests.request('POST', url, auth = HTTPBasicAuth(username, password), data = data, headers = headers)
    response_code = response.status_code
    response_content = response.content
    return response_code, response_content


def update_csv_file (csvfile, row_content):
    for x in csvfile:
        file = open(x,'a')
        file.write(row_content)
        file.close()
 

def extract_jira_issue_key(response_text):
    responseDict = json.loads(response_text)
    return responseDict['key']


def create_dev_jira(row, title_extension, csvfile):
    row['new_title'] = row['title'] + title_extension
    print row['new_title']
    if row['existing_issue_key'] == '':
        data = create_json(row)
        response_code, response_content = http_request(url, username, password, data)
        jira_issue_key = extract_jira_issue_key(response_content)
    else:
        jira_issue_key = row['existing_issue_key']
        response_code = 400

    row_content = str(jira_issue_key) + ' - ' + row['title'] + ',' + row['issuetype'] + ','

    if response_code == 201:
        print 'DEV Build Issue Number: %s' % (jira_issue_key)
        update_csv_file(csvfile, '\n' + row_content + 'created')
    elif jira_issue_key != '':
        update_csv_file(csvfile, '\n' + row_content + 'already exists')
    else:
        print 'JIRA: Failed to Add'
        update_csv_file(csvfile, '\n' + row_content + 'failed')
    return jira_issue_key


def create_jira(jiraDict, title_extension, csvfile):
    print jiraDict['issuetype']
    jiraDict['new_title'] = jiraDict['title'] + title_extension
    print jiraDict['new_title']
    data = create_json(jiraDict)
    response_code, response_content = http_request(url, username, password, data)
    jira_issue_key = extract_jira_issue_key(response_content)
    row_content = str(jira_issue_key) + ' - ' + jiraDict['new_title'] + ',' + jiraDict['issuetype'] + ','
    if response_code == 201:
        print 'Issue Number: %s' % (jira_issue_key)
        update_csv_file(csvfile, '\n' + row_content + 'created')
    else:
        print 'Log: Failed to add'
        update_csv_file(csvfile, '\n' + row_content + 'failed')


if __name__ == '__main__':
    with open(csv_dir) as file:
        event_number = 0
        jiras_csv_headers = 'project_key,title,created'

        reader = csv.DictReader(file)
        timestamp = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))

        for row in reader:
            devCSV = [all_jira_csv]
            prodCSV = [all_jira_csv, prod_jira_csv]
            if row['issuetype'] == 'Story':
                row['issuename'] = row['title']
                jira_issue_key = create_dev_jira(row, ' - DEV Build', devCSV)
                row['description'] = 'Depends:\n' + jira_issue_key + ' '+ row['title'] + '\n\n' + row['description']
                row['story_points'] = 3
                row['estimated_time'] = '1h'
                row['remaining_time'] = '1h'
                create_jira(row, ' - TEST Deployment', devCSV)
                create_jira(row, ' - PROD Deployment', prodCSV)
            elif row['issuetype'] == 'Bug':
                create_jira(row, ' - Bug fix', prodCSV)
            elif row['issuetype'] == 'Task':
                create_jira(row, ' - Task', prodCSV)
            else:
                create_jira(row, ' - Other', prodCSV)

