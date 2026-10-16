from pathlib import Path

p = Path('index.html')
raw = p.read_bytes().decode('utf-8')
crlf = '\r\n' in raw
s = raw.replace('\r\n', '\n') if crlf else raw


def fix(text):
    return text.replace('\n', '\r\n') if crlf else text

# --- Change 1: warmer, more confident, more benefit-led hero copy -------------
old_hero = '''\t\t\t\t<div class="content">
\t\t\t\t\t<h1>Tutoring that <span class="ctt-accent">comes to you</span></h1>

\t\t\t\t\t<p class="major">
\t\t\t\t\t\tWe believe the right tutor can change more than just a mark. Every child learns differently,
\t\t\t\t\t\tso we simplify difficult concepts, teach in a way they understand, build confidence, and create
\t\t\t\t\t\tthose \u201cOh, I finally get it!\u201d moments.
\t\t\t\t\t</p>

\t\t\t\t\t<ul class="actions stacked">
\t\t\t\t\t\t<li><a href="tutors.html" class="button big wide primary">Meet the Tutors</a></li>
\t\t\t\t\t\t<li><a href="contact.html" class="button big wide secondary">Book a Tutor</a></li>
\t\t\t\t\t</ul>
\t\t\t\t</div>'''
new_hero = '''\t\t\t\t<div class="content">
\t\t\t\t\t<p class="ctt-hero-eyebrow">Personal, one-to-one tutoring</p>

\t\t\t\t\t<h1>Every child can thrive <span class="ctt-accent">with the right support</span></h1>

\t\t\t\t\t<p class="major">
\t\t\t\t\t\tWarm, personal tutoring that fits the way your child learns \u2014 at home, in your
\t\t\t\t\t\tarea, or online. We find the tutor who suits them, explain things in a way that
\t\t\t\t\t\tfinally makes sense, and build the confidence that lasts long after the lesson ends.
\t\t\t\t\t</p>

\t\t\t\t\t<ul class="actions stacked">
\t\t\t\t\t\t<li><a href="tutors.html" class="button big wide primary">Meet the Tutors</a></li>
\t\t\t\t\t\t<li><a href="contact.html" class="button big wide secondary">Book a Tutor</a></li>
\t\t\t\t\t</ul>

\t\t\t\t\t<ul class="ctt-hero-points">
\t\t\t\t\t\t<li>
\t\t\t\t\t\t\t<span class="ctt-icon" aria-hidden="true">\u25c9</span>
\t\t\t\t\t\t\t<span>Personalised lessons, matched to your child</span>
\t\t\t\t\t\t</li>
\t\t\t\t\t\t<li>
\t\t\t\t\t\t\t<span class="ctt-icon" aria-hidden="true">\u270e</span>
\t\t\t\t\t\t\t<span>Tutors across three provinces, and online</span>
\t\t\t\t\t\t</li>
\t\t\t\t\t\t<li>
\t\t\t\t\t\t\t<span class="ctt-icon" aria-hidden="true">\u2605</span>
\t\t\t\t\t\t\t<span>20% off your first lesson</span>
\t\t\t\t\t\t</li>
\t\t\t\t\t</ul>
\t\t\t\t</div>'''
assert old_hero in s, "hero block not found"
s = s.replace(old_hero, new_hero)

# --- Change 5/9: reorder sections and refresh the Meet our tutors intro -------
start_marker = '\t\t\t<section class="ctt-section ctt-start-section">'
learning_marker = '\t\t\t<section class="ctt-section">\n\t\t\t\t<div class="ctt-inner">\n\t\t\t\t\t<div class="ctt-learning-box">'
chloe_marker = '\t\t\t<section class="spotlight style1 orient-right'
tutors_marker = '\t\t\t<section class="ctt-section ctt-section-light">'
quote_marker = '\t\t\t<section class="ctt-quote">'

i_start = s.index(start_marker)
i_learning = s.index(learning_marker)
i_chloe = s.index(chloe_marker)
i_tutors = s.index(tutors_marker)
i_quote = s.index(quote_marker)

start_block = s[i_start:i_learning]
learning_block = s[i_learning:i_chloe]
chloe_block = s[i_chloe:i_tutors]
tutors_block = s[i_tutors:i_quote]

old_intro = "\t\t\t\t\t\t<p>Meet a few members of our growing tutoring team. Visit the tutor page to view every profile.</p>"
new_intro = "\t\t\t\t\t\t<p>Meet some of the people behind CTT. Our tutors bring different strengths, qualifications and teaching styles, so we can find the right fit for every learner.</p>"
assert old_intro in tutors_block, "homepage tutors intro not found"
tutors_block = tutors_block.replace(old_intro, new_intro)

# hero -> every child learns differently -> meet our tutors -> getting started -> how CTT started
reordered = learning_block + tutors_block + start_block + chloe_block
s = s[:i_start] + reordered + s[i_quote:]

p.write_text(fix(s), encoding='utf-8')
print("index.html updated")
