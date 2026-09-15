import csv
from datetime import datetime, timezone, timedelta
from fsrs import Scheduler, Card, Rating
import json
import os
import pygame as py
import win32gui
import win32con
import win32api
import random
import shutil
import sqlite3
import time

CARD_INTERVAL = 5 # seconds between each card appearing for review
TIMEZONE = timezone(timedelta(hours=0))

dirname, _ = os.path.split(os.path.abspath(__file__))
THIS_DIRECTORY = f'{dirname}{os.sep}'

def get_all_vocabulary(lesson=10):
    con = sqlite3.connect(f'{THIS_DIRECTORY}vocabulary.db')
    cursor = con.cursor()
    cursor.execute('''
        SELECT
            card_id, kanji, hiragana, english, metadata
        FROM
            vocabulary
        WHERE
            lesson <= ?
        ''',
        (lesson,)
    )
    results = cursor.fetchall()
    cards = []
    if results is not None:
        for result in results:
            cards.append({
                'card_id':result[0],
                'kanji':result[1],
                'hiragana':result[2],
                'english':result[3],
                'metadata':result[4]
            })
    return cards

def init():
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 10)
    py.init()
    screen = py.display.set_mode((500, 50), py.NOFRAME)
    hwnd = py.display.get_wm_info()["window"]
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(
                           hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(255, 0, 128), 0, win32con.LWA_COLORKEY)
    return screen

def load():
    if not os.path.exists(f'{THIS_DIRECTORY}vocabulary.db'):
        shutil.copy(f'{THIS_DIRECTORY}vocabulary.db.template', f'{THIS_DIRECTORY}vocabulary.db')
    all_cards = {}
    all_vocabulary = get_all_vocabulary()
    for vocab in all_vocabulary:
        if vocab['metadata'] is None:
            vocab['metadata'] = Card(card_id=vocab['card_id'])
        else:
            vocab['metadata'] = Card.from_dict(json.loads(vocab['metadata']))
        all_cards[vocab['card_id']] = vocab
    return all_cards

def save(all_cards):
    con = sqlite3.connect(f'{THIS_DIRECTORY}vocabulary.db')
    cursor = con.cursor()
    for card_id in all_cards:
        card = all_cards[card_id]
        card['metadata'] = card['metadata'].to_json()
        cursor.execute('''
            UPDATE
                vocabulary
            SET
                metadata=?
            WHERE
                card_id=?
            ''',
            (card['metadata'], card['card_id'])
        )
    con.commit()

def get_due_card(all_cards):
    options = []
    for card_id in all_cards:
        card = all_cards[card_id]
        due_time = card['metadata'].due
        current_time = datetime.now(TIMEZONE)
        if due_time <= current_time:
            options.append(card)
    if len(options) > 0:
        return random.choice(options)

def main():
    screen = init()
    big_font = py.font.Font(f'{THIS_DIRECTORY}fonts{os.sep}Moshimoji-0Y6R.ttf', 30)
    medium_font = py.font.Font(f'{THIS_DIRECTORY}fonts{os.sep}Moshimoji-0Y6R.ttf', 24)
    logo = py.image.load(f'{THIS_DIRECTORY}assets{os.sep}icon32.png')

    scheduler = Scheduler()
    ratings = {
        'e':4,
        'm':3,
        'h':2,
        'i':1
    }
    done = False

    all_cards = load()
    card = get_due_card(all_cards)
    modes = ['minimized', 'japanese', 'english']
    mode = 1
    while not done:
        screen.fill((255,0,128)) # transparent background colour

        jp_width, _ = big_font.size(card['hiragana'])
        en_width, _ = medium_font.size(card['english'])
        width = max([jp_width, en_width]) + 50

        # bar & logo
        py.draw.rect(
            screen,
            (255, 255, 255),
            py.Rect(
                0, 0,      # top left
                width, 50  # bottom right
            )
        )
        py.draw.circle(
            screen,
            (255, 255, 255),
            (width, 25),  # positon
            25,         # radius
            0           # border thickness
        )

        # mode-specific content
        if modes[mode] == 'japanese':
            screen.blit(logo, (width - 16, 9))

            screen.blit(
                big_font.render(
                    card['hiragana'],
                    True,       # anti-alias
                    (0, 0, 0)
                ),
                (10, 10)        # position
            )
        if modes[mode] == 'english':
            screen.blit(logo, (width - 16, 9))

            screen.blit(
                medium_font.render(
                    card['english'],
                    True,       # anti-alias
                    (0, 0, 0)
                ),
                (10, 10)        # position
            )

        # update screen
        py.display.update()

        # user input
        for event in py.event.get():    
            if event.type == py.QUIT:   
                done = True                
            if event.type == py.KEYDOWN:    
                if event.key == py.K_ESCAPE:  
                    done = True
            if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
                mode += 1
                if mode >= len(modes):
                    # TODO:
                    # - get mouse position on click
                    # - use position to record difficulty
                    # - save difficulty
                    done = True


        # all_cards = load()
        # card = get_due_card(all_cards)
        # print(card['kanji'])
        # print(card['hiragana'])
        # input('Press Enter to reveal')
        # print(f'Eng: {card["english"]}')


        # rating = input('Was that [e]asy [m]edium [h]ard or [i]mpossible > ')
        # rating = ratings.get(rating, 2)
        # updated_metadata, review_log = scheduler.review_card(
        #     card=card['metadata'],
        #     rating=rating,
        #     review_datetime=datetime.now(TIMEZONE)
        # )

        # all_cards[card['card_id']]['metadata'] = updated_metadata

        # save(all_cards)
        # time.sleep(CARD_INTERVAL)

if __name__ == '__main__':
    main()
