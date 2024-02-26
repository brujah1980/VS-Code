import requests

# Define the necessary variables
tenant_id = 'YOUR_TENANT_ID'
client_id = 'YOUR_CLIENT_ID'
client_secret = 'YOUR_CLIENT_SECRET'
user_principal_name = 'USER_PRINCIPAL_NAME'
license_sku_id = 'LICENSE_SKU_ID'

# Get an access token using client credentials flow
token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
token_data = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
    'scope': 'https://graph.microsoft.com/.default'
}
token_response = requests.post(token_url, data=token_data).json()
access_token = token_response['access_token']

# Assign the license to the user
assign_license_url = f'https://graph.microsoft.com/v1.0/users/{user_principal_name}/assignLicense'
assign_license_data = {
    'addLicenses': [
        {
            'skuId': license_sku_id
        }
    ],
    'removeLicenses': []
}
assign_license_headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
assign_license_response = requests.post(assign_license_url, json=assign_license_data, headers=assign_license_headers)

# Check the response status
if assign_license_response.status_code == 200:
    print('License assigned successfully.')
else:
    print('Failed to assign the license.')
