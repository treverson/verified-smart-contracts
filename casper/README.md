# Part I: Formal Verification of Casper Smart Contract

We present the formal verification of the Casper FFG smart contract.


## Scope

The verification target is the Casper contract implementation `simple_casper.v.py`, a critical component of the entire Casper FFG protocol. Specifically, we consider the version [b2a1189].


The Casper FFG protocol is described in the paper "[Casper the Friendly Finality Gadget]", and its implementation consists of the following two main components:

- The smart contract: It provides the important functionality of the protocol, that is, the registration and withdrawal of validators, the vote and slash functions, maintaining the protocol state (i.e., the current dynasty and epoch number, vote status for each epoch, and the current status of validators), and the reward/penalty computation. Most of the protocol logic is implemented in this contract to minimize the burden of the additional network node support.

- The network node support: It provides certain network-level functionality of the protocol that is hard to be implemented in the contract, e.g., delaying the contract, initializing epochs, and fork choice rule. The details are described in [EIP 1011].


While the correctness of the protocol requires the correctness of both the smart contract and the network node support, the goal of this verification effort is limited to verify the full functional correctness of the smart contract, assuming the correctness of the network node support.

We also note that formal reasoning about the protocol itself is not part of the contract verification, but part of the [protocol verification], which is a separate companion effort by another team.


## Formal Specification of Casper Contract

Following our formal verification methodology, we specified the high-level business logic specification of the contract, and refined it to the EVM-level specification against which we formally verified the contract bytecode using our KEVM verifier.

First, we specified [ABSTRACT-CASPER], the abstract high-level business logic specification of the Casper contract. The purpose of the high-level specification is to formalize the abstract behavior of the contract, which can be used as a communication interface between different parties: the contract verification team, the protocol verification team, and the contract developers. The developers are supposed to confirm that this specification captures all of the intended behaviors. The [protocol verification] uses this specification to formalize and verify the entire protocol. We also formalized the [reward-penalty model].

Then, we refined [ABSTRACT-CASPER] to [CASPER], the concrete functional specification of the Casper contract. While both are high-level specifications, [CASPER] is much closer to the actual behavior of the contract. For example, [ABSTRACT-CASPER] simplifies the reward/penalty computation mechanism, where it computes the reward and/or penalty of all validators at the end of each epoch. However, [CASPER] specifies the actual mechanism implemented in the contract, where the reward/penalty is incrementally computed every time a validator votes.

Finally, we refined [CASPER] to [CASPER-EVM], the EVM-level specification of the contract bytecode. [CASPER-EVM] specifies the additional details of the compiled EVM bytecode: the gas consumption, the storage layout, the arithmetic overflow, the fixed-point number arithmetic, the decimal rounding errors, and other EVM quicks.


## Formal Verification Results: Current Progress and Findings

We provide the current results of the formal verification.


### Current Progress

We compiled the contract source code using the Vyper compiler, and verified the compiled EVM bytecode using the KEVM verifier against the functional correctness specification [CASPER-EVM].

Currently, the following functions are verified:

- Constant functions:
  - `main_hash_voted_frac`
  - `deposit_size`
  - `total_curdyn_deposits_scaled`
  - `total_prevdyn_deposits_scaled`
  - `recommended_source_epoch`
  - `recommended_target_hash`
  - `deposit_exists`

- Private functions:
  - `increment_dynasty`
  - `esf`
  - `collective_reward`
  - `insta_finalize`

- Public functions:
  - `logout`
  - `delete_validator`
  - `proc_reward`
  - `vote`


The verification of the following functions is in progress (but now suspended due to the [deprecated Casper FFG]):

- `sqrt_of_total_deposits`
- `initialize_epoch`
- `deposit`
- `withdraw`
- `slash`


#### Assumption

The formal verification results presented here assumes the following conditions:

- the correctness of the network node support
- the correctness of the low-level [signature validation code]
- the soundness of the refinement between [ABSTRACT-CASPER], [CASPER], and [CASPER-EVM]
- the completeness of the high-level specification: [ABSTRACT-CASPER] and [reward-penalty model]
- the correctness of the domain reasoning [lemmas]

