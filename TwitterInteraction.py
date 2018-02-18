'''
This code needs to be called by any scheduler (e.g. cron), in a specific
interval to interact with any direct messages sent to this twitter bot
'''

import transmissionrpc
import pickle
from twython import Twython
from TwitterAuth import (
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)
from TransmissionAuth import (
    rpc_ip,
    rpc_port,
    rpc_username,
    rpc_password
)
from TwitterHandleWhitelist import (
    whitelisted_handle
)
# Create twitter object to integrate with Twitter
twitter = Twython(
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)

# Fetch direct messages from Twitter, if running first time fetch last 5
# messages else fetch from the last message id
# try open the file that contains last message id
last_read_message_id = ""
try:
    fmessage = open("messageids", "r")
    last_read_message_id = pickle.load(fmessage)
except (EOFError, IOError) as e:
    # File not available running first time, fetch 5 messages
    twitter_messages = twitter.get_direct_messages(count=5)
else:
    # old message info fetched, fetch messages after the last one
    twitter_messages = twitter.get_direct_messages(
        since_id=last_read_message_id)
finally:
    fmessage.close()
# iterate over messages and apply logic
# reset last message id if there are messages to iterate
if len(twitter_messages) > 0:
    last_read_message_id = ""

for message in twitter_messages:
    message_txt = message["text"]
    message_id = message["id"]
    message_senderhandle = str(message["sender_screen_name"])

    # first message received from twitter is the recent one,
    # store it for future use
    if last_read_message_id == "":
        last_read_message_id = message_id

    # only interact with whitelisted handles
    if message_senderhandle not in whitelisted_handle:
        twitter.send_direct_message(
            text="I don't know you, you are not a recognized user",
            screen_name=message_senderhandle)
        continue

    if message_txt.lower() == "help":
        helper_text = '''
        Below commands are available
        "torrent status" - Status of the current torrents being downloaded.
        "start" <ID>     - Start a specific torrent
        "stop"  <ID>     - Stop a specific torrent
        "add torrent" <TORRENT URL> - Add and start the torrent link provided.
        '''
        twitter.send_direct_message(
            text=helper_text, screen_name=message_senderhandle)
    elif message_txt.lower() == "torrent status":
        # Create Transmission client object to interact with torrent client
        try:
            tc = transmissionrpc.Client(
                rpc_ip, port=rpc_port, user=rpc_username,
                password=rpc_password)
            torrentlist = tc.get_torrents()
            torrentstr = 'Current status of torrents: '
            i = 0
            while i < len(torrentlist):
                torrentstr = torrentstr + '\n\nID: ' + \
                    str(torrentlist[i].id) + \
                    ' Name: ' + torrentlist[i].name + ' Status: ' + \
                    torrentlist[i].status + ' Percent Done: ' + \
                    str(torrentlist[i].percentDone * 100) + \
                    '%' + ' ETA: ' + torrentlist[i].format_eta()
                i += 1
            twitter.send_direct_message(
                text=torrentstr, screen_name=message_senderhandle)
        except Exception, e:
            twitter.send_direct_message(
                text="Exception occured: " + str(e),
                screen_name=message_senderhandle)
    elif message_txt.lower().startswith("start"):
        try:
            torrent_id = int(message_txt[6:])
            tc = transmissionrpc.Client(
                rpc_ip, port=rpc_port, user=rpc_username,
                password=rpc_password)
            tc.get_torrent(torrent_id).start()
            twitter.send_direct_message(
                text="Successfully started the specified torrent.",
                screen_name=message_senderhandle)
        except Exception, e:
            twitter.send_direct_message(
                text="Exception occured: " + str(e),
                screen_name=message_senderhandle)
    elif message_txt.lower().startswith("stop"):
        try:
            torrent_id = int(message_txt[5:])
            tc = transmissionrpc.Client(
                rpc_ip, port=rpc_port, user=rpc_username,
                password=rpc_password)
            tc.get_torrent(torrent_id).stop()
            twitter.send_direct_message(
                text="Successfully stopped the specified torrent.",
                screen_name=message_senderhandle)
        except Exception, e:
            twitter.send_direct_message(
                text="Exception occured: " + str(e),
                screen_name=message_senderhandle)
    elif message_txt.lower().startswith("add torrent"):
        try:
            torrent_url = str(message_txt[12:])
            tc = transmissionrpc.Client(
                rpc_ip, port=rpc_port, user=rpc_username,
                password=rpc_password)
            tc.add_torrent(torrent_url)
            twitter.send_direct_message(
                text="Successfully added the provided torrent.",
                screen_name=message_senderhandle)
        except Exception, e:
            twitter.send_direct_message(
                text="Exception occured: " + str(e),
                screen_name=message_senderhandle)
    else:
        helper_text = "Sorry, I am unable to recognize any command, please \
        type 'help' to see commands that I understand."
        twitter.send_direct_message(
            text=helper_text, screen_name=message_senderhandle)


# store the last message id to use next time
fmessage = open("messageids", "w")
pickle.dump(last_read_message_id, fmessage)
fmessage.close()
