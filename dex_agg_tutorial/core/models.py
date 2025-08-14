from django.db import models
from .validation import Exchange


class Pair(models.Model):
    """Model representing a token pair."""

    uid = models.IntegerField(unique=True)
    pair_id = models.CharField(max_length=40, unique=True)
    pool_contracts = models.JSONField(
        default=dict,
        blank=True,
        help_text="Mapping of exchange IDs to their pool contract addresses"
    )
    base_token = models.CharField(max_length=20)
    quote_token = models.CharField(max_length=20)
    active_exchanges = models.JSONField(
        default=list,
        blank=True,
        help_text="List of exchange IDs where this pair is active",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # make it so the model orders the pairs by uid for consistent data requests.
    class Meta:
        ordering = ["uid"]

    def __str__(self):
        return self.pair_id

    # Small QOL item so we can call a pair and immediately check if its active
    @property
    def is_active(self):
        """A pair is considered active if it has at least one exchange."""
        return len(self.active_exchanges) > 0
