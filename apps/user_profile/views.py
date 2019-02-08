from django.shortcuts import render
from django.views import View


def overview(request):
    profile_active = 'overview'
    info = 'This is the User Profile page'
    heading = 'Profile'
    title = 'Zephyrus | Profile'
    active = 'profile'
    auth = 'Authorize'
    context = {
        'info': info,
        'heading': heading,
        'title': title,
        'active': active,
        'profile_active': profile_active,
        'auth': auth
    }
    return render(request, 'user_profile/profile.html', context)


def analysis(request):
    profile_active = 'analysis'
    info = 'This is the User Profile page'
    heading = 'Profile'
    title = 'Zephyrus | Profile'
    active = 'profile'
    context = {
        'info': info,
        'heading': heading,
        'title': title,
        'active': active,
        'profile_active': profile_active
    }
    return render(request, 'user_profile/profile.html', context)


def replays(request):
    profile_active = 'replays'
    info = 'This is the User Profile page'
    heading = 'Profile'
    title = 'Zephyrus | Profile'
    active = 'profile'
    context = {
        'info': info,
        'heading': heading,
        'title': title,
        'active': active,
        'profile_active': profile_active
    }
    return render(request, 'user_profile/profile.html', context)


def display_replay(request, context):
    replay = ReplayInfo.objects.latest('uploaded_at')
    summary_info = parse_replay(replay.file)
    for k, player in summary_info.items():
        context[f'{k}'] = player['workers_produced']
    return render(request, 'user_profile/profile.html', context)
