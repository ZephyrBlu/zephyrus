from django.shortcuts import render


def landing_page(request):
    return render(request, 'site_structure/landing-page.html')


def homepage(request):
    info = 'This is the homepage'
    heading = 'Welcome'
    title = 'Zephyrus | Home'
    active = 'home'
    context = {
            'info':info,
            'heading':heading,
            'title': title,
            'active': active
    }
    return render(request, 'site_structure/index.html', context)


def premium(request):
    info = 'This is the premium sign up page'
    heading = 'Premium'
    title = 'Zephyrus | Premium'
    active = 'premium'
    context = {
        'info': info,
        'heading': heading,
        'title': title,
        'active': active
    }
    return render(request, 'site_structure/index.html', context)


def about(request):
    info = 'This is the about page'
    heading = 'About Us'
    title = 'Zephyrus | About Us'
    active = 'about'
    context = {
        'info': info,
        'heading': heading,
        'title': title,
        'active': active
    }
    return render(request, 'site_structure/index.html', context)


def contact(request):
    info = 'This is the contact page'
    heading = 'Contact Us'
    title = 'Zephyrus | Contact Us'
    active = 'contact'
    context = {
        'info': info,
        'heading': heading,
        'title': title,
        'active': active
    }
    return render(request, 'site_structure/index.html', context)
