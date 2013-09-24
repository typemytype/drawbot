# let's introduce 'lists' (or 'arrays' as
# they are called in some other languages)
alist = [1, -2, "asdsd", 4, 50]
print alist
alist.append(1234)
print alist
# fetching an item from the list:
print alist[0]  # the first item
print alist[1]  # the second
# negative numbers start from the end:
print alist[-1]  # the last item
print alist[-2]  # the one before last

print "nested lists:"
print [1, 2, 3, ["a", "b", "c"]]
print [1, 2, 3, ["a", ["deeper"]]]

# assigning a list to another name does
# not make a copy: you just create another
# reference to the same object
anotherlist = alist
anotherlist.append(-9999)
print anotherlist
print alist
acopy = list(alist)
acopy.append(9999)
print acopy
print alist

# strings are also sequences:
astring = "abcdefg"
print astring[2]
print astring[-1]  # from the end

print "getting 'slices' from a list:"
print alist
print alist[2:5]


print "there's a nice builtin function that"
print "creates a list of numbers:"
print range(10)  # from 0 to 10 (not incl. 10!)
print range(5, 10)  # from 5 to 10 (not incl. 10!)
print range(1, 19, 3) # from 1 to 19 in steps of 3

print "let's loop over this list:"
print alist
for item in alist:
    # this is the body of the "for" loop
    print item
    # more lines following can follow
    # you need to indent consistently,
    # this would not work:
#        print "hello"
    # also: use the tab key to manually
    # indent. There are shortcuts to indent
    # or dedent blocks of code: cmd-[ and cmd-]

print "loop over some numbers:"
for item in range(10):
    print item

print "loop over some numbers, doing 'math':"
for i in range(10):
    print i, i * 0.5

print "nested loops:"
for x in range(1, 5):  # outer loop
    print "---"
    for y in range(x, x + 5):  # inner loop
        print x, "*", y, "=", x * y

print "three loops:"
for x in range(2):
    for y in range(2):
        for z in range(2):
            print x, y, z

print "three loops with a counter:"
count = 1
for x in range(2):
    for y in range(2):
        for z in range(2):
            print x, y, z, "count =", count
            count = count + 1
            # alternate spelling:
            #count += 1
