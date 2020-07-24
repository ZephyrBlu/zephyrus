import json

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from zephyrus.settings import FRONTEND_URL
from apps.user_profile.models import FeatureVote

from .permissions import IsOptionsPermission
from .authentication import IsOptionsAuthentication


class FeatureVoteSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    feature_votes = {
        'f1cab883-f18b-49f8-976a-a62e4b4a82c6': [
            'shareable-replay-pages',
            'winrate-page',
            'game-info',
            'demo-website',
            'focus-goal-tracking',
            'other',
        ],
    }

    def preflight(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def fetch(self, request):
        _uuid = list(self.feature_votes.keys())[0]
        votes = list(FeatureVote.objects.filter(
            vote_id=_uuid,
            user_account_id=request.user.email,
        ))

        response = Response({'votes': list((f.feature, f.comment) for f in votes)})
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def write(self, request):
        data = json.loads(request.body)
        features = data['features']
        votes = data['votes']

        if len(votes) > 2:
            limited_votes = {}
            for count, (f, c) in enumerate(votes.items(), start=1):
                if count >= 2:
                    break
                limited_votes[f] = c
            votes = limited_votes

        for _uuid, f in self.feature_votes.items():
            # if features match, then we save votes
            if f == features:
                existing_votes = list(FeatureVote.objects.filter(
                    vote_id=_uuid,
                    user_account_id=request.user.email,
                ))

                # set for keeping track of new votes
                # that match existing votes
                existing_features = set()

                # saving each vote to database
                for feature_code, comment in votes.items():
                    # if client feature_code isn't in our
                    # feature list, stop doing things
                    # either error or malicious
                    if feature_code not in f:
                        break

                    exists = False
                    for v in existing_votes:
                        if feature_code == v.feature and comment == v.comment:
                            exists = True
                            existing_features.add(feature_code)
                            break

                    # if a vote for this feature doesn't already exist
                    # create a new record for it
                    if not exists:
                        new_vote = FeatureVote(
                            vote_id=_uuid,
                            user_account_id=request.user.email,
                            feature=feature_code,
                            comment=comment[:100],
                        )
                        new_vote.save()

                # remove old votes from the database
                # iterate through all existing votes
                # if the feature already existed, leave it
                # else delete the record
                for vote in existing_votes:
                    # feature in existing_features set means
                    # it already existed in the database
                    if vote.feature not in existing_features:
                        vote.delete()
                break

        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response
