import sys
from lxml.html import fromstring, tostring
import re
try:
    import urllib.request as urlrequest
except ImportError:
    import urllib2 as urlrequest

'''
Apparently if you click the first link in any Wikipedia article and do the same on
each subsequent page you end up on the page for philosophy 95% of the time
(https://en.wikipedia.org/wiki/Wikipedia:Getting_to_Philosophy)

Big claim, easy to test

This may have previously been true, but now there are lots more cycles, notably from
the article for Science which comes up quite often. If we purposely jump out of
loops this works quite nicely
'''

if __name__ == "__main__":

    wiki_root = 'https://en.wikipedia.org'
    visited_pgs = []

    next_pg = "/wiki/Special:Random"
    start_pg = ''
    while True:
        this_pg = next_pg
        visited_pgs.append(this_pg)

        # Get the raw HTML for our page
        response = urlrequest.urlopen(wiki_root + next_pg)
        pg_name = response.geturl().split('/wiki/')[1]
        print(pg_name)
        if start_pg == '':
            start_pg = pg_name
        html = response.read()
        tree = fromstring(html)

        # Pull out paragraphs from the div holding the interesting content
        tree = tree.xpath("//div[@class='mw-parser-output']")[0]
        p_nodes = tree.xpath('p')
        for para in p_nodes:
            # Messy way of breaking out of nested loops
            if not next_pg == this_pg:
                break

            # Find wiki links in the page
            link_nodes = para.xpath('a')
            for link in link_nodes:
                link_str = str(tostring(link))
                if 'href="/wiki/' in link_str:
                    # If we haven't previously visited this link, this is our new target page
                    link_match = re.search(r'href=[\'"]?([^\'" >]+)', link_str).group(0)
                    link_bit = link_match.split('href="')[1]
                    next_pg = link_bit

                    if next_pg in visited_pgs:
                        print('Detected loop, picking the next link')
                    else:
                        break

        if '/wiki/Philosophy' in next_pg:
            print('Found it! Took {} steps from {}'.format(len(visited_pgs),start_pg))
            sys.exit()
