## Python port of copy_ad_user.ps1 by David Bird
'''Copy an AD user and create a new user with the same group 
memberships and a password based on the start date.'''
## Imports
import datetime
import calendar
calendar.setfirstweekday(calendar.MONDAY)
### import pyad.adquery

## Functions
def find_day(date):
    '''Use the datetime module to find the day of the week for a given date 
    to make password generation easier.'''
    day, month, year = (int(i) for i in date.split(" "))
    day_number = calendar.weekday(year, month, day)
    # Modify days list to start with Sunday as 0
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    return days[day_number]

### def get_ad_group_memberships()
### '''Use pyad to get the group memberships of an existing user.'''
### ad_query = pyad.adquery.ADQuery()
### ad_query.execute_query(attributes=["memberOf"],
###                        where_clause=f"sAMAccountName='{existing_username}'")
### return ad_query.get_results()

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

# Prompt for job title
title = input("Enter the new user's job title: ")

# Prompt for start date using datetime module
start_date = datetime.datetime.strptime(
    input("Enter the start date of the new user as MMDDYYYY: "), "%m%d%Y").date()
start_day = find_day(start_date.strftime("%d %m %Y"))

## Create additional user details from existing variables
new_password = (start_day) + start_date.strftime("%m%d%Y").capitalize() + "!"
sam_account_name = new_user_first_name.lower() + "." + new_user_last_name.lower()
user_principal_name = sam_account_name + "@" + DOMAIN_NAME
print(new_password)
