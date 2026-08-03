---
id: platform-wallets-payouts
title: Wallets and payouts — bound wallet, changing it, failed payouts, gas
tags: wallet, metamask, rabby, coinbase, walletconnect, bound wallet, payout, payout address, change wallet, otp, gas, fees, custody, base, bnb, monad, kyc, failed payout
---
Roostoo is non-custodial: users sign every transaction from their own EVM wallet
and Roostoo never holds custody of funds. Any EVM-compatible non-custodial wallet
works — MetaMask, Rabby, Coinbase Wallet, or WalletConnect-compatible mobile
wallets. The wallet must be on Base, BNB Chain, or Monad to enroll on that chain
(USDC on Base and Monad; USDT on BNB Chain). Accounts are Google-Auth verified.

BOUND WALLET: the first wallet a user connects becomes their bound wallet, and it
serves both directions — entry fees are debited from it, and Bonus Pool plus
Performance Bonus payouts settle back to it automatically. There is no separate
"payout address" to configure: what you connect with is what you get paid to.

CHANGING IT: wallet changes require OTP verification on the user's email plus a
24-hour confirmation delay before the new wallet activates. Any payouts in flight
during that window settle to the previously bound wallet.

PAYOUT FLOW, via the same audited smart contract that escrowed the entry fees:
competition closes -> contract calculates rankings on net return -> Bonus Pool
distributed per the Distribution Schedule -> Performance Bonuses added for
qualifying Pro/Elite users -> everything settles to bound wallets within 60
minutes.

FAILED PAYOUTS (bridged contract, frozen address, other settlement failure): the
contract holds the payout in a recovery escrow and the user is emailed. The user
has **up to 5 business days** to supply a corrected payout address through the
resolution flow; after that the funds revert to the platform reserve and are no
longer claimable.

GAS: Roostoo pays the gas for payout settlement. Users pay only their wallet-side
gas to confirm the entry transaction (ETH on Base, BNB on BNB Chain, MON on
Monad) plus the entry fee itself in USDC or USDT.
