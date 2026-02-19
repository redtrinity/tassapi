from typing import Optional


def oxford_join(joiner: str, *args, sep: Optional[str] = None, quote_args: Optional[bool] = False) -> str:
    """Create a string that uses the Oxford Comma join style.
    :param joiner: the string that is used to join the values together; for example: 'and' or 'or'
    :param args: arguments to join
    :param sep: the join character, for example ','; defaults to ',' - a space is added"""
    sep = sep.strip() if sep is not None else ","
    joiner = joiner or "and"
    new_args = [f"'{arg}'" for arg in args] if quote_args else args

    if len(args) > 1:
        first_str = f"{sep} ".join(new_args[:-1])
        and_str = f" {joiner} " if len(new_args) == 2 else f", {joiner} "
        last_str = new_args[-1]

        return f"{first_str}{and_str}{last_str}"
    else:
        return "".join(f"'{arg}'" for arg in args)
