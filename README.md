# Dodgeball Server Trust SDK for Python

## Table of Contents
- [Purpose](#purpose)
- [Prerequisites](#prerequisites)
- [Related](#related)
- [Installation](#installation)
- [Usage](#usage)
- [API](#api)

## Purpose
[Dodgeball](https://dodgeballhq.com) enables developers to decouple security logic from their application code. This has several benefits including:
- The ability to toggle and compare security services like fraud engines, MFA, KYC, and bot prevention.
- Faster responses to new attacks. When threats evolve and new vulnerabilities are identified, your application's security logic can be updated without changing a single line of code.
- The ability to put in placeholders for future security improvements while focussing on product development.
- A way to visualize all application security logic in one place.

The Dodgeball Server Trust SDK for Python makes integration with the Dodgeball API easy and is maintained by the Dodgeball team.

## Prerequisites
You will need to obtain a free Dodgeball account in order to leverage the Dodgeball SDK for Python.  If you don't already have an account, please sign up at:

​    https://app.dodgeballhq.com/signup

Once enrolled, you can obtain an API key for your application from the [Dodgeball developer center](https://app.dodgeballhq.com/developer).

## Related
Check out the [Dodgeball Trust Client SDK](https://npmjs.com/package/@dodgeball/trust-sdk-client) for how to integrate Dodgeball into your frontend applications.

## Installation
We will be registering the Dodgeball SDK for .NET with nuget.  But until then, please clone the project and include it as source in your projects.  

## Usage

```python

from dodgeball.interfaces.api_types import DodgeballEvent
from dodgeball.api.dodgeball import Dodgeball


/*
 * However you obtain it, please register your Private API
 * on SDK instantiation
 */
private_key = this.Vars["PRIVATE_API_KEY"];
dodgeball = new Dodgeball(privateKey);

/*
 * Contact Dodgeball for a full specification of the data input
 * vocabulary
 */
checkpoint_data = {
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

# We just use a random session id to demonstrate
session_id = str(uuid4()) 

/*
 * Execute a Dodgeball Checkpoint to protect a resource
 */
db_response = await dodgeball.Checkpoint(
      DodgeballEvent(
        type="PAYMENT",
        ip="128.103.69.86",
        data=checkpointData),
      null, #source token
      session_id
      "test@dodgeballhq.com" # user id
    );


/*
 * Then follow the cases of is_allowed, is_denied, is_running to
 * either give access to the resource, deny access, or pass    
 * control back to the front end to validate the user using MFA 
 * or Shared Secrets 
 */
if (dodgeball.is_allowed(db_response))
{
      // This is the scenario under which we have completed 
      // But we should be in blocked state with MFA
      // Perform back end operations to give access to resources
    } else if (dodgeball.is_denied(db_response)) {
      // Inform the user that their access has been refused
    } else if (dodgeball.is_running(db_response)) {
      // Pass control back to the JS Client to render MFA
    }
```

## API
### Configuration
___
The package requires a secret API key as the first argument to the constructor.
```python
dodgeball = new Dodgeball("secret-api-key...");
```
Optionally, you can pass in several configuration options to the constructor:
```js
const dodgeball = new Dodgeball("secret-api-key...", {
  // Optional configuration
  DodgeballConfig(
    "https://api.dodgeballhq.com", #apiUrl
    True, # isEnabled, allowing for test mode operations,
    apiVersion, # Only "v1" currently supported
    logger # Logger if you wish to integrate your own logging system
});
```
| Option | Default | Description |
|:-- |:-- |:-: |
| `apiUrl` | `https://api.dodgeballhq.com` | The base URL of the Dodgeball API. Useful for sending requests to different environments such as `https://api.sandbox.dodgeballhq.com`. |
| logLevel | LOGGING.ERROR | Required severity of log entries to be shown |

### Call a Checkpoint
___
Checkpoints represent key moments of risk in an application and at the core of how Dodgeball works. A checkpoint can represent any activity deemed to be a risk. Some common examples include: login, placing an order, redeeming a coupon, posting a review, changing bank account information, making a donation, transferring funds, creating a listing.

```js
const checkpointResponse = await dodgeball.checkpoint({
  checkpointName: "CHECKPOINT_NAME",
  event: {
    ip: "127.0.0.1", // The IP address of the device where the request originated
    data: {
      // Arbitrary data to send in to the checkpoint...
      transaction: {
        amount: 100,
        currency: 'USD',
      },
      paymentMethod: {
        token: 'ghi789'
      }
    }
  },
  sourceToken: "abc123...", // Obtained from the Dodgeball Client SDK, represents the device making the request
  sessionId: "session_def456", // The current session ID of the request
  userId: "user_12345", // When you know the ID representing the user making the request in your database (ie after registration), pass it in here. Otherwise leave it blank.
  useVerificationId: "def456" // Optional, if you have a verification ID, you can pass it in here
});
```
| Parameter | Required | Description |
|:-- |:-- |:-- |
| `checkpointName` | `true` | The name of the checkpoint to call. |
| `event` | `true` | The event to send to the checkpoint. |
| `event.ip` | `true` | The IP address of the device where the request originated. |
| `event.data` | `false` | Object containing arbitrary data to send in to the checkpoint. |
| `sourceToken` | `false` | A Dodgeball generated token representing the device making the request. Obtained from the [Dodgeball Trust Client SDK](https://npmjs.com/package/@dodgeball/trust-sdk-client). |
| `sessionId` | `true` | The current session ID of the request. |
| `userId` | `false` | When you know the ID representing the user making the request in your database (ie after registration), pass it in here. Otherwise leave it blank. |
| `useVerificationId` | `false` | If a previous verification was performed on this request, pass it in here. See the [useVerification](#useverification) section below for more details. |

### Interpreting the Checkpoint Response
___
Calling a checkpoint creates a verification in Dodgeball. The status and outcome of a verification determine how your application should proceed. Continue to [possible checkpoint responses](#possible-checkpoint-responses) for a full explanation of the possible status and outcome combinations and how to interpret them.
```ts
const checkpointResponse = {
  success: boolean,
  errors: [
    {
      code: number,
      message: string
    }
  ],
  version: string,
  verification: {
    id: string,
    status: string,
    outcome: string
  }
};
```
| Property | Description |
|:-- |:-- |
| `success` | Whether the request encountered any errors was successful or failed. |
| `errors` | If the `success` flag is `false`, this will contain an array of error objects each with a `code` and `message`. |
| `version` | The version of the Dodgeball API that was used to make the request. Default is `v1`. |
| `verification` | Object representing the verification that was performed when this checkpoint was called. |
| `verification.id` | The ID of the verification that was created. |
| `verification.status` | The current status of the verification. See [Verification Statuses](#verification-statuses) for possible values and descriptions. |
| `verification.outcome` | The outcome of the verification. See [Verification Outcomes](#verification-outcomes) for possible values and descriptions. |

#### Verification Statuses
| Status | Description |
|:-- |:-- |
| `COMPLETE` | The verification was completed successfully. |
| `PENDING` | The verification is currently processing. |
| `BLOCKED` | The verification is waiting for input from the user. |
| `FAILED` | The verification encountered an error and was unable to proceed. |

#### Verification Outcomes
| Outcome | Description |
|:-- |:-- |
| `APPROVED` | The request should be allowed to proceed. |
| `DENIED` | The request should be denied. |
| `PENDING` | A determination on how to proceed has not been reached yet. |
| `ERROR` | The verification encountered an error and was unable to make a determination on how to proceed. |

#### Possible Checkpoint Responses

##### Approved
```js
const checkpointResponse = {
  success: true,
  errors: [],
  version: "v1",
  verification: {
    id: "def456",
    status: "COMPLETE",
    outcome: "APPROVED"
  }
};
```
When a request is allowed to proceed, the verification `status` will be `COMPLETE` and `outcome` will be `APPROVED`.

##### Denied
```js
const checkpointResponse = {
  success: true,
  errors: [],
  version: "v1",
  verification: {
    id: "def456",
    status: "COMPLETE",
    outcome: "DENIED"
  }
};
```
When a request is denied, verification `status` will be `COMPLETE` and `outcome` will be `DENIED`.

##### Pending
```js
const checkpointResponse = {
  success: true,
  errors: [],
  version: "v1",
  verification: {
    id: "def456",
    status: "PENDING",
    outcome: "PENDING"
  }
};
```
If the verification is still processing, the `status` will be `PENDING` and `outcome` will be `PENDING`.

##### Blocked
```js
const checkpointResponse = {
  success: true,
  errors: [],
  version: "v1",
  verification: {
    id: "def456",
    status: "BLOCKED",
    outcome: "PENDING"
  }
};
```
A blocked verification requires additional input from the user before proceeding. When a request is blocked, verification `status` will be `BLOCKED` and the `outcome` will be `PENDING`.

##### Undecided
```js
const checkpointResponse = {
  success: true,
  errors: [],
  version: "v1",
  verification: {
    id: "def456",
    status: "COMPLETE",
    outcome: "PENDING"
  }
};
```
If the verification has finished, with no determination made on how to proceed, the verification `status` will be `COMPLETE` and the `outcome` will be `PENDING`.

##### Error
```js
const checkpointResponse = {
  success: false,
  errors: [
    {
      code: 503,
      message: "[Service Name]: Service is unavailable"
    }
  ],
  version: "v1",
  verification: {
    id: "def456",
    status: "FAILED",
    outcome: "ERROR"
  }
};
```
If a verification encounters an error while processing (such as when a 3rd-party service is unavailable), the `success` flag will be false. The verification `status` will be `FAILED` and the `outcome` will be `ERROR`. The `errors` array will contain at least one object with a `code` and `message` describing the error(s) that occurred.

### Utility Methods
___
There are several utility methods available to help interpret the checkpoint response. It is strongly advised to use them rather than directly interpreting the checkpoint response.

#### `dodgeball.IsAllowed(checkpointResponse)`
The `isAllowed` method takes in a checkpoint response and returns `true` if the request is allowed to proceed.

#### `dodgeball.IsDenied(checkpointResponse)`
The `isDenied` method takes in a checkpoint response and returns `true` if the request is denied and should not be allowed to proceed.

#### `dodgeball.IsRunning(checkpointResponse)`
The `isRunning` method takes in a checkpoint response and returns `true` if no determination has been reached on how to proceed. The verification should be returned to the frontend application to gather additional input from the user. See the [useVerification](#useverification) section for more details on use and an end-to-end example.

#### `dodgeball.IsUndecided(checkpointResponse)`
The `isUndecided` method takes in a checkpoint response and returns `true` if the verification has finished and no determination has been reached on how to proceed. See [undecided](#undecided) for more details.

#### `dodgeball.HasError(checkpointResponse)`
The `hasError` method takes in a checkpoint response and returns `true` if it contains an error.

#### `dodgeball.IsTimeout(checkpointResponse)`
The `isTimeout` method takes in a checkpoint response and returns `true` if the verification has timed out. At which point it is up to the application to decide how to proceed. 

### useVerification
___
Sometimes additional input is required from the user before making a determination about how to proceed. For example, if a user should be required to perform 2FA before being allowed to proceed, the checkpoint response will contain a verification with `status` of `BLOCKED` and  outcome of `PENDING`. In this scenario, you will want to return the verification to your frontend application. Inside your frontend application, you can pass the returned verification directly to the `dodgeball.handleVerification()` method to automatically handle gathering additional input from the user. Continuing with our 2FA example, the user would be prompted to select a phone number and enter a code sent to that number. Once the additional input is received, the frontend application should simply send along the ID of the verification performed to your API. Passing that verification ID to the `useVerification` option will allow that verification to be used for this checkpoint instead of creating a new one. This prevents duplicate verifications being performed on the user. 

**Important Note:** To prevent replay attacks, each verification ID can only be passed to `useVerification` once.

### Track an Event
___
You can track additional information about a user's journey by submitting tracking events from your server. This information will be added to the user's profile and is made available to checkpoints.

```js
await dodgeball.event({
  event: {
    type: "EVENT_NAME", // Can be any string you choose
    data: {
      // Arbitrary data to track...
      transaction: {
        amount: 100,
        currency: 'USD',
      },
      paymentMethod: {
        token: 'ghi789'
      }
    }
  },
  sourceToken: "abc123...", // Obtained from the Dodgeball Client SDK, represents the device making the request
  sessionId: "session_def456", // The current session ID of the request
  userId: "user_12345", // When you know the ID representing the user making the request in your database (ie after registration), pass it in here. Otherwise leave it blank.
})
```
| Parameter | Required | Description |
|:-- |:-- |:-- |
| `event` | `true` | The event to track. |
| `event.type` | `true` | A name representing where in the journey the user is. |
| `event.data` | `false` | Object containing arbitrary data to track. |
| `sourceToken` | `false` | A Dodgeball generated token representing the device making the request. Obtained from the [Dodgeball Trust Client SDK](https://npmjs.com/package/@dodgeball/trust-sdk-client). |
| `sessionId` | `true` | The current session ID of the request. |
| `userId` | `false` | When you know the ID representing the user making the request in your database (ie after registration), pass it in here. Otherwise leave it blank. |

#### End-to-End Example
```js
// In your frontend application...
async placeOrder = async (order, previousVerificationId = null) => {
  const sourceToken = await dodgeball.getSourceToken();

  const endpointResponse = await axios.post("/api/orders", { order }, {
    headers: {
      "x-dodgeball-source-token": sourceToken, // Pass the source token to your API
      "x-dodgeball-verification-id": previousVerificationId // If a previous verification was performed, pass it along to your API
    }
  });

  dodgeball.handleVerification(endpointResponse.data.verification, {
    onVerified: async (verification) => {
      // If an additional check was performed and the request is approved, simply pass the verification ID in to your API
      await placeOrder(order, verification.id);
    },
    onApproved: async () => {
      // If no additional check was required, update the view to show that the order was placed
      setIsOrderPlaced(true);
    },
    onDenied: async (verification) => {
      // If the action was denied, update the view to show the rejection
      setIsOrderDenied(true);
    },
    onError: async (error) => {
      // If there was an error performing the verification, display it
      setError(error);
      setIsPlacingOrder(false);
    }
  });
}
```

```js
// In your API...
@POST('/api/orders')
async (req, res){
  // In moments of risk, call a checkpoint within Dodgeball to verify the request is allowed to proceed
     var dbResponse = await dodgeball.Checkpoint(
      new DodgeballEvent(
        "WITH_MFA",
        "128.103.69.86",
        checkpointData),
      null,
      dateString,
      "test@dodgeballhq.com"
    );

    Assert.IsTrue(dbResponse.success);

    if (dodgeball.IsAllowed(dbResponse))
    {
      // This is the scenario under which we have completed 
      // But we should be in blocked state with MFA
      Assert.Fail("We should be blocked");
    } else if (dodgeball.IsDenied(dbResponse)) {
      Console.WriteLine("Pass a forbidden response to client");
    } else if (dodgeball.IsRunning(dbResponse)) {
      Console.WriteLine("Pass control back to the JS Client to render MFA");
    }
}
```
