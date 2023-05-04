import datetime

import pytest
from uuid import uuid4

from ..simple_env import SimpleEnv
from dodgeball.interfaces.api_types import DodgeballEvent
from dodgeball.api.dodgeball import Dodgeball
from dodgeball.api.dodgeball_config import DodgeballConfig


@pytest.mark.asyncio
class TestDodgeball:
    async def test_post_event(self):
        base_url = SimpleEnv.get_value("BASE_URL")
        secret_key = SimpleEnv.get_value("PRIVATE_API_KEY")

        db_agent = Dodgeball(
            secret_key,
            DodgeballConfig(base_url))

        db_event = DodgeballEvent(
            type="PAYMENT",
            ip="128.103.69.86",
            data={
                "transaction": {
                    "amount": 100,
                    "currency": "USD"
                },
                "paymentMethod": "paymentMethodId",
                "customer": {
                    "primaryEmail": "simpleTest@dodgeballhq.com",
                    "dateOfBirth": "1990-01-01",
                    "primaryPhone": "17609003548",
                    "firstName": "CannedFirst"
                },
                "session": {
                    "userAgent": "unknown user header",
                    "externalId":"UNK  RAW Session"
                },
                "mfaPhoneNumbers": SimpleEnv.get_value("MFA_PHONE_NUMBERS"),
                "email": "test@dodgeballhq.com"
            }
        )

        response = await db_agent.post_event(
            None,
            str(uuid4()),
            "andrew@dodgeballhq.com",
            db_event
        )

        assert response.success

    def create_checkpoint_data(self):
        return {
            "transaction": {
                "amount": 100,
                "currency":"USD",
            },
            "paymentMethod":"paymentMethodId",
            "customer": {
                "primaryEmail":"simpleTest@dodgeballhq.com",
                "dateOfBirth": "1990-01-01",
                "primaryPhone": "17609003548",
                "firstName": "CannedFirst",
            },
            "session": {
                "userAgent": "unknown user header",
                "externalId": "UNK  RAW Session"
            },
            # For now we set a hard-coded list of phone numbers, this can
            # be filled in from the client in order to dynamically set
            "mfaPhoneNumbers": SimpleEnv.get_value("MFA_PHONE_NUMBERS"),
            "email": "test@dodgeballhq.com",
            # Gr4vy Testing
            "gr4vy": {
                "buyerId": "d48f2a52-2cdf-4708-99c5-5bb8717ab11d",
                "paymentMethodId": "3ab6199a-c689-4eae-a43c-fa728857f1f1",
                "transactionId": "d2ed8384-1f35-4fa2-a950-617e55f9f711",
            },
            "merchantRisk": {
                "application": {
                    "id": "ABC123456789XYZ",
                    "time": "2020-12-31 13:45",
                },
                "ipAddress": "65.199.91.101",
                "business": {
                    "name": "Yellowstone Pioneer Lodge",
                    "address": {
                        "line1": "1515 W Park Street",
                        "city": "Livingston",
                        "stateCode": "MT",
                        "postalCode": "59047",
                        "countryCode": "US",
                    },
                    "phone": {
                        "number": "406-222-6110",
                        "countryCode": "US",
                    },
                    "emailAddress": "jdoe@yahoo.com",
                },
                "individual": {
                    "name": "John Doe",
                    "address": {
                        "line1": "1302 W Geyser St",
                        "city": "Livingston",
                        "stateCode": "MT",
                        "postalCode": "59047",
                        "countryCode": "US",
                    },
                    "phone": {
                        "number": "2069735100",
                        "countryCode": "US",
                    },
                    "emailAddress": "jdoe@yahoo.com",
                }
            },

            # Kount Testing
            "kount": {
                "isAuthorized": "A",
                "currency": "USD",
                "email": "ashkan@dodgeballhq.com",
                "ipAddress": "127.0.0.1",
                "paymentToken": "4111111111111111",
                "paymentType": "CARD",
                "totalAmount": "90000",
                "product": {
                    "description": "FlightBooking",
                    "itemSKU": "Online Flight Booking",
                    "price": 633,
                    "quantity": 2,
                    "title": "Flight Trip Booking",
                },
                "name": "Ashkan Test",
                "billingStreet1": "West St.",
                "billingStreet2": "Apt 222",
                "billingCity": "Bellevue",
                "billingState": "WA",
                "bankIdentificationNumber": "4111",
                "ptokCountry": "US",
                "billingEmailAge": 6
            },
            "deduce": {
                "isTest": True
            },
            "seon": {
                "phone": "17609003548",
                "fullName": "Example Name",
                "firstName": "Example",
                "middleName": "string",
                "lastName": "string",
                "dateOfBirth": "1990-01-01",
                "placeOfBirth": "Budapest",
                "photoIdNumber": "56789",
                "userId": "123456",
                "bin": "555555",
            },
            "peopleDataLabs": {
                "enrichCompany": {
                    "name": "Google",
                    "profile": "https://www.linkedin.com/company/google/",
                },
                "enrichPerson": {
                    "firstName": "Elon",
                    "lastName": "Musk",
                    "birthDate":  " ",
                    "company": "Tesla",
                    "primaryEmail":  " ",
                    "phone": " "
                }
            }
        };

    async def test_post_checkpoint(self):
        base_url = SimpleEnv.get_value("BASE_URL")
        secret_key = SimpleEnv.get_value("PRIVATE_API_KEY")
        db_agent = Dodgeball(
            secret_key,
            DodgeballConfig(base_url))

        db_event = DodgeballEvent(
            type="WITH_MFA",
            ip="128.103.69.86",
            data=self.create_checkpoint_data())

        checkpoint_response = await db_agent.checkpoint(
            db_event,
            None,
            str(datetime.datetime.now()),
            "test@dodgeballhq.com"
            );

        assert checkpoint_response.success

        if db_agent.is_allowed(checkpoint_response):
            # This is the scenario under which we have completed
            # But we should be in blocked state with MFA
            assert False
        elif db_agent.is_denied(checkpoint_response):
            # Inform the client that this request has been refused
            assert False
        elif db_agent.is_running(checkpoint_response):
            print("Pass control back to the Client")
        else:
            print("This is an error state!")
            assert False
