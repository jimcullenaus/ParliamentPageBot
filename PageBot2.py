import praw
import prawcore.exceptions as exceptions
import re
import math
import time
from datetime import datetime
import sys, os

class PageBot():
    user_agent = "User-Agent:Parliament Pager:v2.3.0 (by /u/Zagorath)"
    error_note = "No valid paging order was found in this message, sorry."

    def __init__(self):
        # Connect and log in to Reddit
        self.r = praw.Reddit('PageBot', user_agent=self.user_agent)
        #try:
        #    self.o = OAuth2Util.OAuth2Util(self.r, print_log=False)
        #    self.o.refresh(force=True)
        #except Exception as e:
        #    print e

        try:
            s = self.r.subreddit('modelgop')
            print s.top().next()
        except exceptions.Forbidden as f:
            print f
            return

        while True:
            try:
                self._run()
                time.sleep(30)
            except Exception as e:
                # If there's an error that isn't caught,
                # print the time and type of error
                print datetime.now()
                print e
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print exc_type, exc_tb.tb_lineno
                # Wait 15 minutes before trying again
                time.sleep(15*60)
                print "Starting again"
                continue

    def _run(self):
        for self.message in self.r.inbox.unread():
            if "+/u/parliamentpagebot" in self.message.body.lower():
                # pass to page
                print "\nValid page order received"
                self._page()
            elif self.message.body.startswith('**gadzooks!'):
                print "Received mod invite"
                sr = self.message.subreddit # no idea if this works
                #try:
                sr.mod.accept_invite()
                # Commenting out because unsure of how to do this in PRAW 4.
                #except exceptions.InvalidInvite:
                #    print "Mod invite accepting failed"
                #    continue
                self.r.inbox.mark_read(self.message)

            else:
                print "Mentioned but no page order"
                print self.message.body
                self.r.inbox.mark_read(self.message)

    def _page(self):
        '''
        From the current self.message, parse out the page order
        (demarked by "+/u/ParliamentPageBot")
        and page each of the users represented by the message
        '''
        page_orders = re.split("\+\/u\/parliamentpagebot", self.message.body, flags=re.IGNORECASE)
        if len(page_orders) == 2:
            self._parse_order(page_orders[1])
        elif len(page_orders) > 2:
            print "More than one page order received"
            self.reply("More than one paging order found.")
        else:
            print "No page orders received"
            # No valid paging orders were found
            self.reply(self.error_note)
        self.r.inbox.mark_read(self.message)

    def _parse_order(self, page_order):
        '''
        Takes a page order (ideally a string representation of a list
        of subreddits or users to page) and adds all valid entries
        to the to_page list.
        '''
        self.reason = ''
        self.to_page = set()
        print "Page order:", page_order
        try:
            self.reason = page_order.split('[')[1].split(']')[0]
            print "Reason:", self.reason
        except IndexError as e:
            print "No message"
        # Remove the reason and any newlines from the command.
        paging_commands = page_order.replace(self.reason, '')
        paging_commands = paging_commands.replace('\n', ' ')
        paging_commands = paging_commands.replace('\r', ' ')
        here = set(["here", "this", "self"])
        # "item" should be either a subreddit (prefixed with '/r/')
        # or a user (prefixed with '/u/')
        # or should be one of "here", "this", or "self"
        print "Paging list (page order without reason):", paging_commands
        paging_list = paging_commands.split(' ')
        # Remove punctuation from commands
        paging_list = [l.rstrip("'\",.:;?!#&*()@") for l in paging_list]
        for item in paging_list:
            print "Item to be paged:", item
            if item.startswith("/r/") or item.startswith("r/"):
              self._page_subreddit(item)
