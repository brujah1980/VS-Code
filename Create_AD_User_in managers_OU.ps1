## Created by David Bird
# Collecting user account information
$firstname = Read-Host -Prompt "Enter your first name"
$lastname = Read-Host -Prompt "Enter your last name"
# employmentStatus = Read-Host -Prompt "Are they a Temp or Employee?"
$employeeUpn = Read-Host -Prompt "Enter your email address"
$employeeManager = Read-Host -Prompt "Enter your manager's email address"
$startDay = Read-Host -Prompt "Enter the new hire start date"
$startDate = Read-Host -Prompt "Enter the new hire start date"

# Creating variables based on information provided
$fullName = "$lastname, $firstname"
$samAccount = "$firstname.$lastname"
$newPassword = "$startDay$startDate" + '!'
$fullName = "$lastname, $firstname"
$displayName = "$firstname $lastname"

# Connect to Active Directory and get $employeeManager containing OU
$employeeManagerOU = Get-ADUser -Filter "EmailAddress -eq '$employeeManager'" -Properties DistinguishedName |
                    Select-Object -ExpandProperty DistinguishedName

# Create new user account in Active Directory
New-ADUser -Name "$fullName" -GivenName $firstname -Surname $lastname -DisplayName $displayName -SamAccountName $samAccount -UserPrincipalName $employeeUpn -EmailAddress $employeeUpn -Enabled $true -AccountPassword (ConvertTo-SecureString -AsPlainText $newPassword -Force) -PassThru | Move-ADObject -TargetPath $employeeManagerOU