## 
import requests

# Get a list of unassigned extensions
unassigned_extensions_url = 'https://platform.ringcentral.com/restapi/v1.0/account/~/extension'
headers = {
    'Authorization': f'Bearer {access_token}'
}
params = {
    'status': 'Unassigned'
}
response = requests.get(unassigned_extensions_url, headers=headers, params=params)
unassigned_extensions = response.json()['records']

# Ask the user which extension to assign
print('Unassigned Extensions:')
for i, extension in enumerate(unassigned_extensions):
    print(f'{i+1}. {extension["extensionNumber"]}')

selected_extension_index = int(input('Enter the number of the extension to assign: ')) - 1
selected_extension = unassigned_extensions[selected_extension_index]

# Assign the selected extension to a user
assign_extension_url = f'https://platform.ringcentral.com/restapi/v1.0/account/~/extension/{selected_extension["id"]}/users'
response = requests.put(assign_extension_url, headers=headers, json=data)

# Check the response
if response.status_code == 200:
    print('Extension assigned successfully.')
else:
    print('Failed to assign extension.')