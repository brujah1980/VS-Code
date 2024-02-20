# %% [markdown]
# Import Python Functions and libraries.
# 
# External libaries required:
# 
# * ms_actvity_directory

# %%
import calendar
import datetime
import logging
from dataclasses import Field, asdict, dataclass, field

from ms_active_directory import ADDomain, ADUser, ADGroup
from ldap3.utils.dn import parse_dn

logger = logging.getLogger(__name__)

# %% [markdown]
# Environment constants and other values required.
# 
# Update `DOMAIN` and `SD_GROUP` to match requirements.

# %%
# Set environment constants
DOMAIN = "birdsnest.network"
ad_domain = ADDomain(DOMAIN)
session = ad_domain.create_session_as_user(f"david@{DOMAIN}", authentication_mechanism="GSSAPI")
SD_GROUP = "your_service_desk_group"

# %% [markdown]
# Helper functions for script.

# %%
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


def get_existing_user(username: str) -> tuple[ADUser, list[ADGroup]]:
    """Use pyad to get the group memberships of an existing user."""
    user_attributes = [
        "memberOf",
        "title",
        "description",
        "displayName",
        "sAMAccountName",
        "distinguishedName",
        "userPrincipalName",
        "department",
        "company",
    ]
    user = session.find_user_by_sam_name(username, user_attributes)
    groups = session.find_groups_for_user(user)

    return user, groups

# %% [markdown]
# Main user class to contain all the user confguration date. This is an `dataclass` and the properties are the same in activity directory.

# %%
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

    group_memberships: list[ADGroup] = field(metadata={"include_in_dict": False}, default_factory=list)
    """List of groups to add the new user to. Defaults to an empty list."""
    
    company: str
    """Company attribute of the new user."""
    
    department: str
    """Department attribute of the new user."""

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
        dn_pieces: list = parse_dn(existing_user_dn, escape=True)
        dn_pieces = dn_pieces[1:]
        dn_pieces.insert(0, ("CN", self.sam_account_name, ","))
        reconstruct_dn = [f"{k}={v}" for k, v, _ in dn_pieces]
        return ",".join(reconstruct_dn)

    def create_ad_user(self) -> None:
        """Create a new user in Active Directory."""
        attributes = {
            "description": self.title,
            "displayName": self.display_name,
            "manager": self.manager.distinguished_name,
            "mobile": self.mobile,
            "title": self.title,
            "userPrincipalName": self.user_principal_name,
            "company": self.company,
            "department": self.department,
        }

        # Create new user
        new_ad_user = session.create_user(
            username=self.sam_account_name,
            first_name=self.givenname,
            last_name=self.sn,
            object_location=self.copying_from_user.location,
            user_password=self.password,
            common_name=self.display_name,
            company=self.company,
            department=self.department,
            **attributes,
        )

        if self.copying_from_user:
            # Add group memberships to new user
            session.add_users_to_groups([new_ad_user.get_samaccount_name()], self.group_memberships)
        else:
            logging.warning("No group memberships found for the new user.")

# %%
# Set new user variables
# TODO: Add input validation
new_user_first_name = input("Enter the first name of the new user: ")
new_user_last_name = input("Enter the last name of the new user: ")
copying_from_username = input("Enter the username of the user to copy (sAMAccountName): ")
new_user_manager = input("Enter the manager of new user (sAMAccountName): ")
new_user_mobile_number = input("Enter the mobile number of the new user: ")
new_user_title = input("Enter the title of the new user: ")
new_user_start_date = input("Enter the start date of the new user as MMDDYYYY: ")

# %%
new_user_manager, _ = get_existing_user(new_user_manager)
copying_from_user, copying_from_user_groups = get_existing_user(copying_from_username)

new_user = EIADUser(
    givenname=new_user_first_name,
    sn=new_user_last_name,
    title=new_user_title,
    manager=new_user_manager,
    mobile=new_user_mobile_number,
    copying_from_user=copying_from_user,
    group_memberships=copying_from_user_groups,
    department=copying_from_user.department,
    company=copying_from_user.company,
)

# Prompt for start date using datetime module

# TODO: Add error handling. Need to handle the case where the user already exists.
new_user.create_ad_user()


# %%
print(f"User {new_user.full_name} created successfully.")


