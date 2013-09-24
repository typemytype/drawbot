a = 12
b = 15
c = a * b
CAP = "a string"

print c

print CAP

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
print x, X

y = 102
# so this is an error:
print Y
