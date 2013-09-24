print 'this is a so called "string"'
print "this is a so called 'string'"
print "this is a so called \"string\""


print "one string " + "another string"

a = "one string"
b = "another string"

print a + " " + b

print "many " * 10

print "non-ascii should generally work:"
print "Åbenrå © Ђ ק"

print "and now an error:"
print "many " * 10.0
# string multiplication really wants an
# integer number; a float that happens to
# be a whole number is not good enough