We have not formally verified the above assumptions due to time constraints.


### Our Findings


#### Bugs found

We found several bugs in the contract source code in the course of the verification, which have been fixed by the developers. Refer to the following Github issue pages for more details.

- https://github.com/ethereum/casper/issues/57
- https://github.com/ethereum/casper/issues/67
- https://github.com/ethereum/casper/issues/74
- https://github.com/ethereum/casper/issues/75
- https://github.com/ethereum/casper/issues/83

As a (good) side-effect of the Casper contract verification, we also found several issues in the Vyper compiler that resulted in generating an incorrect bytecode from the contract. These issues have been fixed by the Vyper compiler team. Refer to the following for more details.

- https://github.com/ethereum/vyper/issues/767
- https://github.com/ethereum/vyper/issues/768
- https://github.com/ethereum/vyper/issues/775


#### Concerns

We reported several concerns regarding the overall protocol, and the Casper team confirmed that they are intended.

1. We are concerned that the identity (i.e., either the index or the signature-checker) of a validator could be different across multiple chains, which may be exploitable.

   However, we were answered that:
   > It is OK because a validator has to wait two dynasties (two finalized blocks) to join a validator set, then the case in which he has two different identities for the same ether deposit would mean that there were two different finalized blocks (competing forks) and some previous validators were slashed. In such a case, the community is expected to either choose a chain to rally behind or simply both chains continue to exist (like eth/eth-classic) in which the people not at fault continue to have funds on both.


1. We are concerned that the contract executes the arbitrary external signature validation code provided by validators. Although the external code is checked by the [purity checker], we are still concerned about its security unless we formally verify the [purity checker] is complete (i.e., rejecting all possible malicious behaviors including the reentrancy).

   However, we were answered that:
   > The external validation code is inevitable to allow various different signature schemes to be used by different validators. So, there is a trade-off between security vs flexibility.


1. We are concerned that the accountable safety of the protocol can be violated after many epochs without finalization (e.g., in the "network split" case).

   However, we were answered that:
   > It may be assumed that the maximum ESF (epochs since finalization) is sufficiently bound according to the reward-penalty model parameter values.




# Part II: Formal Verification of Casper Protocol

This document describes the protocol verification effort for the Casper smart contract in the proof assistants Coq and Isabelle/HOL. The effort was initially made in concert with lower-level verification in the K Framework of smart contract code written in the Vyper language.

## Background

Our (unfinished) model of the Casper contract behavior is an adaptation of a general model, called Toychain, of a blockchain distributed system in Coq, originally written by Pirlea and Sergey and described in a 2017 paper in the conference on Certified Proofs and Programs (CPP). The advantage of using this model is that it captures the concept of forks in a tree of blocks (different choices of canonical blockchain), which is necessary to fully specify what Casper is supposed to accomplish.

- Paper: <http://ilyasergey.net/papers/toychain-cpp18.pdf>
- GitHub repository: <https://github.com/certichain/toychain>

We only used some of the core components from Toychain:

- datatypes for blocks of transactions, blockchains, and block forest, and accompanying functions and lemmas (e.g., block validation)

- datatypes and functions for (abstract) network node state

- message processing functions and node/network behavior semantics

Among other things, we removed messages exchanged between nodes that are irrelevant to Casper, and many Toychain lemmas (theory) with no bearing on Casper correctness.

We were also basing our work on Yoichi Hirai's abstract Casper protocol model in Isabelle/HOL that verified accountable safety (earlier, less complete models also verified plausible liveness).

## Original plan of work

We planned to verify the Casper contract by working from both ends of the spectrum of abstraction:

1. connecting (instantiating) Yoichi Hirai's most detailed abstract protocol model in Isabelle/HOL to the Coq blockchain model

