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

async def main():

    async def get_stickers(pack_name):
        sticker_sets = await client(GetAllStickersRequest(0))

        sticker_set = sticker_sets.sets[
            {sticker_sets.sets[i].short_name: i for i in range(len(sticker_sets.sets))}[pack_name]]

        stickers = await client(GetStickerSetRequest(
            stickerset=InputStickerSetID(
                id=sticker_set.id, access_hash=sticker_set.access_hash
            )))
        return stickers


    stickers = await get_stickers(stickers)

    hashes = ''
    for i in stickers.documents:
        data = await client.download_file(i)
        with subprocess.Popen(f"cat -| sha1sum", 
            shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as p:
            hashes += p.communicate(data)[0].decode()[:40] + '\n'
    with open('hashes_tele.txt', 'w') as f:
        f.write(hashes)


    local_sticker_hashes = {}
    local_sticker_path = '/home/heyzec/Desktop/Stickers/kabookseeno'
    local_sticker_names = sorted(i for i in os.listdir(local_sticker_path) if i[-4:] == '.tgs')
    for i in local_sticker_names:
        with open(local_sticker_path + '/' + i, 'rb') as f:
            data = f.read()
        with subprocess.Popen(f"cat -| sha1sum", 
            shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as p:
            local_sticker_hashes[p.communicate(data)[0].decode()[:40]] = i
    with open('hashes_local.txt', 'w') as f:
        f.write(''.join(k + '\n' for k in local_sticker_hashes))



    filenames = ['hashes_tele.txt', 'hashes_local.txt']
    # filenames = ['s1.txt', 's2.txt']

    with open(filenames[0]) as f:
        s1 = f.read().strip().split('\n')
    with open(filenames[1]) as f:
        s2 = f.read().strip().split('\n')
    attempt = s1.copy()

    output = subprocess.run(f"diff {filenames[0]} {filenames[1]}",
        shell=True, capture_output=True).stdout.decode()


    changes = []
    for line in output.split('\n'):
        if len(line) == 0:
            continue
        elif line[0] in '><':
            changes += [('+' if line[0] == '>' else '-', line[2:])]

    # Find moves
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

    def add_sticker(to_add, neighbour=None):
        nonlocal attempt
        attempt += [to_add]

        
        if not neighbour is None:
            order_sticker(to_add, neighbour=neighbour)




        async def wrapper(conv):
            async def no_duff(conv, to_add):
                await conv.send_message('/addsticker')
                await conv.get_response()
                await conv.send_message('kabookseeno')
                await conv.get_response()
                await conv.send_file(f"{local_sticker_path}/{local_sticker_hashes[to_add]}")
                assert "Thanks!" in (await conv.get_response()).text
                await conv.send_message(local_sticker_hashes[to_add])
                await conv.get_response()
                if not neighbour is None:
                    _ = order_sticker(to_add, neighbour=neighbour)
                    await _(conv)

            return await no_duff(conv, to_add)
        return wrapper

    def del_sticker(to_del):
        nonlocal attempt
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


    def order_sticker(to_move, neighbour):
        nonlocal attempt
        index1 = attempt.index(to_move)
        obj = attempt.pop(index1)

        index2 = attempt.index(neighbour) + 1
        attempt.insert(index2, obj)

        async def wrapper(conv):
            async def no_duff(conv, to_move, neighbour):
                await conv.send_message('/ordersticker')
                await conv.get_response()
                await send_sticker(conv, to_move)
                await send_sticker(conv, neighbour)
            return await no_duff(conv, index1, index2)
        return wrapper

    async def send_sticker(conv, n):
        await conv.send_file(file=stickers.documents[n])
        return (await conv.get_response()).text
    

    if changes != []:
    
        changes = sorted(changes, key=lambda change: "-+>".index(change[0]))
        
        for change in changes:
            if change[0] != '-':
                print(f"{change[0]} {local_sticker_hashes[change[1]]}")
            else:
                print(f"{change[0]} ?")


        tasks = []

        for change in changes:
            if change[0] == '>':
                to_move = change[1]
                index = s2.index(to_move) - 1
                

                if index != -1:
                    neighbour = s2[index]
                
                    tasks.append(order_sticker(to_move, neighbour))
                else:
                    neighbour = attempt[0]
                    tasks.append(order_sticker(to_move, neighbour))
                    print('1')
                    tasks.append(order_sticker(neighbour, to_move))


                # assert index != -1, "Moving stickers to the 1st is unsupported."

            elif change[0] == '+':
                to_add = change[1]
                neighbour = s2[s2.index(to_add) - 1]
                #Adding last sticker may have issue. Examine neighbour
                tasks.append(add_sticker(to_add, neighbour))
            elif change[0] == '-':
                tasks.append(del_sticker(change[1]))



        print(f"Only one pass required? {attempt == s2}")
        input("Press any key to proceed.")





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
            for i in range(len(local_sticker_names)):
                
                l = emoji_pat.findall(local_sticker_names[i])
                if l != [] and stickers.documents[i].attributes[1].alt != l[0]:

                    await conv.send_message('/editsticker')
                    await conv.get_response()
                    await send_sticker(conv, i)
                    await conv.send_message(local_sticker_names[i])
                    await conv.get_response()
            

            print("Nothing to change. Exiting.")

    await client.disconnect()

client.loop.create_task(main())
client.run_until_disconnected()