##            elif item.startswith("/u/") or item.startswith("u/"):
##                self.to_page.add(item)
            elif item in here:
              self._page_subreddit(self.message.subreddit)
        print "Paging", self.to_page
        self._do_page()

    def _page_subreddit(self, subreddit):
        '''
        Adds users from the specified subreddit's "pagelist"
        to the to_page list
        '''
        # should be unneccessary in PRAW 4 as subreddit is a Subreddit object.
        #s = self.r.subreddit(subreddit.replace('r/', '', 1).replace('/', ''))
        try:
            wiki = subreddit.wiki["pagelist"]
            contents = wiki.content_md.split("\r\n\r\n")
            for user in contents:
                self.to_page.add(user)
        # If there is no pagelist page created
        except exceptions.NotFound as e:
            error_message = "No paging list found at %s/wiki/pagelist" % subreddit
            err_msg = error_message.replace("//", "/")
            self.message.reply(err_msg)
        except exceptions.Forbidden as f:
            error_message = "Sorry, I don't have permission to read the wiki page %s/wiki/pagelist. Make sure the bot has permission to read the wiki, possibly by adding it to the modlist with wiki permission." % subreddit
            err_msg = error_message.replace("//", "/")
            print err_msg
            self.message.reply(err_msg)

    def _do_page(self):
        l = list(self.to_page)
        num_replies = int(math.ceil(len(self.to_page)/3.0))
        if num_replies < 1:
            self.reply("Sorry, but no users to page were found")
            #try:
            #    self.message.reply("Sorry, but no users to page were found")
            #except Exception as e:
            #    print e
            #    wait_ten()
            #    self.message.reply("Sorry, but no users to page were found")
        for i in range(num_replies):
            # Page each of the members
            if i*3 + 2 < len(self.to_page):
                # If there are at least 3 members left to page
                self.reply("Paging {0}, {1}, and {2} {3}".format(l[i*3], l[i*3 + 1], l[i*3 + 2], self.reason))
                #try:
                #    print "Paging {0}, {1}, and {2} {3}".format(l[i*3], l[i*3 + 1], l[i*3 + 2], self.reason)
                #    self.message.reply("Paging {0}, {1}, and {2} {3}".format(l[i*3], l[i*3 + 1], l[i*3 + 2], self.reason))
                #except Exception as e:
                #    print e
                #    wait_ten()
                #    self.message.reply("Paging {0}, {1}, and {2} {3}".format(l[i*3], l[i*3 + 1], l[i*3 + 2], self.reason))
            elif i*3 + 1 < len(self.to_page):
                # If there are two more to be paged, page them
                self.reply("Paging {0} and {1} {2}".format(l[i*3], l[i*3 + 1], self.reason))
                #try:
                #    print "Paging {0} and {1} {2}".format(l[i*3], l[i*3 + 1], self.reason)
                #    self.message.reply("Paging {0} and {1} {2}".format(l[i*3], l[i*3 + 1], self.reason))
                #except Exception as e:
                #    print e
                #    wait_ten()
                #    self.message.reply("Paging {0} and {1} {2}".format(l[i*3], l[i*3 + 1], self.reason))
            else:
                # If only one member left to be paged, page them
                self.reply("Paging {0} {1}".format(l[i*3], self.reason))
                #try:
                #    print "Paging {0} {1}".format(l[i*3], self.reason)
                #    self.message.reply("Paging {0} {1}".format(l[i*3], self.reason))
                #except Exception as e:
                #    print e
                #    wait_ten()
                #    self.message.reply("Paging {0} {1}".format(l[i*3], self.reason))

    def reply(self, message):
        success = False
        i = 0
        print message
        while not success:
            try:
                self.message.reply(message)
                success = True
            except Exception as e:
                i += 1
                if i > 5:
                    return
                print e
                wait_ten()

def wait_ten():
    '''
    Wait 10 minutes, printing each minute
    '''
    for i in range(10):
        print "Trying again in %i minutes" % (10 - i)
        time.sleep(60)
    print "Trying again now"
    time.sleep(2)

#######################################################

if __name__ == '__main__':
    PageBot()
