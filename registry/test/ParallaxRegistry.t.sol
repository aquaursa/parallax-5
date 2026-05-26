// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/ParallaxRegistry.sol";

/// @title ParallaxRegistry exhaustive test suite
/// @notice One test per lifecycle transition + revert path + view function.
contract ParallaxRegistryTest is Test {
    ParallaxRegistry registry;

    address issuer       = address(0xA);
    address otherIssuer  = address(0xB);
    address publicCaller = address(0xC);

    bytes32 constant FP1 = bytes32(uint256(0xa880650b924463c61c78c014f4966e554fa59913941e872e036255259a8da86d));
    bytes32 constant FP2 = bytes32(uint256(0x457e9c2838310f53f4ad77620a6c683c60d94b6bfbfcd4e88c162c973efcdaa4));
    bytes32 constant FP3 = bytes32(uint256(0xdf99c02d4ef547b411bb0ad6ccbbd6a733a3c0de2367bcad30780c7715b19993));

    function setUp() public {
        registry = new ParallaxRegistry();
    }

    // ─── issue() ─────────────────────────────────────────────────────────────

    function test_issue_writesRecordAndEmits() public {
        vm.prank(issuer);
        vm.expectEmit(true, true, false, true);
        emit ParallaxRegistry.Issued(FP1, issuer, block.timestamp);
        registry.issue(FP1);

        ParallaxRegistry.Record memory r = registry.getRecord(FP1);
        assertEq(r.registrant, issuer);
        assertEq(uint8(r.state), uint8(ParallaxRegistry.Lifecycle.Issued));
        assertEq(r.issuedAt, block.timestamp);
        assertEq(r.lastUpdated, block.timestamp);
        assertEq(r.supersededBy, bytes32(0));
        assertEq(registry.issuerCertCount(issuer), 1);
        assertEq(registry.totalIssued(), 1);
    }

    function test_issue_revertsOnZeroFingerprint() public {
        vm.prank(issuer);
        vm.expectRevert(ParallaxRegistry.ZeroFingerprint.selector);
        registry.issue(bytes32(0));
    }

    function test_issue_revertsOnDuplicate() public {
        vm.prank(issuer);
        registry.issue(FP1);

        vm.prank(otherIssuer);
        vm.expectRevert(abi.encodeWithSelector(ParallaxRegistry.AlreadyRegistered.selector, FP1));
        registry.issue(FP1);
    }

    function test_issue_isPermissionless() public {
        vm.prank(otherIssuer);
        registry.issue(FP2);
        assertEq(registry.getRecord(FP2).registrant, otherIssuer);
    }

    // ─── publish() ───────────────────────────────────────────────────────────

    function test_publish_transitionsIssuedToPublished() public {
        vm.startPrank(issuer);
        registry.issue(FP1);
        vm.expectEmit(true, true, false, true);
        emit ParallaxRegistry.Published(FP1, issuer, block.timestamp);
        registry.publish(FP1);
        vm.stopPrank();

        assertEq(uint8(registry.getState(FP1)), uint8(ParallaxRegistry.Lifecycle.Published));
    }

    function test_publish_revertsForNonRegistrant() public {
        vm.prank(issuer);
        registry.issue(FP1);

        vm.prank(otherIssuer);
        vm.expectRevert(abi.encodeWithSelector(ParallaxRegistry.NotRegistrant.selector, FP1, otherIssuer));
        registry.publish(FP1);
    }

    function test_publish_revertsForUnregistered() public {
        vm.prank(issuer);
        vm.expectRevert(abi.encodeWithSelector(ParallaxRegistry.NotRegistered.selector, FP1));
        registry.publish(FP1);
    }

    function test_publish_revertsFromTerminalState() public {
        vm.startPrank(issuer);
        registry.issue(FP1);
        registry.publish(FP1);
        registry.revoke(FP1, "test");
        vm.expectRevert(abi.encodeWithSelector(
            ParallaxRegistry.InvalidTransition.selector,
            FP1, ParallaxRegistry.Lifecycle.Revoked, ParallaxRegistry.Lifecycle.Published
        ));
        registry.publish(FP1);
        vm.stopPrank();
    }

    // ─── supersede() ─────────────────────────────────────────────────────────

    function test_supersede_writesSuccessorAndEmits() public {
        vm.startPrank(issuer);
        registry.issue(FP1);
        registry.publish(FP1);
        registry.issue(FP2);

        vm.expectEmit(true, true, true, true);
        emit ParallaxRegistry.Superseded(FP1, FP2, issuer, block.timestamp);
        registry.supersede(FP1, FP2);
        vm.stopPrank();

        ParallaxRegistry.Record memory r = registry.getRecord(FP1);
        assertEq(uint8(r.state), uint8(ParallaxRegistry.Lifecycle.Superseded));
        assertEq(r.supersededBy, FP2);
    }

    function test_supersede_revertsOnSelfSupersession() public {
        vm.startPrank(issuer);
        registry.issue(FP1);
        registry.publish(FP1);
        vm.expectRevert(ParallaxRegistry.SelfSupersession.selector);
        registry.supersede(FP1, FP1);
        vm.stopPrank();
    }

    function test_supersede_revertsIfSuccessorUnregistered() public {
        vm.startPrank(issuer);
        registry.issue(FP1);
        registry.publish(FP1);
        vm.expectRevert(abi.encodeWithSelector(ParallaxRegistry.NotRegistered.selector, FP2));
        registry.supersede(FP1, FP2);
        vm.stopPrank();
    }

    function test_supersede_revertsFromIssuedState() public {
        vm.startPrank(issuer);
        registry.issue(FP1);
        registry.issue(FP2);
        // FP1 is Issued, not Published — cannot supersede yet
        vm.expectRevert(abi.encodeWithSelector(
            ParallaxRegistry.InvalidTransition.selector,
            FP1, ParallaxRegistry.Lifecycle.Issued, ParallaxRegistry.Lifecycle.Superseded
        ));
        registry.supersede(FP1, FP2);
        vm.stopPrank();
    }

    // ─── revoke() ────────────────────────────────────────────────────────────

    function test_revoke_emitsReason() public {
        vm.startPrank(issuer);
        registry.issue(FP1);
        registry.publish(FP1);
        vm.expectEmit(true, true, false, true);
        emit ParallaxRegistry.Revoked(FP1, issuer, "signature key compromise", block.timestamp);
        registry.revoke(FP1, "signature key compromise");
        vm.stopPrank();
        assertEq(uint8(registry.getState(FP1)), uint8(ParallaxRegistry.Lifecycle.Revoked));
    }

    function test_revoke_revertsForNonRegistrant() public {
        vm.startPrank(issuer);
        registry.issue(FP1);
        registry.publish(FP1);
        vm.stopPrank();

        vm.prank(otherIssuer);
        vm.expectRevert(abi.encodeWithSelector(ParallaxRegistry.NotRegistrant.selector, FP1, otherIssuer));
        registry.revoke(FP1, "attempted hijack");
    }

    // ─── expire() ────────────────────────────────────────────────────────────

    function test_expire_isPermissionless() public {
        vm.startPrank(issuer);
        registry.issue(FP1);
        registry.publish(FP1);
        vm.stopPrank();

        // Any party can mark expired
        vm.prank(publicCaller);
        vm.expectEmit(true, false, false, true);
        emit ParallaxRegistry.Expired(FP1, block.timestamp);
        registry.expire(FP1);

        assertEq(uint8(registry.getState(FP1)), uint8(ParallaxRegistry.Lifecycle.Expired));
    }

    function test_expire_revertsIfNotPublished() public {
        vm.prank(issuer);
        registry.issue(FP1);
        // Still Issued, not Published
        vm.prank(publicCaller);
        vm.expectRevert(abi.encodeWithSelector(
            ParallaxRegistry.InvalidTransition.selector,
            FP1, ParallaxRegistry.Lifecycle.Issued, ParallaxRegistry.Lifecycle.Expired
        ));
        registry.expire(FP1);
    }

    // ─── withdraw() ──────────────────────────────────────────────────────────

    function test_withdraw_byRegistrant() public {
        vm.startPrank(issuer);
        registry.issue(FP1);
        registry.publish(FP1);
        vm.expectEmit(true, true, false, true);
        emit ParallaxRegistry.Withdrawn(FP1, issuer, block.timestamp);
        registry.withdraw(FP1);
        vm.stopPrank();
        assertEq(uint8(registry.getState(FP1)), uint8(ParallaxRegistry.Lifecycle.Withdrawn));
    }

    // ─── Terminal state invariance ───────────────────────────────────────────

    function test_terminalStatesAreAbsorbing() public {
        ParallaxRegistry.Lifecycle[4] memory terminals = [
            ParallaxRegistry.Lifecycle.Superseded,
            ParallaxRegistry.Lifecycle.Revoked,
            ParallaxRegistry.Lifecycle.Expired,
            ParallaxRegistry.Lifecycle.Withdrawn
        ];

        for (uint256 i = 0; i < terminals.length; i++) {
            bytes32 fp = bytes32(uint256(0x100 + i));
            bytes32 successor = bytes32(uint256(0x200 + i));

            vm.startPrank(issuer);
            registry.issue(fp);
            registry.publish(fp);
            registry.issue(successor);

            // Move into the terminal state
            if (terminals[i] == ParallaxRegistry.Lifecycle.Superseded) {
                registry.supersede(fp, successor);
            } else if (terminals[i] == ParallaxRegistry.Lifecycle.Revoked) {
                registry.revoke(fp, "test");
            } else if (terminals[i] == ParallaxRegistry.Lifecycle.Expired) {
                vm.stopPrank();
                registry.expire(fp);
                vm.startPrank(issuer);
            } else if (terminals[i] == ParallaxRegistry.Lifecycle.Withdrawn) {
                registry.withdraw(fp);
            }

            // No further transition succeeds
            vm.expectRevert();
            registry.publish(fp);
            vm.expectRevert();
            registry.revoke(fp, "noop");

            vm.stopPrank();
        }
    }

    // ─── View functions ──────────────────────────────────────────────────────

    function test_getState_unregisteredReturnsNone() public view {
        assertEq(uint8(registry.getState(FP1)), uint8(ParallaxRegistry.Lifecycle.None));
    }

    function test_isEffective_trueForIssuedAndPublished() public {
        vm.prank(issuer);
        registry.issue(FP1);
        assertTrue(registry.isEffective(FP1));

        vm.prank(issuer);
        registry.publish(FP1);
        assertTrue(registry.isEffective(FP1));
    }

    function test_isEffective_falseForTerminalStates() public {
        vm.startPrank(issuer);
        registry.issue(FP1);
        registry.publish(FP1);
        registry.revoke(FP1, "no longer valid");
        vm.stopPrank();
        assertFalse(registry.isEffective(FP1));
    }

    function test_issuerCertCount_tracksMultipleIssuances() public {
        vm.startPrank(issuer);
        registry.issue(FP1);
        registry.issue(FP2);
        registry.issue(FP3);
        vm.stopPrank();
        assertEq(registry.issuerCertCount(issuer), 3);
        assertEq(registry.totalIssued(), 3);
    }

    // ─── Fuzz tests ──────────────────────────────────────────────────────────

    function testFuzz_issueAcceptsAnyNonZeroFingerprint(bytes32 fp) public {
        vm.assume(fp != bytes32(0));
        vm.prank(issuer);
        registry.issue(fp);
        assertEq(uint8(registry.getState(fp)), uint8(ParallaxRegistry.Lifecycle.Issued));
    }

    function testFuzz_arbitraryNonRegistrantsCannotPublish(address caller, bytes32 fp) public {
        vm.assume(fp != bytes32(0));
        vm.assume(caller != issuer);

        vm.prank(issuer);
        registry.issue(fp);

        vm.prank(caller);
        vm.expectRevert(abi.encodeWithSelector(ParallaxRegistry.NotRegistrant.selector, fp, caller));
        registry.publish(fp);
    }
}
