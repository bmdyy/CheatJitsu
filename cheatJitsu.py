# Card-Jitsu Hack - tested on CPPS.io
# William Moody (@bmdyy)
# 12.12.2022

from scapy.all import *
from colorama import Fore, Style

class Card:
    def __init__(self, string):
        tokens = string.split("|")
        self.Number = int(tokens[0])
        self.Id = int(tokens[1])
        self.Element = tokens[2]
        self.Value = int(tokens[3])
        self.Color = tokens[4]
        self.IsSpecial = tokens[5] == "1"

    def __str__(self):
        col = None
        if self.Element == "f":
            col = Fore.RED
        elif self.Element == "w":
            col = Fore.BLUE
        elif self.Element == "s":
            col = Fore.WHITE

        return "%s[%s%d%s]%s" % (col, self.Element.upper(), self.Value, "+" if self.IsSpecial else "", Style.RESET_ALL)

class Hand:
    def __init__(self):
        self.Cards = []

    def __str__(self):
        ret = ""
        for card in self.Cards:
            ret += str(card) + " "
        return ret

    def addCard(self, card):
        self.Cards.append(card)

    def getCardIndexFromNumber(self, cardNumber):
        i = 0
        while i < len(self.Cards):
            if self.Cards[i].Number == cardNumber:
                return i
            i += 1

    def getCardByNumber(self, cardNumber):
        return self.Cards[self.getCardIndexFromNumber(cardNumber)]

    def removeCardByNumber(self, cardNumber):
        self.Cards.pop(self.getCardIndexFromNumber(cardNumber))

class Player:
    def __init__(self, string):
        tokens = string.split("|")
        self.Side = int(tokens[0])
        self.Name = tokens[1]
        self.Unk1 = tokens[2]
        self.Unk2 = tokens[3]
        self.Hand = Hand()

# Variables to store player states
p0 = None
p1 = None

# Callback for processing packets we sniff
def process_packet(packet):
    global p0, p1

    # We only want 'IPv4' packets from '146.59.154.2' with a 'Raw' layer
    if (not packet.haslayer(IP)) or (packet.getlayer(IP).src != "146.59.154.2") or (not packet.haslayer(Raw)):
        return
    
    # Convert the raw bytes into a string (it is all ASCII)
    rawData = bytes(packet.getlayer(Raw)).decode()

    # Card-Jitsu packets start with '%xt%zm', '%xt%uz' or '%xt%cjsi%' we can ignore the rest
    if not (rawData.startswith("%xt%zm") or rawData.startswith("%xt%uz") or rawData.startswith("%xt%cjsi%")):
        return

    # All events are tokens seperated by '%' characters, so we can go ahead and split it up
    tokens = rawData.split("%")[4:-1]
    
    # Handle GAME-START events
    if rawData.startswith("%xt%uz%"):
        # Initialize player variables and print out sides
        p0 = Player(tokens[0])
        p1 = Player(tokens[1])
        print("Game is starting! %s%s%s is %sP0%s and %s%s%s is %sP1%s" % \
         (Fore.YELLOW, p0.Name, Style.RESET_ALL, Fore.YELLOW, Style.RESET_ALL, Fore.MAGENTA, p1.Name, Style.RESET_ALL, Fore.MAGENTA, Style.RESET_ALL))

    # Handle GAME-OVER events
    elif rawData.startswith("%xt%cjsi%"):
        print("Game over!")
    
    # Handle DEAL events
    elif tokens[0] == "deal":
        # Update player hand
        for cardStr in tokens[2:]:
            if tokens[1] == "0":
                p0.Hand.addCard(Card(cardStr))
            else:
                p1.Hand.addCard(Card(cardStr))

        # Display player hand
        if tokens[1] == "0":
            print("%sP0%s: %s" % (Fore.YELLOW, Style.RESET_ALL, p0.Hand))
        else:
            print("%sP1%s: %s" % (Fore.MAGENTA, Style.RESET_ALL, p1.Hand))

    # Handle PICK events
    elif tokens[0] == "pick":
        cardNum = int(tokens[2])
        # Display the picked card and remove it from the player's hand
        if tokens[1] == "0":
            print("%sP0%s picked %s" % (Fore.YELLOW, Style.RESET_ALL, p0.Hand.getCardByNumber(cardNum)))
            p0.Hand.removeCardByNumber(cardNum)
        else:
            print("%sP1%s picked %s" % (Fore.MAGENTA, Style.RESET_ALL, p1.Hand.getCardByNumber(cardNum)))
            p1.Hand.removeCardByNumber(cardNum)
    
    # Handle JUDGE events
    elif tokens[0] == "judge":
        # Display result of the round
        if tokens[1] == "-1":
            print("Players tied the round")
        elif tokens[1] == "0":
            print("%sP0%s won the round" % (Fore.YELLOW, Style.RESET_ALL))
        elif tokens[1] == "1":
            print("%sP1%s won the round" % (Fore.MAGENTA, Style.RESET_ALL))

    # We can ignore POWER events
    elif tokens[0] == "power":
        pass

# Start sniffing for TCP packets
sniff(filter="tcp", prn=process_packet, store=False)