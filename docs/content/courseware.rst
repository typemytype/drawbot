Courseware
==========

Teaching with DrawBot
---------------------

Python is a great language for introducing the basic concepts of programming to entry level students. There are many tutorials and introduction packages available for the language (see the `overview on the python site`_).

DrawBot combines the easy to learn Python with a compact but powerful application in which code, result and feedback are visible at a glance. This section collects scripts and advice on how to specifically use DrawBot in a programming course.
Step by step

Each of the scripts on this page focus on a particular section of Python. Click on the link and copy the text of the script to a new DrawBot window. Read the comments (the lines starting with a #) for clues and help.

.. _overview on the python site: http://www.python.org/about/gettingstarted/

Basic math
----------

How do numbers look in Python? how to write simple sums, multiplication, substrations etc.

.. downloadcode:: basicmath.py

    # this is a comment

    print("some basic numbers:")
    print(12)  # this is an integer number
    print(12.5)  # this is a floating point

    print("results of adding:")
    print(12 + 13)  # results in an integer
    print(12 + 0.5)  # results in a float
    print(0.5 + 12)  # ditto

    print("results of subtracting:")
    print(12 - 8)
    print(12 - 25)

    print("results of multiplication:")
    print(12 * 8)
    print(12 * -25)

    print("results of dividing:")
    print(12 / 2)
    print(11 / 2)
    print(11 // 2)  # integer division
    print(11 % 2)   # modulo

    print("results of 'the power of':")
    print(2 ** 8)
    print(10 ** 2)
    print(2 ** 0.5)

    print("let's cause an error:")
    print(1 / 0)

Strings
-------

Strings contain text, a sequence of letters like beads on a string. This script shows what strings can do.

.. downloadcode:: strings.py

    print('this is a so called "string"')
    print("this is a so called 'string'")
    print("this is a so called \"string\"")

    print("one string " + "another string")

    a = "one string"
    b = "another string"

    print(a + " " + b)

    print("many " * 10)


    print("non-ascii should generally work:")
    print("Åbenrå © Ђ ק")
    print("and now an error:")
    print("many " * 10.0)
    # string multiplication really wants an
    # integer number; a float that happens to
    # be a whole number is not good enough

Variables
---------

Variables are similar to storage boxes, they need to have a name and contain something. This script shows how to name variables in Python, and some neat tricks they can perform.

.. downloadcode:: variables.py

    a = 12
    b = 15
    c = a * b
    CAP = "a string"

    print(c)

    print(CAP)

    # variable names cannot start with a
    # number:
    #1a = 12

    # variable names can contain numbers,
    # just not at the start:
    a1 = 12

    # underscores are allowed:
    _a = 12
    a_ = 13

    #   a-z  A-Z  0-9  _

    # everything is an object
    # this "rebinds" the name 'a' to a new
    # object:
    a = a + 12

    # variable names are case sensitive
    # meaning that:
    x = 12
    # is a different variable from
    X = 13
    print(x)
    print(X)

    y = 102
    # so this is an error:
    print(Y)

Lists and loops
---------------

Lists are sequences of things, like a string is a sequence of letters. But lists can contain things like numbers, variables and other lists. Loops are uses to jump through a list and look at
each one of the items. Loops are a powerful and fast way to work with lots of items.

.. downloadcode:: listsloops.py

    # let's introduce 'lists' (or 'arrays' as
    # they are called in some other languages)
    alist = [1, -2, "asdsd", 4, 50]
    print(alist)
    alist.append(1234)
    print(alist)   
    # fetching an item from the list:
    print(alist[0])  # the first item
    print(alist[1])  # the second
    # negative numbers start from the end:
    print(alist[-1])  # the last item
    print(alist[-2])  # the one before last

    print("nested lists:")
    print([1, 2, 3, ["a", "b", "c"]])
    print([1, 2, 3, ["a", ["deeper"]]])

    # assigning a list to another name does
    # not make a copy: you just create another
    # reference to the same object
    anotherlist = alist
    anotherlist.append(-9999)
    print(anotherlist)
    print(alist)
    acopy = list(alist)
    acopy.append(9999)
    print(acopy)
    print(alist)

    # strings are also sequences:
    astring = "abcdefg"
    print(astring[2])
    print(astring[-1])  # from the end

    print("getting 'slices' from a list:")
    print(alist)
    print(alist[2:5])


    print("there's a nice builtin function that")
    print("creates a list of numbers:")
    print(range(10))  # from 0 to 10 (not incl. 10!)
    print(range(5, 10))  # from 5 to 10 (not incl. 10!)
    print(range(1, 19, 3)) # from 1 to 19 in steps of 3

    print("let's loop over this list:")
    print(alist)
    for item in alist:
        # this is the body of the "for" loop
        print(item)
        # more lines following can follow
        # you need to indent consistently,
        # this would not work:
    #        print("hello")
        # also: use the tab key to manually
        # indent. There are shortcuts to indent
        # or dedent blocks of code: cmd-[ and cmd-]

    print("loop over some numbers:")
    for item in range(10):
        print(item)

    print("loop over some numbers, doing 'math':")
    for i in range(10):
        print(i, i * 0.5)

    print("nested loops:")
    for x in range(1, 5):  # outer loop
        print("---")
        for y in range(x, x + 5):  # inner loop
            print(x, y, x * y)

    print("three loops:")
    for x in range(2):
        for y in range(2):
            for z in range(2):
                print(x, y, z)

    print("three loops with a counter:")
    count = 1
    for x in range(2):
        for y in range(2):
            for z in range(2):
                print(x, y, z, count)
                count = count + 1
                # alternate spelling:
                #count += 1

Functions
---------

Functions are small programs with the program. Rather than write something over and over again, you can write a function and recycle the code in different parts of your program.

.. downloadcode:: functions.py

    # defining a function:
    def myfunction():
        print("hello!")

    # calling the function:
    myfunction()

    # a common error
    # not calling the function:
    myfunction   # note missing ()


    # defining a function that takes an
    # 'argument' (or 'parameter')
    def mysecondfunction(x, y):
        print("hello!")
        print(x, y)

    # calling the function with 2 arguments
    mysecondfunction(123, 456)


    def add2numbers(x, y):
        # you can see 'global' vars
        print(aglobalvariable)
        result = x + y
        return result

    aglobalvariable = "hi!"
    thereturnedvalue = add2numbers(1, 2)
    print(thereturnedvalue)
    # 'result' was a local name inside
    # add2number, so it is not visible at the
    # top level. So the next line would cause
    # an error:
    #print(result)


    def anotherfunc(x, y):
        # calling add2numbers function:
        return add2numbers(x, y)

    print(anotherfunc(1, 2))

Conditions
----------

Sometimes your program needs to respond to particular values or situations. If this value is 4, then go there. If it isn't, just go on.

.. downloadcode:: conditions.py

    # comparisons

    # let's define some variables
    a = 12
    b = 20
    print(a, b)

    print("are a and b equal?")
    print(a == b)

    print("are a and b not equal?")
    print(a != b)

    print("is a greater than b?")
    print(a > b)

    print("is a less than b?")
    print(a < b)

    print("is a greater than or equal to b?")
    print(a >= b)

    print("is a less than or equal to b?")
    print(a <= b)

    result = a < b
    print("result is:")
    print(result)

    print("these are the 'boolean' values:")
    print("the True value:")
    print(True)
    print("the False value:")
    print(False)

    if a < b:
        print("a is less than b")

    if a > b:
        print("a is greater than b")

    print("if/else")
    if a < b:
        print("A")
    else:
        print("B")

    print("if/elif/else")
    if a > b:
        print("A")
    elif a == 12:
        print("B")
    else:
        print("C")

    print("if/elif/elif/.../else")
    if a > b:
        print("A")
    elif a == 10:
        print("B 10")
    elif a == 11:
        print("B 11")
    elif a == 12:
        print("B 12")
    elif a == 13:
        print("B 13")
    else:
        print("C")

    # boolean logic
    if a > 15 and b > 15:
        print("both a and b are greater than 15")
    else:
        print("either one of a and b is NOT greater than 15")

    if a > 15 or b > 15:
        print("a OR b are greater than 15")
    else:
        print("neither a or b ate greater than 15")

    print("a result:")
    print(a > 15 or b > 15)

    # inversing a truth value:
    print("not True:"
    print(not True)
    print("not False:")
    print(not False)
    print("not not False:"
    print(not not False)
    print("not not not False:")
    print(not not not False)

    # grouping subexpressions by using parentheses:
    if (a > b and b == 13) or b == 25:
        print("...")
    if a > b and (b == 13 or b == 25):
        print("...")
    # parentheses nest:
    #if a > b and (b == 13 or (b == 25 and a == 12)):
    #   ...


Random numbers
--------------

Fun things to do with random numbers. The computer is full of them.

.. downloadcode:: randomnumbers.py

    # the random() function returns a pseudo-
    # random number between zero and one
    print("a random number between 0.0 and 1.0:")
    print(random())

    # the randint() function returns a pseudo-
    # random integer number in the range you
    # specify.
    print("a random integer between 0 and 4:")
    print(randint(0, 4))
    print("a random integer between 10 and 20:")
    print(randint(10, 20))

    # use a random number to do different
    # things.
    print("choose randomly between A and B, 6 times:")
    for i in range(6):
        if random() > 0.5:
            print("A")
        else:
            print("B")

Shapes
------

Drawing a couple of the basic shapes. Have a look at the Drawing Primitives pages for a detailed overview of shapes.

.. downloadcode:: shapes.py

    # draw a rectangle
    # rect(x, y, width, height)
    rect(20, 50, 100, 200)

    rect(130, 50, 100, 200)

    oval(240, 50, 100, 200)

    oval(20, 250, 100, 100)

    oval(130, 250, 100, 100)

    rect(240, 250, 100, 100)

    for x in range(20, 300, 50):
        rect(x, 370, 40, 40)

    for x in range(20, 300, 50):
        if random() > 0.5:
            rect(x, 420, 40, 40)
        else:
            oval(x, 420, 40, 40)

Colors
------

Shapes can also be colored. This script shows how work with shapes in colors and transparency values.

.. downloadcode:: colors.py

    # set the current fill color
    # the three numbers are values for
    # red, green and blue (RGB)
    # the values are numbers between
    # 0 and 1
    fill(0, 0, 0.75)

    # draw two rectangles
    rect(50, 50, 150, 250)
    rect(150, 150, 150, 250)

    # set a color
    # note the fourth number: it's the
    # transparency
    fill(1, 0, 0, 0.25)
    rect(250, 250, 150, 250)
    rect(350, 350, 150, 250)
