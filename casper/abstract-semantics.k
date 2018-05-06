module ABSTRACT-SEMANTICS
  imports EVM
  // to avoid unnecessary case analyses
  rule <k> LT W0 W1 => bool2Word(W0  <Int W1) ~> #push ... </k> [trusted]

  rule <k> GT W0 W1 => bool2Word(W0  >Int W1) ~> #push ... </k> [trusted]

  rule <k> EQ W0 W1 => bool2Word(W0 ==Int W1) ~> #push ... </k> [trusted]

  rule <k> ISZERO W => bool2Word(W  ==Int 0 ) ~> #push ... </k> [trusted]

  rule <k> #gasExec(SCHED, EXP W0 W1) => Gexp < SCHED > +Int (Gexpbyte < SCHED > *Int 32) ~> #deductGas ... </k>
    requires W1 =/=K 0 [trusted]

  rule <k> #gasExec(SCHED, SSTORE INDEX VALUE) => Gsstoreset < SCHED > ~> #deductGas ... </k> [trusted]

  rule <k> Ccallgas(SCHED, ISEMPTY:Bool, GCAP, GAVAIL, 0) => Cgascap(SCHED, GCAP, GAVAIL, Cextra(SCHED, ISEMPTY, 0)) ... </k> [trusted]

  rule <k> Ccallgas(SCHED, ISEMPTY:Bool, GCAP, GAVAIL, VALUE)
          => Cgascap(SCHED, GCAP, GAVAIL, Cextra(SCHED, ISEMPTY, VALUE)) +Int Gcallstipend < SCHED > ... </k>
    requires VALUE =/=Int 0 [trusted]

endmodule
