import random

# Each entry: short_question, list of choices (len >= 2), correct answer (exact string)
QUESTION_BANK = [
    ("Capital of Kenya?", ["Nairobi","Mombasa","Kisumu","Eldoret"], "Nairobi"),
    ("Who painted the Mona Lisa?", ["Van Gogh","Leonardo da Vinci","Picasso","Rembrandt"], "Leonardo da Vinci"),
    ("5 + 7 = ?", ["11","12","13","14"], "12"),
    ("Which planet is the Red Planet?", ["Venus","Earth","Mars","Jupiter"], "Mars"),
    ("Largest ocean on Earth?", ["Atlantic","Indian","Pacific","Arctic"], "Pacific"),
    ("What language is this project written in?", ["Java","C++","Python","Go"], "Python"),
    ("Which is a web technology?", ["HTML","Linux","MySQL","SSH"], "HTML"),
    ("HTTP default port?", ["21","22","80","443"], "80"),
    ("Which gas do plants breathe in?", ["Oxygen","Carbon Dioxide","Nitrogen","Helium"], "Carbon Dioxide"),
    ("Symbol for water?", ["CO2","H2O","NaCl","O2"], "H2O"),
]

def get_questions(n):
    """Return n questions as (qid, question, choices, answer) triplets."""
    sample = random.sample(QUESTION_BANK, min(n, len(QUESTION_BANK)))
    qlist = []
    for i, (q, choices, ans) in enumerate(sample, start=1):
        shuffled = choices[:]
        random.shuffle(shuffled)
        qlist.append((i, q, shuffled, ans))
    return qlist
