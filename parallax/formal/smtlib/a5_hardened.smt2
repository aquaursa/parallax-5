; benchmark generated from python API
(set-info :status unknown)
(declare-fun block_time () Int)
(declare-fun oracle_updated () Int)
(assert
 (>= block_time 0))
(assert
 (>= oracle_updated 0))
(assert
 (<= block_time (+ oracle_updated 1800)))
(assert
 (> (- block_time oracle_updated) 86400))
(check-sat)
