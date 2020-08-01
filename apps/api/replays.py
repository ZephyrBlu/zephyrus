import json
import requests
from google.cloud import storage

from django.http import (
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseBadRequest,
)

from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from zephyrus.settings import (
    GS_PROJECT_ID,
    GS_CREDENTIALS,
    REPLAY_STORAGE,
    TIMELINE_STORAGE,
    API_KEY,
    FRONTEND_URL,
)

from apps.user_profile.models import Replay
from apps.process_replays.views import write_replay

from .utils.filter_user_replays import filter_user_replays
from .permissions import IsOptionsPermission


class ReplaySummaryViewset(viewsets.ModelViewSet):
    """
    Returns all user replays played with the given race param
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def preflight(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def retrieve(self, request):
        replay_summary = filter_user_replays(request, None, 'summary')
        response = Response(replay_summary)
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class RaceReplayViewSet(viewsets.ModelViewSet):
    """
    Returns all user replays played with the given race param
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def preflight(self, request, race):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def retrieve(self, request, race=None):
        serialized_replays = filter_user_replays(request, race)

        if serialized_replays is not None:
            response = Response(serialized_replays)
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response
        response = HttpResponseBadRequest({'response': 'No replays found or invalid race'})
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def count(self, request, race=None):
        replay_count = filter_user_replays(request, race, 'count')

        if replay_count is not None:
            response = Response(replay_count)
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response
        elif replay_count is False:
            response = HttpResponseNotFound()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response
        response = HttpResponseBadRequest({'response': 'No replays found or invalid race'})
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class FetchReplayTimeline(APIView):
    """
    Fetches the replay timeline related to the file hash param

    Returns the download URL for the timeline file
    """
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated | IsOptionsPermission]
    authentication_classes = []
    permission_classes = []

    def options(self, request, file_hash):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request, file_hash):
        timeline_url = f'https://www.googleapis.com/storage/v1/b/{TIMELINE_STORAGE}/o/{file_hash}.json.gz?key={API_KEY}'

        response = requests.get(timeline_url, headers={'Accept-Encoding': 'gzip'})
        metadata = response.json()

        response = Response({'timeline_url': metadata['mediaLink']})
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class FetchReplayFile(viewsets.ModelViewSet):
    """
    Returns a link to the downloadable replay file
    """
    authentication_classes = []
    permission_classes = [IsAuthenticatedOrReadOnly | IsOptionsPermission]

    def preflight(self, request, file_hash):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def download(self, request, file_hash):
        replay = list(Replay.objects.filter(file_hash=file_hash))[0]

        storage_client = storage.Client(project=GS_PROJECT_ID, credentials=GS_CREDENTIALS)
        replay_storage = storage_client.get_bucket(REPLAY_STORAGE)
        replay_blob_path = f'{replay.user_account_id}/{replay.battlenet_account_id}/{file_hash}.SC2Replay'
        replay_blob = replay_storage.blob(replay_blob_path)
        downloaded_replay = replay_blob.download_as_string(raw_download=True)

        response = HttpResponse(downloaded_replay, content_type='application/octet-stream')
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Content-Disposition'] = f'attachment; filename="{file_hash}.SC2Replay"'
        return response


class WriteReplaySet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def preflight(self, request):
        response = Response()
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def write(self, request):
        replay_data = json.loads(request.body)
        result = write_replay(replay_data, request)

        response = Response(result)
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

