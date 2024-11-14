from example import add

def test_add_1():
    assert add(2, 3) == 5

def test_add_2():
    assert add(5, 9) == 14

def test_add_3():
    assert add(7, 3) == 10

#def test_add_4():  # this doesn't work
#    assert add(1, 2) == 4