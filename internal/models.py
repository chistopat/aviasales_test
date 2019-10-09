import dataclasses
import typing


@dataclasses.dataclass
class AirFareSearchResponse:
    request_time: str
    response_time: str
    request_id: str
    prised_itineraries: dict

    def __init__(self, data: typing.Any):
        self.request_time = data['RequestTime']
        self.response_time = data['ResponseTime']
        self.request_id = data['RequestId']
        self.prised_itineraries = data['PricedItineraries']
