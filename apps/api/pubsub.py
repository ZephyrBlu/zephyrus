import json
from google.cloud import pubsub_v1

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from zephyrus.settings import (
    GS_PROJECT_ID,
    UPLOAD_FUNC_TOPIC,
    VERIFY_FUNC_TOPIC,
    FRONTEND_URL,
)

from .utils.filter_user_replays import filter_user_replays

from .permissions import IsOptionsPermission
from .authentication import IsOptionsAuthentication


class UploadReplay(APIView):
    """
    Handles replay uploads from the /upload API endpoint

    Creates a File wrapper around uploaded replay file data,
    then hashes the file to create a unique ID.

    Then the replay file is processed and stored in a bucket, or if
    processing is unsuccessful an error is returned and the replay is
    stored in an alternate bucket for failed replays.
    """
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization, content-type'
        return response

    def post(self, request):
        token = str(request.auth)
        file_data = request.body

        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(GS_PROJECT_ID, UPLOAD_FUNC_TOPIC)

        # When you publish a message, the client returns a future.
        publisher.publish(
            topic_path, token=token, data=file_data  # data must be a bytestring.
        )

        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization, content-type'
        return response


class VerifyReplaysViewset(viewsets.ModelViewSet):
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

    def verify(self, request):
        token = str(request.auth)
        unlinked_replays = filter_user_replays(request, None, 'verify')

        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(GS_PROJECT_ID, VERIFY_FUNC_TOPIC)

        for replay in unlinked_replays:
            replay_data = {
                'file_hash': replay.file_hash,
                'user_account': replay.user_account.email,
            }
            byte_data = json.dumps(replay_data).encode('utf-8')

            # When you publish a message, the client returns a future.
            publisher.publish(
                topic_path, token=token, data=byte_data  # data must be a bytestring.
            )

        response = Response({
            'count': len(unlinked_replays),
        })
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response
