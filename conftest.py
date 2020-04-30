from application.domain.assignment import Assignment, Task

def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, Assignment) and isinstance(right, Task):
        return ["failed comparing assignments" ,
         "course_id: {left} != {right}".format(left=left.course_id, right=right.course_id)]