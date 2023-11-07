import pymongo


def check_answer(question_id, answer, user, db):
    questions = db["questions"]
    found = questions.find_one({"id": question_id})
    toRet = False
    if found is not None:
        correct_answer = found["answers"]
        if answer.strip().rstrip().lower() == correct_answer.strip().rstrip().lower():
            toRet = True
    return toRet
