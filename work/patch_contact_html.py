from pathlib import Path

p = Path('contact.html')
s = p.read_text(encoding='utf-8')

# --- Change 2: the enquiry form's subject field -------------------------------
old_label = """\t\t\t\t\t\t\t\t\t<label for="subject">Subject Needed</label>
\t\t\t\t\t\t\t\t\t<input type="text" id="subject" name="subject" required />"""
new_label = """\t\t\t\t\t\t\t\t\t<label for="subject">Subject/s Needed</label>
\t\t\t\t\t\t\t\t\t<input type="text" id="subject" name="subject" placeholder="Example: Mathematics, English and Physical Sciences" required />"""
assert old_label in s, "subject label not found"
s = s.replace(old_label, new_label)

# --- Change 3: the optional learning preferences assessment -------------------
start = s.index("\t\t\tconst assessmentItems = [")
end = s.index("\t\t\tconst assessmentToggle =")
new_block = '''\t\t\t// Original first-person learner statements written for CTT, covering the
\t\t\t// four VARK dimensions and real study situations. Written in the spirit of
\t\t\t// the recognised learning-styles self-assessment the owner cited, without
\t\t\t// copying any of its questions.
\t\t\tconst assessmentItems = [
\t\t\t\t{
\t\t\t\t\ttext: "I understand new work best when I can see a diagram, picture or demonstration of it.",
\t\t\t\t\tstyle: "Visual"
\t\t\t\t},
\t\t\t\t{
\t\t\t\t\ttext: "I remember more when someone explains the work to me out loud.",
\t\t\t\t\tstyle: "Auditory"
\t\t\t\t},
\t\t\t\t{
\t\t\t\t\ttext: "I learn best by reading my notes or textbook carefully and then rewriting the key points.",
\t\t\t\t\tstyle: "Read/write"
\t\t\t\t},
\t\t\t\t{
\t\t\t\t\ttext: "I learn best when I can try something myself, such as building, moving or doing a practical activity.",
\t\t\t\t\tstyle: "Kinesthetic"
\t\t\t\t},
\t\t\t\t{
\t\t\t\t\ttext: "I use colour, mind maps or highlighted notes to help me remember information.",
\t\t\t\t\tstyle: "Visual"
\t\t\t\t},
\t\t\t\t{
\t\t\t\t\ttext: "I talk my way through a problem, or read my notes out loud, when I am studying.",
\t\t\t\t\tstyle: "Auditory"
\t\t\t\t},
\t\t\t\t{
\t\t\t\t\ttext: "I make lists, summaries or flashcards when I revise.",
\t\t\t\t\tstyle: "Read/write"
\t\t\t\t},
\t\t\t\t{
\t\t\t\t\ttext: "I remember things better once I have used them in a real-life example or activity.",
\t\t\t\t\tstyle: "Kinesthetic"
\t\t\t\t},
\t\t\t\t{
\t\t\t\t\ttext: "I picture the page or the diagram in my head when I try to recall what I have learnt.",
\t\t\t\t\tstyle: "Visual"
\t\t\t\t},
\t\t\t\t{
\t\t\t\t\ttext: "I learn well in discussions, where I can ask questions and hear other people's answers.",
\t\t\t\t\tstyle: "Auditory"
\t\t\t\t},
\t\t\t\t{
\t\t\t\t\ttext: "I prefer written instructions and written feedback, because I can read them again later.",
\t\t\t\t\tstyle: "Read/write"
\t\t\t\t},
\t\t\t\t{
\t\t\t\t\ttext: "I get restless and lose focus if I have to sit still for a long time.",
\t\t\t\t\tstyle: "Kinesthetic"
\t\t\t\t}
\t\t\t];

\t\t\tconst scoreOptions = [
\t\t\t\t{ label: "Not like me", value: 0 },
\t\t\t\t{ label: "Sometimes", value: 1 },
\t\t\t\t{ label: "Often", value: 2 },
\t\t\t\t{ label: "Very much like me", value: 3 }
\t\t\t];

'''
s = s[:start] + new_block + s[end:]

# Make the assessment intro note that items are written from the learner's view.
old_intro = """\t\t\t\t\t\t\t\t\t\t<p>
\t\t\t\t\t\t\t\t\t\t\tThese questions help us understand which lesson approaches may suit your child.
\t\t\t\t\t\t\t\t\t\t\tIt is not a diagnosis, and there are no right or wrong answers.
\t\t\t\t\t\t\t\t\t\t</p>"""
new_intro = """\t\t\t\t\t\t\t\t\t\t<p>
\t\t\t\t\t\t\t\t\t\t\tThese questions help us understand which lesson approaches may suit your child.
\t\t\t\t\t\t\t\t\t\t\tThey are written from your child's point of view, so please answer them as your child
\t\t\t\t\t\t\t\t\t\t\twould. It is not a diagnosis, and there are no right or wrong answers.
\t\t\t\t\t\t\t\t\t\t</p>"""
assert old_intro in s, "assessment intro not found"
s = s.replace(old_intro, new_intro)

p.write_text(s, encoding='utf-8')
print("contact.html updated")
