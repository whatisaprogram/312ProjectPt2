import pymongo


def check_answer(question_id, answer, user, db):
    questions = db["Posts"]
    found = questions.find_one({"post_id": question_id})
    toRet = False
    if found is not None:
        correct_answer = found["correct_answers"]
        print("this is correct: ", correct_answer.encode(), "this is actual: ", answer.encode())
        print(answer.strip().rstrip().lower(), correct_answer.strip().rstrip().lower())
        if answer.strip().rstrip().lower() == correct_answer.strip().rstrip().lower():
            print("Is correct")
            toRet = True
    print(toRet)
    return toRet
