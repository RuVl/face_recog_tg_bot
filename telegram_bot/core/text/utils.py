import re


def escape_markdown_v2(text: str | None) -> str | None:
	""" Escape str or return None if None is provided """

	if text is None:
		return None

	return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

# def format_phone_number(phone_number: int | str | None) -> str | None:
#     """ Format phone number. Need to be escaped for the telegram """
#
#     if phone_number is None:
#         return None
#
#     phone_number = str(phone_number)
#
#     if len(phone_number) != 11:
#         return f'bad phone number: {phone_number}'
#
#     return f'+{phone_number[0]} ({phone_number[1:4]}) {phone_number[4:7]}-{phone_number[7:9]}-{phone_number[9:]}'
