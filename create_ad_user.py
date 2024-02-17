## Python port of copy_ad_user.ps1 by David Bird
"""Copy an AD user and create a new user with the same group
memberships and a password based on the start date."""
import calendar
import datetime
import logging
from dataclasses import Field, asdict, dataclass, field

from ms_active_directory import ADDomain, ADUser
from ldap3.utils.dn import parse_dn

logger = logging.getLogger(__name__)


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


def get_existing_user(username: str) -> ADUser:
    """Use pyad to get the group memberships of an existing user."""
    user_attributes = [
        "memberOf",
        "title",
        "description",
        "displayName",
        "sAMAccountName",
        "distinguishedName",
        "userPrincipalName",
    ]
    user = session.find_user_by_sam_name(username, user_attributes)
    groups = session.find_groups_for_user(user)

    return user, groups


# Set environment constants
DOMAIN = "birdsnest.network"
ad_domain = ADDomain(DOMAIN)
session = ad_domain.create_session_as_computer(computer_name="TEST1")
SD_GROUP = "your_service_desk_group"


class ADuserException(Exception):
    """Definig user exceptions"""


@dataclass(kw_only=True)
class EIADUser:
    """Definig the ADUser class to create a new user in Active Directory."""

    givenname: str
    """first name of the new user."""

    sn: str
    """surname/Last Name of the new user."""

    manager: ADUser = field(metadata={"include_in_dict": False})
    """Manager of the new user."""

    title: str
    """User's title."""

    mobile: str
    """Mobile number of the new user."""

    copying_from_user: ADUser = field(metadata={"include_in_dict": False})
    """Existing user to copy attributes from."""

    start_date: datetime.date = field(default_factory=datetime.date.today)
    """Start date of the new user. Defaults to today."""

    @property
    def full_name(self) -> str:
        """User's full name."""
        return f"{self.givenname.capitalize()} {self.sn.capitalize()}"

    @property
    def display_name(self) -> str:
        """User's display name."""
        return f"{self.sn.capitalize()}, {self.givenname.capitalize()}"

    @property
    def start_day(self) -> str:
        """Return the day of the week for the start date of the new user."""
        return find_day(self.start_date)

    @property
    def password(self) -> str:
        """Create a password based on the start date and day of the new user."""
        return f"{self.start_day}{self.start_date.strftime(r'%d%m%Y')}!"

    @property
    def sam_account_name(self) -> str:
        """Defining the sAMAccountName property for the new user."""
        return f"{self.givenname}.{self.sn}".lower()

    @property
    def user_principal_name(self) -> str:
        """Defining the userPrincipalName property for the new user."""
        return f"{self.sam_account_name}@{DOMAIN}"

    @property
    def user_dn(self) -> str:
        """Return the distinguished name of the user's container."""
        existing_user_dn = self.copying_from_user.distinguished_name
        dn_pieces = parse_dn(existing_user_dn, escape=True)
        dn_pieces.insert(1, f"CN={self.sam_account_name}")
        return ",".join(dn_pieces[1:])

    def as_csv(self) -> str:
        """Return a CSV string of the ADUser class."""
        user_dict = asdict(self, dict_factory=EIADUser.dict_factory(EIADUser))
        user_dict.update({"manager": self.manager["displayName"]})
        user_dict.update({"copy_of": self.copying_from_user["sAMAccountName"]})
        return ",".join(user_dict.values())

    def create_ad_user(self) -> None:
        """Create a new user in Active Directory."""
        creation_date = datetime.datetime.now().strftime(r"%m/%d/%Y")
        optional_attributes = {
            "description": f"Created by {SD_GROUP} on {creation_date}",
            "displayName": self.display_name,
            "givenname": self.givenname,
            "manager": self.manager["distinguishedName"],
            "mobile": self.mobile,
            "sAMAccountName": self.sam_account_name,
            "sn": self.sn,
            "title": self.title,
            "userPrincipalName": self.user_principal_name,
        }

        new_ad_user: ADUser = None

        try:
            ou = pyad.adcontainer.ADContainer.from_dn(self.user_dn)
            # Create new user
            new_ad_user = pyad.aduser.ADUser.create(
                self.full_name,
                ou,
                password=self.password,
                optional_attributes=optional_attributes,
            )
            new_ad_user.rename(self.display_name)
        except pyad.pyadexceptions.win32Exception as e:
            raise ADuserException(f"Error creating new user: {self.full_name} !!!") from e

        if self.copying_from_user:
            # Add group memberships to new user
            for group in self.copying_from_user["memberOf"]:
                new_ad_user.add_to_group(group)
        else:
            logging.warning("No group memberships found for the new user.")

    @staticmethod
    def dict_factory(fields: tuple[Field]) -> dict[str, Field]:
        """Return a dictionary of the ADUser class."""
        dict_fields = {}
        for f in fields:
            if f.metadata.get("include_in_dict") is False:
                continue
            dict_fields[f.name] = f
        return dict_fields


if __name__ == "__main__":

    # Set new user variables
    # TODO: Add input validation
    new_user_first_name = input("Enter the first name of the new user: ")
    new_user_last_name = input("Enter the last name of the new user: ")
    copying_from_username = input("Enter the username of the user to copy (sAMAccountName): ")
    new_user_manager = input("Enter the manager of new user (sAMAccountName): ")
    new_user_mobile_number = input("Enter the mobile number of the new user: ")
    new_user_title = input("Enter the title of the new user: ")
    new_user_start_date = input("Enter the start date of the new user as MMDDYYYY: ")

    new_user = EIADUser(
        givenname=new_user_first_name,
        sn=new_user_last_name,
        title=new_user_title,
        manager=get_existing_user(new_user_manager),
        mobile=new_user_mobile_number,
        copying_from_user=get_existing_user(copying_from_username),
    )

    # Prompt for start date using datetime module

    new_user.copying_from_user = get_existing_user(copying_from_username)

    # TODO: Add error handling. Need to handle the case where the user already exists.
    new_user.create_ad_user()

    print(f"User csv: {new_user.as_csv()}")
    print(f"User dict: {new_user.dict_factory(asdict(new_user))}")
    print(f"User {new_user.full_name} created successfully.")
