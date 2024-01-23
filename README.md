
<h1>kobogarden: a Kobo device highlight handling tool</h1> 

Giving e-reader quotes a better future 🌳

## Why this, Alex?

Hi! I've been reading digitally for a few years now, and in the case of non-fiction, *I take a lot of notes*. And, as you might have also experienced, these notes are prone to get lost, buried, and forgotten. 

I'm also very fond of the idea of [Zettelkasten](https://zettelkasten.de/posts/overview/) — a sort of permanent note/idea storage where *everything goes*, ideally promoting growth of singular ideas and thoughts into bigger stuff. Like a sort of garden? 🌻

And so, this is a very personal solution for (maybe) a general problem. This script helps me take the highlights from my device, transform them by accessing the original surrounding context, and then creating tiddlers out of them (for [TiddlyWiki](https://tiddlywiki.com/), a platform akin to Obsidian, in the spirit of Zettelkasten).

<p align="center">

<img src="https://sbsbsb.sbs/images/kobogarden.gif" alt="a gif of the usage of the kobogarden Textual application" width="700"/>
</p>

### And is this, like, something I could use for myself?

Hmm. For this to be of any use for you, you'd need to read on a Kobo device, be a little comfortable with computers, and use TiddlyWiki. Considering the various different pieces that constitute this program,

— there is a **scraper utility** that connects to the Kobo device database;

— and then there's a **parser**, that finds a given highlight in the surrounding context (the `.epub` file);

— finally, all of it is assembled in a [Textual](https://www.textualize.io/) **interface**.

I very much doubt it can be useful out of the box, but maybe there's *something* that might help if you find yourself looking for similar stuff?

Also, there's ![this link](https://sbsbsb.sbs/kobogarden) on my personal website with more details on how all of this works.

### How could I test this?

Because of copyright (and privacy) issues, I'm not providing any of the books I've used as examples. But Jane Eyre is already on public domain, and so I included a sample of my own database, with a copy of the corresponding `.epub` file. As luck would have it, it is *the only book that renders incorrectly*; I'm sorry for that, but won't be making any changes on the code in the near future.

### Alright, Alex — and is this a finished product?

Not really, no; because, as you might have experienced, programming doesn't really have an endgame, and there are a few bugs to tackle and improvements to make. But I also want to focus on other things, and I am generally bad at closure in my life, and making this public brings it to a sort of big checkpoint that allows me breathing space to tackle on other stuff.

### I completely understand, really. It doesn't need to be 100% perfect — this is working for you and that's good enough!

Yes! Thank you for the kind words. I had a lot of fun, experimented with some cool frameworks and, maybe most important, made my life a little easier in a task that is very meaningful to me.

### That's good, Alex. But I sort of thought you were over with this Q&A roleplay in your READMEs.

Well, it's been a while since I made code public, and so I understand that confusion. But I think this is a really good format, becauat the end of the README — when there is very little information to further provide — this derails into something like self-therapy, and I get to reply to someone asking questions but that is really just me having a dialogue with someone, like, an imaginary friend 🧸
