import sys
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

if __name__ == "__main__":
    STATE_PLAYING = 0
    STATE_WON = 1

    while True:
        wiki_root = 'https://en.wikipedia.org'
        visited_pgs = []

        next_pg = "/wiki/Special:Random"
        start_pg = ''
        game_state = STATE_PLAYING

        while game_state is STATE_PLAYING:
            this_pg = next_pg
            visited_pgs.append(this_pg)

            # Get the raw HTML for our page
            response = urlrequest.urlopen(wiki_root + next_pg)

            html = response.read()
            tree = fromstring(html)

            pg_name = tree.xpath("//h1[@id='firstHeading']")[0].text_content()
            if start_pg == '':
                start_pg = pg_name
            print('({}: {}) {}'.format(start_pg, len(visited_pgs), pg_name))

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
                        next_pg = link_bit

                        if next_pg not in visited_pgs:
                            break
                else:
                    continue         # only executed if the inner loop did NOT break
                break                # only executed if the inner loop DID break

            if '/wiki/Philosophy' in next_pg:
                print('Found it! Took {} steps from {}'.format(len(visited_pgs),start_pg))
                game_state = STATE_WON
