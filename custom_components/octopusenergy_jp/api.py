"""API client for Octopus Energy Japan."""
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientSession
import async_timeout

from .const import API_ENDPOINT, TOKEN_VALID_DURATION

_LOGGER = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Exception when authentication fails."""


class APIError(Exception):
    """Exception when API request fails."""


class OctopusEnergyJP:
    """API client for Octopus Energy Japan."""

    def __init__(
        self,
        session: ClientSession,
        email: str,
        password: str,
        account_number: str,
    ) -> None:
        """Initialize the API client."""
        self.session = session
        self.email = email
        self.password = password
        self.account_number = account_number
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry = 0

    async def async_get_token(self) -> str:
        """Get auth token."""
        # If token exists and is not expired, return it
        if self.token and time.time() < self.token_expiry:
            return self.token

        # If refresh token exists, try to use it
        if self.refresh_token:
            try:
                await self._refresh_token()
                return self.token
            except Exception:
                _LOGGER.warning("Failed to refresh token, getting new token")

        # Otherwise get a new token with email/password
        login_mutation = """
        mutation login($input: ObtainJSONWebTokenInput!) {
          obtainKrakenToken(input: $input) {
            token
            refreshToken
          }
        }
        """

        variables = {
            "input": {
                "email": self.email,
                "password": self.password,
            }
        }

        response = await self._graphql_request(login_mutation, variables, auth_required=False)
        try:
            data = response["data"]["obtainKrakenToken"]
            self.token = data["token"]
            self.refresh_token = data["refreshToken"]
            self.token_expiry = time.time() + TOKEN_VALID_DURATION
            return self.token
        except (KeyError, TypeError) as err:
            raise AuthenticationError(f"Failed to get token: {err}") from err

    async def _refresh_token(self) -> None:
        """Refresh the authentication token."""
        login_mutation = """
        mutation refreshToken($input: ObtainJSONWebTokenInput!) {
          obtainKrakenToken(input: $input) {
            token
            refreshToken
          }
        }
        """

        variables = {
            "input": {
                "refreshToken": self.refresh_token,
            }
        }

        response = await self._graphql_request(login_mutation, variables, auth_required=False)
        try:
            data = response["data"]["obtainKrakenToken"]
            self.token = data["token"]
            self.refresh_token = data["refreshToken"]
            self.token_expiry = time.time() + TOKEN_VALID_DURATION
        except (KeyError, TypeError) as err:
            raise AuthenticationError(f"Failed to refresh token: {err}") from err

    async def _graphql_request(
        self, query: str, variables: Dict[str, Any] = None, auth_required: bool = True
    ) -> Dict[str, Any]:
        """Make a request to the GraphQL API."""
        headers = {"Content-Type": "application/json"}

        if auth_required:
            token = await self.async_get_token()
            headers["Authorization"] = token

        try:
            async with async_timeout.timeout(20):
                response = await self.session.post(
                    API_ENDPOINT,
                    headers=headers,
                    json={"query": query, "variables": variables},
                )
                response_json = await response.json()

                if "errors" in response_json:
                    error_message = response_json["errors"][0]["message"]
                    raise APIError(f"GraphQL error: {error_message}")

                return response_json
        except aiohttp.ClientError as err:
            raise APIError(f"Request failed: {err}") from err

    async def async_get_electricity_usage(
        self, from_datetime: datetime, to_datetime: datetime
    ) -> List[Dict[str, Any]]:
        """Get electricity usage data."""
        query = """
        query halfHourlyReadings(
            $accountNumber: String!
            $fromDatetime: DateTime
            $toDatetime: DateTime
        ) {
            account(accountNumber: $accountNumber) {
                properties {
                    electricitySupplyPoints {
                        status
                        agreements {
                            validFrom
                        }
                        halfHourlyReadings(
                            fromDatetime: $fromDatetime
                            toDatetime: $toDatetime
                        ) {
                            consumptionRateBand
                            consumptionStep
                            costEstimate
                            startAt
                            value
                        }
                    }
                }
            }
        }
        """

        variables = {
            "accountNumber": self.account_number,
            "fromDatetime": from_datetime.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "toDatetime": to_datetime.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        }

        try:
            response = await self._graphql_request(query, variables)
            readings = response["data"]["account"]["properties"][0]["electricitySupplyPoints"][0]["halfHourlyReadings"]
            return readings
        except (KeyError, IndexError) as err:
            _LOGGER.error("Failed to parse electricity usage data: %s", err)
            return []

    async def async_get_yesterday_data(self) -> Dict[str, float]:
        """Get yesterday's electricity usage and cost data."""
        # Get yesterday's date in UTC
        today_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_utc = today_utc - timedelta(days=1)
        
        # Get data for the entire day
        from_datetime = yesterday_utc
        to_datetime = today_utc - timedelta(seconds=1)  # 23:59:59 yesterday
        
        readings = await self.async_get_electricity_usage(from_datetime, to_datetime)
        
        if not readings:
            return {"energy_usage": 0.0, "energy_cost": 0.0}
            
        # Calculate total usage and cost
        total_usage = sum(float(reading["value"]) for reading in readings if reading.get("value"))
        total_cost = sum(float(reading["costEstimate"]) for reading in readings if reading.get("costEstimate"))
        
        return {
            "energy_usage": round(total_usage, 2),
            "energy_cost": round(total_cost, 2),
        }

    async def async_get_hourly_data(self, start_at: datetime, end_at: datetime) -> List[Dict[str, Any]]:
        """Get hourly electricity usage data."""
        query = """
        query getAccountMeasurements(
            $propertyId: ID!
            $first: Int!
            $utilityFilters: [UtilityFiltersInput!]
            $startAt: DateTime
            $endAt: DateTime
            $timezone: String
        ) {
            property(id: $propertyId) {
                measurements(
                    first: $first
                    utilityFilters: $utilityFilters
                    startAt: $startAt
                    endAt: $endAt
                    timezone: $timezone
                ) {
                    edges {
                        node {
                            value
                            unit
                            startAt
                            endAt
                            durationInSeconds
                            metaData {
                                statistics {
                                    costExclTax {
                                        pricePerUnit {
                                            amount
                                        }
                                        costCurrency
                                        estimatedAmount
                                    }
                                    costInclTax {
                                        costCurrency
                                        estimatedAmount
                                    }
                                    value
                                    description
                                    label
                                    type
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        variables = {
            "propertyId": self.account_number,
            "first": 100,
            "startAt": start_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "endAt": end_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "timezone": "Asia/Tokyo",
            "utilityFilters": [{
                "electricityFilters": {
                    "readingFrequencyType": "THIRTY_MIN_INTERVAL",
                    "marketSupplyPointId": self.account_number,
                    "readingDirection": "CONSUMPTION"
                }
            }]
        }

        try:
            response = await self._graphql_request(query, variables)
            measurements = response["data"]["property"]["measurements"]["edges"]
            return [edge["node"] for edge in measurements]
        except (KeyError, IndexError) as err:
            _LOGGER.error("Failed to parse hourly data: %s", err)
            return []

    async def async_get_two_weeks_data(self) -> List[Dict[str, Any]]:
        """Get two weeks of electricity usage data."""
        end_at = datetime.utcnow()
        start_at = end_at - timedelta(days=14)
        return await self.async_get_hourly_data(start_at, end_at) 