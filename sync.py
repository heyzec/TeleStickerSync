from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetAllStickersRequest
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetID
import asyncio

import subprocess
import os
import re

import warnings
warnings.filterwarnings("ignore", message="The loop argument is deprecated since Python 3.8, and scheduled for removal in Python 3.10.")

api_id =  # your api_id here (int)
api_hash =  # your api_hash_here (str)
phone =  # your phone number here (str)
username =  # your username here (str)
client = TelegramClient(username, api_id, api_hash, sequential_updates=True)
client.start(phone)
stickers =  'kabookseeno' # your sticker packname here (str)


filenames = ['original.txt', 'target.txt']





local_path = '/home/heyzec/Documents/Stickers/kabookseeno'


async def get_stickers(pack_name):
    """Given pack name, returns a list of Sticker Documents"""
    sticker_sets = await client(GetAllStickersRequest(0))

    sticker_set = sticker_sets.sets[
        {sticker_sets.sets[i].short_name: i for i in range(len(sticker_sets.sets))}[pack_name]]

    stickers = await client(GetStickerSetRequest(
        stickerset=InputStickerSetID(
            id=sticker_set.id, access_hash=sticker_set.access_hash
        )))
    return stickers




async def calc_sticker_hashes():
    global stickers
    print("Hold on, getting stickers...")
    stickers = await get_stickers(stickers)

    tele_hashes = {}
    for doc in stickers.documents:

        emoji = doc.attributes[1].alt
        data = await client.download_file(doc)
        with subprocess.Popen(f"cat -| sha1sum", 
            shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as p:
            tele_hashes[p.communicate(data)[0].decode()[:40]] = emoji




    local_hashes = {}
    local_names = sorted(i for i in os.listdir(local_path) if i[-4:] == '.tgs')
    for i in local_names:
        with open(local_path + '/' + i, 'rb') as f:
            data = f.read()
        with subprocess.Popen(f"cat -| sha1sum", 
            shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as p:
            local_hashes[p.communicate(data)[0].decode()[:40]] = i

    return tele_hashes, local_hashes


def diff(l1, l2):
    def l2l(l): #list to lines
        return ''.join(str(i) + '\n' for i in l)

    prc = subprocess.run(f"diff <(echo '{l2l(l1)}') <(echo '{l2l(l2)}')",
            shell=True, executable='/bin/bash', capture_output=True)
    return prc.stdout.decode()

def get_changes_from_diff_output(diff_output):
    
    changes = []
    for line in diff(original, target).split('\n'):
        if len(line) != 0 and line[0] in '><':
            changes += [('+' if line[0] == '>' else '-', line[2:])]


    if ''.join(change[1] for change in changes).isdigit():
        changes = [(change[0], int(change[1])) for change in changes]

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

def name(n):
    def find_in_dict(d, value):
        for k, v in d.items():
            if v == value:
                return k
        raise KeyError(f"{v} not found in {d}")

    _ = find_in_dict(hash_dict, n)
    return local[_]

def add(attempt, to_add, neighbour=None):
    attempt += [to_add]
    
    if not neighbour is None:
        order_sticker(to_add, neighbour=neighbour)

    async def wrapper(conv):
        async def no_duff(conv, to_add):
            await conv.send_message('/addsticker')
            await conv.get_response()
            await conv.send_message('kabookseeno')
            await conv.get_response()
            await conv.send_file(f"{local_path}/{local_hashes[to_add]}")
            assert "Thanks!" in (await conv.get_response()).text
            await conv.send_message(local_hashes[to_add])
            await conv.get_response()
            if not neighbour is None:
                _ = order(to_add, neighbour=neighbour)
                await _(conv)

        return await no_duff(conv, to_add)
    return wrapper




def delete(attempt, to_del):
    index = attempt.index(to_del)
    attempt.pop(index)
    print(f"Del index: {index}")

    async def wrapper(conv):
        async def no_duff(conv, to_del):
            await conv.send_message('/packstats')
            await send_sticker(conv, to_del)
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
            await send_sticker(conv, to_del)
        return await no_duff(conv, index)
    return wrapper



def order(attempt, to_move, neighbour):
    
    index1 = attempt.index(to_move)
    attempt.pop(index1)

    index2 = attempt.index(neighbour) + 1
    attempt.insert(index2, to_move)
    print(f"Attempt: {attempt}")

    async def wrapper(conv):
        async def no_duff(conv, to_move, neighbour):
            await conv.send_message('/ordersticker')
            await conv.get_response()
            await conv.send_message('kabookseeno')
            await conv.get_response()
            # print(f"Moving {to_move}: {name(to_move)} to beside {neighbour}: {name(neighbour)}...")
            input('>>>')
            await send_sticker(conv, to_move)
            await send_sticker(conv, neighbour)
        return await no_duff(conv, index1, index2)
    return wrapper

async def send_sticker(conv, n):
    document = stickers.documents[n]
    emoji = document.attributes[1].alt
    print(f"I'm sending {emoji}")
    await conv.send_file(file=document)
    return (await conv.get_response()).text


#import random
#target = list(range(18))
#original = target.copy()
#random.shuffle(original)
#original = [1, 6, 2, 5, 3, 4]
#target = [1, 2, 3, 4, 5, 6]


tele, local = client.loop.run_until_complete(calc_sticker_hashes())
original = list(tele.keys())
target = list(local.keys())
hash_dict = {}
for i, e in enumerate(target):
    hash_dict[e] = i
target = list(range(len(target)))
for i in range(len(original)):
    try:
        original[i] = hash_dict[original[i]]
    except KeyError:
        index = len(hash_dict)
        hash_dict[index] = original[i]
        original[index] = original[i]


# print('\n'.join(f"{k} {v}" for k,v in tele.items()))
# print()
# print('\n'.join(f"{k} {v}" for k,v in local.items()))
# input()


changes = get_changes_from_diff_output(diff(original, target))
attempt = original.copy()


tasks = []
for i in range(len(changes)):
    change = changes[i]
    if change[0] != '-':
        print(f"{change[0]} {change[1]} {name(change[1])}")
    else:
        print(f"{change[0]} ?")

    if change[0] == '>':
        to_move = change[1]
        index = target.index(to_move)
        index -= 1
        neighbour = target[index]
        # If neighbour will be moved, pick new neighbour
        while index != -1 and neighbour in [change[1] for change in changes if change is not None]:
            index -= 1
            old = neighbour
            neighbour = target[index]
            # print(f"Neighbour changed from {old} to {neighbour}")

        if index != -1:
            tasks += [order(attempt, to_move, neighbour)]
        else:
            # print('Sadness and depression', input())
            neighbour = attempt[0]
            
            tasks += [order(attempt, to_move, neighbour)]
            #print(attempt)
            tasks += [order(attempt, neighbour, to_move)]


    elif change[0] == '+':
        pass
    elif change[0] == '-':
        pass

    changes[i] = None
    
print()
#print(f"attempt: {attempt}")


print(f"Only one pass required? {attempt == target}")
input("Press any key to proceed.")



async def main():
    if tasks != []:
        async with client.conversation('Stickers') as conv:

            await conv.send_message('/cancel')

            for task in tasks:
                await task(conv)
        print("Complete. Run again to sync emoticons.")
    else:
        emoji_pat =re.compile(
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


        async with client.conversation('Stickers') as conv:
            for i in range(len(local_names)):
                
                l = emoji_pat.findall(local_names[i])
                if l != [] and stickers.documents[i].attributes[1].alt != l[0]:

                    await conv.send_message('/editsticker')
                    await conv.get_response()
                    await send_sticker(conv, i)
                    await conv.send_message(local_names[i])
                    await conv.get_response()
            

            print("Nothing to change. Exiting.")

    await client.disconnect()

client.loop.create_task(main())
client.run_until_disconnected()
