# comparisons

# let's define some variables
a = 12
b = 20
print "a =", a, "and b =", b

print "are a and b equal?"
print a == b

print "are a and b not equal?"
print a != b

print "is a greater than b?"
print a > b

print "is a less than b?"
print a < b

print "is a greater than or equal to b?"
print a >= b

print "is a less than or equal to b?"
print a <= b

result = a < b
print "result is:", result

print "these are the 'boolean' values:"
print "the True value:", True
print "the False value:", False

if a < b:
    print "a is less than b"

if a > b:
    print "a is greater than b"

print "if/else"
if a < b:
    print "A"
else:
    print "B"

print "if/elif/else"
if a > b:
    print "A"
elif a == 12:
    print "B"
else:
    print "C"

print "if/elif/elif/.../else"
if a > b:
    print "A"
elif a == 10:
    print "B 10"
elif a == 11:
    print "B 11"
elif a == 12:
    print "B 12"
elif a == 13:
    print "B 13"
else:
    print "C"


# boolean logic
if a > 15 and b > 15:
    print "both a and b are greater than 15"
else:
    print "either one of a and b is NOT greater than 15"

if a > 15 or b > 15:
    print "a OR b are greater than 15"
else:
    print "neither a or b ate greater than 15"

print "a result:", a > 15 or b > 15

# inversing a truth value:
print "not True:", not True
print "not False:", not False
print "not not False:", not not False
print "not not not False:", not not not False

# grouping subexpressions by using parentheses:
if (a > b and b == 13) or b == 25:
    print "..."
if a > b and (b == 13 or b == 25):
    print "..."
# parentheses nest:
#if a > b and (b == 13 or (b == 25 and a == 12)):
#   ...
