from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime, date
from twython import Twython
from slackclient import SlackClient
import csv
import time

# Selenium setup
path_to_chromedriver = '/Users/Aidan/Downloads/chromedriver'
browser = webdriver.Chrome(executable_path=path_to_chromedriver)

def formatAPDateTime(date_object):
    if date_object.month == 9:
        new_date = "Sept. " + \
            datetime.strftime(date_object, "%d, %Y").lstrip("0")
    elif date_object.month < 3 or date_object.month > 7:
        new_date = datetime.strftime(
            date_object, "%b. ") + datetime.strftime(date_object, "%d, %Y").lstrip("0")
    else:
        new_date = datetime.strftime(
            date_object, "%B ") + datetime.strftime(date_object, "%d, %Y").lstrip("0")
    if date_object.hour == 0:
        new_time = " at 12:" + datetime.strftime(date_object, "%M") + " a.m."
    elif date_object.hour < 12:
        new_time = " at " + datetime.strftime(date_object, "%-I:%M a.m.")
    else:
        new_time = " at " + datetime.strftime(date_object, "%-I:%M p.m.")
    return new_date + new_time

class CrimeReport(object):
    def __init__(self, case_number, code, report_time, status, occurred_time, occurred_time2, building, location, stolen, damaged, description):
        self.case_number = case_number
        self.code = code
        self.report_time = report_time
        self.status = status
        self.occurred_time = occurred_time
        self.occurred_time2 = occurred_time2
        self.building = building
        self.location = location
        self.stolen = stolen
        self.damaged = damaged
        self.description = description

    def __str__(self):
        return self.case_number

    def __repr__(self):
        return "<CrimeReport object id={}>".format(self.case_number)

    def get_dict(self):
        return {'Case Number': self.case_number,
                'Code': self.code,
                'Report Time': self.report_time,
                'Status': self.status,
                'Occurred1': self.occurred_time,
                'Occurred2': self.occurred_time2,
                'Building': self.building,
                'Location': self.location,
                'Stolen': self.stolen,
                'Damaged': self.damaged,
                'Description': self.description}

    @staticmethod
    def get_headers():
        return ['Case Number',
                'Code',
                'Report Time',
                'Status',
                'Occurred1',
                'Occurred2',
                'Building',
                'Location',
                'Stolen',
                'Damaged',
                'Description']

# Parse incident data
def parse_crime(incident_list):
    label_numbers1 = [5, 2, 3, 4, 8, 11, 12, 13, 14]
    label_numbers2 = [1, 6, 7, 9, 10, 15, 16, 17, 18]
    with open('crime.csv', 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CrimeReport.get_headers())
        writer.writeheader()
        for i, incident in enumerate(incident_list):
            if i % 2 == 0:
                label_numbers = label_numbers1
            elif i % 2 == 1:
                label_numbers = label_numbers2
            incident_link_object = incident.find(
                id="ctl00_ContentPlaceHolder1_Results_ctl{0}_IncidentNumberLink".format(str(i).zfill(2)))
            incident_number = incident_link_object.text
            incident_code_object = incident.find(
                id="ctl00_ContentPlaceHolder1_Results_ctl{0}_Label{1}".format(str(i).zfill(2), label_numbers[0]))
            incident_code = incident_code_object.text
            incident_report_object = incident.find(
                id="ctl00_ContentPlaceHolder1_Results_ctl{0}_Label{1}".format(str(i).zfill(2), label_numbers[1]))
            incident_report_text = incident_report_object.text
            incident_report_time = datetime.strptime(
                incident_report_text, "%m/%d/%Y %H:%M")
            incident_case_status_object = incident.find(
                id="ctl00_ContentPlaceHolder1_Results_ctl{0}_Label{1}".format(str(i).zfill(2), label_numbers[2]))
            incident_case_status = incident_case_status_object.text
            incident_occurred_object = incident.find(
                id="ctl00_ContentPlaceHolder1_Results_ctl{0}_Label{1}".format(str(i).zfill(2), label_numbers[3]))
            incident_occurred_span_count = len(
                incident_occurred_object.find_all('span'))
            if incident_occurred_span_count == 1:
                incident_occurred_text = incident_occurred_object.text
                incident_occurred_time = datetime.strptime(
                    incident_occurred_text, " Date: %m/%d/%Y %H:%M")
                incident_occurred_time2 = None
            elif incident_occurred_span_count == 2:
                incident_occurred_text = incident_occurred_object.text[10:26]
                incident_occurred_text2 = incident_occurred_object.text[31:]
                incident_occurred_time = datetime.strptime(
                    incident_occurred_text, "%m/%d/%Y %H:%M")
                incident_occurred_time2 = datetime.strptime(
                    incident_occurred_text2, "%m/%d/%Y %H:%M")
            incident_building_object = incident.find(
                id="ctl00_ContentPlaceHolder1_Results_ctl{0}_Label{1}".format(str(i).zfill(2), label_numbers[4]))
            incident_building = incident_building_object.text
            incident_location_object = incident.find(
                id="ctl00_ContentPlaceHolder1_Results_ctl{0}_Label{1}".format(str(i).zfill(2), label_numbers[5]))
            incident_location = incident_location_object.text
            incident_stolen_object = incident.find(
                id="ctl00_ContentPlaceHolder1_Results_ctl{0}_Label{1}".format(str(i).zfill(2), label_numbers[6]))
            incident_stolen = float(incident_stolen_object.text[1:].replace(',', ''))
            incident_damaged_object = incident.find(
                id="ctl00_ContentPlaceHolder1_Results_ctl{0}_Label{1}".format(str(i).zfill(2), label_numbers[7]))
            incident_damaged = float(incident_damaged_object.text[1:].replace(',', ''))
            incident_description_object = incident.find(
                id="ctl00_ContentPlaceHolder1_Results_ctl{0}_Label{1}".format(str(i).zfill(2), label_numbers[8]))
            incident_description = incident_description_object.text
            crime_report = CrimeReport(incident_number, incident_code, incident_report_time, incident_case_status, incident_occurred_time,
                                       incident_occurred_time2, incident_building, incident_location, incident_stolen, incident_damaged, incident_description)
            create_post(crime_report)
            writer.writerow(crime_report.get_dict())

