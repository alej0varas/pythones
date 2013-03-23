sed -i 's/"\<any\>"/"alguno"/g' Python/bltinmodule.c
find . -name "*.py" -exec sed -i "s/\<any\>(/alguno(/g" '{}' \;
sed -i "s/\<any\>/alguno/g" Lib/test/test_builtin.py 
sed -i "s/\<any\>/alguno/g" Lib/test/test_logging.py 
sed -i 's/"\<any\>"/"alguno"/g' Lib/lib2to3/fixer_util.py 
sed -i "s/'\<any\>'/'alguno'/g" Lib/lib2to3/fixer_util.py 
./configure --with-pydebug
make -j5
./python -m test -j5
./python -c "print(alguno([0,1]))"
