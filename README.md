# wikipedia_fun
Some fun automated versions of classic wikipedia games

![Example of a successful game](https://raw.githubusercontent.com/sarabsethi/wikipedia_fun/master/wiki_game_success.PNG)

I'm using Python 3.6. Dependencies `lxml`,`nltk` - but I think these come with Anaconda anyway 

If you use Python 2.X you'll have to change to using urllib2, but the rest may just work.

Sarab S Sethi (http://www.imperial.ac.uk/people/s.sethi16)

s.sethi16@imperial.ac.uk

## The Wikipedia Game

`start_end_game.py`

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

STRICT_MODE defines whether you have to land on exactly the correct end page or
whether something "close enough" is fine. Recommended value: True

Just a bit of fun - but would love some input from people who know more about word matching
to make it cleverer / faster. Major limitation is matching is done on single words
there's no concept of phrases or titles made up of multiple words

Let me know how you get on - the algorithm was able to get from "Financial engineering" to "Reality" in an impressive 7 steps

## All routes end in Philosophy

`philosophy_game.py`

Apparently if you click the first link in any Wikipedia article and do the same on
each subsequent page you end up on the page for philosophy 95% of the time
(https://en.wikipedia.org/wiki/Wikipedia:Getting_to_Philosophy)

Big claim, easy to test

This may have previously been true, but now there are lots more cycles, notably from
the article for Science which comes up quite often. If we purposely jump out of
loops this works quite nicely
