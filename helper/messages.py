# message factory helpers to keep types consistent across server/client

def make_ready(text):
    return {"message_type": "READY", "text": text}

def make_question(qid, short_question, choices, time_allowed):
    return {
        "message_type": "QUESTION",
        "qid": qid,
        "question": short_question,
        "choices": choices,
        "time_allowed": time_allowed
    }

def make_result(correct, answer, correct_answer, score):
    return {
        "message_type": "RESULT",
        "correct": correct,
        "answer": answer,
        "correct_answer": correct_answer,
        "score": score
    }

def make_leaderboard(players):
    return {"message_type": "LEADERBOARD", "players": players}

def make_finished():
    return {"message_type": "FINISHED", "text": "Game over. Thanks for playing!"}
