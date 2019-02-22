from typing import NamedTuple

from common.utils import snake_to_camel


class KeywordBid(NamedTuple):
    """
    `Yandex Direct API keyword bid <https://tech.yandex.ru/direct/doc/ref-v5/keywordbids/get-docpage/>`
    representation. This entity describes YD API keyword bid *get* response structure.
    Initially this entity filled from YD API data source, but in order this to be changed occasionally,
    data source is decoupled from entity. So you may decide to store KeywordBid data in data base or other source
    and will require minimal changes in application.

    """
    campaign_id: int        #: YD Campaign ID
    ad_group_id: int        #: YD AdGroup ID
    keyword_id: int         #: YD KeywordBid ID
    search: dict            #: Search bids collection data (may include current Bid and AuctionBids data
    network: dict           #: Same as Search bid but for Network
    serving_status: str
    strategy_priority: str

    def as_dict(self) -> dict:
        """Returns a dictionary with keys in YD representation and entity attributes values"""
        return {snake_to_camel(k): v for k, v in self._asdict().items()}

    def __repr__(self):
        return str(self.as_dict())


class KeywordBidRule(NamedTuple):
    """
    Keyword bid calculation rule entity.

    This is a representation of how keyword bids retreived from YD api should be recalculated.
    User sets data in this entity and though, manages calculcation results.
    """
    account: int
    """
    Each rule relates to one given account
    """
    target_type: str
    """
    To which types of Yandex Direct bid entities rule should be applied. 
    This can be Campaign | AdGroup | Keyword.
    """
    target_values: list
    """
    Yandex Direct Ids of chosen target types. For what Ids should the bid be changed.
    """
    target_bid_diff: int
    """
    A difference in percents between the bid for the first maximum forecasted amount and 
    the bid for the second maximum forecasted amount 
    """
    bid_increase_percentage: int
    """
    To what rate should our bid be risen. 
    """
    max_bid: int
    """
    Upper threshold for our bid increase
    """
