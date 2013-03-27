#!/usr/bin/env bash

# "__import__", don't know if its needed

# "abs", In spanish *abs*oluto, I think doesn't need translation

# "any" -> "alguno"
# if [ $1 == "any" ]; then
#     echo si
# fi

test='_'
if [ $# == 1 ]
then
    test=$1
fi

make clean

en="any"
es="alguno"

if [ $test == '_' -o $test == $en ]
then
    echo "Translating $en to $es"
    sed -i 's/"\<'$en'\>"/"'$es'"/g' Python/bltinmodule.c
    find . -name "*.py" -exec sed -i 's/\<'$en'\>(/'$es'(/g' '{}' \;
    sed -i 's/\<'$en'\>/'$es'/g' Lib/test/test_builtin.py
    sed -i 's/\<'$en'\>/'$es'/g' Lib/test/test_logging.py
    sed -i 's/"\<'$en'\>"/"'$es'"/g' Lib/lib2to3/fixer_util.py
    sed -i "s/'\<"$en"\>'/'"$es"'/g" Lib/lib2to3/fixer_util.py
fi

# "all" -> "todos"
en="all"
es="todos"

if [ $test == '_' -o $test == $en ]
then
    echo "Translating $en to $es"
    sed -i 's/"\<'$en'\>"/"'$es'"/g' Python/bltinmodule.c
    find . -name "*.py" -exec sed -i "s/\<$en\>(/$es(/g" '{}' \;
    sed -i 's/\<'$en'\>/'$es'/g' Lib/test/test_builtin.py
    sed -i 's/\<'$en'\>/'$es'/g' Lib/inspect.py
    sed -i 's/"\<'$en'\>"/"'$es'"/g' Lib/lib2to3/fixer_util.py
    sed -i "s/'\<"$en"\>'/'"$es"'/g" Lib/lib2to3/fixer_util.py
fi

# "ascii", it's not a word

# "bin", In spanish *bin*ario, I think doesn't need translation

# "callable" -> invocable
# en="callable"
# es="invocable"
# make clean
# sed -i 's/"\<'$en'\>"/"'$es'"/g' Python/bltinmodule.c
# find . -name "*.py" -exec sed -i "s/\<$en\>(/$es(/g" '{}' \;
# sed -i 's/\<'$en'\>/'$es'/g' Lib/test/test_builtin.py
# sed -i 's/\<'$en'\>/'$es'/g' Lib/inspect.py
# sed -i 's/"\<'$en'\>"/"'$es'"/g' Lib/lib2to3/fixer_util.py
# sed -i "s/'\<"$en"\>'/'"$es"'/g" Lib/lib2to3/fixer_util.py

# "chr",
# "compile",
# "delattr",
# "dir",
# "divmod",
# "eval",
# "exec",
# "format",
# "getattr",
# "globals",
# "hasattr",
# "hash",
# "hex",
# "id",
# "input",
# "isinstance"
# "issubclass"
# "iter",
# "len",
# "locals",
# "max",
# "min",
# "next",
# "oct",
# "ord",
# "pow",
# "print",
# "repr",
# "round",
# "setattr",
# "sorted",
# "sum",
# "vars",

# build and test
./configure --with-pydebug
make -j5

./python -m test -j5


# "Test translated Python's builtins"
en="any"
es="alguno"

if [ $test == '_' -o $test == $en ]
then
    output=`./python -c 'print(True == '$es'([0,1]) and "OK")'`
    if [ $output != "OK" ];
    then
	echo "FAIL on $en -> $es"
	exit 0
    fi
fi

en="all"
es="todos"

if [ $test == '_' -o $test == $en ]
then
    output=`./python -c 'print(True == '$es'([1,1]) and "OK")'`
    if [ $output != "OK" ];
    then
	echo "FAIL on $en -> $es"
	exit 0
    fi
fi
