import time
from RPLCD.i2c import CharLCD
import sys
import os
from lxml.html import fromstring, tostring
import re
try:
    import urllib.request as urlrequest
except ImportError:
    import urllib2 as urlrequest

'''
Version of philosophy_game.py to run on a raspberry pi continuously, and show text
outputs on an I2C LCD screen

---

Apparently if you click the first link in any Wikipedia article and do the same on
each subsequent page you end up on the page for philosophy 95% of the time
(https://en.wikipedia.org/wiki/Wikipedia:Getting_to_Philosophy)

Big claim, easy to test

This may have previously been true, but now there are lots more cycles, notably from
the article for Science which comes up quite often. If we purposely jump out of
loops this works quite nicely
'''

N_WON_SAVEF = 'num_games_won.txt'
def get_n_won():
    '''
    Get total number of games won (from savefile)
    '''

    if os.path.exists(N_WON_SAVEF):
        with open(N_WON_SAVEF, 'r') as f:
            n_won = f.readline()
    else:
        n_won = 0

    return int(n_won)


def increment_games_won(lcd, n_steps):
    '''
    Increment the number of games won in the save file
    '''

    # Print current page
    line_2 = '* Philosophy *'[:LCD_W].center(LCD_W)
    flashes = 0
    while flashes < 3:
        lcd.cursor_pos = (1, 0)
        lcd.write_string(''.center(LCD_W))
        time.sleep(0.5)
        lcd.cursor_pos = (1, 0)
        lcd.write_string(line_2)
        time.sleep(1)
        flashes = flashes + 1

    # Print number of steps
    lcd.cursor_pos = (2, 0)
    line_3 = '#{}'.format(n_steps).center(LCD_W)
    lcd.write_string(line_3)

    n_won = get_n_won() + 1

    with open(N_WON_SAVEF, 'w') as f:
        f.write('{}'.format(n_won))

    return n_won


LCD_W = 20
def update_screen(start_pg_name, pg_name, n_steps, n_won, scroll_ix, lcd):
    # Print start page (and scroll text if long enough)
    lcd.cursor_pos = (0, 0)
    line_1 = '{}'.format(start_pg_name)[scroll_ix:scroll_ix+LCD_W].center(LCD_W)
    lcd.write_string(line_1)
    if len(start_pg_name) > LCD_W:
        scroll_ix = scroll_ix + 1
        if scroll_ix + LCD_W > len(start_pg_name):
            scroll_ix = 0

    # Print current page
    lcd.cursor_pos = (1, 0)
    line_2 = '{}'.format(pg_name)[:LCD_W].center(LCD_W)
    lcd.write_string(line_2)

    # Print number of steps
    lcd.cursor_pos = (2, 0)
    line_3 = '#{}'.format(n_steps).center(LCD_W)
    lcd.write_string(line_3)

    # Print number of games won (with commas for thousands, millions etc.)
    lcd.cursor_pos = (3, 0)
    line_4 = f'{n_won:,} wins'[:LCD_W].center(LCD_W)
    lcd.write_string(line_4)

    print('{}\n{}\n{}\n{}'.format(line_1, line_2, line_3, line_4))

    return scroll_ix


if __name__ == "__main__":
    STATE_PLAYING = 0
    STATE_WON = 1
    STATE_IMPOSSIBLE = 2

    n_won = get_n_won()

    lcd = CharLCD('PCF8574', 0x27)

    while True:
        wiki_root = 'https://en.wikipedia.org'
        visited_pgs = []
        no_link_pgs = []

        next_pg = "/wiki/Special:Random"
        start_pg_name = ''
        game_state = STATE_PLAYING
        scroll_ix = 0

        while game_state is STATE_PLAYING:
            this_pg = next_pg
            next_pg = ''
            visited_pgs.append(this_pg)

            try:
                # Get the raw HTML for our page
                response = urlrequest.urlopen(wiki_root + this_pg)
                html = response.read()
                tree = fromstring(html)

                pg_name = tree.xpath("//h1[@id='firstHeading']")[0].text_content()
                if start_pg_name == '':
                    start_pg_name = pg_name

                scroll_ix = update_screen(start_pg_name, pg_name, len(visited_pgs)-1, n_won, scroll_ix, lcd)

                # Pull out paragraphs from the div holding the interesting content
                tree = tree.xpath("//div[@class='mw-parser-output']")[0]
                p_nodes = tree.xpath('p')

                for para in p_nodes:
                    # Find wiki links in the page
                    link_nodes = para.xpath('a')
                    for link in link_nodes:
                        link_str = str(tostring(link))
                        if 'href="/wiki/' in link_str:
                            # If we haven't previously visited this link, this is our new target page
                            link_match = re.search(r'href=[\'"]?([^\'" >]+)', link_str).group(0)
                            link_bit = link_match.split('href="')[1]

                            if link_bit not in visited_pgs and not (link_bit.startswith('/wiki/Special:')):
                                next_pg = link_bit
                                break
                    else:
                        continue         # only executed if the inner loop did NOT break
                    break                # only executed if the inner loop DID break

            except Exception:
                print('Unexpected error when parsing page {}'.format(this_pg))

            # Remember which pages leave us with no links
            if next_pg == '':
                no_link_pgs.append(this_pg)

            # Make sure we have a valid next page to go to
            ix = -2
            while next_pg in no_link_pgs or next_pg == '':
                try:
                    next_pg = visited_pgs[ix]
                    ix = ix - 1
                except IndexError:
                    print('Reached dead end - game impossible from {}'.format(start_pg_name))
                    game_state = STATE_IMPOSSIBLE
                    break

            if next_pg == '/wiki/Philosophy':
                n_won = increment_games_won(lcd, len(visited_pgs))
                print('Found it! Took {} steps from {} (n_won = {})'.format(len(visited_pgs),start_pg_name,n_won))
                game_state = STATE_WON
