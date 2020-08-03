from __future__ import annotations
from random import shuffle
from copy import deepcopy
from .data import utcnow
def check_validity(original_list, results, candidate):
    for i,j in zip(original_list, candidate):
        if i==j:
            return False
    
    for r in results:
        for i,j in zip(r, candidate):
            if i==j:
                return False

    return True


def pair_reviewers(user_ids, for_each:int): #TODO for_each too big
    results = []
    if len(user_ids)-1<for_each:
        for_each= len(user_ids)-1
    while len(results)<for_each:
        list_copy = deepcopy(user_ids)

        shuffle(list_copy)
        while not check_validity(user_ids, results, list_copy):
            shuffle(list_copy)
        results.append(list_copy)
        
    return results




if __name__ == "__main__":
    from random import randint
    from timeit import default_timer as timer
    students = []
    while len(students)<30:
        r = randint(1, 100)
        if r not in students:
            students.append(r)

    
    start = timer()
    r= pair_reviewers(students, 5)
    end = timer()