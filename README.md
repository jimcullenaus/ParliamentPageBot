# ParliamentPageBot

## How to use

1. Make sure the bot's user account is an approved submitter or a mod on the subreddit you wish to have the bot leave messages.

2. Create a list of users to be paged on the subreddit you wish to use for paging, at /r/<subreddit>/wiki/pagelist. This list must be one user per line, with blank lines in between to display as separate paragraphs. Ensure the bot has permission to read the wiki. This can be done either by inviting the bot to be a moderator with wiki permissions, or by making the wiki publicly visible.

3. Call the bot by ending a message with "+/u/ParliamentPageBot <subreddit> [<message>]". <subreddit> may be changed for the name of the subreddit *whose paging list* you want to page. <message> will be swapped out for the message appended to the page. Ensure to *keep* the square brackets in tact. Multiple <subreddit>s may be included in a single message. You can substitute the word "here" if the subreddit whose pagelist you want to page is the same as the one on which the bot is being
   summoned.

   For instance, the Purple party might maintain a list of all its users at /r/PurpleParty/wiki/pagelist, and also have a separate subreddit for its executive. This executive might have a pagelist at /r/PurpleExecutive/wiki/pagelist. If there is a post on /r/PurpleParty that someone wants to bring to the attention of *all* the Purple party members, they would end their post with "+/u/ParliamentPageBot here [to bring this to attention]". If there was a post on /r/PurpleParty
   that they wish to bring only to the attention of the executive, they could write "+/u/ParliamentPageBot /r/PurpleExecutive [to notify the execs]".

   Similarly, in /r/Parliament, a user might want to bring something to the attention of both the Red and Blue party executives, so they might write a message such as "+/u/ParliamentPageBot /r/RedExec /r/BlueExec [for bipartisan support]".

## How to run your own

You are required to install PRAW and OAuth2Util, and set up a Reddit bot account that is authorisd using OAuth. Follow the instructions on the PRAW website for how to install PRAW on your system, and on GitHub at SmBe19/praw-OAuth2Util for how to install OAuth2Util and authorise it with your bot's Reddit account.

Once the prerequisites are installed, it is as simple as running the Python script and leaving it running. Replace "/u/ParliamentPageBot" with the name of the bot account you have authorised in all commands.
