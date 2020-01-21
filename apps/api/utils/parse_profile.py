import re
import requests


def parse_profile(url):
    url_data = re.search('(?!/profile/)\d/\d/\d*', url)

    if not url_data:
        return None

    region_id = int(url_data.group().split('/')[0])

    data_url = f'https://starcraft2.com/en-us/api/sc2/profile/{url_data.group()}?locale=en_US'
    profile_data = requests.get(data_url).json()

    realm_id = int(profile_data['summary']['realm'])
    profile_id = int(profile_data['summary']['id'])
    profile_name = profile_data['summary']['displayName']

    regions = {1: 'NA', 2: 'EU', 3: 'KR'}

    return {
        str(region_id): {
            'realm_id': realm_id,
            'profile_id': [profile_id],
            'region_name': regions[region_id],
            'profile_name': profile_name,
        }
    }
