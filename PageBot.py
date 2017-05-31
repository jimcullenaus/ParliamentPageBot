import praw
from praw.exceptions import APIException
from prawcore.exceptions import RequestException, NotFound, Forbidden
from praw.models import Comment, Message

import re, math, logging, time
import sys, os, traceback

class PageBot():
	user_agent = "User-Agent:Parliament Pager:v2.3.1 (by /u/Zagorath)"

	def __init__(self):
		self.r = praw.Reddit('PageBot', user_agent=self.user_agent)
		logging.basicConfig(
			filename='pagebot.log',
			level=logging.INFO,
			format='%(asctime)s - %(levelname)s - %(message)s'
		)
		self.me = self.r.user.me().name

		while True:
			try:
				self.run()
				time.sleep(30)
			except RequestException as f:
				logging.warning("Failed to connect or other RequestException, "
						"outside of writing.")
				time.sleep(30)
			except Exception as e:
				# If there's an error that isn't otherwise caught
				# Make sure it is logged.
				logging.critical(e)
				exc_type, exc_obj, exc_tb = sys.exc_info()
				msg = str(exc_type) + str(exc_tb.tb_lineno)
				logging.critical(msg)

				# Wait 15 minutes before trying again
				time.sleep(15*60)
				logging.debug("Starting again")
				continue

	def run(self):
		"""Runs through all unread messages in the inbox
		Passes valid mentions to the pager
		Accepts mod invites
		"""
		for self.message in self.r.inbox.unread():
			# Handle PMs. Mostly dealing with mod & approved submitter status
			if isinstance(self.message, Message):
				# If the message is a mod invitation, accept it
				if self.message.body.startswith('**ggadzooks!'):
					self.accept_mod_invite()
				# If it's not a mod invite (mod acceptance, removal, approved submitter)
				else:
					logging.info("Message with id {} received titled {}".format(
						self.message.id, self.message.subject))
			# If the message is a comment
			elif isinstance(self.message, Comment):
				# If it mentions this bot and prefixes it with +
				if "+/u/{}".format(self.me).lower() in self.message.body.lower():
					self._log(logging.INFO, "Valid page order received")
					self.page()
				# If it's a comment that mentions but doesn't prefix with +
				elif "u/{}".format(self.me).lower() in self.message.body.lower():
					self._log(logging.INFO, "Bot mentioned, no page order")
				# If it's a comment reply
				else:
					stop_messages = set(['stop', 'fuck', 'unsubscribe'])
					stopped = False
					# If indicates user wants to be removed from paging list contact mods.
					for word in stop_messages:
						if self.message.body.contains(word):
							unsub = ("This bot replies to all users on the subreddit's "
							      "paging list. Contact mods of the subreddit "
							      "being paged if you wish to be removed from the list.")
							self.reply(unsub)
							stopped = True
							self._log(logging.CRITICAL, "Request to stop replied to")
					# If the comment has an unknown cause
					if not stopped:
						self._log(logging.INFO, "Unknown comment received")
			self._log(logging.DEBUG, "Message dealt with")
			self.message.mark_read()
			self._log(logging.DEBUG, "Message marked unread")

	def page(self):
		"""From the current self.message, parse out the page order
		(demarked by "+/u/ParliamentPageBot" in this bot's main incarnation)
		and page each of the users represented by the message.
		"""
		self._log(logging.DEBUG, "Comment with body '{}' of type '{}'".format(
			self.message.body, type(self.message.body)))
		page_orders = re.split(
			"\+\/u\/{}".format(self.me),
			self.message.body,
			flags=re.IGNORECASE
		)
		logging.debug("page_orders are '{}' of type '{}'".format(
			page_orders, type(page_orders)))
		# If exactly one page order is found
		if len(page_orders) == 2:
			self.parse_order(page_orders[1])
		# If too many page orders are found
		elif len(page_orders) > 2:
			self.reply("More than one paging order found. "
			          "Please only use one page order per comment. "
			          "You can, however, page multiple subreddits' pagelists "
			          "by including more than one in the command.")
			self._log(logging.INFO, "More than one page order found")
		# This code should never be reached
		else:
			self._log(
				logging.ERROR,
				"Paging syntax was used without valid order "
			)

	def parse_order(self, page_order):
		"""Takes a page order and adds all valid entries to the to_page list
		page_order is the string representing list of subreddits to page,
		and an instruction to be delivered with the command (in square brackets)
		"""
		self.reason = ''
		self.to_page = set()
		logging.debug(
			"Page order in {} is {}".format(self.message.id, page_order))
		try:
			self.reason = page_order.split('[')[1].split(']')[0]
			logging.debug("Reason for {} is {}".format(self.message.id, self.reason))
		except IndexError as e:
			self._log(logging.INFO, "No message contained in comment")
		# Remove the reason and any newlines from the command
		paging_commands = page_order.replace(self.reason, '')
		paging_commands = paging_commands.replace('\n', ' ')
		paging_commands = paging_commands.replace('\r', ' ')

		here = set(['here', 'this', 'self'])
		self._log(logging.DEBUG,
			"Paging list (page order without reason): '{}'".format(paging_commands))
		paging_list = paging_commands.split(' ')
		logging.debug("Paging list: '{}'".format(paging_list))
		# Remove punctuation from commands
		paging_list = [l.rstrip("'\",.:;?!#&*()@") for l in paging_list]
		# "item" should either be a subreddit (prefixed with /r/)
		# or should be one of "here", "this", or "self"
		for item in paging_list:
			logging.debug("Item to be paged: {} of type {}".format(item, type(item)))
			# if the item is a specified subreddit
			if item.startswith("/r/") or item.startswith("r/"):
				logging.debug("{} starts with /r/ or r/".format(item))
				sub_name = item.replace('r/', '', 1).replace('/', '')
				logging.debug("Subreddit's name is {}".format(sub_name))
				s = self.r.subreddit(sub_name)
				self.add_users(s)
			# TODO: work out specific username paging, put it here
			elif item.lower() in here:
				logging.debug("The item is in the 'here' list")
				self.add_users(self.message.subreddit)
		logging.debug("Users being paged: ".format(self.to_page))
		self.page_users()
		logging.debug("All users have been paged")


	def add_users(self, subreddit):
		"""Adds users from the specified subreddit's "pagelist"
		to the to_page list
		"""
		try:
			wiki = subreddit.wiki['pagelist']
			contents = wiki.content_md.split('\r\n\r\n')
			logging.debug(
				"Adding users to the to_page list from {}".format(subreddit))
			for user in contents:
				self.to_page.add(user)
				if not isinstance(user, basestring):
					logging.critical(
						"Attempting to add '{}' to page list, not a str".format(user))
		# If there is no pagelist page created
		except NotFound as e:
			error_message = "No paging list found at /r/{}/wiki/pagelist".format(
				subreddit.display_name)
			self._log(logging.INFO, "No wiki was found for {}".format(
				subreddit.display_name))
			self.reply(error_message)
		except Forbidden as f:
			error_message = ("Sorry, I don't have permission to read the wiki page "
			             "/r/{}/wiki/pagelist. Make sure the bot has permission to "
			             "read the wiki, either by adding it to the modlist with "
			             "wiki permission, or by making the wiki public.".format(
				subreddit.display_name))
			self._log(logging.INFO, "Was unable to view /r/{} wiki".format(
				subreddit.display_name))
			self.reply(error_message)

	def page_users(self):
		l = list(self.to_page)
		num_replies = int(math.ceil(len(self.to_page)/3.0))
		if num_replies < 1:
			self._log(logging.WARNING, "No users were found to page")
			self.reply("Sorry, but no users to page were found")
		for i in range(num_replies):
			# Page each of the members
			if i*3 + 2 < len(self.to_page):
				# If there are at least 3 members left to page, page the next three
				self.reply("Paging {0}, {1}, and {2} {3}".format(
					l[i*3], l[i*3 + 1], l[i*3 + 2], self.reason))
			elif i*3 + 1 < len(self.to_page):
				# If there are two more to be paged, page them
				self.reply("Paging {0} and {1} {2}".format(
					l[i*3], l[i*3 + 1], self.reason))
			else:
				# If only one member left to be paged, page them
				self.reply("Paging {0} {1}".format(l[i*3], self.reason))


	def reply(self, message):
		"""Replies to self.message with the given message
		If it to connect, it waits 1 minute before trying again,
		doubling the time interval until it works.
		"""
		success = False
		minutes = 1
		while not success:
			try:
				self.message.reply(message)
				success = True
			except RequestException as e:
				logging.warning("Failed to connect or other RequestException, "
						"while writing.")
				time.sleep(minutes * 60)
				minutes *= 2
				if minutes > 32:
					self._log(
						logging.ERROR,
						"Have tried for over an hour to reply to message"
					)
					return

	def accept_mod_invite(self):
		logging.info("Received mod invite to {}".format(self.message.subreddit))
		sr = self.message.subreddit
		try:
			sr.mod.accept_invite()
		except APIException as e:
			logging.warning(
				"APIException raised in attempting to accept mod invite."
			)

	def _log(self, level, message):
		message += " -- by {} with id {}".format(
			self.message.author,
			self.message.id)
		logging.log(level, message)

##############################################################

if __name__ == '__main__':
	PageBot()
