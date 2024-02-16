## Python port of copy_ad_user.ps1 by David Bird
"""Copy an AD user and create a new user with the same group
memberships and a password based on the start date."""
import calendar
import datetime

from dataclasses import dataclass, field

import pyad.adcontainer
import pyad.addomain
import pyad.adgroup
import pyad.adquery
import pyad.adsearch
import pyad.aduser
import pyad.pyadexceptions


## Functions
def find_day(date: datetime.date) -> str:
    """Use the datetime module to find the day of the week for a given date
    to make password generation easier."""
    day_number = calendar.weekday(date.year, date.month, date.day)
    # Modify days list to start with Sunday as 0
    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    return days[day_number]


def get_existing_user(username: str) -> pyad.aduser.ADUser:
    """Use pyad to get the group memberships of an existing user."""
    try:
        ad_query = pyad.adquery.ADQuery()
        ad_query.execute_query(
            attributes=["memberOf", "title", "description"],
            where_clause=f"sAMAccountName='{username}'",
        )
    except pyad.pyadexceptions.noObjectFoundException as e:
        raise ADuserException(f'Error user objection named "{username}" does not exist.') from e

    results = ad_query.get_all_results()
    existing_user = results[0]

    groups = []
    for group in existing_user["memberOf"]:
        new_group = pyad.adgroup.ADGroup.from_dn(group)
        groups.append(new_group)

    existing_user["memberOf"] = groups

    return existing_user


# Set environment constants
DOMAIN_NAME = "birdsnest.network"
SD_GROUP = "your_service_desk_group"

pyad.pyad_setdefaults(ldap_server=DOMAIN_NAME)

### pyad.pyad_setdefaults(ldap_server=DOMAIN_NAME)


class ADuserException(Exception):
    """Definig user exceptions"""


@dataclass
class ADUser:
    """Definig the ADUser class to create a new user in Active Directory."""

    first_name: str
    last_name: str
    manager: str
    title: str
    mobile_number: str
    existing_username: str
    existing_user: pyad.aduser.ADUser = field(init=False)
    start_date: datetime.date = field(default_factory=datetime.date.today, init=False, repr=False)

    @property
    def full_name(self) -> str:
        """Define full name property for the new user."""
        return f"{self.first_name.capitalize()} {self.last_name.capitalize()}"

    @property
    def start_day(self) -> str:
        """Define start day property for the new user."""
        return find_day(self.start_date)

    @property
    def password(self) -> str:
        """Create a password based on the start date of the new user."""
        return f"{self.start_day}{self.start_date.strftime(r'%d%m%Y')}!"

    @property
    def sam_account_name(self) -> str:
        """Defining sam_account_name property for the new user."""
        return f"{self.first_name}.{self.last_name}".lower()

    @property
    def principal_name(self) -> str:
        """Defining the UPN property for the new user."""
        return f"{self.sam_account_name}@{DOMAIN_NAME}"

    @property
    def user_dn(self) -> str:
        """Return the distinguished name of the user's container."""
        return ",".join(pyad.adsearch.by_cn(self.existing_username).split(",")[1:])

    def create_ad_user(self) -> None:
        """Create a new user in Active Directory."""
        optional_attributes = {
            "givenname": self.first_name,
            "sn": self.last_name,
            "displayName": self.full_name,
            "userPrincipalName": self.principal_name,
            "sAMAccountName": self.sam_account_name,
            "mobile": self.mobile_number,
            "title": self.title,
            "description": (f"Created by {SD_GROUP}" f" on {datetime.datetime.now().strftime('%m/%d/%Y')}"),
            "manager": self.manager,
        }

        new_ad_user: pyad.aduser.ADUser = None

        try:
            ou = pyad.adcontainer.ADContainer.from_dn(self.user_dn)
            # Create new user
            new_ad_user = pyad.aduser.ADUser.create(
                self.sam_account_name,
                ou,
                password=self.password,
            )
        except pyad.pyadexceptions.win32Exception as e:
            raise ADuserException(f"Error creating new user: {self.full_name} !!!") from e

        if self.existing_user:
            # Add group memberships to new user
            for group in self.existing_user["memberOf"]:
                new_ad_user.add_to_group(group)
        else:
            raise ADuserException("No group memberships found for the new user.")

    def as_dict(self) -> dict[str, str]:
        """Return the new user as a dictionary."""
        return {
            "full_name": self.full_name,
            "sam_account_name": self.sam_account_name,
            "manager": self.manager,
            "mobile_number": self.mobile_number,
            "start_date": self.start_date.strftime(r"%m%d%Y"),
            "title": self.title,
        }


if __name__ == "__main__":

    # Set new user variables
    new_user_first_name = input("Enter the first name of the new user: ")
    new_user_last_name = input("Enter the last name of the new user: ")
    existing_username = input("Enter the username of the user to copy from: ")
    new_user_manager = input("Enter the manager of new user: ")
    new_user_mobile_number = input("Enter the mobile number of the new user: ")
    new_user_title = input("Enter the title of the new user: ")

    new_user = ADUser(
        first_name=new_user_first_name,
        last_name=new_user_last_name,
        title=new_user_title,
        manager=new_user_manager,
        mobile_number=new_user_mobile_number,
        existing_username=existing_username,
    )

    # Prompt for start date using datetime module
    start_date = datetime.datetime.strptime(
        input("Enter the start date of the new user as MMDDYYYY: "), r"%m%d%Y"
    ).date()
    new_user.start_date = start_date

    new_user.existing_user = get_existing_user(existing_username)

    new_user.create_ad_user()
    print(f"User {new_user.full_name} created successfully.")
