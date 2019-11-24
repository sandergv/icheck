#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

SCRIPT="$DIR/internet-checker.py"

#python3 "SCRIPT" $@

echo "#!/bin/bash

python3 $SCRIPT \$@
" > icheck