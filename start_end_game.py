import sys
from lxml.html import fromstring, tostring
import re
from nltk.corpus import wordnet as wn
from itertools import product
import nltk
import numpy as np
try:
    import urllib.request as urlrequest
except ImportError:
    import urllib2 as urlrequest

'''
My go at automating the Wikipedia game (https://en.wikipedia.org/wiki/Wikipedia:Wiki_Game)

Given a starting wikipedia article, just by following links try to get to an unrelated
end article

Uses wordnet to derive a similarity score between the title of the end page and the
title of each link in a Wikipedia page, then jumps to the best. Turns out the most
fiddly bit was dealing with cycles and pages with no links or in non-standard formats
Otherwise surprisingly simple and seems to work well!

RANDOM_MODE generates random start and end points. This is pretty tough and most
of the time the game ends on failure. Set the links manually to give the game a
better chance of finishing. Recommended value: False

Sarab S Sethi (http://www.imperial.ac.uk/people/s.sethi16)
s.sethi16@imperial.ac.uk
'''

START_PAGE_LINK = '/wiki/Ginza'
END_PAGE_LINK = '/wiki/Reason'
RANDOM_MODE = 0

def get_syns_from_wiki_link(link, no_nouns=False):
    '''
    Takes a wikipedia link (e.g. /wiki/Financial_engineering) and returns
    synonyms from wordnet.

    If the page has multiple words in its title, try finding synonyms for each word
    until valid results are found

    Input:
        link (str): link to wikipedia page
    Output:
        syns (list): synonyms found from wordnet for word_str
    '''

    title_str = link.split('/wiki/')[1]
    title_str = re.sub('[^A-Za-z0-9]+', ' ', title_str)
    separate_words = title_str.split(' ')

    syns = []
    for word in separate_words:
        word_syns = wn.synsets(word)

        # Filter out nouns
        if no_nouns:
            non_nouns_syns = []
            for s in word_syns:
                if '.n.' not in str(s): non_nouns_syns.append(s)
            word_syns = non_nouns_syns

        if word_syns is not None and len(word_syns) > 0:
            syns += word_syns
            # Valid synonyms found for word

    return syns

def get_rand_start_end_links():
    '''
    Get random links to start and end the game on
    Check that you can actually get synonyms for both before returning - filter
    out nouns to make it a bit easier

    N.B. In practice this is pretty impossible and almost always results in a
    failed game
    '''
    start_syns = None
    end_page_syns = None
    # We need to make sure we can actually find synonyms for the start and end
    # pages before committing to them
    while start_syns is None:
        start_response = urlrequest.urlopen('https://en.wikipedia.org/wiki/Special:Random')
        start_link = start_response.geturl().split('en.wikipedia.org')[1]
        start_syns = get_syns_from_wiki_link(start_link, no_nouns=True)
    while end_page_syns is None:
        end_response = urlrequest.urlopen('https://en.wikipedia.org/wiki/Special:Random')
        end_link = end_response.geturl().split('en.wikipedia.org')[1]
        end_page_syns = get_syns_from_wiki_link(end_link, no_nouns=True)

    return start_link, end_link

if __name__ == '__main__':
    nltk.download('wordnet')

    wiki_root = 'https://en.wikipedia.org'
    visited_pgs = []

    backwards_steps = 0
    bad_pgs = ['']

    if RANDOM_MODE:
        START_PAGE_LINK, END_PAGE_LINK = get_rand_start_end_links()
        print('Randomly generated start and end pages')

    # Get target link word and its synonyms
    end_page_syns = get_syns_from_wiki_link(END_PAGE_LINK)
    if len(end_page_syns) == 0:
        print('No synonyms found for the end link - try a different end point')
        sys.exit()

    print('Start link: {}, end link: {}'.format(START_PAGE_LINK.split('/wiki/')[1],END_PAGE_LINK.split('/wiki/')[1]))
    #print('Looking for words matching {}'.format(matched_end_word))


    next_pg = START_PAGE_LINK
    while True:
        this_pg = next_pg
        next_pg = ''
        visited_pgs.append(this_pg)
        response = urlrequest.urlopen(wiki_root + this_pg)
        html = response.read()

        # Read HTML into a lxml object
        tree = fromstring(html)
        try:
            # Empirically this div is where content is held on Wikipedia
            tree = tree.xpath("//div[@class='mw-parser-output']")[0]
        except:
            # Some wikipedia pages strangely don't have this section - treat them as bad pages and backtrack
            print('{} not a valid page, going backwards one step'.format(this_pg))
            try:
                next_pg = visited_pgs[-2]
            except:
                print('Can\'t step backwards anymore, end of game')
                sys.exit()
            bad_pgs.append(this_pg)
            continue

        # The content we're looking for is in <p></p> tags
        p_nodes = tree.xpath('p')

        best_link_score = 0
        for para in p_nodes:
            # Links are in <a href='/wiki/Blah_blah' .../> form
            link_nodes = para.xpath('a')

            for link in link_nodes:
                link_str = str(tostring(link))
                if 'href="/wiki/' in link_str:
                    # I don't really understand regex that well...
                    link_match = re.search(r'href=[\'"]?([^\'" >]+)', link_str).group(0)
                    link_bit = link_match.split('href="')[1]

                    if link_bit.lower() == END_PAGE_LINK.lower():
                        print('Found it - game over!')
                        print('Got from {} to {} in {} steps'.format(START_PAGE_LINK,END_PAGE_LINK,len(visited_pgs)))
                        sys.exit()

                    # Get synonyms for a word in the link title
                    link_syns = get_syns_from_wiki_link(link_bit)
                    if link_syns is None:
                        continue

                    # Find the similarity of this link's synonyms to our target end page synonyms
                    scores = []
                    for i,j in list(product(end_page_syns,link_syns)):
                        score = i.wup_similarity(j) # Wu-Palmer Similarity
                        # Distribution is probably bimodal at least (most words have multiple meanings)
                        # Therefore let's only look for the average of good matches to our word
                        if score is None or score < 0.3: scores.append(0)
                        else: scores.append(score)
                    mean_score = np.mean(np.asarray(scores))

                    # Update our tracker of the best link to follow
                    if mean_score > best_link_score and not (link_bit in visited_pgs):
                        next_pg = link_bit
                        best_link_score = mean_score

        # If there were no links on this page, mark it as bad. Then backtrack until
        # we find a non-bad page we have visited to find a different link
        if next_pg == '':
            print('No links found on page {}, going backwards {} steps'.format(this_pg,backwards_steps+1))
            bad_pgs.append(this_pg)
            while next_pg in bad_pgs:
                try:
                    next_pg = visited_pgs[-1 * (2 + backwards_steps)]
                except:
                    print('Can\'t step backwards anymore, end of game')
                    sys.exit()
                backwards_steps += 1
        else:
            backwards_steps = 0

        print('Next page is {}. Match score = {}'.format(next_pg.split('/wiki/')[1],round(best_link_score,2)))
