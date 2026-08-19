# Turns a Prolog source file into a C string constant.
BEGIN {
    print "/* Generated from lib/boot.pl by tools/pl2c.awk -- do not edit. */"
    print "#include \"prolog.h\""
    print ""
    print "const char boot_pl[] ="
}
{
    line = $0
    gsub(/\\/, "\\\\", line)
    gsub(/"/, "\\\"", line)
    printf "\"%s\\n\"\n", line
}
END {
    print ";"
}
