import pymongo


def increment_question_id(a_db_instance):
    question_ids = a_db_instance["question_ids"]
    found = question_ids.find_one()
    if found is None:
        question_ids.insert_one({"id": 1})
        return 1
    else:
        current_id = found["id"]
        newvalues = {"$set": {"id": current_id + 1}}
        question_ids.update_one({"id": current_id}, newvalues)
        return current_id + 1


def add_question(a_db_instance, a_dictionary, username):
    questions = a_db_instance["questions"]
    new_id = increment_question_id(a_db_instance)
    toinsert = {"id": new_id, "username": username, "title": a_dictionary["title"],
                "description": a_dictionary["description"],
                "method": a_dictionary["method"], "answers": a_dictionary["answers"], "imgurl": a_dictionary["imgurl"]}
    questions.insert_one(toinsert)
    return new_id


def get_all_questions(db):
    questions = db["questions"]
    qs = questions.find()
    all_questions = []
    for q in qs:
        all_questions.append(q)
    print(all_questions)
    return all_questions
