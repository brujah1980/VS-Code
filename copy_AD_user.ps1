## Created by ChatGPT by request from David Bird
## Azure section created by David Bird

# Set constants, be sure to change these to match your environment.
$domainName = "contoso.com"

# Prompt for existing user details
$existingUsername = Read-Host -Prompt "Enter the existing username to copy details from"

# Get existing user details
$existingUser = Get-ADUser -Identity $existingUsername -Properties MemberOf, DistinguishedName

# Prompt for start day and date
$startDay = Read-Host -Prompt "Enter the start day (e.g., Monday)"
$startDate = Read-Host -Prompt "Enter the start date (e.g., 01012022)"

# Generate password from start day and date
$password = $startDay.ToLower() + $startDate

# Ensure the password does not contain "/"
while ($password -match "/") {
    Write-Host "Generated password contains '/'. Modifying..."
    $startDate = Read-Host -Prompt "Enter the start date (e.g., 01012022)"
    $password = $startDay.ToLower() + $startDate
}

# Capitalize the first letter and add an exclamation mark
$password = $password.Substring(0,1).ToUpper() + $password.Substring(1) + "!"

# Prompt for new user details
$firstName = Read-Host -Prompt "Enter the first name"
$lastName = Read-Host -Prompt "Enter the last name"

# Generate the new username with a period between first name and last name
$newUsername = "$firstName.$lastName"
$userUPN = "$newUsername@$domainName"

# Prompt for user's title
$userTitle = Read-Host -Prompt "Enter the user's title"

# Prompt for cell phone number
$cellPhoneNumber = Read-Host -Prompt "Enter the cell phone number"

# Set the path for the new user (use the OU from the existing user)
$newUserPath = $existingUser.DistinguishedName -replace "CN=$existingUsername,", ""

# Create the new user
New-ADUser -SamAccountName $newUsername -UserPrincipalName "$userUpn" -GivenName $firstName -Surname $lastName -Name "$firstName $lastName" -DisplayName "$lastName, $firstName" -Enabled $true -Path $newUserPath -AccountPassword ($password | ConvertTo-SecureString -AsPlainText -Force)

# Set the description for the new user
Set-ADUser -Identity $newUsername -Description $userTitle

# Set the mobile number for the new user
Set-ADUser -Identity $newUsername -Mobile $cellPhoneNumber

# Set the manager's name for the new user
# Note: You can modify this line to prompt for the manager's name if needed
Set-ADUser -Identity $newUsername -Manager ""

# Set the email address for the new user
Set-ADUser -Identity $newUsername -EmailAddress $userUPN

# Add the new user to the same groups as the existing user
foreach ($group in $existingUser.MemberOf) {
    Add-ADGroupMember -Identity $group -Members $newUsername
}

Write-Host "User account created successfully with password generated from start day and date, description set to user's title, mobile number set, OU copied, manager's name set to empty, email address generated, and new username generated."

# Run Start-ADSyncSyncCycle
Start-ADSyncSyncCycle -PolicyType Delta
