import unittest

from core.callback_factory import PaginatorFactory
from core.database import engine
from core.database.methods.location import get_all_locations
from core.database.methods.user import check_if_admin, get_moderator, delete_moderator, get_moderator_with_location


class TestConditionParser(unittest.IsolatedAsyncioTestCase):
	def setUp(self):
		engine.echo = True

	async def test_if_admin(self):
		# self.assertEqual(await get_moderator(2), None)
		#
		# self.assertTrue(await check_if_admin(1285638448))
		# self.assertFalse(await check_if_admin(-12345))
		#
		# locations = await get_all_locations()
		# print(locations)
		#
		# self.assertEqual(locations[0].address, "TEST location")
		#
		# print(str(PaginatorFactory(menu='menuuuu', action='change_page', page=1)))

		# await delete_moderator(2)
		# await delete_moderator(1)
		# await delete_moderator(3453)
		user = await get_moderator_with_location(1346110354)

		print(user.location.address)

		pass
