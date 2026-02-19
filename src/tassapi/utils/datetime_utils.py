import re

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import partial
from typing import Any, ClassVar, Optional, TypeVar

T = TypeVar("T")
Date = str | date
Datetime = str | datetime


fraction_re = re.compile(r"\.(\d+)")
iso_date_ptn = re.compile(r"^\d{4}-\d{2}-\d{2}$")
iso_timestamp_ptn = re.compile(
    r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])T([01]\d|2[0-3]):[0-5]\d:[0-5]\d(\.\d{0,6})?$"
)

odata_iso_date_ptn = re.compile(r"^\d{4}-\d{2}-\d{2}$")
odata_iso_timestamp_ptn = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?$")


def date_to_isoformat(value: Date | Datetime, raw: Optional[bool] = False) -> Optional[Datetime]:
    """Convert a UTC date string to an ISO date format; default returns as 'Z'.
    Note; datetime values in TASS are not timezone/offset aware; the presumption is the datetime
    value is 'local', so 'Z' or offset value must be removed.
    :param value: datetime value to convert
    :param raw: return native datetime value
    :param as_zulu: return 'Z' at end of date string instead of '+00:00'; default is True"""
    result = datetime.fromisoformat(value).isoformat(timespec="microseconds").removesuffix("Z")

    if "+" in result:
        result = result.partition("+")[0]
    elif "-" in result[10:]:  # avoid any '-' values in the date
        result = result.partition("-")[0]

    if raw:
        try:
            return datetime.strptime(result, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            raise

    return result


def is_timestamp_string(s: str) -> bool:
    """Determine if a string value is a timestamp string that can be reformatted.
    :param s: string"""
    try:
        return (
            bool(datetime.fromisoformat(s))
            and isinstance(s, str)
            and all(char in s for char in ("T", "-", ":"))
            and any(char.isdigit() for char in s)
        )
    except ValueError:
        return False


def is_iso_date(s: str) -> bool:
    """Return True/False if string matches ISO 8601 date format 'YYYY-mm-dd'.
    :param s: string"""
    return bool(iso_date_ptn.fullmatch(s))


def is_iso_timetamp(s: str) -> bool:
    """Return True/False if string matches ISO 8601 date format 'YYYY-mm-ddTHH:MM:SSZ'"""
    return bool(iso_timestamp_ptn.fullmatch(s))


def is_odata_date_str(v: str) -> bool:
    """Is ISO8601 YYYY-mm-dd or YYYY-mm-ddTHH:MM:SSZ pattern recognized as Edm.Date/Edm.DateTimeOffset values."""
    return bool(odata_iso_date_ptn.fullmatch(v) or odata_iso_timestamp_ptn.fullmatch(v))


def datetime_to_string(dt: datetime, *, fmt: Optional[str] = None, precision: Optional[int] = None) -> str:
    """Convert a datetime object to string.
    :param dt: datetime object
    :param fmt: optional date format; default is '%Y-%m-%dT%H:%M:%S.%f'
    :param precision: optional maximum level of precision for microseconds; default is 3"""
    fmt = fmt or "%Y-%m-%dT%H:%M:%S.%f"
    precision = int(precision or 3)

    if "%f" in fmt and precision:
        new_fmt = fmt.replace("%f", "")
        old_ms = dt.strftime("%f")
        new_ms = old_ms[:-precision].ljust(precision, "0")
        out = f"{dt.strftime(new_fmt)}{new_ms}"
    else:
        out = dt.strftime(fmt)

    return out


@dataclass(frozen=True)
class DateTimeFormats:
    date_fmt: ClassVar[str] = '%Y-%m-%d'
    timestamp_fmt: ClassVar[str] = "%Y-%m-%dT%H:%M:%S.%f"
    today_midnight_fmt: ClassVar[str] = "%Y-%m-%dT00:00:00.000"
    candidates: ClassVar[Sequence[str]] = (
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%fZ",
    )
    ms_precision: ClassVar[int] = 3
    field_candidates: ClassVar[Sequence[str]] = (
        "absent_date",  # date fields
        "birth_date",
        "date_arrival",
        "dob",
        "doe",
        "dol",
        "end_date",
        "expiry_date",
        "finish_date",
        "jour_date",
        "last_occ_date",
        "lst_up_date",
        "note_date",
        "photo_update_on",
        "shed_end_date",
        "shed_start_date",
        "start_date",
        "str_ent_date",
        "term_date",
        "tran_date",
        "valid_date",
        "visa_expiry",
        "corr_date",  # datetime fields
        "date_uploaded",
        "note_date",
        "par_date",
        "update_on",
        "updated_on",
        "abs_from_time",  # time fields
        "abs_to_time",
        "absent_time",
        "med_time",
    )


def _clamp_ms_precision(v: Any) -> int:
    """Clamp the microsecond precision to the range 0-6."""
    try:
        n = int(v)
    except Exception:
        return 0

    if n < 0:
        return 0

    if n > 6:
        return 6

    return n


def _rebuild_parsed_datetime(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    microsecond: int,
    tzinfo: Any,  # tz is not precisely typable without protocols
) -> "ParsedDatetime":
    """Rebuild function used by pickle. Metadata is applied afterwards by __setstate__.
    Note: 'tzinfo' technically not required; if it is provided then 'strftime' behaviour might change.
    If truly naive datetime is required, drop 'tzinfo' as a param."""
    # create normal datetime (or ParsedDatetime base) then wrap via __new__
    base = datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)

    # metadata applied via pickle "state" afterwards, so defaults are fine here
    return ParsedDatetime(base, fmt=None, ms_precision=0, parse_method=None, had_z=False)


