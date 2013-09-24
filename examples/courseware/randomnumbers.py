# the random() function returns a pseudo-
# random number between zero and one
print "a random number between 0.0 and 1.0:"
print random()

# the randint() function returns a pseudo-
# random integer number in the range you
# specify.
print "a random integer between 0 and 4:"
print randint(0, 4)
print "a random integer between 10 and 20:"
print randint(10, 20)

# use a random number to do different
# things.
print "choose randomly between A and B, 6 times:"
for i in range(6):
    if random() > 0.5:
        print "A"
    else:
        print "B"
