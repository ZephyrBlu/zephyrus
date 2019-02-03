from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.upload_file.models import ReplayInfo
from .models import ReplaySerializer


# returns all replays
class ReplayList(generics.ListAPIView):
    queryset = ReplayInfo.objects.all()
    serializer_class = ReplaySerializer


# returns particular replay based on pk ID in database
class Replay(generics.RetrieveAPIView):
    queryset = ReplayInfo.objects.all()
    serializer_class = ReplaySerializer


# returns last uploaded replay
class LatestReplay(APIView):
    def get(self, request, format=None):
        replay = ReplayInfo.objects.latest('uploaded_at')
        serializer = ReplaySerializer(replay)
        return Response(serializer.data)
