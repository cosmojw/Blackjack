import pygame
import random
import os
import sys

def create_path(relative_path: str) -> str:
    path: str
    if hasattr(sys, '_MEIPASS'):
        path = os.path.join(sys._MEIPASS, relative_path)
    else:
        path = os.path.join(os.path.abspath("."), relative_path)
    return path

class Button:
    def __init__(self,text,font_size,color,hover_color,shadow_color,width,height,pos,elevation):
        font = pygame.font.Font(None,font_size)

        # Core Attributes
        self.pressed = False
        self.elevation = elevation
        self.dynamic_elevation = elevation
        self.original_y_pos = pos[1]
        self.color = color
        self.hover_color = hover_color
        self.action_triggered = False

        # top rectangle
        self.top_rect = pygame.Rect(pos,(width,height))
        self.top_color = self.color
        
        # text
        self.text_surf = font.render(text,False,'#F5F2D0')
        self.text_rect = self.text_surf.get_rect(center=self.top_rect.center)

        # bottom rectangle
        self.bottom_rect = pygame.Rect(pos,(width, height))
        self.bottom_color = shadow_color

        # hitbox so no glitch
        self.hitbox = pygame.Rect((pos[0], self.original_y_pos - self.dynamic_elevation),(width, height+self.dynamic_elevation))

    def draw(self,clickable=True):
        # set button to extended state
        self.top_rect.y = self.original_y_pos - self.dynamic_elevation
        # text centered to center of top rectangle
        self.text_rect.center = self.top_rect.center

        # bottom rectangle 
        self.bottom_rect.midtop = self.top_rect.midtop
        self.bottom_rect.height = self.top_rect.height + self.dynamic_elevation

        pygame.draw.rect(screen,self.bottom_color,self.bottom_rect,border_radius = 12)
        pygame.draw.rect(screen,self.top_color,self.top_rect,border_radius = 12)
        screen.blit(self.text_surf,self.text_rect)
        
        if clickable == True:
            self.check_click()

    def check_click(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.hitbox.collidepoint(mouse_pos):
            self.top_color = self.hover_color
            if pygame.mouse.get_pressed()[0]:
                self.dynamic_elevation = 0
                self.pressed = True
            else:
                if self.pressed:
                    self.dynamic_elevation = self.elevation
                    self.action_triggered = True
                    self.pressed = False
        else:
            self.dynamic_elevation = self.elevation
            self.top_color = self.color
            self.pressed = False

class Text:
    def __init__(self,text,font_size,color,pos):
        font = pygame.font.Font(None,font_size)
        self.text_surf = font.render(text,False,color)
        self.text_rect = self.text_surf.get_rect(center=pos)

    def draw(self):
        screen.blit(self.text_surf,self.text_rect)

class Card:
    def __init__(self,rank,suit,face_up=True):
        self.rank = rank
        self.suit = suit
        self.face_up = face_up
        if self.rank == 'A':
            self.rank = '1'
        if self.rank == 'J':
            self.rank = '11'
        if self.rank == 'Q':
            self.rank = '12'
        if self.rank == 'K':
            self.rank = '13'
    def draw(self,width,height,pos):
        image_folder = "Sprites"
        image_filename = str(self.suit) + ' ' + str(self.rank) + '.png'
        full_image_path = os.path.join(image_folder, image_filename)
        try:
            # Load the image and convert it to the display's pixel format for faster blitting
            loaded_image = pygame.image.load(create_path(full_image_path)).convert_alpha() # Use convert_alpha() for images with transparency
            loaded_image = pygame.transform.scale(loaded_image,(width,height))
        except pygame.error as e:
            print(f"Error loading image: {e}")
            # Handle the error, maybe exit the game or use a placeholder
            loaded_image = None
        if loaded_image:
            # Place the image at coordinates (x, y) - e.g., the top-left corner
            screen.blit(loaded_image, pos)
        else:
            global running
            running = False
        if self.face_up == False:
            image_folder = "Sprites"
            image_filename = 'Card Back 1.png'
            full_image_path = os.path.join(image_folder, image_filename)
            loaded_image = pygame.image.load(create_path(full_image_path)).convert_alpha()
            loaded_image = pygame.transform.scale(loaded_image,(width,height))
            screen.blit(loaded_image, pos)

# ~~~ GAME LOGIC ~~~
def make_shoe(): # returns an ordered deck
    ranks = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
    suits = ['Hearts','Spades','Clubs','Diamonds']
    return [(r,s) for r in ranks for s in suits] # Returns a list of cards as tuples

def get_card(game): # returns last card in shoe
    if not game["shoe"]:
        return None # returns None if shoe list is empty
    return game["shoe"].pop()

def card_value(card): # returns an integer
    r,_ = card
    if r in ('J','Q','K'):
        return 10
    if r == 'A':
        return 1
    return int(r)

def hand_value(hand): # returns tuple of high and low value
    if not hand:
        return 0, 0
    low_v = 0
    aces = 0

    for card in hand:
        if card[0] == 'A':
            aces += 1
        low_v += card_value(card)
    if aces > 0:
        high_v = low_v + 10
    else:
        high_v = low_v
    return low_v,high_v,aces

def get_valid_value(values): # returns values under 21
    valid_values = []
    for value in values:
        if value > 21:
            continue
        else:
            valid_values.append(value)
    return max(valid_values)

def start_round(game):
    game["shoe"] = []
    game["player_hand"] = []
    game["dealer_hand"] = []

    game["shoe"].clear()
    game["shoe"].extend(make_shoe())
    random.shuffle(game["shoe"])

    game["player_hand"].append(get_card(game))
    game["dealer_hand"].append(get_card(game))
    game["player_hand"].append(get_card(game))
    game["dealer_hand"].append(get_card(game))
    
    # Check for Blackjack
    if hand_value(game["player_hand"])[1] == 21 and len(game["player_hand"]) == 2:
        game["status"] = "blackjack"

def handle_hit(game):
    card = get_card(game)
    if card is None:
        game["status"] = "empty shoe"
    else:
        game["player_hand"].append(card)
        if hand_value(game["player_hand"])[0] > 21:
            game["status"] = "busted"

def handle_stand(game):

    low_v,high_v,aces = hand_value(game["dealer_hand"])
    while ((aces == False and low_v < 17) or (aces == True and high_v <= 17) or (aces == True and low_v < 17 and high_v > 21)):
        game["dealer_hand"].append(get_card(game))
        low_v,high_v,aces = hand_value(game["dealer_hand"])
    if low_v > 21:
        game["status"] = "win"
    elif get_valid_value(hand_value(game["dealer_hand"])[:2]) > get_valid_value(hand_value(game["player_hand"])[:2]):
        game["status"] = "loss"
    elif get_valid_value(hand_value(game["dealer_hand"])[:2]) < get_valid_value(hand_value(game["player_hand"])[:2]):
        game["status"] = "win"
    else:
        game["status"] = "draw"

def deal_new_hands(game):
    if len(game["shoe"]) < 8:
        game["status"] = "empty shoe"
    else:
        game["player_hand"] = []
        game["dealer_hand"] = []
        game["player_hand"].append(get_card(game))
        game["dealer_hand"].append(get_card(game))
        game["player_hand"].append(get_card(game))
        game["dealer_hand"].append(get_card(game))

def update_game(game):
    """Handle all game logic updates"""
    if game["action"] == "hit":
        handle_hit(game)
        game["state"] = "game"
        game["action"] = ""

    elif game["action"] == "stand":
        handle_stand(game)
        game["state"] = "game"

    elif game["action"] == "play again":
        deal_new_hands(game)
        game["state"] = "game"
        game["action"] = ""
    
    if game["status"] == "empty shoe":
        game["shoe"].clear()
        game["shoe"].extend(make_shoe())
        random.shuffle(game["shoe"])

    if game["status"] != game["previous_status"] and game["status"] in ("win", "blackjack"):
        game["win_count"] += 1
    game["previous_status"] = game["status"]

# ~~~ RENDERING ~~~
def draw_title():
    screen.fill("Black")
    title.draw()
    start_button.draw()
    quit_button.draw()

def draw_game(game):
    clickable = True
    if game["status"] != "playing":
        clickable = False

    screen.fill("#288214")
    hit_button.draw(clickable=clickable)
    stand_button.draw(clickable=clickable)
    dealer_text.draw()
    player_text.draw()

    win_count_text = Text(f"WINS: {game['win_count']}",screen.get_height()//10,"#E28282",(screen.get_width()//6,screen.get_height()//15))
    win_count_text.draw()

    # Draws updates
    draw_hand(game["dealer_hand"])
    draw_hand(game["player_hand"])
    
    # Game over screens
    if game["status"] != "playing":    
        draw_game_over(game)

def draw_game_over(game):
    dim_screen = pygame.Surface((screen.get_width(),screen.get_height()))
    dim_screen.fill((0,0,0))
    dim_screen.set_alpha(150)

    screen.blit(dim_screen,(0,0))
    
    y_pos = screen.get_height()*2

    if game["status"] == "blackjack":
        Text("BLACKJACK",screen.get_height()//5,'#F5F2D0',(screen.get_width()//2,y_pos+game["dynamic_y_pos"])).draw()
    if game["status"] == "busted":
        Text("BUSTED",screen.get_height()//5,'#F5F2D0',(screen.get_width()//2,y_pos+game["dynamic_y_pos"])).draw()        
    if game["status"] == "win":
        Text("YOU WIN",screen.get_height()//5,'#F5F2D0',(screen.get_width()//2,y_pos+game["dynamic_y_pos"])).draw()
    if game["status"] == "loss":
        Text("YOU LOSE",screen.get_height()//5,'#F5F2D0',(screen.get_width()//2,y_pos+game["dynamic_y_pos"])).draw()
    if game["status"] == "draw":
        Text("DRAW",screen.get_height()//5,'#F5F2D0',(screen.get_width()//2,y_pos+game["dynamic_y_pos"])).draw()
    if game["status"] == "empty shoe":
        Text("EMPTY SHOE",screen.get_height()//5,'#F5F2D0',(screen.get_width()//2,y_pos+game["dynamic_y_pos"])).draw()
    if game["status"] != "playing" and (y_pos+game["dynamic_y_pos"]) > screen.get_height()//2:
        game["dynamic_y_pos"] -= 15

    title_button.draw()
    play_again_button.draw()
    win_count_text = Text(f"WINS: {game['win_count']}",screen.get_height()//10,"#FFD256",(screen.get_width()//6,screen.get_height()//15))
    win_count_text.draw()

def draw_hand(hand):
    w = screen.get_width() * (5 / 32)
    h = screen.get_width() * (15 / 64)
    height = screen.get_height()
    spacing = w // 10
    card_count = len(hand)
    increment = (screen.get_width() - (2*(screen.get_width() // 5)))// (card_count + 1)
    start_x = (increment-(w//2)) + (screen.get_width() // 5)
    y_pos = height - h - spacing if hand == game["player_hand"] else spacing

    for i, card in enumerate(hand):
        if hand == game["player_hand"]:
            face_up = True
        elif game["action"] == "stand":
            face_up = True
        else:
            face_up = (i != 1)
        x_pos = start_x + i * increment
        Card(card[0], card[1], face_up=face_up).draw(w, h, (x_pos, y_pos))

def render(game):
    """Handle all rendering"""
    if game["state"] == "title":
        draw_title()
    elif game["state"] == "game":
        draw_game(game)

# ~~~ INPUT HANDLING ~~~
def handle_button_actions(game):
    if start_button.action_triggered:
        start_button.action_triggered = False
        game["state"] = "game"
        start_round(game)
    if quit_button.action_triggered:
        quit_button.action_triggered = False
        global running
        running = False

    if hit_button.action_triggered:
        hit_button.action_triggered = False
        game["state"] = game["action"] = "hit"
    if stand_button.action_triggered:
        stand_button.action_triggered = False
        game["state"] = game["action"] = "stand"
    
    if title_button.action_triggered:
        title_button.action_triggered = False
        game["state"] = "title"
        game["action"] = ""
        game["status"] = "playing"
        game["dynamic_y_pos"] = 0
        game["win_count"] = 0

    if play_again_button.action_triggered:
        play_again_button.action_triggered = False
        game["state"] = "game"
        game["action"] = "play again"
        game["status"] = "playing"
        game["dynamic_y_pos"] = 0

# ~~~ SETUP ~~~
pygame.init()
# Window setup
monitor_size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
screen = pygame.display.set_mode(monitor_size)
pygame.display.set_caption("Blackjack")
# Text
title = Text("BLACKJACK",screen.get_height()//4,'#F5F2D0',(screen.get_width()//2,screen.get_height()//5))
dealer_text = Text("DEALER CARDS",screen.get_height()//10,'#F5F2D0',(screen.get_width()//2,screen.get_height()//15))
player_text = Text("YOUR CARDS",screen.get_height()//10,'#F5F2D0',(screen.get_width()//2,screen.get_height()-screen.get_height()//18))
# Buttons
start_button = Button("START",screen.get_height()//7 * 8 // 10,"#DA8325F8","#92490DFF","#321904FF",screen.get_width()//4, screen.get_height()//10, (screen.get_width()//2 - screen.get_width()//4//2,screen.get_height()//2), 10)
quit_button = Button("QUIT",screen.get_height()//7 * 8 // 10,"#DA8325F8","#92490DFF","#321904FF",screen.get_width()//4, screen.get_height()//10, (screen.get_width()//2 - screen.get_width()//4//2,screen.get_height()//2+screen.get_height()//8), 10)
hit_button = Button("HIT",screen.get_height()//8 * 6 // 10,"#DA8325F8","#92490DFF","#321904FF",screen.get_width()//9, screen.get_height()//14, (screen.get_width()//10,screen.get_height() * 8 // 10), 8)
stand_button = Button("STAND",screen.get_height()//8 * 6 // 10,"#DA8325F8","#92490DFF","#321904FF",screen.get_width()//9, screen.get_height()//14, (screen.get_width()-screen.get_width()//9-screen.get_width()//10,screen.get_height() * 8 // 10), 8)
title_button = Button("TITLE SCREEN",screen.get_height()//10 * 6 // 10,"#D23624FF","#750D0DFF","#381212FF",screen.get_width()//5, screen.get_height()//14, ((screen.get_width()-screen.get_width()//5)-screen.get_width()//12,screen.get_height()//12), 8)
play_again_button = Button("PLAY AGAIN",screen.get_height()//10 * 6 // 10,"#D23624FF","#750D0DFF","#381212FF",screen.get_width()//5, screen.get_height()//14, ((screen.get_width()-screen.get_width()//5)-screen.get_width()//12,screen.get_height()//12+screen.get_height()*1.2 //14), 8)

# Tracking variables
game = {
    "state": "title",
    "status": "playing",
    "previous_status": "playing",
    "action": "",
    "shoe": [],
    "player_hand": [],
    "dealer_hand": [],
    "dynamic_y_pos": 0,
    "win_count": 0,
}
# # In game tracking variables
# win_count_text = Text(f"WINS: {game['win_count']}",screen.get_height()//10,"#E28282",(screen.get_width()//5,screen.get_height()//15))

# ~~~ MAIN LOOP ~~~
running = True
while running:       
    for event in pygame.event.get():
        # If user clicks the X button
        if event.type == pygame.QUIT:
            running = False
    handle_button_actions(game)
    update_game(game)
    render(game)

    # Update display with what was rendered above
    pygame.display.flip()

pygame.quit()