import unittest

TIDDLER_TITLES = """a brilliant sentence to summarize the relationship between the song and the artist, in the context of commercial pop music
a description of (commercial) contemporary pop in comparison to older works of music
a very utilitarian argument to immerse in classical music instead of rock or pop
another wording for the motivation behind the dive into classical music
apropos of John Cage, Iggy and the Stooges vs. Morton Feldman
before streaming only a small proportion of all the music ever made was available
Brian Eno on how Frank Zappa (did not) influence him
eight steps beyond – gateways into classical music
however, in contrast to the grandioseness evoked in the need for music...
more hints of anti-capitalism, standardisation of the human experience, etc.
still on the topic of Cage — thoughts on the importance of art
ten Frank Zappa songs as chosen by Paul Morley
the big technological lump of music as data
the end of pop music as a cohesive, linear event
the motivation behind Sound Mind ties to the change in our relationship to music
the need for music in the modern age
writing as an exercise in finding out what our thoughts are""".splitlines()

# look for tiddlers in folder

PATH = "/home/apinto/paogarden/tiddlers/"

for tid in TIDDLER_TITLES:
    with open(PATH + tid + '.tid', "r+") as t:
        tid_content = t.readlines()
        # find the line that starts with 'tags:'
        tags_line_info = next(filter(lambda line_info: line_info[1].startswith("tags:"),
                                     list(enumerate(tid_content))))
        # add the tag
        new = (tid_content[:tags_line_info[0]] +
               ["tags: book-quote [[A Sound Mind]]\n"] +
               tid_content[tags_line_info[0] + 1:])
        if (len(tid_content) == len(new)):
            t.seek(0)
            t.write("".join(new))
            t.truncate()
        else:
            print("failed on " + tid)
            input()

class TestAddTagToBookQuotes(unittest.TestCase):
    def test_add_tag_to_book_quotes(self):
        pass
