import sendgrid
import os
from sendgrid.helpers.mail import *

sg = sendgrid.SendGridAPIClient(api_key='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')
data = {
  "personalizations": [
    {
      "to": [
        {
          "email": "georgedendle@walkerdendle.co.uk"
        }
      ],
      "subject": "Your Tickets are ready!"
    }
  ],
  "from": {
    "email": "sc19gbd@leeds.ac.uk"
  },
  "content": [
    {
      "type": "text/plain",
      "value": "Please find your ticket attached."
    }
  ]
}
response = sg.client.mail.send.post(request_body=data)


print(response.status_code)
print(response.body)
print(response.headers)