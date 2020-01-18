# import beatifulsoup scraping lib


def scrape_profile_url(url):
    # check url, if invalid return None
    # if valid, scrape data and return

    isUrlValid = True

    if not isUrlValid:
        return None

    # scrape profile

    profile_info = {
        'profile_name': '',
        'profile_id': None,
        'region_id': 1,
        'realm_id': 1,
    }

    return profile_info
