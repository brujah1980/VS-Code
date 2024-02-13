## Python port of Copy_AD_User.ps1 by David Bird
## Imports
import pyad.adquery
import datetime
import calendar

## Functions
def findDay(date):
    day, month, year = (int(i) for i in date.split(" "))
    dayNumber = calendar.weekday(year, month, day)
    # Modify days list to start with Sunday as 0
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    return days[dayNumber]

# Set environment constants
DOMAIN_NAME = "example.com"
SD_GROUP = "your_service_desk_group"
### pyad.pyad_setdefaults(ldap_server=DOMAIN_NAME)

# Set new user variables
new_user_first_name = input("Enter the new users first name: ")
new_user_last_name = input("Enter the new users last name: ")
existing_username = input("Enter the username of the user to copy from: ")
new_user_manager = input("Enter the new users managers name: ")
# Get existing user's details
### ad_query = pyad.adquery.ADQuery()
### ad_query.execute_query( attributes=["memberOf", "manager"], where_clause=f"sAMAccountName='{existing_username}'" )
### group_memberships = ad_query.get_single_result()["memberOf"]
### manager = ad_query.get_single_result()["manager"]D

# Prompt for start date using datetime module
start_date = datetime.datetime.strptime(input("Enter the start date of the new user as MMDDYYYY: "), "%m%d%Y").date()
start_day = findDay(start_date.strftime("%d %m %Y"))

## Create additional user details from existing variables
new_password = (start_day) + start_date.strftime("%m%d%Y").capitalize() + "!"
sam_account_name = new_user_first_name.lower() + "." + new_user_last_name.lower()
