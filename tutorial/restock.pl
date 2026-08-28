/*  A complete program: fill the orders in a file, print the report, and
    exit with a status that says whether it worked.

        ./prolog -q tutorial/restock.pl

    Run it from the top of the source tree. This interpreter has no argv
    flag, so the two file names are written here rather than taken from
    the command line.
*/

:- ['tutorial/level4'].

:- initialization(main).

orders_file('tutorial/orders.txt').
report_file('/tmp/stock-report.txt').

main :-
    orders_file(Orders),
    report_file(Report),
    catch(( load_orders(Orders),
            save_report(Report),
            report,
            format("~nwritten to ~w~n", [Report])
          ),
          Error,
          ( print_message(error, Error), halt(1) )),
    halt.