2. capturing Daejun Park's abstraction in K of the Casper contract code written in Vyper (<https://github.com/runtimeverification/verified-smart-contracts/blob/casper/casper/abstract-casper.k>)

The rationale was that if Yoichi's proofs capture the informal results in Vitalik's paper (<https://arxiv.org/abs/1710.09437>), and there is a direct, mostly formal, connection between the high-level abstract protocol model down to Vyper code via Coq and Daejun's K abstraction, the protocol and its implementation is adequately verified. 

Yoichi was primarily using Isabelle/HOL, transferring key blockchain definitions from Coq to instantiate his high-level protocol abstraction, while Karl Palmskog and Lucas Pena were encoding Daejun's Casper K abstraction in Coq.

## Current state of work

The current Casper contract Coq model can be found in the following GitHub repository: <https://github.com/palmskog/caspertoychain>

The following Isabelle/HOL tasks were finished by Yoichi:

- basic "smoke test" of instantiation of environments in Isabelle/HOL

- basic instantiation of blockchain definitions in Coq for the abstract Casper model

We do not currently have access to Yoichi's Isabelle/HOL code instantiating the blockchain definitions.

The following Isabelle/HOL tasks were in progress but are unfinished:

- formal proof of plausible liveness for the most up-to-date and detailed model of Casper behavior

- transfer/translation of definitions and results from the Coq model of Casper

- full instantiation in Isabelle/HOL of all relevant blockchain definitions, including of (low-level) Casper state and behavior, giving end-to-end proofs of accountable safety and plausible liveness

The following Coq tasks were finished by Karl and Lucas:

- encoding of (datatypes for) the Casper contract state, recording, e.g., which validator has voted in an epoch

- encoding of Casper contract transactions (voting, slashing, etc.)

- definition of basic structure for computing the Casper contract state for a network node (processing transactions in a blockchain from the initial Casper state)

- incomplete but executable definitions of functions for updating the Casper contract state when receiving new transactions/messages, and accompanying lemmas that describe more abstractly how the state can change

Coq tasks that were in progress but are unfinished:

- axiomatization of operations related to rewards for validators (and slashing of their Ether contributions/deposits when they misbehave)

- complete definition of Casper contract behavior as Coq functions and accompanying characterizing lemmas for those functions

- instantiation of reward/slashing operations and datatype with something realistic, such as fixed-decimal numbers

- establishment of a connection between the Coq model and the K abstraction, e.g., through differential testing of particular contract state instances

- transfer/translation of accountable safety and plausible liveness from the Isabelle/HOL protocol model






[b2a1189]: <https://github.com/ethereum/casper/blob/b2a1189506710c37bbdbbf3dc79ff383dbe13875/casper/contracts/simple_casper.v.py>
[Casper the Friendly Finality Gadget]: <https://arxiv.org/abs/1710.09437>
[ABSTRACT-CASPER]: <https://github.com/runtimeverification/verified-smart-contracts/blob/master/casper/abstract-casper.k>
[EIP 1011]: <https://eips.ethereum.org/EIPS/eip-1011>
[protocol verification]: <https://github.com/palmskog/caspertoychain>
[CASPER]: <https://github.com/runtimeverification/verified-smart-contracts/blob/master/casper/casper.k>
[CASPER-EVM]: <https://github.com/runtimeverification/verified-smart-contracts/blob/master/casper/casper-spec.ini>
[reward-penalty model]: <https://github.com/runtimeverification/verified-smart-contracts/blob/master/casper/reward-penalty-model.pdf>
[lemmas]: <https://github.com/runtimeverification/verified-smart-contracts/blob/master/casper/verification.k>
[signature validation code]: <https://github.com/ethereum/casper/blob/b2a1189506710c37bbdbbf3dc79ff383dbe13875/casper/contracts/simple_casper.v.py#L391-L403>
[purity checker]: <https://github.com/ethereum/casper/blob/master/casper/contracts/purity_checker.py>
[deprecated Casper FFG]: <https://medium.com/@djrtwo/casper-%EF%B8%8F-sharding-28a90077f121>