def create_post(crime_object):
    tweet = crime_object.code + " reported on " + \
        formatAPDateTime(crime_object.report_time) + " at " + \
        crime_object.location + "."
    if len(tweet) > 140:
        tweet = tweet[:138] + "..."
    if crime_object.occurred_time2:
        slack_post = "*Case:* {}\n*Incident Code:* {}\n*Reported*: {}\n*Case status:* {}\n*Occurred between:* {} *and * {}\n*Building:* {}\n*Location:* {}\n*Stolen:* ${:,.2f}\n*Damaged:* ${:,.2f}\n{}".format(
            crime_object.case_number,
            crime_object.code,
            formatAPDateTime(crime_object.report_time),
            crime_object.status,
            formatAPDateTime(crime_object.occurred_time),
            formatAPDateTime(crime_object.occurred_time2),
            crime_object.building,
            crime_object.location,
            crime_object.stolen,
            crime_object.damaged,
            crime_object.description
        )
    else:
        slack_post = "*Case:* {}\n*Incident Code:* {}\n*Reported*: {}\n*Case status:* {}\n*Occurred:* {}\n*Building:* {}\n*Location:* {}\n*Stolen:* ${:,.2f}\n*Damaged:* ${:,.2f}\n{}".format(
            crime_object.case_number,
            crime_object.code,
            formatAPDateTime(crime_object.report_time),
            crime_object.status,
            formatAPDateTime(crime_object.occurred_time),
            crime_object.building,
            crime_object.location,
            crime_object.stolen,
            crime_object.damaged,
            crime_object.description
        )
        print(tweet)
        print(slack_post)
    #twitter = Twython(APP_KEY, APP_SECRET, TOKEN_KEY, TOKEN_SECRET)
    #twitter.update_status(status=tweet)
    slack_client.api_call("chat.postMessage", channel='C5NAM8SN8', text=slack_post, as_user=True)

# Date calculation
today = date.today()
day_one = date(2000, 1, 1)
diff = today - day_one
days = diff.days

url = "https://scsapps.unl.edu/policereports/MainPage.aspx"
browser.get(url)

# Browse to today's page
browser.execute_script("__doPostBack('ctl00$ContentPlaceHolder1$DateSelection',{0})".format(days))

# Pass HTML to BeautifulSoup
html = browser.page_source
soup = BeautifulSoup(html, "html.parser")

# Get incidents
incidents = soup.find(id='ctl00_ContentPlaceHolder1_SummarySection_HTML')
incident_list = incidents.find_all('li')
parse_crime(incident_list)
