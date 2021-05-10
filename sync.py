#!/usr/bin/env python3
import asyncio

import subprocess
import os
import re

import warnings
warnings.filterwarnings("ignore",
                        message="The loop argument is deprecated since Python 3.8, and scheduled for removal in Python 3.10.")

from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetAllStickersRequest, GetStickerSetRequest
from telethon.tl.types import InputStickerSetID
from telethon.errors import FloodWaitError

api_id =  # your api_id here (int)
api_hash =  # your api_hash_here (str)
phone =  # your phone number here (str)
username =  # your username here (str)

this_file_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(this_file_path)
client = TelegramClient(username, api_id, api_hash, sequential_updates=True)
client.start(phone)
stickers =  'kabookseeno' # your sticker packname here (str)



#local_path = '/media/Shared/kabookseeno'
# local_path = '/home/heyzec/Documents/Windows Documents/Actually Documents/Stickers/kabookseeno'
local_path = os.path.abspath(this_file_path + '/../kabookseeno')


async def get_stickers(pack_name):
    """Given pack name, returns a list of Sticker Documents"""
    print(f"Hold on, getting stickers for {pack_name}...")
    sticker_sets = await client(GetAllStickersRequest(0))
    sticker_set = sticker_sets.sets[
        {sticker_sets.sets[i].short_name: i for i in range(len(sticker_sets.sets))}[pack_name]]
    stickers = await client(GetStickerSetRequest(
        stickerset=InputStickerSetID(
            id=sticker_set.id, access_hash=sticker_set.access_hash
        )))
    return stickers

