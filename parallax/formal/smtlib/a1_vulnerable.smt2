; benchmark generated from python API
(set-info :status unknown)
(declare-fun attacker_dep () Int)
(declare-fun donation () Int)
(declare-fun victim_dep () Int)
(declare-fun pool_after_attacker () Int)
(declare-fun pool_after_donation () Int)
(declare-fun victim_shares () Int)
(assert
 (= attacker_dep 1))
(assert
 (> donation 0))
(assert
 (> victim_dep 0))
(assert
 (= pool_after_attacker 1))
(assert
 (= pool_after_donation (+ 1 donation)))
(assert
 (= victim_shares (div (* victim_dep 1) pool_after_donation)))
(assert
 (= victim_shares 0))
(check-sat)
