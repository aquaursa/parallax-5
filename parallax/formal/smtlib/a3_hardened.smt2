; benchmark generated from python API
(set-info :status unknown)
(declare-fun expected () Int)
(declare-fun recovered () Int)
(assert
 (> expected 0))
(assert
 (and (distinct recovered 0) true))
(assert
 (= recovered expected))
(assert
 (let (($x83 (= recovered 0)))
 (or $x83 (and (distinct recovered expected) true))))
(check-sat)