async def calc_sticker_hashes(stickers):
    tele_hashes = {}
    for doc in stickers.documents:
        try:
            data = await client.download_file(doc)
        except FloodWaitError as e:
            print("telethon.errors.rpcerrorlist.FloodWaitError: Need wait n seconds:", e.seconds)
        with subprocess.Popen("cat -| sha1sum",
                              shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as p:
                              tele_hashes[p.communicate(data)[0].decode()[:40]] = doc

    local_hashes = {}
    local_names = sorted(i for i in os.listdir(local_path) if i[-4:] == '.tgs')
    for filename in local_names:
        with open(local_path + '/' + filename, 'rb') as f:
            data = f.read()
        with subprocess.Popen("cat -| sha1sum",
                              shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as p:
                              local_hashes[p.communicate(data)[0].decode()[:40]] = filename

    return tele_hashes, local_hashes


def diff(l1, l2):
    """Runs the external diff command between 2 lists."""
    def l2l(l): #list to lines
        output = ''
        for s in l:
            assert isinstance(s, str), f"Invalid value {s}, diff function only accepts lists of str"
            output += s + '\n'
        return output

    prc = subprocess.run(f"diff <(echo '{l2l(l1)}') <(echo '{l2l(l2)}')",
            shell=True, executable='/bin/bash', capture_output=True)
    return prc.stdout.decode()

def get_changes_from_diff_output(diff_output):
    changes = []
    for line in diff_output.split('\n'):
        if len(line) != 0 and line[0] in '><':
            changes += [('+' if line[0] == '>' else '-', line[2:])]

    # Convert objects added and removed to move
    added = set(e[1] for e in changes if e[0] == '+')
    removed = set(e[1] for e in changes if e[0] == '-')
    dupes = [e for e in added if e in removed][::-1]
    for e in dupes:
        for a in changes:
            if a[0] == '+' and a[1] == e:
                break
        for r in changes:
            if r[0] == '-' and r[1] == e:
                break
        changes.insert(0, ('>',  e))
        changes.remove(a)
        changes.remove(r)

    changes = sorted(changes, key=lambda change: "-+>".index(change[0]))
    return changes

async def premain():
    return await calc_sticker_hashes(await get_stickers(stickers))

tele_hashes, local_hashes = client.loop.run_until_complete(premain())

class Sticker:
    instances = {}
    def __new__(cls, shash, *args, **kwargs):
        """Ensures every instance has a unique hash. Like a singleton for each hash."""
        if shash in cls.instances:
            return cls.instances[shash]
        else:
            instance = super(Sticker, cls).__new__(cls)
            cls.instances[shash] = instance
            return instance

    def __init__(self, shash, *args):
        if not hasattr(self, 'shash'):
            self.shash = shash
            self.id_no = len(Sticker.instances) - 1




    def __repr__(self):
        return f"Sticker({str(self.id_no)})"

    def __str__(self):
        if hasattr(self, 'filename'):
            return self.filename
        return self.emoji_tele

    def add_tele_attributes(self, document):
        self.document = document
        self.emoji_tele = document.attributes[1].alt

    def add_local_attributes(self, filename):
        self.filename = filename
        emoji_re = re.compile(
                "["
                "\U0001F1E0-\U0001F1FF"  # flags (iOS)
                "\U0001F300-\U0001F5FF"  # symbols & pictographs
                "\U0001F600-\U0001F64F"  # emoticons
                "\U0001F680-\U0001F6FF"  # transport & map symbols
                "\U0001F700-\U0001F77F"  # alchemical symbols
                "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
                "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                "\U0001FA00-\U0001FA6F"  # Chess Symbols
                "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                "\U00002702-\U000027B0"  # Dingbats
                # "\U000024C2-\U0001F251"
                "☁️" 
                "]+")
 
        matches = emoji_re.findall(filename)
        if matches != []:
            self.emoji_local = matches[0]


    async def send_sticker(self, conv):
        try:
            await conv.send_file(file=self.document)
        except AttributeError:
            await conv.send_file(f"{local_path}/{self.filename}")
        await asyncio.sleep(0.1)
        return (await conv.get_response()).text


def get_arrangement(sticker_list):
    output = []
    for sticker in sticker_list:
        output.append(sticker.id_no)
    return output

#import random
#_ = list(local_hashes.items())
#random.shuffle(_)
#local_hashes = dict(_)

local = []
for shash, filename in local_hashes.items():
    s = Sticker(shash)
    s.add_local_attributes(filename)
    local.append(s)
tele = []
for shash, doc in tele_hashes.items():
    s = Sticker(shash)
    s.add_tele_attributes(doc)
    tele.append(s)

print(f"Local: {get_arrangement(local)}")
print(f"Tele: {get_arrangement(tele)}")

async def add(conv, attempt, to_add, neighbour=None):
    attempt += [to_add]

    await conv.send_message('/addsticker')
    await conv.get_response()
    await conv.send_message(stickers)
    await conv.get_response()
    assert "Thanks!" in await to_add.send_sticker(conv)
    await conv.send_message(to_add.filename)
    if 'There we go.' not in (await conv.get_response()).text:
        await conv.send_message('☁')
        assert 'There we go' in (await conv.get_response()).text, "IDK what's wrong"
    # if not neighbour is None:
        # _ = await order(conv, attempt, to_add, neighbour)
        # await _(conv)


async def delete(conv, attempt, to_del):
    print("TO DEL", to_del)
    index = attempt.index(to_del)
    attempt.pop(index)

    print(f"Del index: {index}")

    await conv.send_message('/packstats')
    await to_del.send_sticker(conv)
    await conv.send_message('This message will be deleted. Send `Yes, I am totally sure` to continue.')

    yay = False
    while True:
        await asyncio.sleep(1)
        x = client.iter_messages('Stickers')
        for _ in range(3):
            y = (await x.__anext__()).text
            if y == "Yes, I am totally sure":
                yay = True
                break
        if yay:
            break

    await conv.send_message('/delsticker')
    await conv.get_response()
    await to_del.send_sticker(conv)



async def order(conv, attempt, to_move, neighbour):
    #input(f"Move {to_move.id_no}: {to_move} to beside {neighbour.id_no}: {neighbour}?")
    index1 = attempt.index(to_move)
    attempt.pop(index1)

    index2 = attempt.index(neighbour) + 1
    attempt.insert(index2, to_move)


    # print(find_in_dict(hash_dict, to_move))
    # print(tele)

    await conv.send_message('/ordersticker')
    assert "Choose the sticker pack you're interested in." in (await conv.get_response()).text
    await conv.send_message(stickers)
    assert "Please send me the sticker you want to move." == (await conv.get_response()).text
    assert "Please send me the sticker that will be the new neighbor" in await to_move.send_sticker(conv)
    assert "I moved your sticker." in await neighbour.send_sticker(conv)



changes = get_changes_from_diff_output(diff([str(s.id_no) for s in tele],
                                            [str(s.id_no) for s in local]))
attempt = tele.copy()
instances = list(Sticker.instances.values())
print('Changes:', changes)
for i in range(len(changes)):
    change = changes[i]
    print(int(change[1]))
    changes[i] = (change[0], instances[int(change[1])])


async def main():
    if changes != []:

        async with client.conversation('Stickers') as conv:
            await conv.send_message('/cancel')
            await conv.get_response()

        for i in range(len(changes)):
            async with client.conversation('Stickers') as conv:
                change = changes[i]
                if change[0] != '-':
                    print(f"\n {change[1].id_no} {change[1].filename} [{change[0]}]")
                else:
                    print(f"{change[0]} ?")

                if change[0] == '>':
                    to_move = change[1]
                    index = local.index(to_move)
                    index -= 1
                    neighbour = local[index]
                    # If neighbour will be moved, pick new neighbour
                    while index != -1 and neighbour in [change[1] for change in changes if change is not None]:
                        index -= 1
                        old = neighbour
                        neighbour = local[index]
                        # print(f"Neighbour changed from {old} to {neighbour}")

                    if index != -1:
                        await order(conv, attempt, to_move, neighbour)
                    else:
                        # print('Sadness and depression', input())
                        neighbour = attempt[0]

                        await order(conv, attempt, to_move, neighbour)
                        #print(attempt)
                        await order(conv, attempt, neighbour, to_move)


                elif change[0] == '+':
                    to_add = change[1]
                    neighbour = local[local.index(to_add) - 1]
                    #Adding last sticker may have issue. Examine neighbour
                    await add(conv, attempt, to_add, neighbour)
                elif change[0] == '-':
                    await delete(conv, attempt, change[1])

                changes[i] = None
        print("Complete. Run again to sync emoticons.")

    else:

        no_changes = True
        async with client.conversation('Stickers') as conv:

            for sticker in local:
                if hasattr(sticker, 'emoji_local') and sticker.emoji_local != sticker.emoji_tele:
                    print(f"Changing emoji to {sticker.filename} from {sticker.emoji_tele}")
                    await conv.send_message('/editsticker')
                    await conv.get_response()
                    await sticker.send_sticker(conv)
                    await conv.send_message(sticker.filename)
                    await conv.get_response()
                    no_changes = False

        if no_changes:
            print("No changes. Exiting.")
        else:
            print("Emojis synced.")



client.loop.run_until_complete(main())
client.disconnect()
