## Python port of copy_ad_user.ps1 by David Bird
'''Copy an AD user and create a new user with the same group
memberships and a password based on the start date.'''
## Imports
from dataclasses import dataclass, field
import datetime
import calendar
from typing import Generator
import pyad.adquery
import pyad.aduser
import pyad.adcontainer
import pyad.pyadexceptions

## Functions
def find_day(date: str) -> str:
    '''Use the datetime module to find the day of the week for a given date
    to make password generation easier.'''
    day, month, year = (int(i) for i in date.split(" "))
    day_number = calendar.weekday(year, month, day)
    # Modify days list to start with Sunday as 0
    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
        ]
    return days[day_number]

def get_ad_group_memberships(username: str) -> Generator[dict[str, str], None, None]:
    '''Use pyad to get the group memberships of an existing user.'''
    try:
        ad_query = pyad.adquery.ADQuery()
        ad_query.execute_query(attributes=["memberOf", "title", "description"],
                               where_clause=f"sAMAccountName='{username}'")
    except pyad.pyadexceptions.noObjectFoundException as e:
        raise ADuserException(f"Error getting group memberships for {username}.") from e

    return ad_query.get_results()

# Set environment constants
DOMAIN_NAME = "example.com"
SD_GROUP = "your_service_desk_group"
### pyad.pyad_setdefaults(ldap_server=DOMAIN_NAME)

class ADuserException(Exception):
    '''Definig user exceptions'''
    pass

@dataclass
class ADUser:
    '''Definig the ADUser class to create a new user in Active Directory.'''

    first_name: str
    last_name: str
    manager: str
    title: str
    mobile_number: str
    new_group_memberships: dict[str, str] = field(default_factory=dict, init=False)
    _start_date: datetime.date = field(default_factory=datetime.date.today, init=False, repr=False)

    @property
    def full_name(self) -> str:
        '''Define full name property for the new user.'''
        return f"{self.first_name.capitalize()} {self.last_name.capitalize()}"

    @property
    def start_day(self) -> str:
        '''Define start day property for the new user.'''
        return find_day(self.start_date.strftime("%d %m %Y"))

    @property
    def password(self) -> str:
        """Create a password based on the start date of the new user."""
        return f"{self.start_day}{self.start_date.strftime("%d %m %Y")}"

    @property
    def sam_account_name(self) -> str:
        '''Defining sam_account_name property for the new user.'''
        return f"{self.first_name}.{self.last_name}".lower()

    @property
    def principal_name(self) -> str:
        '''Defining the UPN property for the new user.'''
        return f"{self.sam_account_name}@{DOMAIN_NAME}"

    @property
    def start_date(self) -> datetime.date:
        '''Defining the start_date property for the new user.'''
        return self._start_date.strftime("%m%d%Y")

    @start_date.setter
    def start_date(self, value: datetime.date):
        '''Setting the start_date property for the new user.'''
        self._start_date = value

    def create_ad_user(self) -> None:
        '''Create a new user in Active Directory.'''
        optional_attributes = {
            "mobile": self.mobile_number,
            "title": self.title,
            "manager": self.manager
        }

        try:
        # Create new user
            new_ad_user = pyad.aduser.ADUser.create(
                self.full_name,
                container_object=pyad.adcontainer.ADContainer.from_dn("CN=Users,DC=example,DC=com"),
                password=self.password,
                upn_suffix=DOMAIN_NAME,
                optional_attributes=optional_attributes,
            )
        except pyad.pyadexceptions.genericADSIException as e:
            raise ADuserException(f"Error creating new user {self.full_name}.") from e

        if self.new_group_memberships:
            # Add group memberships to new user
            for group in self.new_group_memberships:
                new_ad_user.add_to_group(group)
        else:
            raise ADuserException("No group memberships found for the new user.")

    def as_dict(self) -> dict[str, str]:
        return {
            "full_name": self.full_name,
            "sam_account_name": self.sam_account_name,
            "manager": self.manager,
            "mobile_number": self.mobile_number,
            "start_date": self.start_date.strftime("%m%d%Y"),
            "title": self.title
        }

if __name__ == "__main__":

    # Set new user variables
    new_user_first_name = input("Enter the new users first name: ")
    new_user_last_name = input("Enter the new users last name: ")
    existing_username = input("Enter the username of the user to copy from: ")
    new_user_manager = input("Enter the new users managers name: ")
    new_user_mobile_number = input("Enter the new users mobile number: ")
    new_user_title = input("Enter the new users job title: ")

    new_user = ADUser(first_name=new_user_first_name,
                    last_name=new_user_last_name,
                    title=new_user_title,
                    manager=new_user_manager,
                    mobile_number=new_user_mobile_number)

    # Prompt for start date using datetime module
    start_date = datetime.datetime.strptime(
        input("Enter the start date of the new user as MMDDYYYY: "), "%m%d%Y").date()
    new_user.start_date = start_date

    new_user.new_group_memberships = get_ad_group_memberships(existing_username)

    new_user.create_ad_user()
    print(f"User {new_user.full_name} created successfully.")
