from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .queries import get_token_price
from .models import Pair


class DefaultView(APIView):
    def get(self, request):
        welcome_message = "Thank you for choosing to use my awesome price API!"
        return Response(welcome_message, status=200)


class PriceView(APIView):
    """
    View to access the best price from 2 exchanges for supported tokenpairs.

    * no authentication
    """

    def get(self, request, token_pair: str):
        """
        Return the price for a given token pair.
        """
        # Check if token pair exists in database and has active exchanges
        try:
            pair = Pair.objects.get(pair_id=token_pair.upper())
            if not pair.active_exchanges:
                return Response(
                    {"error": f"Token pair {token_pair} is not active on any exchange"},
                    status=400,
                )
        except Pair.DoesNotExist:
            return Response(
                {"error": f"Token pair {token_pair} is not supported"}, status=404
            )

        # Get price if pair is valid
        price = get_token_price(token_pair)
        return Response({"price": price, "pair": token_pair}, status=200)


class PairsView(APIView):
    """
    View to see the supported tokenpairs for the dex aggregator

    * no authentication for Get
    * Admin authentication for Post
    """

    def get(self, request, format=None):
        """
        Return a list of all available token pairs to query.
        """
        # Get pairs that have at least one active exchange
        pairs = Pair.objects.exclude(active_exchanges=[]).values()
        return Response(pairs, status=200)

    def post(self, request, format=None):
        """
        Add a new token pair to the available token pairs.
        Only admin users can create pairs.
        """
        # Check admin permission for POST requests only
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=403)
        try:
            data = request.data

            # Check if pair already exists
            pair_id = data.get("pair_id")
            if Pair.objects.filter(pair_id=pair_id).exists():
                return Response({"error": f"Pair {pair_id} already exists"}, status=400)

            # Generate uid automatically (max existing + 1)
            max_uid = Pair.objects.aggregate(models.Max("uid"))["uid__max"]
            next_uid = (max_uid or 0) + 1

            # Create new pair
            pair = Pair(
                uid=next_uid,
                pair_id=pair_id,
                pool_contracts=data.get("pool_contracts", {}),
                base_token=data.get("base_token"),
                quote_token=data.get("quote_token"),
                active_exchanges=data.get("active_exchanges", []),
            )
            pair.save()

            return Response(
                {"message": f"Created pair {pair.pair_id}", "pair_id": pair.pair_id},
                status=201,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=400)
