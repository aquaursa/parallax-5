; benchmark generated from python API
(set-info :status unknown)
(declare-fun pre_shares () Int)
(declare-fun pre_assets () Int)
(declare-fun deposit () Int)
(declare-fun post_shares () Int)
(declare-fun post_assets () Int)
(assert
 (>= pre_shares 0))
(assert
 (>= pre_assets 0))
(assert
 (> deposit 0))
(assert
 (>= post_shares 0))
(assert
 (>= post_assets 0))
(assert
 (= post_assets (+ pre_assets deposit)))
(assert
 (let (($x50 (= post_shares (+ pre_shares (div (* deposit pre_shares) pre_assets)))))
 (let (($x36 (= pre_shares 0)))
 (ite $x36 (and (> deposit 1000000) (= post_shares deposit)) $x50))))
(assert
 (let (($x63 (>= pre_shares 1000)))
 (let (($x59 (> pre_assets 0)))
 (=> $x59 $x63))))
(assert
 (let (($x59 (> pre_assets 0)))
 (=> (> pre_shares 0) $x59)))
(assert
 (or (and (> post_assets 0) (< post_shares 1000)) (and (> post_shares 0) (<= post_assets 0))))
(check-sat)
