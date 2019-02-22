
# this is a structure of main yandex direct authentication params
YD_API_AUTH_DATA = ('token', )

# structure of main yandex direct auth headers
YD_API_AUTH_HEADERS = ('Authorization', )

# Structure of main yandex direct oauth api request fields for token retrieval
YD_OAUTH_DATA = ('client_id', 'client_secret')

YD_OAUTH_TOKEN_FIELD_NAME = 'access_token'

# Structure of main yandex direct keyword bid groups
YD_KEYWORD_BIDS_GROUPS = ('ad_group_id', 'campaign_id', 'keyword_id')

# Structure of main yandex direct keyword bid field names
YD_KEYWORD_BIDS_FIELDNAMES = ("KeywordId", "AdGroupId", "CampaignId", "ServingStatus", "StrategyPriority")

# Structure of extra yandex direct keyword bid response fields
YD_KEYWORD_BIDS_EXTRA_FIELDNAMES = ('Search', 'Network')

# Structure of main yandex direct keyword bid search fields
YD_KEYWORD_BIDS_SEARCH_FIELDS = ("Bid", "AuctionBids")

# Structure of main yandex direct keyword bid network fields
YD_KEYWORD_BIDS_NETWORK_FIELDS = ("Bid", "Coverage")

# Structure of Yandex Direct keyword bids *SET* response possible error tags
YD_KEYWORD_BIDS_SET_ERROR_RESULTS = ('Warnings', 'Errors')

# Structure of main yandex direct campaigns field names
YD_CAMPAIGNS_FIELDNAMES = ("Id", "Name")

YD_ADS_FIELDNAMES = ("AdGroupId", "CampaignId", "Id", "Type")

YD_ADS_TYPES = ('TextAd', 'DynamicTextAd', 'MobileAppAd',
                 'TextImageAd', 'MobileAppImageAd', 'TextAdBuilderAd', 'MobileAppAdBuilderAd',
                 'CpcVideoAdBuilderAd', 'CpmBannerAdBuilderAd')

YD_SITELINKS_COLLECTION_FIELDNAMES = ("Id", "Sitelinks")

YD_SITELINK_FIELDNAMES = ('CollectionId', 'Title', 'Href')


class YdAPiV5EndpointsStruct:
    """
    This structure holds main API methods of Yandex Direct v5.
    """
    KEYWORD_BIDS = 'keywordbids'
    CLIENTS = 'clients'
    CAMPAIGNS = 'campaigns'
    ADS = 'ads'
    SITELINKS = 'sitelinks'
    # add new endpoints here ...


class YmAPIv2EndPointsStruct:
    """
    This structure holds main API methods of Yandex Market v2.
    """
    CAMPAIGNS = 'campaigns'
    FEEDS = 'feeds'


class YdAdTypes:
    TEXT_AD = "TEXT_AD"
    MOBILE_APP_AD = "MOBILE_APP_AD"
    DYNAMIC_TEXT_AD = "DYNAMIC_TEXT_AD"
    IMAGE_AD = "IMAGE_AD"
    CPC_VIDEO_AD = "CPC_VIDEO_AD"
    CPM_BANNER_AD = "CPM_BANNER_AD"