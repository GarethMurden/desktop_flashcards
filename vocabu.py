import csv
from datetime import datetime, timezone, timedelta
from fsrs import Scheduler, Card, Rating
import json
import os
import random
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

def load():
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
	scheduler = Scheduler()
	ratings = {
		'e':4,
		'm':3,
		'h':2,
		'i':1
	}
	while True:
		all_cards = load()
		card = get_due_card(all_cards)
		print(card['kanji'])
		print(card['hiragana'])
		input('Press Enter to reveal')
		print(f'Eng: {card["english"]}')
		rating = input('Was that [e]asy [m]edium [h]ard or [i]mpossible > ')
		rating = ratings.get(rating, 2)
		updated_metadata, review_log = scheduler.review_card(
			card=card['metadata'],
			rating=rating,
			review_datetime=datetime.now(TIMEZONE)
		)

		all_cards[card['card_id']]['metadata'] = updated_metadata

		save(all_cards)
		time.sleep(CARD_INTERVAL)

if __name__ == '__main__':
	main()
