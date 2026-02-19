# tassapi
Python implementation of the TASS API released in 2026.

## Support
This is provided 'as is'; absolutely no support is provided.

## License
Licensed under the Apache License Version 2.0. See `LICENSE` for details.


## API documentation reference
https://api.developer.tassweb.com.au/


## Requirements
- Python 3.12.10 or newer
- requests


## About
This is a basic demo implementation of the TASS API released to schools in 2026.

### Usage
This implementation uses `requests` as the foundation layer of all activity. To start using this:
- An instance of `TassAPIServer` must be created with appropriate properties
- An instance of `APISession` is subsequently created with the instance of `TassAPIServer` as the argument
- Instances of endpoints are created with the instance of `APISession` as the argument
- Endpoint methods are called to perform the standard HTTP actions on that endpoint

The `tassapi` folder should be placed in a folder/virtualenv where your Pythin install is able to reach it.


### Response
API responses return an `APIResponse`` object; this is a wrapper for `requests.Response`. Any property/method
available in a `requests.Response` object should be accessible through `APIResponse`.

For example, if a `student` response is returned from Students.get("stud_code"):
```
>>> from pprint import pprint
>>> student = Students(session).get("stud_code")
>>> print(student)
<APIResponse [200]>
>>> pprint(dir(student))
['__class__',
 '__delattr__',
 '__dict__',
 '__dir__',
 '__doc__',
 '__eq__',
 '__format__',
 '__ge__',
 '__getattr__',
 '__getattribute__',
 '__getstate__',
 '__gt__',
 '__hash__',
 '__init__',
 '__init_subclass__',
 '__le__',
 '__lt__',
 '__module__',
 '__ne__',
 '__new__',
 '__reduce__',
 '__reduce_ex__',
 '__repr__',
 '__setattr__',
 '__sizeof__',
 '__str__',
 '__subclasshook__',
 '__weakref__',
 '_has_more',
 '_json_cache',
 '_json_cached',
 'data',
 'digest_data',
 'filename',
 'has_file_stream',
 'has_json',
 'has_more',
 'has_raw_resp',
 'json',
 'r',
 'raise_for_status',
 'resp_ok',
 'safe_statuses']
>>> pprint(student.headers)
{'Content-Length': '1055', 'Content-Type': 'application/json; charset=utf-8', 'Server': 'Microsoft-IIS/10.0', 'Strict-Transport-Security': 'max-age=2592000, max-age=31536000; includeSubdomains', 'X-Powered-By': 'ASP.NET', 'Date': 'Thu, 19 Feb 2026 23:11:32 GMT'}
```

There are several properties/methods in `APIResponse` used to extend the functionality of a `requests.Response` object:
- `data` (property): returns the JSON payload from the response (if the response has a JSON payload), during the deserialization process a custom hook is used to convert datetime strings to a wrapped instance of `datetime`, the JSON is deserialized into a wrapped instance of `dict` (`PatchableDict`) in order to add JSON patch generator functionality
- `digest_data` (property): returns a tuple of the digest type and value (where these values are present in the `headers` property) for a remote file resource, this is used to verify the downloaded or uploaded file matches the expected digest value
- `filename` (property): returns the remote resource filename (where present in `headers`), this is used as a default filename for any downloaded files
- `has_file_stream` (property): indicates the response has a filestream present, used for indicating a response has a remote resource that can be downloaded
- `has_json` (property): indicates the response has a JSON payload
- `has_more` (property): indicates additional data is available when paginating an endpoint that supports pagination
- `has_raw_resp` (property): indicates the original `requests.Response` object is attached/wrapped
- `r` (property): the original `requests.Response` object
- `raise_for_response` (method): re-implements the `requests.Response.raise_for_status` method to handle `safe_statuses` passed to the request and implements custom parsing of the response for any specific error details the server may have provided regarding the API request if it failed
- `resp_ok` (property): custom implementation of `requests.Response.ok` to handle `safe_statuses` passed to the request
- `safe_statuses` (property): a list/set/tuple of HTTP status codes that would otherwise indicate failure, but are used to represent a successful action


#### Pagination
Where an endpoint supports pagination, a `PaginatedResult` object is returned. This object has:
- `pages` (property): an iterator containing each page as an instance of `Page`
- `results` (property): yields individual page results (the JSON payload deserialized into an instance of `PatchableDict`)
- `data` (property): returns all the page results as a single object
- `refresh_cache` (method): refreshes the internal pagination cache properties used by `data` and `pages`

`Page` object has:
- `response` (property): the `APIResponse` object
- `offset` (property): the offset value for that page
- `top` (property); the maximum number of records that page could hold (derived from `$top` OData param in the request)
- `page_num` (property): the page number (i.e. `1`)

#### Example
```
from pathlib import Path
from pprint import pprint

from tassnewapi import APISession, TassAPIServer
from tassnewapi import Students

# create the instance of 'TassAPIServer' with server specific base URL and secrets
server = TassAPIServer(
    base="https://tass.example.org/api",
    key='the_client_key',
    secret='the_client_secret',
    cmpy_code='10',
    attachment_dest=Path("/tmp"),
)

# create the instance of 'APISession' that will be shared by any endpoints the server config has
# permission for
shared_session = APISession(test_server)

# create an instance of the 'Students' endpoint
s = Students(shared_session)


# get individual student
student = s.get("stud_code")

pprint(student.data)
```

`student`:
```
{'alt_id': '11223344',
 'boarder': False,
 'campus_code': None,
 'ceider': None,
 'cmpy_code': '01',
 'compare_flg': '1',
 'date_arrival': None,
 'distance_ed': False,
 'dob': ParsedDatetime(2010, 3, 30, 0, 0),
 'doe': ParsedDatetime(2022, 1, 1, 0, 0),
 'dol': None,
 'e_mail': 'student@example.org',
 'entry_lev': 7,
 'ffpos': False,
 'first_name': 'Sarah',
 'form_cls': 'A',
 'fte': 1.0,
 'gender': 'F',
 'house': 'KNGR',
 'idm_id': None,
 'mob_phone': None,
 'multipar_flg': False,
 'next_yr_ind': 'A',
 'other_name': None,
 'par_code': '654321',
 'pctut_grp': 'A',
 'preferred_name': 'Sarah',
 'preferred_surname': 'Citizen',
 'prev_school': 'Wallaby Kids',
 'privacy_flg': False,
 'religion': 'CH',
 'resident_sts': 'AUS',
 'sms_flg': False,
 'stud_code': '123456',
 'stud_govt_id': '',
 'stud_id': 'a_uid_value',
 'surname': 'Citizen',
 'update_on': ParsedDatetime(2026, 2, 11, 10, 45, 12, 557000),
 'usi': None,
 'visa_expiry': None,
 'visa_subclass': None,
 'web_access_ind': True,
 'year_grp': 11}
```
