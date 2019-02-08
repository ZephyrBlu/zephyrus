import hashlib
from django.shortcuts import render, redirect
from .forms import ReplayFileForm
from django.core.validators import FileExtensionValidator
from django.core.files.storage import default_storage
from apps.processreplays.views import parse_replay
from .models import ReplayInfo
from apps.user_profile.models import BattlenetAccount


def sha256sum(f):
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    for n in iter(lambda: f.readinto(mv), 0):
        h.update(mv[:n])
    return h.hexdigest()


def upload_form(request, context):
    if request.method == 'POST':
        file_extension_checker = FileExtensionValidator(['sc2replay'])
        file_extension_checker(request.FILES['file'])

        form = ReplayFileForm(request.POST, request.FILES)
        if form.is_valid():
            current_user = request.user
            # user_battlenet = BattlenetAccount.objects.all()

            raw_replay = parse_replay(request.FILES['file'])
            file_hash = sha256sum(request.FILES['file'])
            request.FILES['file'].name = f'{file_hash}.SC2Replay'
            filename = request.FILES['file'].name
            bucket_path = f'{current_user.email}/{filename}'

            replay = ReplayInfo(file_path=bucket_path, player1=raw_replay['player1'], player2=raw_replay['player2'])
            replay.save()

            file_contents = request.FILES['file'].open(mode='rb')
            current_replay = default_storage.open(bucket_path, 'w')
            current_replay.write(file_contents.read())
            current_replay.close()
        return redirect('/profile/')
    else:
        form = ReplayFileForm()
        context['form'] = form
    return render(request, 'upload_file/upload_form.html', context)
