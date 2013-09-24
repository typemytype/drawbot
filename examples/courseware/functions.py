# defining a function:
def myfunction():
    print "hello!"

# calling the function:
myfunction()

# a common error
# not calling the function:
myfunction   # note missing ()


# defining a function that takes an
# 'argument' (or 'parameter')
def mysecondfunction(x, y):
    print "hello!", x, y

# calling the function with 2 arguments
mysecondfunction(123, 456)


def add2numbers(x, y):
    # you can see 'global' vars
    print aglobalvariable
    result = x + y
    return result

aglobalvariable = "hi!"
thereturnedvalue = add2numbers(1, 2)
print thereturnedvalue
# 'result' was a local name inside
# add2number, so it is not visible at the
# top level. So the next line would cause
# an error:
#print result


def anotherfunc(x, y):
    # calling add2numbers function:
    return add2numbers(x, y)

print anotherfunc(1, 2)
