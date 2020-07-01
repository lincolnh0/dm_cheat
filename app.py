from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from collections import defaultdict, deque
import poker

class PokerState(object):
    def __init__(self):
        self.hand = []
        self.table = []

    def setHand(self, hand):
        self.hand = hand

    def setTable(self, card):
        self.table += card

    def getPermutations(self, cards_to_guess=2):
        ''' 
        Generate all possible hands based on cards provided.
        Can exclude specific cards during the process.
        '''
        probability_table = defaultdict(deque)
        if cards_to_guess == 2:
            for card_1 in range(52):
                if card_1 in (self.table + self.hand): continue
                for card_2 in range(card_1 + 1, 52):
                    if card_2 in (self.table + self.hand): continue
                    hand, score = poker.returnHandScore(self.table + [card_1, card_2])
                    probability_table[score] += [(card_1, card_2)]

        elif cards_to_guess == 1:
            for card in range(52):
                if card in (self.table + self.hand): continue
                hand, score = poker.returnHandScore(base_cards + [card])
                probability_table[score] += [card]
        return probability_table

    def getProbability(self):
        # Get all possible hands your opponents can have
        opponent_permutations = self.getPermutations(2)
        opponent_possibilities = sum([len(x) for x in opponent_permutations.values()])

        hand, score = poker.returnHandScore(self.hand + self.table)
        hand_sum = poker.returnTieBreakScore(hand, score)
        opponent_win_probability = sum([len(opponent_permutations[x]) for x in opponent_permutations if x > score])

        # Tie-break evaluation
        for same_score_hand in opponent_permutations[score]:
            tie_hand, tie_score = poker.returnHandScore(self.table + list(same_score_hand))
            tie_hand_sum = poker.returnTieBreakScore(tie_hand, tie_score)
            if tie_hand_sum > hand_sum:opponent_win_probability += 1

        opponent_win_probability /= opponent_possibilities

        probabilty_result = ''
        for i in range(1, 6):
            probabilty_result += f'{ i } opponent(s): {round(100 * (1 - opponent_win_probability) ** i, 2)}%\n'

        return probabilty_result

    

app = Flask(__name__)

clients = {}
card_prefixes = ['\u2660', '\u2665', '\u2663', '\u2666']

@app.route('/', methods=['POST'])
def index():
    """Send a dynamic reply to an incoming text message"""
    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)
    sender = request.values.get('From', None)

    # Start our TwiML response
    resp = MessagingResponse()

    if body == 'new game':
        clients[sender] = PokerState()
        resp.message('Please enter your hand separated by spaces, for example "\u2660 A \u2660 10"')

    if body[0] in card_prefixes and clients.get(sender):
        cards = body.split(' ')
        card_ids = []
        for card in cards:
            card_ids.append(poker.returnCardID(card.strip()))
        
        if len(clients[sender].hand) < 2:
            clients[sender].setHand(card_ids)
            resp.message('Please enter the flop, turn, river as they are dealt.')
        else:
            clients[sender].setTable(card_ids)
            resp.message(clients[sender].getProbability())

    


    # Determine the right reply for this message
    if body == 'hello':
        resp.message("Hi!")
    elif body == 'bye':
        resp.message("Goodbye")

    return str(resp)
    