class ParsedDatetime(datetime):
    """Subclasses 'datetime' to extend functionality (stores datetime format string tempalte for string conversion)
    when round-tripping from string to datetime to string.

    Attributes:
        - self.fmt: the strptime compatible format string that matched the input
        - self.ms_precision: number of fractional second digits in the original input
        - self.parse_method: how parsing was performed, for example 'strptime', 'generated_strptime', 'manual', etc
        - self.had_z: indicates the original datetime value had 'Z' suffix
    :param base: datetime
    :param fmt: optional format string, such as '%Y-%m-%d'; this is used when round-tripping to string representation
    :param ms_precision: optional level of microsecond precision, mininum of 0, maximum of 6
    :param parse_method: optional indicator of how the datetime was parsed, such as 'derived', 'manual', 'strftime'
    :param had_z: bool; indicates the original string value had a 'Z' suffix indicating UTC/Zulu time"""

    fmt: Optional[str]
    ms_precision: int
    parse_method: Optional[str]
    had_z: bool

    def __new__(
        cls,
        base: datetime,
        *,
        fmt: Optional[str],
        ms_precision: int,
        parse_method: Optional[str] = None,
        had_z: bool = False,
    ) -> "ParsedDatetime":
        obj = datetime.__new__(
            cls,
            base.year,
            base.month,
            base.day,
            base.hour,
            base.minute,
            base.second,
            base.microsecond,
            tzinfo=base.tzinfo,
        )

        obj.fmt = fmt
        obj.ms_precision = _clamp_ms_precision(ms_precision)
        obj.parse_method = parse_method
        obj.had_z = bool(had_z)

        return obj

    def _as_datetime(self) -> datetime:
        """Return plain stdlib datetime with the same timestamp fields as self. Used internally for various dunder
        methods."""
        return datetime(
            self.year, self.month, self.day, self.hour, self.minute, self.second, self.microsecond, tzinfo=self.tzinfo
        )

    def _wrap(self, base: datetime, *, method: Optional[str]) -> "ParsedDatetime":
        """Wrap a datetime result back into ParsedDatetime, carry metadata forward.
        Keep fmt/ms_precision (still useful for formatting), but adjust parse_method to reflect
        the value is no longer the original parsed."""
        return type(self)(base, fmt=self.fmt, ms_precision=self.ms_precision, parse_method=method, had_z=self.had_z)

    def _derived_method(self) -> str:
        """Decide the parse_method when arithmetic changes the timestamp."""
        return "derived"

    def __add__(self, other: object):
        if not isinstance(other, timedelta):
            return NotImplemented

        base = self._as_datetime() + other
        return self._wrap(base, method=self._derived_method())

    def __radd__(self, other: object):
        # support timedelta + ParsedDatetime
        if not isinstance(other, timedelta):
            return NotImplemented

        base = other + self._as_datetime()
        return self._wrap(base, method=self._derived_method())

    def __sub__(self, other: object):
        if not isinstance(other, (datetime, timedelta)):
            return NotImplemented

        # keep standard behaviour, datetime - datetime > timedelta
        if isinstance(other, datetime):
            return datetime.__sub__(self, other)

        base = self._as_datetime() - other
        return self._wrap(base, method=self._derived_method())

    def __reduce_ex__(self, protocol: int):
        """Tell pickle how to rebuild this object, including extra metadata."""
        ctor_args = (
            self.year,
            self.month,
            self.day,
            self.hour,
            self.minute,
            self.second,
            self.microsecond,
            self.tzinfo,
        )

        # "state" is applied after construction; __setstate__ handles it if defined,
        # otherwise pickle sets attributes from the dict.
        state = {
            "fmt": getattr(self, "fmt", None),
            "ms_precision": getattr(self, "ms_precision", 0),
            "parse_method": getattr(self, "parse_method", None),
            "had_z": getattr(self, "had_z", False),
        }

        return (_rebuild_parsed_datetime, ctor_args, state)

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Apply our extra attributes during unpickling."""
        self.fmt = state.get("fmt")
        self.ms_precision = _clamp_ms_precision(state.get("ms_precision", 0))
        self.parse_method = state.get("parse_method")
        self.had_z = bool(state.get("had_z", False))

    def __str__(self) -> str:
        """String representation.
        If this datetime was parsed with an exact format-string, attempt to use that format. Fall back to native
        datetime string representation."""
        if self.fmt:
            try:
                s = self.strfprecisetime(self.fmt.removesuffix("Z"), ms_precision=self.ms_precision)
                return f"{s}{'Z' if self.had_z else ''}"
            except Exception:
                pass

        return super().__str__()

    def replace(self, **kwargs) -> "ParsedDatetime":
        """Keep 'replace' mutator but wrap back to ParsedDatetime."""
        base = self._as_datetime().replace(**kwargs)
        return self._wrap(base, method=self._derived_method())

    def astimezone(self, tz=None) -> "ParsedDatetime":
        """Keep 'astimezone' mutator but wrap back to ParsedDatetime."""
        base = self._as_datetime().astimezone(tz)
        # timezone conversion changes representation, but not instance; still derived
        return self._wrap(base, method=self._derived_method())

    def strfprecisetime(self, fmt: str, *, ms_precision: Optional[int] = None) -> str:
        """Like 'strftime' but trim microsecond precision if 'ms_precision' specified.
        :param fmt: datetime format string; for example '%Y-%m-%dT%H:%M:%S.%fZ'"""
        if "%f" not in fmt:
            return super().strftime(fmt)

        sentinel = "{__frac__}"
        ms_precision = _clamp_ms_precision(int(ms_precision if ms_precision is not None else 6))
        out = super().strftime(fmt.replace("%f", sentinel))
        frac = f"{self.microsecond:06d}"[:ms_precision]

        return out.replace(sentinel, frac)


def infer_ms_precision(s: str) -> int:
    """Attempt to infer the precision of any microseconds in a date string.
    :param s: string"""
    m = fraction_re.search(s)

    return _clamp_ms_precision(len(m.group(1)) if m else 0)


def normalize_for_strptime(s: str) -> tuple[str, bool]:
    """Normalize input for stdlib .striptime. Strips 'Z' from string value and just returns a naive datetime string."""
    had_z = s.endswith(("Z", "z"))

    if had_z:
        s = s[:-1]

    return (s, had_z)


def datetime_from_string(
    dt: str,
    *,
    formats: Sequence[str],
    fmt: Optional[str] = None,
    ms_precision: Optional[int] = None,
) -> ParsedDatetime:
    """Attempt to convert a string value to a datetime object. Uses either a nominated format string or heuristics
    to determine the correct datetime format.
    :param dt: date string
    :param formats: sequence of formats to use when testing for date format
    :param fmt: override format by providing a datetime format string template
    :param ms_precision: provide an exact microsecond precision level, otherwise level is inferred from string"""
    if not isinstance(dt, str):
        raise TypeError(f"'dt' must be {str.__name__}; got {type(dt).__name__}")

    norm, had_z = normalize_for_strptime(dt)
    ms_precision = _clamp_ms_precision(ms_precision if ms_precision is not None else infer_ms_precision(norm))

    def finalize(parsed: datetime, used_fmt: Optional[str], method: str) -> ParsedDatetime:
        # remember 'Z' purely as decoration for round-tripping
        return ParsedDatetime(parsed, fmt=used_fmt, ms_precision=ms_precision, parse_method=method, had_z=had_z)

    if fmt:
        parsed = datetime.strptime(norm, fmt.removesuffix("Z"))
        return finalize(parsed, fmt, "manual")

    last_err: Optional[Exception] = None
    attempted_formats: list[str] = []

    for fmt in formats:
        try:
            parsed = datetime.strptime(norm, fmt.removesuffix("Z"))
            return finalize(parsed, fmt, "strptime")
        except ValueError as e:
            if fmt not in attempted_formats:
                attempted_formats.append(fmt)
            last_err = e

    # last ditch pattern match
    if iso_timestamp_ptn.match(dt):
        return finalize(parsed, "%Y-%m-%dT%H:%M:%S.%f", "regex")

    formats_str = ", ".join(f"'{fmt}'" for fmt in attempted_formats)
    err_msg = f"Could not parse datetime {dt!r} with either regex pattern match or datetime formats"
    raise ValueError(f"{err_msg}: {formats_str}") from last_err


def parse_datetime_from_json_value(
    obj: Any,
    *,
    formats: Sequence[str],
    fmt: Optional[str] = None,
    ms_precision: Optional[int] = None,
) -> Any:
    """Attempt to parse a datetime object from a JSON string using format heuristics. Returns either the original
    value if the value is not a string object or cannot be converted to a 'ParsedDatetime' object, otherwise returns
    a 'ParsedDatetime' object if the value can be converted.
    :param obj: obj to parse
    :param formats: sequence of formats to use when testing for date format
    :param fmt: if the date format is known, provide it; for example: '%Y-%m-%dT%H:%M:%S.%f', otherwise best effort
                is made to work out the correct format type
    :param ms_precision: if the datetime has microseconds, provide a level of precision that will be retained; minimum
                         is '0', maximum is '6'; default is '6'"""
    fn = partial(parse_datetime_from_json_value, formats=formats, fmt=fmt, ms_precision=ms_precision)

    if isinstance(obj, str):
        try:
            return datetime_from_string(obj, formats=formats, fmt=fmt, ms_precision=ms_precision)
        except (ValueError, TypeError):
            return obj

    if isinstance(obj, list):
        return [fn(v) for v in obj]

    if isinstance(obj, dict):
        return {k: fn(v) for k, v in obj.items()}

    return obj


def datetime_obj_hook(
    obj: dict[str, Any],
    formats: Optional[Sequence[str]] = None,
    fmt: Optional[str] = None,
    ms_precision: Optional[int] = None,
    field_candidates: Optional[Sequence[str]] = None,
) -> dict[str, Any]:
    """Object hook callable for parsing JSON object during 'json.loads' operations to parse datetime like strings
    into native datetime objects (other types are left alone). Emits a dictionary result. This should only be called
    where 'obj' is guaranteed to be a dictionary object with string keys and any value type.
    Note: top level strings in JSON objects such as '["2025-12-31T23:59:59.123454Z"]' are not parsed by object hooks
          used in 'json.loads'
    :param obj: object to parse
    :param formats: sequence of formats to use when testing for date format
    :param fmt: if the date format is known, provide it; for example: '%Y-%m-%dT%H:%M:%S.%f', otherwise best effort
                is made to work out the correct format type
    :param ms_precision: if the datetime has microseconds, provide a level of precision that will be retained; minimum
                         is '0', maximum is '6'; default is '6'
    :param field_candidates: optional sequence of fieldnames that are candidates for converting string value to
                             'ParsedDatetime' object"""
    # raising inside a hook will lead to nasty failure modes, so don't operate on the object, return the unmodified obj
    if not isinstance(obj, dict):
        return obj

    formats = formats if formats is not None else DateTimeFormats.candidates
    ms_precision = ms_precision if ms_precision is not None else DateTimeFormats.ms_precision
    field_candidates = frozenset(
        field_candidates if field_candidates is not None else DateTimeFormats.field_candidates
    )

    for k, v in obj.items():
        if k.casefold() in field_candidates:
            obj[k] = parse_datetime_from_json_value(v, formats=formats, fmt=fmt, ms_precision=ms_precision)

    return obj


def timestamp_now_as_str(fmt: Optional[str] = None) -> str:
    """Generate a timestamp as a string using 'datetime.now()'. Microseconds precision is capped to 3.
    :param fmt: optional datetime format string; defaults to '%Y-%m-%sT%H:%M:%S.%f' if not provided."""
    fmt = DateTimeFormats.timestamp_fmt if fmt is None else fmt
    return str(ParsedDatetime(datetime.now(), fmt=fmt, ms_precision=3))


def today_midnight_ts() -> str:
    """Generates a timestamp string that returns 'YYYY-mm-ddT00:00:00.000' (midnight)."""
    return timestamp_now_as_str(fmt=DateTimeFormats.today_midnight_fmt)


def today_as_str() -> str:
    return datetime.now().strftime(DateTimeFormats.date_fmt)
